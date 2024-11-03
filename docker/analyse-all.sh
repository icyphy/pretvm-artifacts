#!/bin/sh

make build-patmos file=satellite-controller/src/satellite_attitude_controller

make list-symbols file=satellite-controller/src/satellite_attitude_controller | while read -r line; do make analysis file=satellite-controller/src/satellite_attitude_controller symbol="$line"; done 2> stderr.log
