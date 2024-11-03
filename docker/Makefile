build-patmos:
	patmos-clang -target riscv32-unknown-elf -c -O1 -mserialize-auto -mllvm -mserialize-all -march=rv32i -mabi=ilp32 ${file}.c -o ${file}.o

list-symbols:
	nm -an ${file}.o | grep T | awk '{print $$3}' | sed '/./,$$!d'

analysis: 
	platin wcet -i ${file}.c.pml -b ${file}.o --report --analysis-entry ${symbol} 
