import sys
import matplotlib.pyplot as plt

file = sys.argv[1]

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
            currentModuleResults = {"exec_time": list(), "completion": list()}
        if "Iteration" in line:
            # start_lag = int(line.split(" ")[2].split("=")[1])
            exec_time = int(line.split(" ")[3].split("=")[1])
            completion = int(line.split(" ")[4].split("=")[1])
            # currentModuleResults["start_lag"].append(int(start_lag/1000))
            currentModuleResults["exec_time"].append(int(exec_time/1000))
            currentModuleResults["completion"].append(int(completion/1000))
    results[currentModule] = currentModuleResults
            

results["Gyroscope"]["wcet"] = 21
results["Gyroscope"]["deadline"] = 41

results["SensorFusion"]["wcet"] = 62
results["SensorFusion"]["deadline"] = -1
        
results["Controller"]["wcet"] = 173
results["Controller"]["deadline"] = -1

results["Motor"]["wcet"] = 2
results["Motor"]["deadline"] = 300

all_values = []
for data in results.values():
    all_values.extend(data["exec_time"])
    all_values.extend(data["completion"])
    all_values.append(data["wcet"])
    all_values.append(data["deadline"])

global_min = min(all_values)
global_max = max(all_values)
bin_width = 7  # Define the bin width
bins = range(global_min, global_max + bin_width, bin_width)
alpha=0.7

# Create 3x3 subplots
fig, axs = plt.subplots(4, 2, figsize=(8, 6))
fig.suptitle('Satellite controller execution statistics')

# Plot histograms for each module
for i, (module, data) in enumerate(results.items()):
    ax = axs[i][0]
    ax.hist(data["exec_time"], bins=bins, alpha=alpha)
    wcet = data["wcet"]
    if wcet > 0:
        ax.axvline(wcet, color='r', linestyle='solid', linewidth=1, label='WCET')
        ax.legend(loc='upper right')
    if i == 0:
        ax.set_title('Execution time')
    if i == 3:
        ax.set_xlabel('Time [usec]')
    ax.set_ylabel(module, rotation=90)

    ax = axs[i][1]
    ax.hist(data["completion"], bins=bins, alpha=0.8)
    deadline = data["deadline"]
    if deadline > 0:
        ax.axvline(deadline, color='r', linestyle='solid', linewidth=1, label='Deadline')
        ax.legend(loc='upper right')
    if i == 0:
        ax.set_title('Completion time')
    if i == 3:
        ax.set_xlabel('Time [usec]')

    # ax.set_xlabel('Time [usec]')
    # ax.set_ylabel('Frequency')
    # ax.text(0.5, -0.1, f'Subtitle: {module}', ha='center', va='center', transform=ax.transAxes)
    # ax.text(0.5, -0.2, 'Caption: Histogram of start lag, exec time, and completion', ha='center', va='center', transform=ax.transAxes)


plt.tight_layout()
plt.savefig('satellite_controller_stats.pdf')
# plt.show()