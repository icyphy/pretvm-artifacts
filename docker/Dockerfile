FROM ubuntu:20.04

# Timezone
ENV TZ="UTC"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime
RUN echo $TZ > /etc/timezone && rm -rf /var/lib/apt/lists/*

# Base Configuration
RUN apt update -y
RUN apt install -y git wget curl tar sudo apt-utils
ENV LANG en_US.utf8

# Dependencies
RUN apt install -y build-essential ninja-build cmake ruby ruby-dev python3 liblpsolve55-dev \
  lp-solve pkg-config libssl-dev gcc-riscv64-unknown-elf libc6-dev-i386 gcc-multilib
RUN gem install bundler -v 2.4.22

# Compiling patmos-clang and preparing platin
COPY setup_platin.sh /setup_platin.sh
RUN chmod +x ./setup_platin.sh
RUN /setup_platin.sh

# Fixing Quirks

RUN echo "export LD_LIBRARY_PATH=/usr/lib/lp_solve:$LD_LIBRARY_PATH" >> /source.sh
RUN echo "source /source.sh" >> /root/.bashrc

# Entrypoint

WORKDIR /root/rtas25
ENTRYPOINT ["/bin/bash"]
