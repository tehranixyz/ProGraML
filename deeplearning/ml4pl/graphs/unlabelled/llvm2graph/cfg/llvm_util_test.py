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
"""Unit tests for //deeplearning/ml4pl/graphs/unlabelled/llvm2graph/cfg:llvm_util."""
import pyparsing

from compilers.llvm import opt
from deeplearning.ml4pl.graphs.unlabelled.llvm2graph.cfg import llvm_util
from labm8.py import app
from labm8.py import test


FLAGS = app.FLAGS

# Bytecode generated by clang using the following command:
# $ clang -emit-llvm -S -xc - < foo.c -o - > foo.ll
# Original C source code:
#
#     #include <stdio.h>
#     #include <math.h>
#
#     int DoSomething(int a, int b) {
#       if (a % 5) {
#         return a * 10;
#       }
#       return pow((float)a, 2.5);
#     }
#
#     int main(int argc, char **argv) {
#       for (int i = 0; i < argc; ++i) {
#         argc += DoSomething(argc, i);
#       }
#
#       printf("Computed value %d", argc);
#       return 0;
#     }
SIMPLE_C_BYTECODE = """
; ModuleID = '-'
source_filename = "-"
target datalayout = "e-m:o-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-apple-macosx10.12.0"

@.str = private unnamed_addr constant [18 x i8] c"Computed value %d\00", align 1

; Function Attrs: norecurse nounwind readnone ssp uwtable
define i32 @DoSomething(i32, i32) #0 {
  %3 = srem i32 %0, 5
  %4 = icmp eq i32 %3, 0
  br i1 %4, label %7, label %5

; <label>:5                                       ; preds = %2
  %6 = mul nsw i32 %0, 10
  br label %12

; <label>:7                                       ; preds = %2
  %8 = sitofp i32 %0 to float
  %9 = fpext float %8 to double
  %10 = tail call double @llvm.pow.f64(double %9, double 2.500000e+00)
  %11 = fptosi double %10 to i32
  br label %12

; <label>:12                                      ; preds = %7, %5
  %13 = phi i32 [ %6, %5 ], [ %11, %7 ]
  ret i32 %13
}

; Function Attrs: nounwind readnone
declare double @llvm.pow.f64(double, double) #1

; Function Attrs: nounwind ssp uwtable
define i32 @main(i32, i8** nocapture readnone) #2 {
  %3 = icmp sgt i32 %0, 0
  br i1 %3, label %4, label %7

; <label>:4                                       ; preds = %2
  br label %10

; <label>:5                                       ; preds = %22
  %6 = phi i32 [ %24, %22 ]
  br label %7

; <label>:7                                       ; preds = %5, %2
  %8 = phi i32 [ %0, %2 ], [ %6, %5 ]
  %9 = tail call i32 (i8*, ...) @printf(i8* nonnull getelementptr inbounds ([18 x i8], [18 x i8]* @.str, i64 0, i64 0), i32 %8)
  ret i32 0

; <label>:10                                      ; preds = %4, %22
  %11 = phi i32 [ %25, %22 ], [ 0, %4 ]
  %12 = phi i32 [ %24, %22 ], [ %0, %4 ]
  %13 = srem i32 %12, 5
  %14 = icmp eq i32 %13, 0
  br i1 %14, label %17, label %15

; <label>:15                                      ; preds = %10
  %16 = mul nsw i32 %12, 10
  br label %22

; <label>:17                                      ; preds = %10
  %18 = sitofp i32 %12 to float
  %19 = fpext float %18 to double
  %20 = tail call double @llvm.pow.f64(double %19, double 2.500000e+00) #4
  %21 = fptosi double %20 to i32
  br label %22

; <label>:22                                      ; preds = %15, %17
  %23 = phi i32 [ %16, %15 ], [ %21, %17 ]
  %24 = add nsw i32 %23, %12
  %25 = add nuw nsw i32 %11, 1
  %26 = icmp slt i32 %25, %24
  br i1 %26, label %10, label %5
}

; Function Attrs: nounwind
declare i32 @printf(i8* nocapture readonly, ...) #3

attributes #0 = { norecurse nounwind readnone ssp uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="penryn" "target-features"="+cx16,+fxsr,+mmx,+sse,+sse2,+sse3,+sse4.1,+ssse3" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { nounwind readnone }
attributes #2 = { nounwind ssp uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="penryn" "target-features"="+cx16,+fxsr,+mmx,+sse,+sse2,+sse3,+sse4.1,+ssse3" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #3 = { nounwind "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="penryn" "target-features"="+cx16,+fxsr,+mmx,+sse,+sse2,+sse3,+sse4.1,+ssse3" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #4 = { nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"PIC Level", i32 2}
!1 = !{!"Apple LLVM version 8.0.0 (clang-800.0.42.1)"}
"""

