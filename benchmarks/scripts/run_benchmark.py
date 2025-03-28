#!/usr/bin/env python3

"""
This utility collects and processes tracing data of LF benchmarks running on top
of a RPi4. A logic analyzer can be used to collect the traces, otherwise, the LF
tracing mechasim is used.
The supported operation systems for the RPi4 are Raspbian and QNX. The utility 

The configuration includes:
    - The general purpose machine (called `host`) on top of which this utility 
      will run. The C code of the LF program will be generated on the host, 
      without being compiled. 
    - The embedded machine (a RPi4, called `remote`) on top of which the programs 
      will be run. The behavior is platform dependent:
        - In case of Raspbian: the C generated code will be copied to the remote, 
          compiled and will be executed. The generated `.lft` files will also be 
          converted into `.csv` on the remote, using `trace_to_csv` utility. Then, 
          the generated csv files will be copied back to the host.
        - In case of QNX: the C generated code will be cross-compiled on the host,
          then copied to the remote and executed. The generated `.lft` files will be
          copied to the host, and the `trace_to_csv` utility will be run on the host 
          to convert the `.lft` files into `.csv` files.
        - In both cases, thecolected `.csv` files will be stored in a directory that 
          is given as an argument to the script. 
    - In case, a logical analyzer is use, it will be connected to the host via USB, 
      and to the remote via its pins. 

Assumptions:
    - When using a logic analyser:
        - The host machine is a Linux machine (Ubuntu 20.04)
        - The startup and shutdown of the main reactor includes initializing and 
          finalyzing the remote host GPIO
        - Reactions include the needed trace instructions (toggling pins)
        - The LF program `cmake-include`s `pigpio.txt`. This links the needed library.
        - Every program has a companion csv file that describes the signals to trace.
          This is useful for processing the collected tracing data.
    - If the platform is QNX, it is assumed that:
        - The QNX support files are located under `benchmarks/timing/src/qnxSupport/`
        - The QNX toolchain is installed on the host machine.
        - The script (`qnxsdp-env.sh`) will already be ran on the terminal, before creating 
          the virtual environment. It is meant to set the environment variables (e.g., PATH,
          QNX_HOST, QNX_TARGET) needed to use the QNX Software Development Platform (SDP).
          This step ensures that QNX tools and compilers are accessible in the terminal 
          session.
        - EGS is installed on the host machine and the `egs.py` is made executable and added 
          to the PATH.

Procedure description (some of steps are optional, or platform dependent):
1. Process the arguments to retreive necessary information about the remote device.
2. Connect to the remote device. If unable to connect, then abort. Else, clean.
3. (Optional) Initialize the Logic 2 analyzer software 
4. For every LF program under src/ do:
    4.1. LF compile the program with --no-compile option
    4.2. If not QNX: secure copy the generated directory to the remote.
    4.3. If not QNX: Remotely compile (cmake and make) each program. (). run from ethat directory:
         If QNX: Corss-compile the program and copy the generated file to the remote.
    4.4. (Optional) Start capturing the trace in the host (or if tracing is used, do nothing.)
    4.5. Remotely run all programs (check first if a superuser privilege is needed)
    4.6. If not QNX: Run tracing remotely to get a non-empty trace files and generate csv. 
            Then secury copy the csv files to the host.
         If QNX: Secure copy the generated trace files to the host, then convert them to csv (on the host).
            NOTE: A strange behavior was observed when secure copying the binary `.lft` files
            from the remote to the host. The files were empty. The same command, when ran from the terminal
            instead of the python script, is correct. As a workaround, the `.lft` files were renamed as 
              `.txt` files on the remote, transfered, and the renamed again ad `.lft` in the host.
    4.7. (Optional) Once done, stop the analyser software and save the tracing data (or if
    tracing is used, scp trace data back to host.)
    4.8. Close connection to remote host
5. (Optional) Process the tracing data

Dependencies:
- sshpass (for allowing passing in password on the commandline)
  Only use this script for non-safety-critical boards. This is NOT secure!
"""

import argparse
import paramiko  # pip install paramiko

