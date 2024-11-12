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
import imageio
import os

# NOTE: Ensure that there is a credentials.py that defines the IP, username, and
# password of the target platform.
import credentials

################## CONFIGS ##################

# Platform config: RPI4, ODROID-XU4
PLATFORM = "RPI4"

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
    help="Specify an existing experiment directory and run post processing only. E.g., timing/2024-03-03_23-18-51"
)

def post_process_timing_precision(csv):
    try:
        df = pd.read_csv(csv)
    except FileNotFoundError:
        print("ERROR: file not found - " + str(csv))
        return None
    
    # Strip leading and trailing spaces from column names
    df.columns = df.columns.str.strip()
    
    # Keep only "Reaction starts" events
    df = df[df['Event'] == 'Reaction starts']
    
    # Remove rows where 'Reactor' starts with 'delay' and 'NO REACTOR'
    df['Reactor'] = df['Reactor'].str.strip()
    df = df[~df['Reactor'].str.startswith('delay')]
    df = df[~df['Reactor'].str.startswith('NO REACTOR')]
    
    # Sort the DataFrame by 'Reactor', 'Destination', and 'Elapsed Physical Time'
    df = df.sort_values(by=['Reactor', 'Destination', 'Elapsed Physical Time'])
    
    # Group by Reactor and Destination
    groups = df.groupby(['Reactor', 'Destination'])
    
    # Group by 'Reactor' and 'Destination', then calculate the difference in 'Elapsed Physical Time'
    df['Time Difference'] = groups['Elapsed Physical Time'].diff()
    
    # Remove rows with NaN 'Time Difference'
    df = df.dropna(subset=['Time Difference'])
    
    # Calculate standard deviation for 'Time Difference' in each group
    std_deviation = groups['Time Difference'].std()

    # Printing standard deviations
    print("Standard Deviations of Time Differences for each Group:")
    print(std_deviation)
    
    return df

def post_process_timing_accuracy(csv):
    try:
        df = pd.read_csv(csv)
    except FileNotFoundError:
        return None
    
    # Strip leading and trailing spaces from column names
    df.columns = df.columns.str.strip()
    
    # Keep only "Reaction starts" events
    df = df[df['Event'] == 'Reaction starts']
    
    # Remove rows where 'Reactor' starts with 'delay' and 'NO REACTOR'
    df['Reactor'] = df['Reactor'].str.strip()
    df = df[~df['Reactor'].str.startswith('delay')]
    df = df[~df['Reactor'].str.startswith('NO REACTOR')]
    
    # Sort the DataFrame by 'Reactor', 'Destination', and 'Elapsed Physical Time'
    df = df.sort_values(by=['Reactor', 'Destination', 'Elapsed Physical Time'])
    
    # Group by Reactor and Destination
    grouped = df.groupby(['Reactor', 'Destination'])
    
    # Define a custom function to filter out the initial rows based on "Elapsed Logical Time"
    def filter_initial_rows(group):
        # Filter out initial rows
        filtered_group = group[group['Elapsed Logical Time'] >= 20000000]
        if len(filtered_group) > 1:
            # FIXME: The goal here is to remove data points from the shutdown
            # phase, which usually spans the last logical tag. If this
            # assumption is not respected, this strategy no longer works.
            
            # Find the maximum 'Elapsed Logical Time' in the filtered group
            max_elapsed_logical_time = filtered_group['Elapsed Logical Time'].max()
            
            # Filter out the rows with the maximum 'Elapsed Logical Time'
            filtered_group = filtered_group[filtered_group['Elapsed Logical Time'] < max_elapsed_logical_time]
            
            # Return the filtered group only if it contains >= 20 rows after all filters
            return filtered_group if len(filtered_group) >= 20 else None
        else:
            return None
    
    # Remove the first "reaction starts" data point for each group.
    df_filtered = grouped.apply(filter_initial_rows)
    
    # Calculate lag, i.e., elapsed physical time - elasped logical time.
    df_filtered['Lag'] = df_filtered['Elapsed Physical Time'] - df_filtered['Elapsed Logical Time']
    
    # Add a 'Group' column for easier handling in plotting
    df_filtered['Group'] = df_filtered.apply(lambda x: f"{x['Reactor']}, {x['Destination']}", axis=1)

    return df_filtered

