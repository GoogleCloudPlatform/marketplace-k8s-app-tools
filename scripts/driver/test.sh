#!/bin/bash

data="data"
for chart in "$data"/chart/*; do
  [[ -e "$chart" ]] || continue
  echo "$chart"
done
