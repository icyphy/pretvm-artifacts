# This script uses run_benchmark.py to perform the performance experiment
# by running the performance benchmark twice, once with the NP scheduler
# and the other with the GEDF_NP scheduler.

import argparse
from pathlib import Path
from datetime import datetime
import run_benchmark
import pandas as pd
import seaborn as sns 
import matplotlib.pyplot as plt
import shutil
import imageio
import os
import re
import numpy as np
import pprint

# NOTE: Ensure that there is a credentials.py that defines the IP, username, and
# password of the target platform.
import credentials

################## CONFIGS ##################

# Platform config: RPI4, ODROID-XU4
PLATFORM = "RPI4"

# Number of times the programs are repeated
REPEAT = 10

# FIXME: This is completely useless!
# This is ONLY used for naming files.
# The script runs both LB and EGS regardless.
STATIC_SCHEDULER_NAMES = ["LB", "EGS"]

# Plot config
ANNOTATE_MEAN_STD = False

# If empty, the script runs the entire src directory.
# Input just the LF program name without the .lf extension.
# TIPS: Add a simple program here to test the script workflow.
SELECT_PROGRAMS = [] # e.g., "ADASModel", "PingPong"

# Exclude programs based on schedulers.
EXCLUDED_PROGRAMS = {
    "NP": [],
    "LB": [],
    "EGS": []
}

# Dash mode
DASH_MODE = False

# Generate GIF
GENERATE_GIF    = False
NUM_FRAMES      = 50
FPS             = 5

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
    help="Specify an existing experiment directory and run post processing only. E.g., performance/2024-03-03_23-18-51"
)

def extract_times_from_file(file_path):
    pattern = r"---- Elapsed physical time \(in nsec\): ([\d,]+)"
    times = []

    with open(file_path, 'r') as file:
        for line in file:
            match = re.search(pattern, line)
            if match:
                # Remove commas and convert the number to an integer
                time_value = int(match.group(1).replace(',', ''))
                times.append(time_value)
                
    return times

def calculate_statistics(times):
    if len(times) == 0:
        return None
    mean = np.mean(times)
    max_val = np.max(times)
    std_dev = np.std(times, ddof=1)  # Use ddof=1 for sample standard deviation
    return {"mean": mean, "max": max_val, "std": std_dev}

def generate_latex_table(program_names, program_stats, references, file_path):
    code = f"% Generated table at {file_path}\n"
    code += r"""
    \begin{table*}[ht]
        \centering
        \begin{tabular}{lcccccccccc}
        \toprule 
        & & \multicolumn{3}{c}{Average (us)} & \multicolumn{3}{c}{Maximum (us)} &
        \multicolumn{3}{c}{Standard Deviation (us)} \\ 
        \cmidrule(lr){3-5} \cmidrule(lr){6-8} \cmidrule(lr){9-11}
        Program & LoC (\lf) & DY & LB & EG & DY & LB & EG & DY & LB & EG \\ 
        \midrule 
    """
    for program in program_names:
        # .3g = 3 significant digits
        if program in list(program_stats['DY'].keys()):
            np_mean = format(program_stats['DY'][program]['mean'] / 1000, '.3g')
            np_max  = format(program_stats['DY'][program]['max'] / 1000, '.3g')
            np_std  = format(program_stats['DY'][program]['std'] / 1000, '.3g')
        else:
            np_mean = "-"
            np_max  = "-"
            np_std  = "-"
        if program in list(program_stats['LB'].keys()):
            lb_mean = format(program_stats['LB'][program]['mean'] / 1000, '.3g')
            lb_max  = format(program_stats['LB'][program]['max'] / 1000, '.3g')
            lb_std  = format(program_stats['LB'][program]['std'] / 1000, '.3g')
        else:
            lb_mean = "-"
            lb_max  = "-"
            lb_std  = "-"
        if program in list(program_stats['EGS'].keys()):
            egs_mean = format(program_stats['EGS'][program]['mean'] / 1000, '.3g')
            egs_max  = format(program_stats['EGS'][program]['max'] / 1000, '.3g')
            egs_std  = format(program_stats['EGS'][program]['std'] / 1000, '.3g')
        else:
            egs_mean = "-"
            egs_max  = "-"
            egs_std  = "-"
        code += f"\n\\texttt{{{program}}}"
        if references[program] is not None:
            code += f"~\cite{{{references[program]}}}"
        code += f"  & {program_stats['LOC'][program]}  & {np_mean} & {lb_mean} & {egs_mean} & {np_max} & {lb_max} & {egs_max} & {np_std} & {lb_std} & {egs_std} \\\\"
    code += r"""
        \bottomrule
        \end{tabular} 
        \caption{Average, maximum, and standard deviation of the
        benchmark execution times using the
        dynamic scheduler (DY), the static \textsc{Load
        Balanced} scheduler (LB), and the static \textsc{Edge Generation}
        scheduler (EGS).} 
        \label{tab:accuracy_results}
    \end{table*}
    """

    with open(file_path, 'w') as file:
        file.write(code)
    
