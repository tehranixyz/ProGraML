# This package constructs program graphs from LLVM intermediate representations.
#
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

load("@io_bazel_rules_docker//python3:image.bzl", "py3_image")

py_library(
    name = "call_graph",
    srcs = ["call_graph.py"],
    visibility = ["//visibility:public"],
    deps = [
        "//labm8/py:app",
        "//labm8/py:labtypes",
        "//third_party/py/networkx",
        "//third_party/py/pydot",
        "//third_party/py/pyparsing",
    ],
)

py_library(
    name = "graph_builder",
    srcs = ["graph_builder.py"],
    visibility = ["//deeplearning/ml4pl:__subpackages__"],
    deps = [
        ":call_graph",
        ":llvm_statements",
        ":node_encoder",
        "//compilers/llvm:opt_util",
        "//deeplearning/ml4pl/graphs:nx_utils",
        "//deeplearning/ml4pl/graphs:programl_pb_py",
        "//deeplearning/ml4pl/graphs/unlabelled/llvm2graph/cfg:llvm_util",
        "//labm8/py:app",
        "//third_party/py/networkx",
    ],
)

py_test(
    name = "graph_builder_test",
    srcs = ["graph_builder_test.py"],
    deps = [
        ":graph_builder",
        "//deeplearning/ml4pl/graphs:programl_pb_py",
        "//labm8/py:test",
        "//third_party/py/networkx",
    ],
)

py_test(
    name = "graph_builder_regression_test",
    timeout = "long",
    srcs = ["graph_builder_regression_test.py"],
    data = ["//deeplearning/ml4pl/testing/data/bytecode_regression_tests:bytecodes"],
    deps = [
        ":graph_builder",
        "//deeplearning/ml4pl/graphs:programl",
        "//labm8/py:fs",
        "//labm8/py:test",
    ],
)

py_binary(
    name = "llvm2graph",
    srcs = ["llvm2graph.py"],
    deps = [
        ":graph_builder",
        "//deeplearning/ml4pl/graphs:programl",
        "//deeplearning/ml4pl/graphs:programl_pb_py",
        "//labm8/py:app",
        "//labm8/py:pbutil",
    ],
)

py3_image(
    name = "llvm2graph_image",
    srcs = ["llvm2graph.py"],
    base = "@phd_base//image",
    main = "llvm2graph.py",
    deps = [":llvm2graph"],
)

py_library(
    name = "llvm_statements",
    srcs = ["llvm_statements.py"],
    deps = [
        "//compilers/llvm:opt_util",
        "//deeplearning/ml4pl/graphs:nx_utils",
        "//deeplearning/ml4pl/graphs:programl_pb_py",
        "//deeplearning/ml4pl/graphs/unlabelled/llvm2graph/cfg:llvm_util",
        "//deeplearning/ncc:rgx_utils",
        "//deeplearning/ncc/inst2vec:inst2vec_preprocess",
        "//labm8/py:app",
        "//labm8/py:bazelutil",
        "//labm8/py:decorators",
        "//third_party/py/networkx",
        "//third_party/py/numpy",
    ],
)

py_test(
    name = "llvm_statements_test",
    srcs = ["llvm_statements_test.py"],
    deps = [
        ":llvm_statements",
        "//deeplearning/ml4pl/graphs:programl",
        "//labm8/py:test",
    ],
)

py_library(
    name = "node_encoder",
    srcs = ["node_encoder.py"],
    data = [
        "//deeplearning/ml4pl/graphs/unlabelled/llvm2graph/node_embeddings:dictionary",
        "//deeplearning/ml4pl/graphs/unlabelled/llvm2graph/node_embeddings:embeddings",
    ],
    visibility = ["//deeplearning/ml4pl/models:__subpackages__"],
    deps = [
        "//deeplearning/ml4pl/graphs:programl_pb_py",
        "//deeplearning/ncc/inst2vec:inst2vec_preprocess",
        "//labm8/py:app",
        "//labm8/py:bazelutil",
        "//labm8/py:decorators",
        "//third_party/py/numpy",
    ],
)
