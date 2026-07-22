#!/usr/bin/env python3
#
# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import yaml
import argparse

def is_crd_file(file_path):
    with open(file_path, 'r') as file:
        try:
            content = yaml.safe_load(file)
            if isinstance(content, dict) and content.get('kind') == 'CustomResourceDefinition':
                return True
        except yaml.YAMLError as e:
            print(f"Error reading {file_path}: {e}")
    return False

def append_crd_to_file(file_path, output_file):
    outpath = f"/{output_file.split('/')[1]}/{output_file.split('/')[2]}"
    os.mkdir(outpath)
    with open(file_path, 'r') as infile:
        with open(output_file, 'a') as outfile:
            # Append the content of the CRD file to the output file
            outfile.write(infile.read())
            outfile.write("\n---\n")  # Append YAML separator

def check_crd_directory(directory, output_file):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path) and filename.endswith('.yaml'):
            if is_crd_file(file_path):
                append_crd_to_file(file_path, output_file)
            else:
                print(f"File '{filename}' is not a CRD kind file.")

def main():
    parser = argparse.ArgumentParser(description='Process CRD files in a directory.')
    parser.add_argument('--directory', type=str, help='Directory containing CRD manifest files')
    parser.add_argument('--output_file', type=str, help='Output file to append validated CRDs')
    args = parser.parse_args()

    check_crd_directory(args.directory, args.output_file)
    print(f"CRD files appended to '{args.output_file}'")

if __name__ == "__main__":
    main()