def extract_timing_accuracy_outliers(df):
    # Calculate the IQR for 'Lag'
    Q1 = df['Lag'].quantile(0.25)
    Q3 = df['Lag'].quantile(0.75)
    IQR = Q3 - Q1

    # Define the criteria for an outlier
    is_outlier = ((df['Lag'] > (Q3 + 1.5 * IQR)) | (df['Lag'] < (Q1 - 1.5 * IQR)))

    # Filter the DataFrame to extract outliers
    outliers_df = df[is_outlier]

    return outliers_df

def post_process_execution_time(csv):
    try:
        df = pd.read_csv(csv)
    except FileNotFoundError:
        return None
    
    # Strip leading and trailing spaces from column names
    df.columns = df.columns.str.strip()
    
    # Filter out rows without 'Reaction starts' or 'Reaction ends'
    df = df[(df['Event'] == 'Reaction starts') | (df['Event'] == 'Reaction ends')]
    
    df['Reactor'] = df['Reactor'].str.strip()
    df = df[~df['Reactor'].str.startswith('delay') & ~df['Reactor'].str.startswith('NO REACTOR')]
    df = df.sort_values(by=['Reactor', 'Destination', 'Elapsed Physical Time'])
    
    # Calculate execution times
    starts = df[df['Event'] == 'Reaction starts'].groupby(['Reactor', 'Destination']).first().reset_index()
    ends = df[df['Event'] == 'Reaction ends'].groupby(['Reactor', 'Destination']).first().reset_index()
    
    execution_times = ends['Elapsed Physical Time'] - starts['Elapsed Physical Time']
    starts['Execution Time'] = execution_times
    
    return starts

def post_process_instruction_execution_times(csv):
    try:
        df = pd.read_csv(csv)
    except FileNotFoundError:
        return None
    
    # Strip leading and trailing spaces from column names
    df.columns = df.columns.str.strip()
    
    # Remove EXE, DU, WU, and WLT
    df = df[~df['Event'].str.contains('EXE|DU|WLT|WU|End EXE|End DU|End WLT|End WU')]
    
    # Filter to keep only relevant events
    df = df[df['Event'].str.contains('ADD|ADDI|ADV|ADVI|BEQ|BGE|BLT|BNE|DU|JAL|JALR|STP|WLT|WU|End')]

    # Separate start and end events
    start_events = df[~df['Event'].str.startswith('End')].copy()
    end_events = df[df['Event'].str.startswith('End')].copy()
    
    # Sort both data frames by Worker and Elapsed physical time
    start_events = start_events.sort_values(by=['Source', 'Elapsed Physical Time'])
    end_events = end_events.sort_values(by=['Source', 'Elapsed Physical Time'])
    
    start_events.reset_index(drop=True, inplace=True)
    end_events.reset_index(drop=True, inplace=True)

    # Remove 'End ' prefix from end events to align with start events
    end_events['Event'] = end_events['Event'].str.replace('End ', '')

    # Renaming end_events columns
    end_events.rename(columns=lambda x: 'End_' + x if x != 'Elapsed Physical Time' else x, inplace=True)
    
    # Rename columns for clarity if needed
    start_events.rename(columns={'Elapsed Physical Time': 'Start Time'}, inplace=True)
    end_events.rename(columns={'Elapsed Physical Time': 'End Time'}, inplace=True)

    # Concatenate start and end events to calculate execution times
    execution_times_df = pd.concat([start_events, end_events], axis=1)
    
    # Calculate instruction execution time
    execution_times_df['Instruction Execution Time'] = execution_times_df['End Time'] - execution_times_df['Start Time']
    
    # Prepare for plotting
    execution_times_df['Group'] = execution_times_df['Event'] + ", " + execution_times_df['Source'].astype(str)

    return execution_times_df