# LLVM-generated dot file for the DoSomething() function of a simple C program.
# Original C source code:
#
#     #include <stdio.h>
#     #include <math.h>
#
#     int DoSomething(int a, int b) {
#       if (a % 5) {
#         return a * 10;
#       }
#       return pow((float)a, 2.5);
#     }
#
#     int main(int argc, char **argv) {
#       for (int i = 0; i < argc; ++i) {
#         argc += DoSomething(argc, i);
#       }
#
#       printf("Computed value %d", argc);
#       return 0;
#     }
#
# I converted tabs to spaces in the following string.
SIMPLE_C_DOT = """
digraph "CFG for 'DoSomething' function" {
  label="CFG for 'DoSomething' function";
  
  Node0x7f86c670c590 [shape=record,label="{%2:\l  %3 = alloca i32, align 4\l  %4 = alloca i32, align 4\l  %5 = alloca i32, align 4\l  store i32 %0, i32* %4, align 4\l  store i32 %1, i32* %5, align 4\l  %6 = load i32, i32* %4, align 4\l  %7 = srem i32 %6, 5\l  %8 = icmp ne i32 %7, 0\l  br i1 %8, label %9, label %12\l|{<s0>T|<s1>F}}"];
  Node0x7f86c670c590:s0 -> Node0x7f86c65001a0;
  Node0x7f86c670c590:s1 -> Node0x7f86c65001f0;
  Node0x7f86c65001a0 [shape=record,label="{%9:\l\l  %10 = load i32, i32* %4, align 4\l  %11 = mul nsw i32 %10, 10\l  store i32 %11, i32* %3, align 4\l  br label %18\l}"];
  Node0x7f86c65001a0 -> Node0x7f86c65084b0;
  Node0x7f86c65001f0 [shape=record,label="{%12:\l\l  %13 = load i32, i32* %4, align 4\l  %14 = sitofp i32 %13 to float\l  %15 = fpext float %14 to double\l  %16 = call double @llvm.pow.f64(double %15, double 2.500000e+00)\l  %17 = fptosi double %16 to i32\l  store i32 %17, i32* %3, align 4\l  br label %18\l}"];
  Node0x7f86c65001f0 -> Node0x7f86c65084b0;
  Node0x7f86c65084b0 [shape=record,label="{%18:\l\l  %19 = load i32, i32* %3, align 4\l  ret i32 %19\l}"];
  }
"""


def test_NodeAttributesToBasicBlock_unrecognized_label():
  """Test that error is raised if label is not recognized."""
  with test.Raises(ValueError):
    llvm_util.NodeAttributesToBasicBlock({"label": "invalid label"})


def test_NodeAttributesToBasicBlock_name():
  """Test name extraction."""
  label = (
    '"{%2:\l  %3 = alloca i32, align 4\l  %4 = alloca i32, align 4\l  '
    "%5 = alloca i8**, align 8\l  %6 = alloca i32, align 4\l  "
    "store i32 0, i32* %3, align 4\l  store i32 %0, i32* %4, "
    "align 4\l  store i8** %1, i8*** %5, align 8\l  store i32 0, "
    'i32* %6, align 4\l  br label %7\l}"'
  )
  assert llvm_util.NodeAttributesToBasicBlock({"label": label})["name"] == "%2"


