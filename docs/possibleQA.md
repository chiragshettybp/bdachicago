# Hadoop Cluster Assignment — Possible Viva Questions and Answers

This guide prepares you to explain the assignment brief, the electricity
analytics workflow, and the difference between the repository's Docker cluster
and a cluster made from three physical lab computers. Answers are grounded in
the current project configuration. Do not claim a service, physical-cluster
run, or performance result has passed unless you have that run's logs/evidence.

## Important: Docker cluster versus physical lab cluster

The repository's [`infra/compose.yaml`](../infra/compose.yaml) defines three
containers named `master`, `worker1`, and `worker2`. The master starts the HDFS
NameNode, YARN ResourceManager, MapReduce History Server, and HiveServer2.
Each worker starts an HDFS DataNode and YARN NodeManager. They use the same
Hadoop configuration and project files, and each container has a persistent
host-mounted state directory.

This is useful for learning, repeatable development, and testing whether Hadoop
services can communicate. Docker gives the containers separate process and
network namespaces and names them on a virtual network. **When all containers
run on one computer, however, they share that computer's physical CPU, memory,
storage hardware, operating system kernel, and network interface. They are not
three physical computers and do not prove multi-machine fault tolerance or
physical-cluster performance.**

Therefore, the Compose environment is a **local multi-container Hadoop
simulation**, not a replacement for the assignment's requirement to use three
lab systems. If the instructor requires three physical systems, execute the
final evidence run on those systems and record their hostnames/IPs, roles,
service status, and job evidence. Do not present a laptop-only Docker run as
fulfilling that requirement.

The Compose setup currently covers Hadoop/HDFS/YARN and Hive services. Its
service list does not include MongoDB. [`scripts/start_mongo.sh`](../scripts/start_mongo.sh)
starts a separate local MongoDB container; that is a standalone MongoDB service,
not a MongoDB cluster distributed across Hadoop workers. Pig and Hive are
installed in the shared tools directory, but their assignment jobs must still
be invoked with input/output paths configured for the actual HDFS cluster.

## A. Assignment overview

### 1. What is the objective of this assignment?

To configure Hadoop storage and YARN processing over multiple nodes, then
demonstrate data storage, distributed processing, and analytics using MongoDB,
Hadoop MapReduce, Pig, and Hive. The outputs should be checked and supported
with reproducible evidence.

### 2. What are the three assignment themes?

1. **MongoDB analytics:** import records, create indexes, run aggregation
   pipelines, and profile query execution.
2. **Hadoop file management and MapReduce:** store and manage files in HDFS,
   then execute a distributed job through YARN.
3. **Pig and Hive analytics:** clean/transform data with Pig Latin, store/query
   data through Hive, and compare Text and RCFile formats.

### 3. What dataset does this project use?

The project uses UCI ElectricityLoadDiagrams20112014. It contains 370 client
columns and 15-minute power readings from 2011–2014. The prepared data is
converted into daily client records and annual client summaries.

### 4. Why use more than one processing technology?

The tools have different roles and provide a way to compare approaches:
MongoDB uses document queries and aggregation pipelines; Hadoop MapReduce
processes HDFS input across YARN tasks; Pig expresses transformation flow in
Pig Latin; Hive provides SQL-style querying over HDFS-backed tables.

### 5. How is the electricity data interpreted?

The values are kW for 15-minute intervals. Interval energy is `kW / 4` kWh.
Zero values are retained. The source encodes Portuguese daylight-saving
transitions using its stated conventions, so time-of-day comparisons around
those dates need care.

## B. Hardware, roles, and networking

### 6. What is the minimum physical setup specified by the assignment?

At least three lab computers on the same network: one master and at least two
workers.

### 7. What does the master do?

The master coordinates HDFS metadata with the NameNode, schedules YARN work
with the ResourceManager, and may host the JobHistory Server, HiveServer2, and
MongoDB depending on the agreed lab design.

