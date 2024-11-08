#!/bin/sh

make build-patmos file=pretvm-instructions/inst_lib

make list-symbols file=pretvm-instructions/inst_lib | while read -r line; do make analysis file=pretvm-instructions/inst_lib symbol="$line"; done 2> stderr.log