def test_NodeAttributesToBasicBlock_text():
  """Test text extraction."""
  label = (
    '"{%2:\l  %3 = alloca i32, align 4\l  %4 = alloca i32, align 4\l  '
    "%5 = alloca i8**, align 8\l  %6 = alloca i32, align 4\l  "
    "store i32 0, i32* %3, align 4\l  store i32 %0, i32* %4, "
    "align 4\l  store i8** %1, i8*** %5, align 8\l  store i32 0, "
    'i32* %6, align 4\l  br label %7\l}"'
  )
  assert (
    llvm_util.NodeAttributesToBasicBlock({"label": label})["text"]
    == """\
%3 = alloca i32, align 4
%4 = alloca i32, align 4
%5 = alloca i8**, align 8
%6 = alloca i32, align 4
store i32 0, i32* %3, align 4
store i32 %0, i32* %4, align 4
store i8** %1, i8*** %5, align 8
store i32 0, i32* %6, align 4
br label %7\
"""
  )


def test_ControlFlowGraphFromDotSource_invalid_source():
  """Test that exception is raised if dot can't be parsed."""
  with test.Raises(pyparsing.ParseException):
    llvm_util.ControlFlowGraphFromDotSource("invalid dot source!")


def test_ControlFlowGraphFromDotSource_graph_name():
  """Test that CFG has correct name."""
  g = llvm_util.ControlFlowGraphFromDotSource(SIMPLE_C_DOT)
  assert g.graph["name"] == "DoSomething"


def test_ControlFlowGraphFromDotSource_num_nodes():
  """Test that CFG has correct number of nodes."""
  g = llvm_util.ControlFlowGraphFromDotSource(SIMPLE_C_DOT)
  assert g.number_of_nodes() == 4


def test_ControlFlowGraphFromDotSource_num_edges():
  """Test that CFG has correct number of edges."""
  g = llvm_util.ControlFlowGraphFromDotSource(SIMPLE_C_DOT)
  assert g.number_of_edges() == 4


def test_ControlFlowGraphFromDotSource_is_valid():
  """Test that CFG is valid."""
  g = llvm_util.ControlFlowGraphFromDotSource(SIMPLE_C_DOT)
  # Control flow graphs are not guaranteed to be valid. That is, the may contain
  # fusible basic blocks. This can happen if the creating the graph from
  # unoptimized bytecode.
  assert g.ValidateControlFlowGraph()


def test_ControlFlowGraphFromDotSource_node_names():
  """Test that CFG names are as expected."""
  g = llvm_util.ControlFlowGraphFromDotSource(SIMPLE_C_DOT)
  node_names = sorted(
    [g.nodes[n]["name"] for n in g.nodes], key=lambda x: int(x[1:])
  )
  assert node_names == ["%2", "%9", "%12", "%18"]


def test_ControlFlowGraphFromDotSource_edges():
  """Test that CFG edges are as expected."""
  g = llvm_util.ControlFlowGraphFromDotSource(SIMPLE_C_DOT)
  node_name_to_index_map = {g.nodes[n]["name"]: n for n in g.nodes}
  edges = set(g.edges)

  assert (node_name_to_index_map["%2"], node_name_to_index_map["%9"]) in edges
  assert (node_name_to_index_map["%2"], node_name_to_index_map["%12"]) in edges
  assert (node_name_to_index_map["%9"], node_name_to_index_map["%18"]) in edges
  assert (node_name_to_index_map["%12"], node_name_to_index_map["%18"]) in edges


