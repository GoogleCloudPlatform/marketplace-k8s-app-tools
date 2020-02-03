#!/usr/bin/env python3

import sys
import re

# Extract useful information from deployer logs, based on common errors found in the past.

content = sys.stdin.read()

# Python exceptions
m = re.search("Traceback.*\n(.*(  )+.*\n)*.*\n", content)
if m:
  sys.stdout.write(m.group(0))

# Tar errors.
m = re.search("tar: .*: Cannot open: No such file or directory", content)
if m:
  sys.stdout.write(m.group(0))
