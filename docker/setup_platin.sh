#!/bin/bash
set -eu
dir=$(realpath "${1:-${PWD}}")
mkdir -p "$dir"
pushd "${dir}"
# platin
if [[ ! -d ${dir}/gems ]] ; then
        mkdir gems
        export GEM_HOME="${dir}/gems"
        git clone https://github.com/tanneberger/platin.git
        pushd platin
        ./setup.sh
        popd
fi
# patmos-clang
if [[ ! -d ${dir}/patmos-llvm/tools/clang ]] ; then
        git clone https://gitlab.cs.fau.de/fusionclock/llvm.git patmos-llvm 
        pushd patmos-llvm
        git checkout llvm_70_pml_arm
        pushd tools
        git clone https://gitlab.cs.fau.de/fusionclock/clang-riscv.git clang
        pushd clang
        git checkout clang_70_pml_arm
        popd
        popd
        popd
fi
if [[ ! -f ${dir}/build/patmos-llvm/bin/clang-7 ]] ; then
        mkdir -p build/patmos-llvm
        pushd build/patmos-llvm
        LD=ld.gold cmake -G "Ninja" -DCMAKE_EXPORT_COMPILE_COMMANDS=1 -DCMAKE_BUILD_TYPE=Debug -DLLVM_TARGETS_TO_BUILD="ARM;X86;AArch64" -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD="RISCV" -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_INCLUDE_TESTS=OFF -DCLANG_ENABLE_ARCMT=OFF -DCLANG_ENABLE_STATIC_ANALYZER=OFF -DLLVM_BUILD_TOOLS=OFF ../../patmos-llvm/ 
        ninja clang llvm-dis llvm-ar llvm-as llvm-objdump -j 8
        popd
fi
if [[ ! -L ${dir}/build/patmos-llvm/bin/patmos-clang-7 ]] ; then
        pushd build/patmos-llvm
        for file in bin/*; do
                if [[ -x "$file" ]]; then
                        ln -sr "$file" ./bin/"patmos-$(basename "$file")";
                fi;
        done
        popd
fi

# leave folder
popd
setup="${dir}/source.sh"
echo "#!/bin/bash" > "${setup}"
echo export PATH="${dir}"/build/patmos-llvm/bin:"${dir}"/platin:'$PATH' >> "${setup}"
echo export GEM_HOME="${dir}"/gems >> "${setup}"
echo "use 'source ${dir}/source.sh' to setup Platin!"