def test_ControlFlowGraphsFromBytecodes_num_graphs():
  """Test that expected number of CFGs are created."""
  g = list(
    llvm_util.ControlFlowGraphsFromBytecodes(
      [SIMPLE_C_BYTECODE, SIMPLE_C_BYTECODE, SIMPLE_C_BYTECODE,]
    )
  )

  assert len(g) == 6


def test_ControlFlowGraphsFromBytecodes_one_failure():
  """Errors during construction of CFGs are buffered until complete."""
  # The middle job of the three will throw an opt.optException.
  generator = llvm_util.ControlFlowGraphsFromBytecodes(
    [SIMPLE_C_BYTECODE, "Invalid bytecode!", SIMPLE_C_BYTECODE,]
  )

  g = []
  # We can still get all of the valid CFGs out of input[0] and input[2]. The
  # exception from input[1] is will be raised once all processes have completed.
  g.append(next(generator))
  g.append(next(generator))
  g.append(next(generator))
  g.append(next(generator))
  # Instead of StopIteration, an ExceptionBuffer will be thrown, which contains
  # all the that were thrown, along with the inputs that caused the exception.
  with test.Raises(llvm_util.ExceptionBuffer) as e_ctx:
    next(generator)
  assert len(e_ctx.value.errors) == 1
  assert e_ctx.value.errors[0].input == "Invalid bytecode!"
  assert isinstance(e_ctx.value.errors[0].error, opt.OptException)


# LLVM-generated dot file for a FizzBuzz() function.
# Original C source code:
#
#    int FizzBuzz(int i) {
#      if (i % 15 == 0) {
#        return 1;
#      }
#      return 0;
#    }
#
# I converted tabs to spaces in the following string.
FIZZBUZZ_DOT = """
digraph "CFG for 'FizzBuzz' function" {
  label="CFG for 'FizzBuzz' function";
  
  Node0x7f8d5f507570 [shape=record,label="{%1:\l  %2 = alloca i32, align 4\l  %3 = alloca i32, align 4\l  store i32 %0, i32* %3, align 4\l  %4 = load i32, i32* %3, align 4\l  %5 = srem i32 %4, 15\l  %6 = icmp eq i32 %5, 0\l  br i1 %6, label %7, label %8\l|{<s0>T|<s1>F}}"];
  Node0x7f8d5f507570:s0 -> Node0x7f8d5f507930;
  Node0x7f8d5f507570:s1 -> Node0x7f8d5f5079c0;
  Node0x7f8d5f507930 [shape=record,label="{%7:\l\l  store i32 1, i32* %2, align 4\l  br label %9\l}"];
  Node0x7f8d5f507930 -> Node0x7f8d5f507b50;
  Node0x7f8d5f5079c0 [shape=record,label="{%8:\l\l  store i32 0, i32* %2, align 4\l  br label %9\l}"];
  Node0x7f8d5f5079c0 -> Node0x7f8d5f507b50;
  Node0x7f8d5f507b50 [shape=record,label="{%9:\l\l  %10 = load i32, i32* %2, align 4\l  ret i32 %10\l}"];
}
"""


def test_ControlFlowGraphFromDotSource_fizz_buzz():
  """Test the fizz buzz graph properties."""
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  assert cfg.graph["name"] == "FizzBuzz"
  assert cfg.number_of_nodes() == 4
  assert cfg.number_of_edges() == 4

  # Create a map of node names to indices.
  name_to_node = {data["name"]: node for node, data in cfg.nodes(data=True)}

  # Test that graph has required edges.
  assert cfg.has_edge(name_to_node["%1"], name_to_node["%7"])
  assert cfg.has_edge(name_to_node["%1"], name_to_node["%8"])
  assert cfg.has_edge(name_to_node["%7"], name_to_node["%9"])
  assert cfg.has_edge(name_to_node["%8"], name_to_node["%9"])


def test_BuildFullFlowGraph_fizz_buzz():
  """Test flow graph name."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  assert sig.graph["name"] == "FizzBuzz"


def test_BuildFullFlowGraph_num_nodes():
  """Test flow graph node count."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  assert sig.number_of_nodes() == 13