### 8. What does a worker do?

A worker normally runs a DataNode to store HDFS blocks and a NodeManager to
launch YARN containers/tasks. In this project configuration, the worker roles
are named `worker1` and `worker2`.

### 9. Why configure hostnames and IP connectivity?

Hadoop daemons and clients contact one another using configured hostnames and
ports. Each hostname must resolve to the intended machine and the required
ports must be reachable across the lab network.

### 10. How do you check that machines can communicate?

Check each machine's hostname and address, verify name resolution, and test
network reachability using the lab-approved tools. Then verify the Hadoop
services themselves using HDFS and YARN reports; a successful ping alone does
not show that Hadoop is configured correctly.

### 11. Why does the official guide mention SSH?

SSH is commonly used by Hadoop's administrative scripts to start/stop daemons
on remote hosts. For a physical cluster, configure approved SSH access for the
Hadoop account and test it from the master to each worker. The current Docker
entrypoint starts container daemons directly; that does not demonstrate remote
SSH administration between physical computers.

### 12. Why must Java and Hadoop versions match?

The Hadoop daemons and clients must be compatible and configured consistently.
Using the same tested Java/Hadoop versions and configuration on every host
avoids version/classpath differences and inconsistent daemon behavior.

### 13. How should worker hostnames be provided?

The Hadoop `workers` file should contain the actual worker hostnames, one per
line. The repository has a `workers` file for its `worker1` and `worker2`
container roles; physical deployment must replace/confirm those with the lab
machines' actual hostnames.

### 14. What ports should be opened?

Use the ports required by the selected Hadoop version and site configuration
for NameNode, DataNodes, ResourceManager, NodeManagers, and any UIs/services
being used. Confirm the current version's documentation and lab firewall policy;
do not open arbitrary ports or expose Hadoop services to untrusted networks.

## C. Hadoop configuration and startup

### 15. Which Hadoop configuration files are important?

`core-site.xml`, `hdfs-site.xml`, `yarn-site.xml`, and `mapred-site.xml`. They
define filesystem location, HDFS storage/replication, YARN resource management,
and MapReduce execution on YARN. Java and daemon environment settings must also
be set correctly on every host.

### 16. What does `fs.defaultFS` do in this project?

It points Hadoop clients to the default HDFS NameNode URI. The Docker
configuration uses `hdfs://master:9000`; a physical cluster must use the
reachable hostname and port of its actual NameNode.

### 17. What does HDFS replication mean?

Replication is the number of copies HDFS attempts to maintain for each block.
The current project sets `dfs.replication` to 2. A replication factor of 2
requires enough live DataNodes and does not make the setup highly available;
it also cannot protect against every correlated failure.

### 18. What are the NameNode and DataNode?

The NameNode tracks filesystem namespace and block-location metadata. DataNodes
store the actual HDFS blocks and report their status to the NameNode.

### 19. What are the ResourceManager and NodeManager?

The ResourceManager allocates cluster resources and schedules applications.
Each NodeManager reports local resources and launches task containers on its
machine.

### 20. Why initialize/format the NameNode only once?

Formatting initializes new HDFS namespace metadata. Reformatting an established
NameNode can discard the namespace and make existing block data inaccessible.
Only format a newly created, intentionally empty HDFS state after confirming
the target paths; do not format as a routine troubleshooting step.

### 21. What does the Docker entrypoint do on first startup?

On the master container it formats the NameNode only if the mounted state does
not already have a NameNode VERSION file, then starts the NameNode,
ResourceManager, History Server, creates HDFS base directories, and starts
HiveServer2. On workers it starts the DataNode and NodeManager. Container state
is held under separate host-mounted directories.

### 22. How do you verify HDFS and YARN are running?

