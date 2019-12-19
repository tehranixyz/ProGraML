# Copyright 2019 the ProGraML authors.
#
# Contact Chris Cummins <chrisc.101@gmail.com>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains TODO: one line summary.

TODO: Detailed explanation of the file.
"""
from typing import Optional

import pandas as pd
import sqlalchemy as sql

import build_info
from deeplearning.ml4pl import run_id as run_id_lib
from deeplearning.ml4pl.graphs.labelled import graph_tuple_database
from deeplearning.ml4pl.models import batch
from deeplearning.ml4pl.models import checkpoints
from deeplearning.ml4pl.models import epoch
from deeplearning.ml4pl.models import log_database
from deeplearning.ml4pl.models import schedules
from labm8.py import app
from labm8.py import pbutil
from labm8.py import prof
from labm8.py import progress
from labm8.py import sqlutil


FLAGS = app.FLAGS

app.DEFINE_enum(
  "keep_checkpoints",
  schedules.KeepCheckpoints,
  schedules.KeepCheckpoints.ALL,
  "How many checkpoints to keep.",
)
app.DEFINE_list(
  "detailed_batch_types",
  [],
  "The types of epochs to keep detailed batch logs for.",
)
app.DEFINE_enum(
  "keep_detailed_batches",
  schedules.KeepDetailedBatches,
  schedules.KeepDetailedBatches.ALL,
  "The type of detailed batches to keep.",
)
app.DEFINE_string(
  "tag",
  "",
  "An arbitrary tag which will be stored as a flag in the parameters table. "
  "Use this to group multiple runs of a model with a meaningful name, e.g. for "
  "grouping the 'k' run IDs of a k-fold dataset.",
)
app.DEFINE_integer(
  "logger_buffer_size_mb",
  32,
  "Tuning parameter. The maximum size of the log buffer, in megabytes.",
)
app.DEFINE_integer(
  "logger_buffer_length",
  1024,
  "Tuning parameter. The maximum length of the log buffer.",
)
app.DEFINE_integer(
  "logger_flush_seconds",
  10,
  "Tuning parameter. The maximum number of seconds between flushes.",
)
app.DEFINE_boolean(
  "fail_on_logger_error", True, "Raise an error if log writing fails."
)


class Logger(object):
  """An database-backed logger with asynchronous writes.

  This class exposes callbacks for recording logging events during the execution
  of a model.
  """

  def __init__(
    self,
    db: log_database.Database,
    max_buffer_size: Optional[int] = None,
    max_buffer_length: Optional[int] = None,
    max_seconds_since_flush: Optional[float] = None,
    log_level: int = 2,
    ctx: progress.ProgressContext = progress.NullContext,
  ):
    self.db = db
    self.ctx = ctx
    self._writer = sqlutil.BufferedDatabaseWriter(
      db,
      ctx=ctx,
      max_buffer_size=max_buffer_size,
      max_buffer_length=max_buffer_length,
      max_seconds_since_flush=max_seconds_since_flush,
      log_level=log_level,
    )

    # Build a set of epoch types to keep detailed batches for.
    self.detailed_batch_epoch_types = set()
    for detailed_batch_type in FLAGS.detailed_batch_types:
      if detailed_batch_type == "train":
        self.detailed_batch_epoch_types.add(epoch.Type.TRAIN)
      elif detailed_batch_type == "val":
        self.detailed_batch_epoch_types.add(epoch.Type.VAL)
      elif detailed_batch_type == "test":
        self.detailed_batch_epoch_types.add(epoch.Type.TEST)
      else:
        raise app.UsageError(
          "Unknown --detailed_batch_types: " f"'{detailed_batch_type}'"
        )

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    del exc_type
    del exc_val
    del exc_tb
    self._writer.Close()
    self.CheckForError()

  def CheckForError(self) -> None:
    """Check for errors in log writing.

    Raises:
      OSError: If log writing has failed.
    """
    if self._writer.error_count and FLAGS.fail_on_logger_error:
      raise OSError(
        f"Stopping now because since the last time I checked there have been "
        f"been {self._writer.error_count} log writing failures. "
        "Disable these checks using --fail_on_logger_error=false"
      )

  #############################################################################
  # Event callbacks.
  #############################################################################

  def OnStartRun(
    self, run_id: run_id_lib.RunId, graph_db: graph_tuple_database.Database
  ) -> None:
    """Register the creation of a new run ID.

    This records the experimental parameters of a run.
    """
    # Record the run ID and experimental parameters.
    flags = {k.split(".")[-1]: v for k, v in app.FlagsToDict().items()}
    self._writer.AddMany(
      # Record run ID.
      [log_database.RunId(run_id=str(run_id))]
      +
      # Record flag values.
      log_database.Parameter.CreateManyFromDict(
        run_id, log_database.ParameterType.FLAG, flags
      )
      +
      # Record graph database stats.
      log_database.Parameter.CreateManyFromDict(
        run_id,
        log_database.ParameterType.INPUT_GRAPHS_INFO,
        graph_db.stats_json,
      )
      +
      # Record build info.
      log_database.Parameter.CreateManyFromDict(
        run_id,
        log_database.ParameterType.BUILD_INFO,
        pbutil.ToJson(build_info.GetBuildInfo()),
      )
    )

  def OnBatchEnd(
    self,
    run_id: run_id_lib.RunId,
    epoch_type: epoch.Type,
    epoch_num: int,
    batch_num: int,
    timer: prof.ProfileTimer,
    data: batch.Data,
    results: batch.Results,
  ):
    if epoch_type in self.detailed_batch_epoch_types:
      details = log_database.BatchDetails.Create(data=data, results=results)
    else:
      details = None

    self._writer.AddOne(
      log_database.Batch.Create(
        run_id=run_id,
        epoch_type=epoch_type,
        epoch_num=epoch_num,
        batch_num=batch_num,
        timer=timer,
        data=data,
        results=results,
        details=details,
      )
    )

  def OnEpochEnd(
    self,
    run_id: run_id_lib.RunId,
    epoch_type: epoch.Type,
    epoch_num: epoch.Type,
    results: epoch.Results,
  ):
    del epoch_type
    del results

    schedule = FLAGS.keep_detailed_batches()

    if schedule == schedules.KeepDetailedBatches.NONE:
      pass
    elif schedule == schedules.KeepDetailedBatches.ALL:
      pass
    elif schedule == schedules.KeepDetailedBatches.LAST_EPOCH:

      def DeleteOldDetailedBatchLogs(session):
        """Delete old detailed batch logs."""
        detailed_batches_to_delete = [
          row.id
          for row in session.query(log_database.Batch.id).filter(
            log_database.Batch.run_id == run_id,
            log_database.Batch.epoch_num != epoch_num,
          )
        ]
        if detailed_batches_to_delete:
          session.query(log_database.BatchDetails).filter(
            log_database.BatchDetails.id.in_(detailed_batches_to_delete)
          ).delete(synchronize_session=False)
          self.ctx.Log(
            2,
            "Deleted %s old batch log details",
            len(detailed_batches_to_delete),
          )

      self._writer.AddLambdaOp(DeleteOldDetailedBatchLogs)
      self.CheckForError()

  #############################################################################
  # Save and restore checkpoints.
  #############################################################################

  def Save(self, checkpoint: checkpoints.Checkpoint) -> None:
    """Save a checkpoint.

    Args:
      checkpoint: A model checkpoint, as generated by model.GetCheckpoint().
    Returns:
      pass
    """
    keep_schedule = FLAGS.keep_checkpoints()

    checkpoint = log_database.Checkpoint.Create(checkpoint)

    # Delete old checkpoints if required.
    if keep_schedule == schedules.KeepCheckpoints.ALL:
      pass
    elif keep_schedule == schedules.KeepCheckpoints.LAST:
      self._writer.AddLambdaOp(
        lambda session: session.query(log_database.Checkpoint)
        .filter(log_database.Checkpoint.run_id == checkpoint.run_id)
        .delete()
      )
    else:
      raise NotImplementedError("unreachable")

    self._writer.AddOne(checkpoint)

  def Load(
    self, checkpoint_ref: checkpoints.CheckpointReference
  ) -> checkpoints.Checkpoint:
    """Load model data.

    Args:
      checkpoint_ref: A checkpoint to load. If epoch_num is not set, the best
        validation results are selected.

    Returns:
      A checkpoint instance.

    Raises:
      ValueError: If no corresponding entry in the checkpoint table exists.
    """
    # A previous Save() call from this logger might still be buffered. Flush the
    # buffer before loading from the database.
    self.Flush()

    with self.db.Session() as session:
      epoch_num = checkpoint_ref.epoch_num

      # If no epoch number was provided, select the best epoch from the log
      # database.
      if epoch_num is None:
        # Get the per-epoch summary table of model results.
        tables = {
          name: df
          for name, df in self.db.GetTables(run_ids=[checkpoint_ref.run_id])
        }
        # Select the epoch with the best validation accuracy.
        epochs = tables["epochs"][tables["epochs"]["val_accuracy"].notnull()]
        if not len(epochs):
          raise ValueError("No epochs found!")
        best_epoch_idx = epochs["val_accuracy"].idxmax()
        best_epoch = epochs.iloc[best_epoch_idx]
        epoch_num = best_epoch["epoch_num"]

      checkpoint_entry = (
        session.query(log_database.Checkpoint)
        .filter(
          log_database.Checkpoint.run_id == str(checkpoint_ref.run_id),
          log_database.Checkpoint.epoch_num == int(epoch_num),
        )
        .options(sql.orm.joinedload(log_database.Checkpoint.data))
        .first()
      )
      # Check that the requested checkpoint exists.
      if not checkpoint_entry:
        available_checkpoints = [
          f"{checkpoint_ref.run_id}@{row.epoch_num}"
          for row in session.query(log_database.Checkpoint.epoch_num)
          .join(log_database.CheckpointModelData)
          .filter(log_database.Checkpoint.run_id == str(checkpoint_ref.run_id))
          .order_by(log_database.Checkpoint.epoch_num)
        ]
        raise ValueError(
          f"Checkpoint not found: {checkpoint_ref}. "
          f"Available checkpoints: {available_checkpoints}"
        )

      checkpoint = checkpoints.Checkpoint(
        run_id=run_id_lib.RunId.FromString(checkpoint_entry.run_id),
        epoch_num=checkpoint_entry.epoch_num,
        best_results=self.db.GetBestResults(
          run_id=checkpoint_ref.run_id, session=session
        ),
        model_data=checkpoint_entry.model_data,
      )

    return checkpoint

  def GetParameters(self, run_id: run_id_lib.RunId) -> pd.DataFrame:
    self.Flush()
    return self.db.GetRunParameters(run_id)

  def Session(self) -> log_database.Database.SessionType:
    """Return a database session.

    This flushes the current write buffer before creating the session.
    """
    self.Flush()
    return self._writer.db.Session()

  def Flush(self) -> None:
    """Flush the current write buffer and block until completion."""
    self._writer.Flush()

  @classmethod
  def FromFlags(cls, ctx: progress.ProgressContext = progress.NullContext):
    if not FLAGS.log_db:
      raise app.UsageError("--log_db not set")

    return cls(
      FLAGS.log_db(),
      ctx=ctx,
      max_buffer_size=FLAGS.logger_buffer_size_mb * 1024 * 1024,
      max_buffer_length=FLAGS.logger_buffer_length,
      max_seconds_since_flush=FLAGS.logger_flush_seconds,
    )
