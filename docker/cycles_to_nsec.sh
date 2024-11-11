#!/bin/bash

result_file=$1
result_file_final=$2
nsec_per_cycle=40
temp_file="temp.txt"
> "$temp_file"
> "$result_file_final"

# Parse the result file and calculate the WCET in nanoseconds
while IFS= read -r line; do
  if [[ $line =~ "cycles" ]]; then
    cycles=$(echo $line | sed 's/[^0-9]*//g')
    new_cycles=$((cycles * $nsec_per_cycle))
    line="  WCET(ns): $new_cycles"
  fi
  echo "$line"
  echo "$line" >> "$temp_file"
done < "$result_file"

mv $temp_file $result_file_final