def main(args=None):
    # Parse arguments.
    args = parser.parse_args(args)
    
    # Variable declarations
    expr_data_dirname = "experiment-data/"
    
    # Locate the benchmark directories
    script_path = Path(__file__).resolve() # Get the path to the script
    script_dir = script_path.parent
    benchmark_dir = script_dir.parent
    performance_benchmark_dir = benchmark_dir / "performance" / "src"
    performance_benchmark_srcgen = benchmark_dir / "performance" / "src-gen"
    
    # Create an experiment data directory, if none exist.
    expr_data_dir = benchmark_dir / expr_data_dirname
    expr_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a performance directory, if none exist.
    performance_dir = expr_data_dir / "performance"
    performance_dir.mkdir(exist_ok=True)
    
    # Create a directory for this experiment run.
    # Time at which the script starts
    if args.experiment_dir is None:
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format: Year-Month-Day_Hour-Minute-Second
        expr_run_dir = performance_dir / (time + "-" + PLATFORM + "-" + "_".join(STATIC_SCHEDULER_NAMES) + "-" + ("_".join(SELECT_PROGRAMS) if len(SELECT_PROGRAMS) > 0 else "ALL"))
        expr_run_dir.mkdir()
    else:
        expr_run_dir = performance_dir / args.experiment_dir
    np_dir = expr_run_dir / "NP"
    lb_dir = expr_run_dir / "LB"
    egs_dir = expr_run_dir / "EGS"
    
    # Storing plots
    plots_dir = expr_run_dir / "plots"
    plots_dir.mkdir(exist_ok=True)
    
    # Storing frames for creating GIFs
    if GENERATE_GIF:
        frames_dir = expr_run_dir / "frames"
        frames_dir.mkdir(exist_ok=True)
    
    if args.experiment_dir is None:
        # Prepare arguments for each run_benchmark call.
        args_1 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=NP", "-dd="+str(np_dir.resolve()), "--src=performance/src", "--src-gen=performance/src-gen"]
        args_2 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=STATIC", "-f=--mapper=LB", "-dd="+str(lb_dir.resolve()), "--src=performance/src", "--src-gen=performance/src-gen"]
        args_3 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=STATIC", "-f=--mapper=EGS", "-dd="+str(egs_dir.resolve()), "--src=performance/src", "--src-gen=performance/src-gen"]
        if DASH_MODE:
            args_2.append("-f=--dash")
            args_3.append("-f=--dash")

        # For performance experiments, turn off tracing.
        args_1.append("--no-tracing")
        args_2.append("--no-tracing")
        args_3.append("--no-tracing")

        # For performance experiments, repeat programs.
        args_1.append("--repeat="+str(REPEAT))
        args_2.append("--repeat="+str(REPEAT))
        args_3.append("--repeat="+str(REPEAT))

        # For performance experiments, turn on fast mode.
        # FIXME: lfc commandline has no --fast!
        # args_1.append("-f=--fast")
        # args_2.append("-f=--fast")
        # args_3.append("-f=--fast")
        
        # Select programs
        if len(SELECT_PROGRAMS) > 0:
            for prog in SELECT_PROGRAMS:
                args_1.append("--select="+prog)
                args_2.append("--select="+prog)
                args_3.append("--select="+prog)
                
        # Exclude programs based on scheduler.
        if len(EXCLUDED_PROGRAMS) > 0:
            for prog in EXCLUDED_PROGRAMS['NP']:
                args_1.append("--exclude="+prog)
            for prog in EXCLUDED_PROGRAMS['LB']:
                args_2.append("--exclude="+prog)
            for prog in EXCLUDED_PROGRAMS['EGS']:
                args_3.append("--exclude="+prog)
                
        # Run the benchmark runner using the NP and the STATIC scheduler.
        # NOTE: The 2nd run's src-gen is copied back the host. So it's better to
        # be static because we want to inspect the graphs.
        run_benchmark.main(args_1) # NP   
        run_benchmark.main(args_2) # LB
        run_benchmark.main(args_3) # EGS
        
        # Move the static src-gen to the experiment folder for record keeping.
        # Use shutil.copytree to copy the directory
        try:
            target_dir = expr_run_dir / "src-gen"
            shutil.copytree(performance_benchmark_srcgen, target_dir)
            print(f"Directory {performance_benchmark_srcgen} copied to {target_dir} successfully.")
        except Exception as e:
            print(f"Error occurred: {e}")
    
    # Get a list of benchmark names
    if len(SELECT_PROGRAMS) > 0:
        program_names = SELECT_PROGRAMS
    else:
        # Extract all program names from the benchmark directory.
        program_names = [str(file).split("/")[-1][:-3] for file in performance_benchmark_dir.glob('*') if file.is_file()]
    
    # Create a dictionary for program stats
    program_stats = {
        'DY':{}, 'LB':{}, 'EGS':{},
        'LOC':{
            'ADASModel': 91,
            'CoopSchedule': 54,
            'Counting': 179,
            'LongShort': 31,
            'Philosophers': 314,
            'PingPong': 124,
            'ThreadRing': 217,
            'Throughput': 166,
        },
    }

    references = {
        'ADASModel': 'lin2023lfverifier',
        'CoopSchedule': 'Jellum:23:RTOS',
        'Counting': 'menard2023performance',
        'LongShort': None,
        'Philosophers': 'menard2023performance',
        'PingPong': 'menard2023performance',
        'ThreadRing': 'menard2023performance',
        'Throughput': 'menard2023performance',
    }

    # Generate timing variation plots for each program.
    for program in program_names:
        
        txt_dy = np_dir / (program + ".txt")
        txt_lb = lb_dir / (program + ".txt")
        txt_egs = egs_dir / (program + ".txt")

        times_dy = extract_times_from_file(txt_dy)
        times_lb = extract_times_from_file(txt_lb)
        times_egs = extract_times_from_file(txt_egs)

        stats_dy = calculate_statistics(times_dy)
        stats_lb = calculate_statistics(times_lb)
        stats_egs = calculate_statistics(times_egs)

        if stats_dy is None: raise Exception(f"When running {program}, stats_dy is None.")
        if stats_lb is None: raise Exception(f"When running {program}, stats_lb is None.")
        if stats_egs is None: raise Exception(f"When running {program}, stats_egs is None.")

        stats_dy["data"] = times_dy
        stats_lb["data"] = times_lb
        stats_egs["data"] = times_egs

        program_stats['DY'][program] = stats_dy
        program_stats['LB'][program] = stats_lb
        program_stats['EGS'][program] = stats_egs

    generate_latex_table(program_names, program_stats, references, expr_run_dir / "table.tex")

    with open(expr_run_dir / "data.txt", "w") as file:
        pprint.pprint(program_stats, stream=file)

if __name__ == "__main__":
    main()