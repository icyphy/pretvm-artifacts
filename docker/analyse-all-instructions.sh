#!/bin/bash

result_file="result_pretvm_instructions_cycles.txt"
result_file_final="result_pretvm_instructions.txt"

make build-patmos file=pretvm-instructions/inst_lib

make list-symbols file=pretvm-instructions/inst_lib \
| while read -r line; do make analysis file=pretvm-instructions/inst_lib symbol="$line"; done 2> stderr.log \
| grep -e "  cycles: " -e "analysis-entry:" >> $result_file


./cycles_to_nsec.sh $result_file $result_file_finalresult_file_final="result_pretvm_instructions.txt"
rm $result_file