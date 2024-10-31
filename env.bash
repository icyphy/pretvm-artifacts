PROJECT_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export RISCV_TOOL_PATH_PREFIX=/opt/xpack-riscv-none-elf-gcc-14.2.0-2
export LFC=$PROJECT_ROOT/lingua-franca/build/install/lf-cli/bin/lfc
source $PROJECT_ROOT/flexpret/env.bash
