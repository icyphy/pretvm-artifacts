import sys
import matplotlib
import matplotlib.pyplot as plt
import statistics

matplotlib.rcParams.update({
    'font.size': 12,          # Default text size
    'axes.titlesize': 15,     # Title font size
    'axes.labelsize': 15,     # Axis label font size
    'xtick.labelsize': 15,    # X-axis tick label font size
    'ytick.labelsize': 15,    # Y-axis tick label font size
    'legend.fontsize': 12,    # Legend font size
    'figure.titlesize': 16    # Figure title font size
})

figsize = (8,7)
alpha=0.7

# Result file
file = sys.argv[1]

# Output path
output = sys.argv[2]

results = {}

with open(file, 'r') as file:
    currentModule = None
    currentModuleResults = {}
    for line in file:
        if 'Module=' in line:
            print(f"Processing module {line.strip()}")
            newModule = line.strip().split("=")[-1]
            if currentModule=="Gyroscope" and newModule == "Gyroscope":
                continue
            if currentModule is not None:
                results[currentModule] = currentModuleResults
            currentModule = newModule
            currentModuleResults = {"exec_time": list(), "start_time": list()}
        if "Iteration" in line:
            start_lag = int(line.split(" ")[2].split("=")[1])
            exec_time = int(line.split(" ")[3].split("=")[1])
            completion = int(line.split(" ")[4].split("=")[1])
            currentModuleResults["start_time"].append(int(start_lag/1000))
            currentModuleResults["exec_time"].append(int(exec_time/1000))
            # currentModuleResults["completion"].append(int(completion/1000))
    results[currentModule] = currentModuleResults
            

results["Gyroscope"]["wcet"] = 21
results["Gyroscope"]["deadline"] = 20

results["SensorFusion"]["wcet"] = 62
results["SensorFusion"]["deadline"] = -1
        
results["Controller"]["wcet"] = 173
results["Controller"]["deadline"] = -1

results["Motor"]["wcet"] = 2
results["Motor"]["deadline"] = 300

all_values = []
for data in results.values():
    all_values.extend(data["exec_time"])
    all_values.extend(data["start_time"])
    all_values.append(data["wcet"])
    all_values.append(data["deadline"])

global_min = min(all_values)
global_max = max(all_values)
bin_width = 7  # Define the bin width
bins = range(global_min, global_max + bin_width, bin_width)

# Create 3x3 subplots
fig, axs = plt.subplots(2, 4, figsize=figsize)
fig.subplots_adjust(hspace=0.12, wspace=0.3)
# fig.suptitle('Satellite controller execution statistics')

# Plot histograms for each module
for i, (module, data) in enumerate(results.items()):
    ax = axs[0][i]
    start_mean = statistics.mean(data["start_time"])
    start_std = statistics.stdev(data["start_time"])
    print(f"{module} start_time_mean={start_mean} start_time_std={start_std}")
    ax.hist(data["start_time"], bins=bins, alpha=alpha, align='left')
    deadline = data["deadline"]
    if deadline > 0:
        ax.axvline(deadline, color='r', linestyle='solid', linewidth=1, label='Deadline')
        ax.legend(loc='upper right')
    
    if i == 0:
        ax.set_ylabel('Release time')
    
    #ax.set_xlabel(module)

    ax = axs[1][i]
    exec_time_mean = statistics.mean(data["exec_time"])
    exec_time_std = statistics.stdev(data["exec_time"])
    print(f"{module} exec_time_mean={exec_time_mean} exec_time_std={exec_time_std}")
    ax.hist(data["exec_time"], bins=bins, alpha=alpha, align='left')
    wcet = data["wcet"]
    if wcet > 0:
        ax.axvline(wcet, color='r', linestyle='solid', linewidth=1, label='WCET')
        ax.legend(loc='upper right')
    
    if i == 0:
        ax.set_ylabel('Execution time')

    ax.set_xlabel(module)

plt.tight_layout()
plt.savefig(f'{output}/satellite_controller_stats.pdf')
plt.show()
