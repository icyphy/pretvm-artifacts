{ pkgs }:
let
  riscv32-pkgs = pkgs.pkgsCross.riscv32-embedded;
  buildPackages = riscv32-pkgs.buildPackages;
in
pkgs.mkShell {
  buildInputs = with pkgs; [
    pkg-config
    gnumake
    openocd
    picotool
    python312Packages.pyserial
    buildPackages.gcc
    buildPackages.binutils
    buildPackages.libcCross
    newlib-nano
  ];

  shellHook = ''
    export REACTOR_UC_PATH=$(pwd)/../reactor-uc
    export OBJDUMP=${buildPackages.gcc-arm-embedded}/arm-none-eabi/bin/objdump
    export OBJCOPY=${buildPackages.gcc-arm-embedded}/arm-none-eabi/bin/objcopy
  '';
}