# from saleae import automation   # pip install logic2-automation
import sys
import csv
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Define the arguments to pass in the command line
# The values default to
parser = argparse.ArgumentParser(description="Set of the lft trace files to render.")
parser.add_argument("-hn", "--hostname", type=str, help="Hostname of the RPi.", default="raspberrypi.local")
parser.add_argument("-un", "--username", type=str, help="Username", default="pi")
parser.add_argument("-pwd", "--password", type=str, help="Password", default="raspberry")
parser.add_argument(
    "-f",
    "--flag",
    type=str,
    action='append',
    help="Set a flag passed into the LF compiler (--flag can be specified multiple times)",
)
parser.add_argument(
    "-s",
    "--select",
    type=str,
    action='append',
    help="Select a list of programs to run instead of the entire directory (--select can be specified multiple times). No .lf extension is needed.",
)
parser.add_argument(
    "-e",
    "--exclude",
    type=str,
    action='append',
    help="Exclude a list of programs from running (--exclude can be specified multiple times). No .lf extension is needed. --exclude takes priority over --select.",
)
parser.add_argument(
    "-nt",
    "--no-tracing",
    action="store_true",
    help="Do not use tracing, simply observe outputs.",
)
parser.add_argument(
    "--src",
    type=str,
    help="Specify a src directory containing the LF programs"
)
parser.add_argument(
    "--src-gen",
    type=str,
    help="Specify the src-gen directory for the generated code from LFC. This needs to correspond to the src path."
)
parser.add_argument(
    "-dd",
    "--data-dir",
    type=str,
    help="Specify a directory to store the CSVs returned from the embedded board"
)
parser.add_argument(
    "-p",
    "--post-analysis",
    type=str,
    help="Specify a python script for post analysis"
)
parser.add_argument(
    "--post-only", action="store_true", help="Only perform post analyses, skip all steps involving the remote platform."
)
parser.add_argument(
    "--repeat", type=int, default=0, help="The number of times the LF program should repeat (for performance benchmarking)"
)
parser.add_argument(
    "-nl", "--no-lfc", action="store_true", help="Skip re-compiling the LF code if src-gen already exists."
)
parser.add_argument(
    "-ns", "--no-scp", action="store_true", help="Skip secure copying the LF code if src-gen is already copied."
)
parser.add_argument(
    "-nc", "--no-cmake", action="store_true", help="Skip compiling cmake projects if src-gen is already compiled."
)
parser.add_argument("-nr", "--no-run", action="store_true", help="Skip running the compiled programs.")
parser.add_argument("-np", "--no-parse", action="store_true", help="Skip conversion of traces to csv")
# Creat the SSh client
client = paramiko.SSHClient()
# Veryfing host keys
client.load_system_host_keys()
# OR: Since this is meant to run on a private local network, we can avoid verifying
# host key, using AutoAddPolicy
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())


####################################################
###############    Host Functions    ###############
####################################################


def host_close_connection_to_remote():
    # Close the client itself
    client.close()


def host_compile_lf_file(args, filename):
    # cmd = ["lfc-dev", "-n", f"{args.flags}", f"{filename}"]
    cmd = ["lfc-dev", "-n"]
    if not args.no_tracing:
        cmd.append("--tracing")
    cmd += args.flag + [filename]
    print("Executing local command: " + " ".join(cmd))
    result = host_execute_cmd(cmd)
    print("Exit code:", result.returncode)
    print("Output:", result.stdout)
    print("Error:", result.stderr)


def host_compile_lf_files_in_dir(args, dir, selected, excluded):
    # Enumerate over files in the directory
    for filename in os.listdir(dir):
        if filename.endswith(".lf"):
            if filename not in excluded:
                if selected is None or filename in selected:
                    file_path = os.path.join(dir, filename)
                    print(file_path)
                    host_compile_lf_file(args, file_path)


def host_connect_to_remote(args):
    try:
        # When automated on a runner, it is possible to use client.load_system_host_keys()
        client.connect(args.hostname, username=args.username, password=args.password)
        return True
    except Exception as e:
        print(e)
        return False


def host_create_dir(dir):
    cmd = ["mkdir", "-p", dir]
    result = host_execute_cmd(cmd)
    print("Exit code:", result.returncode)
    print("Output:", result.stdout)
    print("Error:", result.stderr)


def host_execute_cmd(cmd, shell=False):
    print("Executing command: " + str(cmd))
    # Enable the lf conda environment and inherit the current environment.
    env = os.environ.copy()
    # subprocess.run('bash -c "conda deactivate base; conda activate lf; python -V"', shell=shell, env=env)
    return subprocess.run(cmd, shell=shell, capture_output=True, text=True, encoding='ISO-8859-1', env=env)