Use `hdfs dfsadmin -report` to inspect live DataNodes and `yarn node -list
-states RUNNING` to inspect NodeManagers. Also check the NameNode safe mode and
submit a sample MapReduce example through YARN. This repository's
[`scripts/verify_cluster.sh`](../scripts/verify_cluster.sh) checks for at least
two live DataNodes and two RUNNING NodeManagers and launches the Hadoop Pi
example. These checks confirm registered services, but do not alone prove that
the nodes are physically distinct computers.

### 23. How can you tell whether a job actually ran on workers?

Use YARN application/job logs and the ResourceManager UI to inspect task
attempts and assigned NodeManagers. Record worker hostnames and task placement.
For the assignment's physical-cluster claim, corroborate task execution with
the physical host inventory; container hostnames by themselves are not enough.

### 24. What is HDFS safe mode?

It is a protective NameNode state during startup/recovery in which HDFS does
not allow normal namespace modifications. Wait for it to leave safe mode and
investigate missing DataNodes or block reports if it remains enabled.

## D. Docker questions and honest comparison

### 25. Why use Docker in this project?

Docker provides isolated, repeatable Hadoop roles without separately
installing every service on the host. It is useful for development, debugging,
reproducing configuration, and demonstrating the master/worker service layout.

### 26. How is Docker configured here?

Compose starts three named services (`master`, `worker1`, `worker2`) from the
same pinned base image. All mount the project at `/project`, mount prepared
Java/Hadoop/Hive/Pig tools read-only under `/opt`, and use separate persistent
state folders. Environment variables point to the tool installation and Hadoop
configuration.

### 27. Do the containers have separate hostnames and network identities?

Yes. Compose assigns the names `master`, `worker1`, and `worker2` and provides
service discovery on the Compose network. Hadoop configuration uses `master`
as its service endpoint. These are container network identities, not separate
physical machines.

### 28. Are three Docker containers the same as three computers?

No. They are separate container environments but, on one laptop, share its
physical CPU, RAM, disk devices, network connection, and kernel. They do not
meet a requirement that explicitly says to use three lab systems.

### 29. What does the Docker demonstration prove?

If actually run and verified, it can demonstrate Hadoop daemons operating in
separate containers, HDFS block storage across container DataNodes, YARN
registration, and MapReduce task submission. It can also help debug job logic.
It does not prove physical multi-host connectivity, independent hardware
failure handling, lab-network performance, or compliance with a three-computer
requirement.

### 30. Why not simply claim Docker is a replacement?

Because the assignment explicitly requires three lab systems. Saying one
computer's containers are three physical systems would be inaccurate. Present
Docker as a development/simulation environment and report the physical lab run
separately.

### 31. What differences remain between Docker and the physical cluster?

Physical deployment needs actual hostnames/IPs, network/firewall setup,
consistent installations on each machine, HDFS data directories on separate
disks, SSH administration if using Hadoop scripts, and physical resource
monitoring. Docker's service DNS, mounted state paths, and container scheduler
do not configure these lab-machine details.

### 32. Does the current Docker Compose file run MongoDB?

No. Its services are `master`, `worker1`, and `worker2`, all for Hadoop-related
roles; the master also starts HiveServer2. MongoDB is started separately by
`scripts/start_mongo.sh`, and the current script uses a single MongoDB
container. Do not describe that as a sharded or multi-node MongoDB cluster.

### 33. Is Pig/Hive automatically executed when Compose starts?

No. Compose starts the long-running Hadoop and Hive services. Pig and Hive
commands/queries are separate job steps. They need to be run with the correct
HDFS input/output locations after the services are available.

### 34. How should Docker be used if the lab is unavailable?

Use it for development and record it accurately as a single-host,
multi-container test. Ask the instructor whether that is acceptable as a
temporary substitute, but do not assume it satisfies the stated physical
hardware requirement. Keep physical-lab evidence pending until that run occurs.

## E. Theme 1 — MongoDB analytics

### 35. What does the MongoDB theme demonstrate?