def combine_df(df_np, df_lb, df_egs):
    data_frames = []
    if df_np is not None: 
        df_np['Dataset'] = 'DY'
        data_frames.append(df_np)
    if df_lb is not None: 
        df_lb['Dataset'] = 'LB'
        data_frames.append(df_lb)
    if df_egs is not None: 
        df_egs['Dataset'] = 'EGS'
        data_frames.append(df_egs)
    
    # Combine the data from DY and STATIC datasets
    combined_df = pd.concat(data_frames).reset_index(drop=True)
    combined_df['Group'] = combined_df['Reactor'] + ", " + combined_df['Destination'].astype(str)

    # Further filter to remove groups that don't have any data
    # This is done by filtering groups with size > 0
    group_sizes = combined_df.groupby('Group').size()
    valid_groups = group_sizes[group_sizes > 0].index
    combined_df = combined_df[combined_df['Group'].isin(valid_groups)]
    
    return combined_df

def generate_plot_timing_precision(plots_dir, program, df):

    # Now, 'combined_df' contains only groups with data
    plt.figure(figsize=(12, 8))
    ax = sns.boxplot(x='Group', y='Time Difference', hue='Dataset', data=df, palette="Set3")

    # If enabled, annotate the plot with mean and std.
    if ANNOTATE_MEAN_STD:
        # Calculate means and standard deviations for annotations
        stats_df = df.groupby(['Group', 'Dataset'])['Time Difference'].agg(['mean', 'std']).reset_index()
        
        # Variables to adjust the position of the annotations for readability
        hue_order = ['DY', 'LB', 'EGS']  # Adjust based on your actual hue order
        width = 0.35  # Approximate width of the bars
        for i, group in enumerate(df['Group'].unique()):
            for j, scheduler in enumerate(hue_order):
                # Extract mean and std for the current group and hue
                means = stats_df[(stats_df['Group'] == group) & (stats_df['Dataset'] == scheduler)]['mean'].values
                stds = stats_df[(stats_df['Group'] == group) & (stats_df['Dataset'] == scheduler)]['std'].values
                
                # Check if means and stds have value. They could be empty if
                # there is only one single data point.
                if means.size == 0: continue
                else: mean = means[0]
                if stds.size == 0: continue
                else: std = stds[0]
                
                # Position of the annotations
                x_pos = i + width * (j - 0.5)  # Adjust this formula as needed
                y_pos = df[(df['Group'] == group) & (df['Dataset'] == scheduler)]['Time Difference'].max()  # Top of the box
                
                # Annotate the plot with mean and std
                plt.text(x_pos, y_pos, f'{scheduler}\nMean: {mean:.2f}\nSTD: {std:.2f}', ha='center', va='bottom')

    plt.title("Timing Precision: DY vs. STATIC" + " (" + ", ".join(STATIC_SCHEDULER_NAMES) + ")")
    plt.xlabel('Group (Reactor, Destination)')
    plt.ylabel('Time Difference')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(f"{plots_dir}/{program}_timing_precision.svg", format='svg')

def generate_group_statistics(df, plots_dir, program):
    # Calculate means, standard deviations, and maxes for all groups.
    aggregated_stats = df.groupby(['Group', 'Dataset'])['Lag'].agg(['mean', 'std', 'max']).reset_index()

    # Save to JSON file
    json_filename = f"{plots_dir}/{program}_timing_accuracy_stats.json"
    aggregated_stats.to_json(json_filename, orient='records', indent=4)

    return aggregated_stats

def generate_program_statistics(df):
    # Calculate means, standard deviations, and maxes directly.
    mean_lag = df['Lag'].mean()
    std_lag = df['Lag'].std()
    max_lag = df['Lag'].max()
    
    # Create a dictionary with the calculated statistics.
    aggregated_stats = {
        'mean': mean_lag,
        'std': std_lag,
        'max': max_lag
    }

    return aggregated_stats