# Note: func must accept full_entry_path as the first argument and has at most
# two other arguments.
def host_forall_subdirs_do(func, dir, arg1=None, arg2=None, arg3=None):
    for entry in os.listdir(dir):
        full_entry_path = os.path.join(dir, entry)
        # Check if the entry is a directory
        if os.path.isdir(full_entry_path):
            func(full_entry_path, arg1, arg2, arg3)


def host_rm_dir(dir):
    cmd = ["rm", "-rf", dir]
    result = host_execute_cmd(cmd)
    print("Exit code:", result.returncode)
    print("Output:", result.stdout)
    print("Error:", result.stderr)


def host_scp_dir(src, dest, args, from_host_to_remote=True):
    _src = src
    _dest = dest
    remote_prefix = f"{args.username}@{args.hostname}:"
    if from_host_to_remote:
        _dest = remote_prefix + _dest
    else:
        _src = remote_prefix + _src
    # Construct the scp command
    scp_command = f'sshpass -p "{args.password}" scp -r {_src} {_dest}'
    print(f"Executing: {scp_command}")
    # Execute the scp command
    # FIXME: For some reason, to execute this command on macOS, shell must be
    # True, otherwise the OS returns a File Not Found error.
    result = host_execute_cmd(scp_command, shell=True)
    # Check result
    if result.returncode == 0:
        print(f"Successfully copied {_src} to {_dest}")
    else:
        print(f"Error copying {_src} to {_dest}: {result.stderr}")


def host_process_trace_data():
    return 1


####################################################
###############   Remote Functions   ###############
####################################################


# FIXME: How to remove arg1 and arg2?
def remote_compile_cmake_project(dir, arg1, arg2, arg3):
    print("Compiling: " + dir)
    cmd = f"cd {dir} ; mkdir build ; cd build ; cmake .. ; make"
    _, _, stderr = remote_execute_cmd(cmd)
    remote_print(stderr, is_err=True)


def remote_create_dir(dir):
    command = f"mkdir -p {dir}"
    remote_execute_cmd(command)


def remote_execute_cmd(cmd):
    print("Executing remote command: " + cmd)
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdin, stdout, stderr


def remote_forall_files_in_dir_do(func, dir, arg1=None, arg2=None, arg3=None):
    ls_command = f"find {dir} -maxdepth 1 -type f"  # List all files under the remote dir.
    _, stdout, _ = remote_execute_cmd(ls_command)
    files = stdout.readlines()
    files = [file.strip() for file in files]
    print(files)
    for file in files:
        func(file, arg1, arg2, arg3)


# Note: func must accept full_entry_path as the first argument and has at most
# two other arguments.
def remote_forall_subdirs_do(func, dir, arg1=None, arg2=None, arg3=None):
    ls_command = f"ls -d {dir}/*/"  # List all subdirs under the remote dir.
    _, stdout, _ = remote_execute_cmd(ls_command)
    dirs = stdout.readlines()
    dirs = [dir.strip() for dir in dirs]
    print(dirs)
    for _dir in dirs:
        func(_dir, arg1, arg2, arg3)


def remote_print(stdout_or_stderr, is_err=False):
    """
    Performing a read() on stdout or stderr changes its state,
    so this is not done by default in remote_execute_cmd.
    This is a helper function for explicitly printing outputs.    
    """
    prefix = "STDOUT"
    if is_err:
        prefix = "STDERR"
    print(f'{prefix}:{stdout_or_stderr.read().decode("utf8")}')


def remote_rm_dir(dir):
    cmd = f"rm -rf {dir}"
    _, stdout, stderr = remote_execute_cmd(cmd)
    remote_print(stdout)
    remote_print(stderr, is_err=True)


def remote_run_program(dir, data_dir, command_line_args, arg3=None):
    """
    Extract the binary name
    Assuming the binary name is the last part of the dir path.
    E.g., path = /home/nkagamihara/benchmarks/CoopSchedule/,
    then bin = CoopSchedule.
    Since we first cd into data_dir, the trace file is generated
    there too. This directory is likely stored in the remote_data variable.
    """
    bin = os.path.basename(os.path.normpath(dir))
    cmd = f"cd {data_dir}"
    if (command_line_args.repeat == 0):
        cmd += f" && {dir}build/{bin}"
    else:
        # Repeat the execution and write outputs in a txt file.
        cmd += f" && for i in {{1..{command_line_args.repeat}}}; do {dir}build/{bin}; done > {bin}.txt"
    if not command_line_args.no_tracing:
        cmd += f" && mv main_0.lft {bin}.lft" # Rename the .lft file to that we know which is which.
    _, stdout, stderr = remote_execute_cmd(cmd)
    remote_print(stdout)
    remote_print(stderr, is_err=True)
    

