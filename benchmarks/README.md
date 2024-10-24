# Running Timing Benchmarks Automatically
Simply run
```
python scripts/experiment_timing.py
```
Detailed configurations can be found in the script.

# Workflow for Updating Plots
Sometimes we have collected the data and just want to regenerate the graphs. In
this case, use the `--experiment-dir` flag. For example,
```
python scripts/experiment_timing.py --experiment-dir=2024-03-30_00-51-22-RPI4-LOAD_BALANCED_EGS-ALL
```
And then, go back to the root directory and run
```
sh scripts/update_pdf_diagrams.sh 2024-03-30_00-51-22-RPI4-LOAD_BALANCED_EGS-ALL
```
The new plots will be automatically added to `images/plots`.

# Running Timing Benchmarks Manually
To run a set of timing benchmarks using a particular scheduler and collect
tracing data back, first `cd` into the timing directory, then invoke a command
of the following form:
```
python ../script/run_benchmark.py -hn=<board-ip-address> -un=<board-username> -pwd="<board-password>" -f="<lfc-flag-1>" -f="<lfc-flag-2>" ...
```

For example, to run the benchmark suite using the STATIC scheduler:
```
python ../script/run_benchmark.py -hn=<Board-IP-Address> -un=<Board-Username> -pwd="<Board-Password>" -f="--scheduler=STATIC" -f="--static-scheduler=LOAD_BALANCED"
```