def generate_plot_timing_accuracy(plots_dir, program, df):
    
    # Sample in case data set is very large.
    n_samples = min(len(df), 10000)
    sampled_df = df.sample(n=n_samples)

    # Now, 'combined_df' contains only groups with data
    plt.figure(figsize=(12, 8))
    hue_order = ['DY', 'LB', 'EGS']
    ax = sns.stripplot(x='Group', y='Lag', hue='Dataset', hue_order=hue_order, palette='flare', data=sampled_df, size=7, jitter=True, dodge=True)
    
    # Generate and save statistics to JSON
    stats_df = generate_group_statistics(df, plots_dir, program)
    
    # If enabled, annotate the plot with mean and std.
    if ANNOTATE_MEAN_STD:
        # Variables to adjust the position of the annotations for readability
        width = 0.2  # Approximate width of the bars
        for i, group in enumerate(df['Group'].unique()):
            for j, scheduler in enumerate(hue_order):
                # Extract mean and std for the current group and hue
                means = stats_df[(stats_df['Group'] == group) & (stats_df['Dataset'] == scheduler)]['mean'].values
                stds = stats_df[(stats_df['Group'] == group) & (stats_df['Dataset'] == scheduler)]['std'].values
                
                # Check if means and stds have value. They could be empty if
                # there is only one single data point.
                if means.size == 0: continue
                else: mean = means[0]
                if stds.size == 0: continue
                else: std = stds[0]
                
                # Position of the annotations
                x_pos = i + width * (j - 0.5)  # Adjust this formula as needed
                y_pos = df[(df['Group'] == group) & (df['Dataset'] == scheduler)]['Lag'].max()  # Top of the box
                
                # Annotate the plot with mean and std
                plt.text(x_pos, y_pos, f'{scheduler}\nMean: {mean:.2f}\nSTD: {std:.2f}', ha='center', va='bottom')

    plt.title("Timing Accuracy: DY vs. STATIC" + " (" + ", ".join(STATIC_SCHEDULER_NAMES) + ")")
    plt.xlabel('Group (Reactor, Destination)')
    plt.ylabel('Lag')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(f"{plots_dir}/{program}_timing_accuracy.svg", format='svg')