def remote_run_trace_conversion(file, dir, convert_for_chrome=False, arg3=None):
    convert_command = f"cd {dir} && trace_to_csv {file}"
    if convert_for_chrome:
        convert_command += f" && trace_to_chrome {file}"
    print(convert_command)
    _, stdout, stderr = remote_execute_cmd(convert_command)
    remote_print(stdout)
    remote_print(stderr, is_err=True)


####################################################
###############         Main         ###############
####################################################


def main(args=None):
    
    # Step 1.
    args = parser.parse_args(args)
    
    # Get the path to the script
    script_path = Path(__file__).resolve()
    script_dir = script_path.parent
    benchmarks_dir = script_dir.parent
    
    if args.src is None:
        print("--src is not specified! Abort.")
        exit(1)
    if args.src_gen is None:
        print("--src-gen is not specified! Abort.")
        exit(1)

    # Host directories
    host_src = benchmarks_dir / args.src
    host_src_gen = benchmarks_dir / args.src_gen
    host_data = benchmarks_dir / "data"

    # Remote directories
    remost_dest = "~/benchmarks"
    remote_data = "~/benchmarks-data"
    
    # Time at which the script starts
    time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format: Year-Month-Day_Hour-Minute-Second

    # Check if the --post-only flag is set. If so, skip all prior steps and just
    # perform post analyses.
    if not args.post_only:

        # Step 2.
        if not host_connect_to_remote(args):
            print("Run Benchmark: Cannot connect to host! Abort.")
            sys.exit(1)
        else:
            print("Run Benchmark: Connected to remote host " + args.hostname + ".")

        # Step 3 (skipped).
        remote_execute_cmd("hostname")

        # Step 4.1.
        selected = None
        excluded = []
        if args.select is not None:
            selected = [prog + ".lf" for prog in args.select] # Add the .lf extension.
        if args.exclude is not None:
            excluded = [prog + ".lf" for prog in args.exclude] # Add the .lf extension.
        if not args.no_lfc:
            host_rm_dir(host_src_gen)
            host_compile_lf_files_in_dir(args, host_src, selected, excluded)

        # Step 4.2.
        if not args.no_scp:
            remote_rm_dir(remost_dest)
            remote_create_dir(remost_dest)
            host_forall_subdirs_do(host_scp_dir, host_src_gen, remost_dest, args, True)

        # Step 4.3
        if not args.no_cmake:
            remote_forall_subdirs_do(remote_compile_cmake_project, remost_dest)

        # Step 4.4
        # Skipped. Assuming tracing is in use

        if not args.no_run:
            # Step 4.5: run programs and collect trace files in a remote data directory.
            remote_rm_dir(remote_data)
            remote_create_dir(remote_data)
            remote_forall_subdirs_do(func=remote_run_program, dir=remost_dest, arg1=remote_data, arg2=args)
            
            # Step 4.6: run tracing remotely
            if not args.no_tracing:
                convert_for_chrome = True
                remote_forall_files_in_dir_do(remote_run_trace_conversion, remote_data, remote_data, convert_for_chrome)

                # Step 4.7
                host_create_dir(host_data)

                if args.data_dir is None:
                    data_entry_dir = host_data / time
                else:
                    data_entry_dir = args.data_dir
                host_scp_dir(remote_data, data_entry_dir, args, from_host_to_remote=False)
            
            # If this is true, we are doing performance benchmarking.
            # Copy the txt file back to host.
            elif args.repeat > 0:
                if args.data_dir is None:
                    data_entry_dir = host_data / time
                else:
                    data_entry_dir = args.data_dir
                host_scp_dir(remote_data, data_entry_dir, args, from_host_to_remote=False)
            
        # Step 4.8
        host_close_connection_to_remote()

    # Step 5: Post-Processing
    if args.post_analysis is not None:
        with open(args.post_analysis, "r") as file:
            script_content = file.read()
        exec(script_content)
    
if __name__ == "__main__":
    main()
