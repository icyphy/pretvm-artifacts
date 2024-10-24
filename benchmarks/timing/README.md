# Comments about the programs

LF programs which are ***not*** supported yet by the static scheduler are those with:
- logical/physical actions, 
- and deadlines (to be supported).
In addition, timers are needed in order to define the hyperperiods and check for
timing constraints.

Logical actions that behave like connections should be rewritten using connections.  

| LF prog.    | Inc |Timers | Deadline | After delay | Logical Action | Physical Action |
|-------------|-----|-------|----------|-------------|----------------|-----------------|
| ADASModel   | no  |  2    | yes      | yes         | yes            | yes             |
| AircraftDoor| no  |  0    | -        | -           | -              | -               |
| Alarm       | no  |  0    | -        | -           | yes            | -               |
| CoopSchedule| yes |  1    | -        | -           | -              | -               |
| Elelction   | no  |  0    | -        | -           | yes            | -               |
| Elelction2  | no  |  0    | -        | yes         | -              | -               |
| Elevator    | yes |  3    | -        | -           | yes            | -               |
| Factorial   | yes |  1    | -        | -           | yes            | -               |
| Fibonacci   | yes |  1    | -        | -           | yes            | -               |
| PingPong    | no  |  0    | -        | -           | yes            | -               |
| Pipe        | yes |  1    | -        | -           | yes            | -               |
| ProcessMsg  | yes |  1    | -        | -           | yes            | -               |
| ProcessSync | yes |  1    | -        | -           | -              | -               |
| Railroad    | yes |  1    | -        | -           | yes            | -               |
| Ring        | no  |  0    | -        | yes         | yes            | -               |
| RoadsideUnit| no  |  0    | -        | -           | yes            | -               |
| SafeSend    | no  |  0    | -        | yes         | yes            | -               |
| Subway      | no  |  0    | -        | -           | yes            | -               |
| Thermostat  | yes |  1    | -        | -           | yes            | -               |
| TrafficLight| yes |  2    | -        | -           | yes            | -               |
| TrainDoor   | no  |  0    | -        | yes         | -              | -               |
| UnsafeSend  | no  |  0    | -        | yes         | yes            | -               |