def generate_plot_reaction_execution_time(plots_dir, program, df):    
    plt.figure(figsize=(12, 8))
    ax = sns.boxplot(x='Group', y='Execution Time', hue='Dataset', data=df, palette="Set2")
    
    # Annotate each plot with mean, std, and max
    groups = df['Group'].unique()
    for i, group in enumerate(groups):
        group_df = df[df['Group'] == group]
        mean = group_df['Execution Time'].mean()
        std = group_df['Execution Time'].std()
        max_time = group_df['Execution Time'].max()
        
        # Positioning for the text annotation
        x = i
        # Adjust y position as needed, placing annotations at the top
        y = ax.get_ylim()[1]  # Get the current upper limit of the y-axis to position the annotation
        plt.text(x, y, f'Mean: {mean:.2f}\nSTD: {std:.2f}\nMax: {max_time}', ha='center', va='bottom', rotation=70, fontsize=9)
        
    plt.title("Execution Times: DY vs. STATIC" + " (" + ", ".join(STATIC_SCHEDULER_NAMES) + ")")
    plt.xlabel('Group (Reactor, Destination)')
    plt.ylabel('Execution Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(f"{plots_dir}/{program}_execution_time.svg", format='svg')
    
def generate_plot_vm_execution_time(plots_dir, program, df):
    plt.figure(figsize=(12, 8))
    ax = sns.boxplot(x='Group', y='Instruction Execution Time', data=df, palette="Set2")

    # Annotate each plot with mean, std, and max
    groups = df['Group'].unique()
    for i, group in enumerate(groups):
        group_df = df[df['Group'] == group]
        mean = group_df['Instruction Execution Time'].mean()
        std = group_df['Instruction Execution Time'].std()
        max_time = group_df['Instruction Execution Time'].max()
        
        # Positioning for the text annotation
        x = i
        # Adjust y position as needed, placing annotations at the top
        y = ax.get_ylim()[1]  # Get the current upper limit of the y-axis to position the annotation
        plt.text(x, y, f'Mean: {mean:.2f}\nSTD: {std:.2f}\nMax: {max_time}', ha='center', va='bottom', rotation=70, fontsize=9)

    plt.title("Instruction Execution Times")
    plt.xlabel('Instruction Type, Source')
    plt.ylabel('Instruction Execution Time')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot
    plt.savefig(f"{plots_dir}/{program}_vm_execution_time.svg", format='svg')

def create_animation_timing_accuracy(program, df_np, df_lb, plots_dir, frames_dir, gif_name, num_frames=50, fps=5):
    # Ensure directories exist
    os.makedirs(frames_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    
    # Sort the DataFrame by 'Reactor', 'Destination', and 'Elapsed Physical Time'
    df_np = df_np.sort_values(by=['Elapsed Physical Time'])
    df_lb = df_lb.sort_values(by=['Elapsed Physical Time'])

    # Calculate the total number of frames needed based on the largest dataset
    max_length = max(len(df_np), len(df_lb))
    chunk_size = max_length // num_frames + (1 if max_length % num_frames > 0 else 0) 

    # Generate each frame
    for frame in range(num_frames):
        plt.clf()
        plt.figure(figsize=(12, 8))

        # Current end index for each dataset
        end_idx_np = min((frame + 1) * chunk_size, len(df_np))
        end_idx_lb = min((frame + 1) * chunk_size, len(df_lb))
        
        # Combine the current chunks from both datasets
        current_df_np = df_np.iloc[:end_idx_np]
        current_df_lb = df_lb.iloc[:end_idx_lb]
        current_combined_df = pd.concat([current_df_np, current_df_lb])
        
        # Generate and plot the current combined DataFrame
        ax = sns.boxplot(x='Group', y='Lag', hue='Dataset', data=current_combined_df, palette="Set3")
        
        plt.xticks(rotation=45)
        plt.xlabel('Group (Reactor, Destination)')
        plt.ylabel('Lag')
        plt.title("Timing Accuracy: DY vs. STATIC")
        plt.tight_layout()

        # Save the current frame
        frame_path = os.path.join(frames_dir, f'{program}_frame_{frame:04}.png')
        plt.savefig(frame_path)
        plt.close()

    # Compile all frames into a GIF
    frame_filenames = sorted([os.path.join(frames_dir, f) for f in os.listdir(frames_dir) if f.startswith(f'{program}_frame_')])
    images = [imageio.imread(filename) for filename in frame_filenames]
    gif_path = os.path.join(plots_dir, gif_name)
    imageio.mimsave(gif_path, images, fps=fps)

def generate_latex_table(program_names, program_stats, file_path):
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
        code += f"\n\\texttt{{{program}}}  & {program_stats['LOC'][program]}  & {np_mean} & {lb_mean} & {egs_mean} & {np_max} & {lb_max} & {egs_max} & {np_std} & {lb_std} & {egs_std} \\\\"
    code += r"""
        \bottomrule
        \end{tabular} 
        \caption{Average, maximum, and standard deviation of the lags in microseconds of the
        dynamic scheduler (DY), the static \textsc{Load
        Balanced} scheduler (LB), and the static \textsc{Edge Generation}
        scheduler (EG).} 
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
    timing_benchmark_dir = benchmark_dir / "timing" / "src"
    timing_benchmark_srcgen = benchmark_dir / "timing" / "src-gen"
    
    # Create an experiment data directory, if none exist.
    expr_data_dir = benchmark_dir / expr_data_dirname
    expr_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a timing directory, if none exist.
    timing_dir = expr_data_dir / "timing"
    timing_dir.mkdir(exist_ok=True)
    
    # Create a directory for this experiment run.
    # Time at which the script starts
    if args.experiment_dir is None:
        time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Format: Year-Month-Day_Hour-Minute-Second
        expr_run_dir = timing_dir / (time + "-" + PLATFORM + "-" + "_".join(STATIC_SCHEDULER_NAMES) + "-" + ("_".join(SELECT_PROGRAMS) if len(SELECT_PROGRAMS) > 0 else "ALL"))
        expr_run_dir.mkdir()
    else:
        expr_run_dir = timing_dir / args.experiment_dir
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
        args_1 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=NP", "-dd="+str(np_dir.resolve()), "--src=timing/src", "--src-gen=timing/src-gen"]
        args_2 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=STATIC", "-f=--mapper=LB", "-dd="+str(lb_dir.resolve()), "--src=timing/src", "--src-gen=timing/src-gen"]
        args_3 = ["-hn=" + IP, "-un=" + UN, "-pwd=" + PW, "-f=--scheduler=STATIC", "-f=--mapper=EGS", "-dd="+str(egs_dir.resolve()), "--src=timing/src", "--src-gen=timing/src-gen"]
        if DASH_MODE:
            args_2.append("-f=--dash")
            args_3.append("-f=--dash")
        
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
            shutil.copytree(timing_benchmark_srcgen, target_dir)
            print(f"Directory {timing_benchmark_srcgen} copied to {target_dir} successfully.")
        except Exception as e:
            print(f"Error occurred: {e}")
    
    # Get a list of benchmark names
    if len(SELECT_PROGRAMS) > 0:
        program_names = SELECT_PROGRAMS
    else:
        # Extract all program names from the benchmark directory.
        program_names = [str(file).split("/")[-1][:-3] for file in timing_benchmark_dir.glob('*') if file.is_file()]
    
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
    
    # Generate timing variation plots for each program.
    for program in program_names:
        
        csv_np = np_dir / (program + ".csv")
        csv_lb = lb_dir / (program + ".csv")
        csv_egs = egs_dir / (program + ".csv")
        
        ##################################
        # Generate timing precision plot #
        ##################################
        df_np_timing_precision = post_process_timing_precision(csv_np)
        df_lb_timing_precision = post_process_timing_precision(csv_lb)
        df_egs_timing_precision = post_process_timing_precision(csv_egs)
        df_combined = combine_df(df_np_timing_precision, df_lb_timing_precision, df_egs_timing_precision)
        generate_plot_timing_precision(plots_dir, program, df_combined)
        
        #################################
        # Generate timing accuracy plot #
        #################################
        df_np_timing_accuracy = post_process_timing_accuracy(csv_np)
        df_lb_timing_accuracy = post_process_timing_accuracy(csv_lb)
        df_egs_timing_accuracy = post_process_timing_accuracy(csv_egs)
        df_combined = combine_df(df_np_timing_accuracy, df_lb_timing_accuracy, df_egs_timing_accuracy)
        generate_plot_timing_accuracy(plots_dir, program, df_combined)
        
        # Extract outliers
        if df_np_timing_accuracy is not None:
            np_timing_accuracy_outliers_df = extract_timing_accuracy_outliers(df_np_timing_accuracy)
            np_timing_accuracy_outliers_df.to_csv(f"{plots_dir}/{program}_timing_accuracy_outliers_NP.csv", index=False)
        if df_lb_timing_accuracy is not None:
            lb_timing_accuracy_outliers_df = extract_timing_accuracy_outliers(df_lb_timing_accuracy)
            lb_timing_accuracy_outliers_df.to_csv(f"{plots_dir}/{program}_timing_accuracy_outliers_LB.csv", index=False)
        if df_egs_timing_accuracy is not None:
            egs_timing_accuracy_outliers_df = extract_timing_accuracy_outliers(df_egs_timing_accuracy)
            egs_timing_accuracy_outliers_df.to_csv(f"{plots_dir}/{program}_timing_accuracy_outliers_EGS.csv", index=False)
        
        # Generate GIFs for timing accuracy
        # FIXME: Account for the EGS df for animation.
        if GENERATE_GIF:
            gif_name = f"{program}_timing_accuracy_animation.gif"
            create_animation_timing_accuracy(program, df_np_timing_accuracy, df_lb_timing_accuracy, plots_dir, frames_dir, gif_name, num_frames=NUM_FRAMES, fps=FPS)
        
        # Populating program stats for generating LaTeX table.
        if df_np_timing_accuracy is not None:
            program_stats['DY'][program] = generate_program_statistics(df_np_timing_accuracy)
        if df_lb_timing_accuracy is not None:
            program_stats['LB'][program] = generate_program_statistics(df_lb_timing_accuracy)
        if df_egs_timing_accuracy is not None:
            program_stats['EGS'][program] = generate_program_statistics(df_egs_timing_accuracy)
        
        #########################################
        # Generate reaction execution time plot #
        #########################################
        df_np_reaction_exec = post_process_execution_time(csv_np)
        df_lb_reaction_exec = post_process_execution_time(csv_lb)
        df_egs_reaction_exec = post_process_execution_time(csv_egs)
        df_combined_reaction_exec = combine_df(df_np_reaction_exec, df_lb_reaction_exec, df_egs_reaction_exec)
        generate_plot_reaction_execution_time(plots_dir, program, df_combined_reaction_exec)
        
        ####################################
        # Generate PretVM instruction plot #
        ####################################
        df_lb_vm_exec = post_process_instruction_execution_times(csv_lb)
        generate_plot_vm_execution_time(plots_dir, program, df_lb_vm_exec)

    generate_latex_table(program_names, program_stats, expr_run_dir / "table.tex")

if __name__ == "__main__":
    main()