Document ingestion of the prepared daily client records, indexes supporting
client/year or date lookups, aggregation to annual measures, and measured query
performance. MongoDB is a separate analytics/storage path from HDFS/YARN in
this project.

### 36. Is MongoDB distributed across the Hadoop workers here?

No. The current project starts one MongoDB development container separately.
It is not configured as a replica set or sharded cluster, and it does not
automatically share Hadoop's HDFS data. State this distinction explicitly.

### 37. What is an index and why create one?

An index is an auxiliary data structure that can reduce the documents MongoDB
must scan for a query. It costs storage and index-build time, so compare indexed
and unindexed execution with the same query and dataset.

### 38. What does an aggregation pipeline do?

It passes documents through ordered stages such as matching, grouping,
calculating sums/averages/maxima, and projecting output fields. The stages for
this dataset can group daily records by client and year.

### 39. What should be measured for a fair MongoDB comparison?

Use the same query, same imported data, and repeated runs. Record the query
plan/explain statistics, documents and index keys examined, elapsed time,
server setup, and whether results are cold or warm. Do not compare different
data scopes or silently omit failed runs.

### 40. What must be done before connecting the MongoDB workflow to the lab?

Decide whether MongoDB is required only on the master or must itself be
distributed. Configure a reachable connection URI and network/firewall policy,
confirm the importer writes to a dedicated database, then run and preserve
import, index, aggregation, and profiling evidence. Do not imply the Hadoop
cluster automatically distributes MongoDB documents.

## F. Theme 2 — HDFS and MapReduce

### 41. What HDFS operations should be demonstrated?

Create a run directory, upload the prepared file, list/stat/read it, retrieve a
small verification file, compare transferred bytes, and remove only the
temporary test directory. Keep input and results for evidence; avoid broad
deletions.

### 42. What does the MapReduce job calculate?

The Python Streaming mapper groups daily client records by client and year.
The reducer calculates day count, total kWh, mean daily kWh, maximum daily kWh,
and peak kW. In Hadoop mode the records are processed through Hadoop Streaming
with YARN.

### 43. What is the mapper's role?

It parses each input record, validates its structure/numeric values, emits a
key such as client plus year, and emits partial values for aggregation.

### 44. What is the reducer's role?

It receives sorted mapper output for each key, combines partial values, and
emits the final annual client summary.

### 45. What is Hadoop Streaming?

It is Hadoop MapReduce's interface for using executables or scripts as mapper
and reducer programs, communicating through standard input and output. This
project uses Python scripts; Hadoop/YARN still schedules the tasks.

### 46. What is YARN's role in this job?

YARN allocates resources and launches the MapReduce application/task
containers on NodeManagers. Verify the application completed successfully and
inspect task logs, not just the command's initial submission response.

### 47. What is the purpose of the sample MapReduce job?

It validates the installed Hadoop example JAR, HDFS access, YARN scheduling,
and task completion before running the assignment's own job. A successful Pi
example is a smoke test, not evidence that all assignment themes completed.

## G. Theme 3 — Pig and Hive

### 48. What is Pig Latin?

Pig Latin is a high-level dataflow language for loading, filtering, transforming,
and storing large datasets. Pig compiles a script into Hadoop jobs; this
project's Pig script validates daily rows while retaining valid zero loads.

### 49. Why preserve zero readings in Pig?

Zero is a valid measured value and includes zero-filled pre-client periods.
Filtering zero values would change total consumption and bias averages. The
script rejects malformed or negative values but retains zero.

### 50. What is Hive?

Hive provides SQL-like definitions and queries over files in Hadoop storage.
The project defines the prepared daily schema and queries annual client
metrics.

### 51. What is the difference between Text and RCFile?

Text is row-oriented delimited text and easy to inspect. RCFile is a
columnar-oriented Hadoop format intended to improve analytical storage and
query behavior. Compare output equivalence as well as size and query time.

### 52. How do you make the Text/RCFile comparison fair?

