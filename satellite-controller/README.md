# WCET analysis

```shell
docker pull einspaten/rtas25:v2
docker run -ti -v ${PWD}/docker/:/root/rtas25/ -v ${PWD}:/root/rtas25/satellite-controller einspaten/rtas25:v2 
> ./analyse_all.sh
```


# Plot results
After running the program generating a `results.txt` (the one used in the paper is already checked into this repo) run
```
python3 scripts/plotSatellite.py results.txt .
```
