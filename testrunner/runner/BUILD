# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

load(
    "@io_bazel_rules_go//go:def.bzl",
    "go_binary",
)
load(
    "@io_bazel_rules_docker//go:image.bzl",
    "go_image",
)

binary_srcs = [
    "main.go",
]

binary_deps = [
    "//asserts:go_default_library",
    "//conditions:go_default_library",
    "//flags:go_default_library",
    "//gcp:go_default_library",
    "//specs:go_default_library",
    "//tests:go_default_library",
    "@com_github_golang_glog//:go_default_library",
]

go_binary(
    name = "main",
    srcs = binary_srcs,
    deps = binary_deps,
)

go_image(
    name = "go_image",
    srcs = binary_srcs,
    deps = binary_deps,
)
