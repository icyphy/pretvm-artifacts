#!/bin/bash

result_file="result_satellite_controller.txt"

make build-patmos file=satellite-controller/src/satellite_attitude_controller

make list-symbols file=satellite-controller/src/satellite_attitude_controller \
  | while read -r line; do make analysis file=satellite-controller/src/satellite_attitude_controller symbol="$line"; done 2> stderr.log \
  | grep -e "  cycles: " -e "analysis-entry:" >> $result_file


./cycles_to_nsec.sh $result_file