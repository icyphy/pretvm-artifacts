# This script uses run_benchmark.py to perform the timing experiment
# by running the timing benchmark twice, once with the NP scheduler
# and the other with the GEDF_NP scheduler.

import argparse
from pathlib import Path
from datetime import datetime
import run_benchmark
import pandas as pd
import seaborn as sns 
import matplotlib.pyplot as plt
import shutil

# NOTE: Ensure that there is a credentials.py that defines the IP, username, and
# password of the target platform.
import credentials

################## CONFIGS ##################

# Platform config
PLATFORM = "RPI4"

# Static scheduler config
STATIC_SCHEDULER = "LOAD_BALANCED" # LOAD_BALANCED, EGS, or MOCASIN

# Plot config
ANNOTATE_MEAN_STD = True

# Programs selected
SELECT_PROGRAMS = []

#############################################

if PLATFORM == "RPI4":
    IP = credentials.IP_RPI4
    UN = credentials.UN_RPI4
    PW = credentials.PW_RPI4
elif PLATFORM == "ODROID-XU4":
    IP = credentials.IP_ODROID
    UN = credentials.UN_ODROID
    PW = credentials.PW_ODROID
else:
    raise Exception("The specified platform is not supported.")

parser = argparse.ArgumentParser()
parser.add_argument(
    "-ed",
    "--experiment-dir",
    type=str,
    help="Specify an existing experiment directory and run post processing only. E.g., timing/2024-03-03_23-18-51"
)
    
def main(args=None):
    # Parse arguments.
    args = parser.parse_args(args)
    
    # Variable declarations
    expr_data_dirname = "experiment-data/"
    
    # Locate the benchmark directories
    script_path = Path(__file__).resolve() # Get the path to the script
    script_dir = script_path.parent
    benchmark_dir = script_dir.parent
    benchmark_src = benchmark_dir / "savina" / "src" / "micro"
    benchmark_srcgen = benchmark_dir / "savina" / "src-gen" / "micro"
    
    # Create an experiment data directory, if none exist.
    expr_data_dir = benchmark_dir / expr_data_dirname
    expr_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a savina directory, if none exist.
    sub_expr_dir = expr_data_dir / "savina"
    sub_expr_dir.mkdir(exist_ok=True)
    
    # Create a directory for this experiment run.
    # Time at which the script starts
    if args.experiment_dir is None:
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format: Year-Month-Day_Hour-Minute-Second
        expr_run_dir = sub_expr_dir / (time + "-" + PLATFORM + "-" + STATIC_SCHEDULER)
        expr_run_dir.mkdir()
    else:
        expr_run_dir = expr_data_dir / args.experiment_dir
    np_dir = expr_run_dir / "NP"
    static_dir = expr_run_dir / "STATIC"
    
    plots_dir = expr_run_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    if args.experiment_dir is None:
        # Prepare arguments for each run_benchmark call.
        args_1 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=NP", "-dd="+str(np_dir.resolve()), "--no-tracing", "--src=savina/src/micro", "--src-gen=savina/src-gen/micro"]
        args_2 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=STATIC", "-f=--static-scheduler="+STATIC_SCHEDULER, "-dd="+str(static_dir.resolve()), "--no-tracing", "--src=savina/src/micro", "--src-gen=savina/src-gen/micro"]
        
        # Enter program selections
        if len(SELECT_PROGRAMS) > 0:
            for prog in SELECT_PROGRAMS:
                args_1.append("--select="+prog)
                args_2.append("--select="+prog)
                
        # Run the benchmark runner using the NP and the STATIC scheduler.
        # NOTE: The 2nd run's src-gen is copied back the host. So it's better to
        # be static because we want to inspect the graphs.
        run_benchmark.main(args_1) # NP   
        run_benchmark.main(args_2) # STATIC
        
        # Move the static src-gen to the experiment folder for record keeping.
        # Use shutil.copytree to copy the directory
        try:
            target_dir = expr_run_dir / "src-gen"
            shutil.copytree(benchmark_srcgen, target_dir)
            print(f"Directory {benchmark_srcgen} copied to {target_dir} successfully.")
        except Exception as e:
            print(f"Error occurred: {e}")
    
    # Get a list of benchmark names
    if len(SELECT_PROGRAMS) > 0:
        program_names = SELECT_PROGRAMS
    else:
        # Extract all program names from the benchmark directory.
        program_names = [str(file).split("/")[-1][:-3] for file in benchmark_src.glob('*') if file.is_file()]
        
    # Generate timing variation plots for each program.
    for program in program_names:
        
        pass

if __name__ == "__main__":
    main()