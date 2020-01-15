#!/bin/bash

set -eo pipefail

cd "/data/$1"
coverage run --source=. -m unittest discover -p "*_test.py"
coverage report -m