Use identical records, schema, query, and cluster resources; exclude/identify
warm-up runs; repeat measurements; record table/file sizes; and verify the
answers match before interpreting performance.

### 53. Does creating Hive tables prove Pig and Hive worked?

No. Preserve Pig job completion/output counts, Hive table locations, actual
query results, YARN job/application status, and Text/RCFile benchmark
measurements. A table definition alone does not prove data was successfully
transformed or queried.

## H. Verification, evidence, and troubleshooting

### 54. What evidence should be collected for the physical cluster?

- Machine inventory: physical hostname, IP, assigned role, OS, CPU, RAM, disk.
- Java and Hadoop versions on each machine.
- Relevant Hadoop configuration files and actual workers hostnames.
- HDFS live DataNode report and YARN RUNNING NodeManager report.
- A completed sample YARN MapReduce application and its logs.
- HDFS upload/read/round-trip evidence.
- MongoDB import, indexes, aggregation, and profiling evidence.
- Pig output and Hive Text/RCFile query/benchmark results.
- Dataset fingerprint, run date, commands, and any failed/retried stages.
- Evidence that records which physical hosts actually executed work.

### 55. What should you say if the Docker run passes but the lab run has not happened?

Say: “The three-container Docker environment passed the checks I actually ran.
It is a single-host development simulation, not the required three-physical-
system run. The physical lab deployment and its assignment evidence are still
pending.” Then show the logs and describe the next lab steps.

### 56. What if a worker does not register?

Check hostname resolution, network reachability, Java/Hadoop versions,
configuration consistency, daemon logs, data-directory ownership, and
firewall/port rules. For HDFS check the NameNode report; for YARN check the
ResourceManager node list. Fix the cause before restarting or formatting
anything.

### 57. What if HDFS stays in safe mode?

Inspect DataNode registration and block reports, NameNode logs, storage
permissions, and disk availability. Do not force-leave safe mode or reformat
the NameNode without understanding the state and having an approved recovery
plan.

### 58. What if a MapReduce application is accepted but never completes?

Check YARN application state, NodeManager health, available memory/vcores,
container launch logs, HDFS input accessibility, and mapper/reducer stderr.
“Submitted” or “accepted” is not the same as “succeeded.”

### 59. How do you know analytics are correct across tools?

Use a common prepared input, define the same grouping and metric formulas,
compare row/group counts and numeric outputs within a stated tolerance, and
retain source and output fingerprints. Matching performance timings alone do
not prove result correctness.

### 60. What are the current project's important limitations to disclose?

- A laptop's three Docker containers are not three separate lab computers.
- The Compose setup does not include MongoDB; its separate MongoDB helper starts
  one standalone container.
- The lab guide explicitly says its physical-machine steps have not yet been
  verified on the actual college systems.
- Local Python/MapReduce cross-checks do not prove Hadoop/YARN, Pig, Hive, or
  MongoDB completed successfully on the physical cluster.
- A successful sample job verifies cluster basics, not every analytical
  theme.

## Short presentation summary

> “We use three roles: one master coordinates HDFS and YARN, while two workers
> store HDFS blocks and execute tasks. Docker can reproduce those logical roles
> for local development, but three containers on one host are not three
> physical lab systems. The assignment's physical run must be verified on the
> lab computers. We then demonstrate MongoDB aggregation, HDFS and YARN
> MapReduce, and Pig/Hive processing, preserving outputs and cross-checking
> analytical results.”

## References in this repository

- [Official Apache Hadoop Cluster Setup guide](https://apache.github.io/hadoop/hadoop-project-dist/hadoop-common/ClusterSetup.html)
- [Project Docker Compose configuration](../infra/compose.yaml)
- [Hadoop site configuration](../infra/hadoop/)
- [Cluster verification script](../scripts/verify_cluster.sh)
- [Electricity dataset distributed run guide](./THREE-SYSTEM-RUN.md)
- [Validation record](./validation.md)
