#!/bin/bash

result_file="result.txt"
nsec_per_cycle=40
temp_file="temp.txt"
> "$temp_file"

make build-patmos file=satellite-controller/src/satellite_attitude_controller

make list-symbols file=satellite-controller/src/satellite_attitude_controller \
  | while read -r line; do make analysis file=satellite-controller/src/satellite_attitude_controller symbol="$line"; done 2> stderr.log \
  | grep -e "  cycles: " -e "analysis-entry:" | tee $result_file

# Parse the result file and calculate the WCET in nanoseconds
while IFS= read -r line; do
  if [[ $line =~ "cycles" ]]; then
    cycles=$(echo $line | sed 's/[^0-9]*//g')
    new_cycles=$((cycles * $nsec_per_cycle))
    line="  WCET(ns): $new_cycles"
  fi
  echo "$line" >> "$temp_file"
done < "$result_file"

mv $temp_file $result_file