# Artifacts for Unified Quasi-Static Scheduling for Concurrent MoCs

## Getting started

### Requirements
- Linux environment, tested on Ubuntu 24.04
- Java 17, download [here](https://www.oracle.com/java/technologies/javase/jdk17-archive-downloads.html)


### Setup

1. Install dependencies
```shell
sudo apt install cmake verilator sbt 
```

2. Clone repo with submodule
```shell
git clone https://github.com/icyphy/pretvm-artifacts --recursive
```

3. Build the lingua franca compiler
```shell
cd lingua-franca
./gradlew assemble
```

4. Build the FlexPRET emulator

First download and install riscv-none-elf-gcc-14.2.0-2

```shell
  wget -q --show-progress https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases/download/v14.2.0-2/xpack-riscv-none-elf-gcc-14.2.0-2-linux-x64.tar.gz -O gcc.tar.gz
  tar xvf gcc.tar.gz --directory=/opt
```

Then source `env.bash` in the root of this artifact repo, it will add some environmental variables needed for the rest of the install and also when running programs

```shell
source env.bash
```

Then build the FlexPRET emulator and the FlexPRET SDK
```shell
cd flexpret
cmake -B build && cd build
make all install

cd sdk
cmake -B build && cd build
make
```

5. HelloWorld to verify installation
TODO: Add this step.


### WCET

You can either build the docker image yourself or pull it from dockerhub.

**Building it Yourself**
```bash
    $ sudo docker build ./docker -t einspaten/rtas25:v2
```

**Pulling it from Dockerhub**
```bash
    $ sudo docker pull einspaten/rtas25:v2
```

**Using the Docker Image**
```bash
    $ sudo docker run -ti -v ${PWD}/docker/:/root/rtas25/ -v ${PWD}/satellite-controller:/root/rtas25/satellite-controller -v ${PWD}/pretvm-instructions:/root/rtas25/pretvm-instructions einspaten/rtas25:v2
    $ ./analyse-all.sh
```

## TODOs
- [ ] Bring EGS as a submodule here and document how to set it up using a virtual environment etc,
- [ ] Create a FlexPRET config for the RTAS submission so others easily can build it  
- [ ] we should also add the source links here and how to run the script to compile and do WCET analysis
