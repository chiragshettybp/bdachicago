# Report outline

1. **Dataset** — cite UCI ElectricityLoadDiagrams20112014; state the source
   file, 370 clients, interval period, date range, and measured data scope.
2. **Cleaning and conversion** — describe semicolon parsing, decimal-comma
   conversion, validation, interval-end timestamps, and `kWh = kW / 4`.
3. **Data semantics** — explain retained zeroes, later-created client columns,
   and Portuguese daylight-saving encoding.
4. **Processing design** — show Python preparation and the MongoDB, Hadoop
   MapReduce, Pig, and Hive paths.
5. **Analysis** — report annual total kWh, mean daily kWh, maximum daily kWh,
   peak kW, and observed client/year coverage.
6. **Validation** — compare annual aggregates from the reference calculation,
   MapReduce, MongoDB, and Hive. Include row counts and any differences.
7. **Performance** — state hardware, storage formats, repetitions, timing
   method, and whether runs used one laptop or distinct physical machines.
8. **Limitations** — describe the dataset's DST treatment and avoid interpreting
   transition-hour values as ordinary clock-hour measurements.
9. **Dashboard** — capture Page 1 with a client ID, yearly metrics, the yearly
   total-kWh pie chart, and annual usage bar chart; capture Page 2 for a selected
   year with the highest/lowest clients and ranked client list.
10. **Evidence** — include dashboard screenshots, command output, tool versions,
   and the generated manifest/report paths.

Do not claim a distributed or physical-cluster run unless you have its logs and
results as evidence.