def test_BuildFullFlowGraph_node_text():
  """Test flow graph nodes have expected text."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  # Create a map of node names to indices.
  name_to_node = {data["name"]: node for node, data in sig.nodes(data=True)}

  # Block %1.
  assert sig.nodes[name_to_node["%1.0"]]["text"] == "%2 = alloca i32, align 4"
  assert sig.nodes[name_to_node["%1.1"]]["text"] == "%3 = alloca i32, align 4"
  assert (
    sig.nodes[name_to_node["%1.2"]]["text"] == "store i32 %0, i32* %3, align 4"
  )
  assert (
    sig.nodes[name_to_node["%1.3"]]["text"] == "%4 = load i32, i32* %3, align 4"
  )
  assert sig.nodes[name_to_node["%1.4"]]["text"] == "%5 = srem i32 %4, 15"
  assert sig.nodes[name_to_node["%1.5"]]["text"] == "%6 = icmp eq i32 %5, 0"
  # Note the conditional branch instruction has had the labels stripped.
  assert sig.nodes[name_to_node["%1.6"]]["text"] == "br i1 %6"

  # Block %7.
  assert (
    sig.nodes[name_to_node["%7.0"]]["text"] == "store i32 1, i32* %2, align 4"
  )

  # Block %8.
  assert (
    sig.nodes[name_to_node["%8.0"]]["text"] == "store i32 0, i32* %2, align 4"
  )

  # Block %9.
  assert (
    sig.nodes[name_to_node["%9.0"]]["text"]
    == "%10 = load i32, i32* %2, align 4"
  )
  assert sig.nodes[name_to_node["%9.1"]]["text"] == "ret i32 %10"


def test_BuildFullFlowGraph_num_edges():
  """Test flow graph edge count."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  assert sig.number_of_edges() == 13


def test_BuildFullFlowGraph_edges():
  """Test flow graph has expected edges."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  # Create a map of node names to indices.
  name_to_node = {data["name"]: node for node, data in sig.nodes(data=True)}

  # Block %1.
  assert sig.has_edge(name_to_node["%1.0"], name_to_node["%1.1"])
  assert sig.has_edge(name_to_node["%1.1"], name_to_node["%1.2"])
  assert sig.has_edge(name_to_node["%1.2"], name_to_node["%1.3"])
  assert sig.has_edge(name_to_node["%1.3"], name_to_node["%1.4"])
  assert sig.has_edge(name_to_node["%1.4"], name_to_node["%1.5"])
  assert sig.has_edge(name_to_node["%1.5"], name_to_node["%1.6"])
  assert sig.has_edge(name_to_node["%1.6"], name_to_node["%7.0"])
  assert sig.has_edge(name_to_node["%1.6"], name_to_node["%8.0"])

  # Block %7.
  assert sig.has_edge(name_to_node["%7.0"], name_to_node["%7.1"])
  assert sig.has_edge(name_to_node["%7.1"], name_to_node["%9.0"])

  # Block %8.
  assert sig.has_edge(name_to_node["%8.0"], name_to_node["%8.1"])
  assert sig.has_edge(name_to_node["%8.1"], name_to_node["%9.0"])

  # Block %9.
  assert sig.has_edge(name_to_node["%9.0"], name_to_node["%9.1"])


def test_BuildFullFlowGraph_entry_block():
  """Test flow graph has expected entry block."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  # Create a map of node names to indices.
  name_to_node = {data["name"]: node for node, data in sig.nodes(data=True)}

  assert sig.nodes[name_to_node["%1.0"]]["entry"]


def test_BuildFullFlowGraph_exit_block():
  """Test flow graph has expected exit block."""
  # This test assumes that ControlFlowGraphFromDotSource() behaves as expected.
  # test_ControlFlowGraphFromDotSource_fizz_buzz() will fail if this is not the
  # case.
  cfg = llvm_util.ControlFlowGraphFromDotSource(FIZZBUZZ_DOT)
  sig = cfg.BuildFullFlowGraph()

  # Create a map of node names to indices.
  name_to_node = {data["name"]: node for node, data in sig.nodes(data=True)}

  assert sig.nodes[name_to_node["%9.1"]]["exit"]


def test_ControlFlowGraphFromDotSource_positions():
  """A control flow graph with two nested loops.

    int A() {
      int n = 0;
      for (int i = 0; i < 10; ++i) {
        switch (n) {
          case 0:
            n += 1;
          case 1:
            n += 2;
          default:
            n += 3;
            break;
        }
      }
      return n;
    }
  """
  cfg = llvm_util.ControlFlowGraphFromDotSource(
    """
digraph "CFG for 'A' function" {
	label="CFG for 'A' function";

	Node0x7ff981522700 [shape=record,label="{%0:\l  %1 = alloca i32, align 4\l  %2 = alloca i32, align 4\l  store i32 0, i32* %1, align 4\l  store i32 0, i32* %2, align 4\l  br label %3\l}"];
	Node0x7ff981522700 -> Node0x7ff981522980;
	Node0x7ff981522980 [shape=record,label="{%3:\l\l  %4 = load i32, i32* %2, align 4\l  %5 = icmp slt i32 %4, 10\l  br i1 %5, label %6, label %21\l|{<s0>T|<s1>F}}"];
	Node0x7ff981522980:s0 -> Node0x7ff981522b50;
	Node0x7ff981522980:s1 -> Node0x7ff981522bd0;
	Node0x7ff981522b50 [shape=record,label="{%6:\l\l  %7 = load i32, i32* %1, align 4\l  switch i32 %7, label %14 [\l    i32 0, label %8\l    i32 1, label %11\l  ]\l|{<s0>def|<s1>0|<s2>1}}"];
	Node0x7ff981522b50:s0 -> Node0x7ff981522b90;
	Node0x7ff981522b50:s1 -> Node0x7ff981522d30;
	Node0x7ff981522b50:s2 -> Node0x7ff981522db0;
	Node0x7ff981522d30 [shape=record,label="{%8:\l\l  %9 = load i32, i32* %1, align 4\l  %10 = add nsw i32 %9, 1\l  store i32 %10, i32* %1, align 4\l  br label %11\l}"];
	Node0x7ff981522d30 -> Node0x7ff981522db0;
	Node0x7ff981522db0 [shape=record,label="{%11:\l\l  %12 = load i32, i32* %1, align 4\l  %13 = add nsw i32 %12, 2\l  store i32 %13, i32* %1, align 4\l  br label %14\l}"];
	Node0x7ff981522db0 -> Node0x7ff981522b90;
	Node0x7ff981522b90 [shape=record,label="{%14:\l\l  %15 = load i32, i32* %1, align 4\l  %16 = add nsw i32 %15, 3\l  store i32 %16, i32* %1, align 4\l  br label %17\l}"];
	Node0x7ff981522b90 -> Node0x7ff981522740;
	Node0x7ff981522740 [shape=record,label="{%17:\l\l  br label %18\l}"];
	Node0x7ff981522740 -> Node0x7ff981522d70;
	Node0x7ff981522d70 [shape=record,label="{%18:\l\l  %19 = load i32, i32* %2, align 4\l  %20 = add nsw i32 %19, 1\l  store i32 %20, i32* %2, align 4\l  br label %3\l}"];
	Node0x7ff981522d70 -> Node0x7ff981522980;
	Node0x7ff981522bd0 [shape=record,label="{%21:\l\l  %22 = load i32, i32* %1, align 4\l  ret i32 %22\l}"];
}
"""
  )
  positions = set()
  for _, _, position in cfg.edges(data="position"):
    positions.add(position)
  assert positions == {0, 1, 2}


if __name__ == "__main__":
  test.Main()
