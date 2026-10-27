# Viva Preparation — Chicago 311 Service Request Analytics

Model answers for the questions teachers most likely ask, grounded in **this
exact project**. Numbers in **bold** are the ones to quote confidently.
Everything here is verifiable from the code in this repository.

---

## 1. The 30-second project pitch

**Q: Tell me about your project.**

> I built a big-data analytics pipeline over the City of Chicago's open-data
> **311 Service Requests** dataset — **14.9 million** service requests across
> **39 columns**, from the new 311 system launched on **18 Dec 2018**. A
> preparation stage validates the raw CSV and aggregates it into one row per
> **service request type per day**. That normalized file is then processed by
> five engines: a Python reference implementation, a **Hadoop MapReduce**
> Streaming job, a **Pig** cleaning script, **Hive** (Text vs RCFile), and
> **MongoDB** aggregation. A three-page **Flask** dashboard visualizes annual
> summaries: per-type yearly profiles, year-wise rankings with Top-K, and a
> real-examples page. The Python and MapReduce results are **cross-checked
> against each other** before anything is saved.

**Q: Why this dataset?**

> It is real, large (14.9M rows), publicly downloadable, and mixes categorical
> dimensions (request type, department, status, origin) with temporal data
> (created/closed timestamps) — ideal for demonstrating distributed
> group-by/aggregation, which is the core of the assignment (MapReduce, Pig,
> Hive, MongoDB).

---

## 2. Dataset questions ("how many features…")

**Q: How many features/columns does the dataset have?**

> **39 columns**. Each row is one service request identified by **SR_NUMBER**,
> which is unique — the portal shows its cardinality equals the row count
> (~**14.9M** rows).

**Q: Which columns did you actually use?**

> Required for every row: `SR_NUMBER`, `SR_TYPE`, `CREATED_DATE`. Used when
> present: `STATUS` (Completed/Open/Canceled), `CLOSED_DATE` (for resolution
> time). The other ~35 columns (street parts, ZIP, ward, community area,
> police district/beat, duplicate flags, lat/long) are retained in the raw CSV
> but the analytics group by **request type**, so they are not aggregated.

**Q: What are the most important categorical values?**

> `SR_TYPE` — e.g. *311 INFORMATION ONLY CALL* (4.92M real requests),
> *Aircraft Noise Complaint* (2.39M), *Graffiti Removal Request* (680K),
> *Pothole in Street Complaint* (405K). `SR_SHORT_CODE` is the compact code for
> the same type (311IOC, AVN, GRAF, PHF…). `OWNER_DEPARTMENT` — 311 City
> Services, Streets and Sanitation, Aviation, CDOT, DWM, DOB… `ORIGIN` — Phone
> Call (~57%), Internet (~27%), Mobile Device. `STATUS` — Completed ~97%,
> Open ~1.5%, Canceled ~1.4%.

**Q: Any data-quality traps in this dataset?**

> Three I handle:
> 1. **INFORMATION ONLY CALLS (~4.9M)** are logged at the 311 Center address
>    (`2111 W Lexington ST`) — they would completely skew any location-based
>    analysis, so I aggregate by type, not by address.
> 2. **`DUPLICATE` flag** — ~707K rows are marked duplicates of a parent
>    request; the flag exists but I do not de-duplicate (each row is still a
>    real citizen contact).
> 3. **`LEGACY_RECORD`** — a small share came from the pre-2018 system.
>    Also: `CREATED_DEPARTMENT` is null in ~41% of rows; `CLOSED_DATE` can be
>    earlier than `CREATED_DATE` in bad rows — my prepare stage only counts
>    resolution time when `CLOSED_DATE >= CREATED_DATE`.

**Q: What does your normalized file look like?**

> `daily.tsv`, **6 tab-separated columns**:
> `date | sr_type | requests | completed | canceled | resolution_days`.
> One row per **(creation date, request type)**. `resolution_days` is the sum
> of `(CLOSED_DATE − CREATED_DATE)` in days for requests completed that day —
> storing the **sum** (not the mean) lets every engine correctly compute the
> annual weighted average later. A `manifest.json` records the source
> **SHA-256**, row counts, and date range for reproducibility.

---

## 3. What is Hadoop? (detailed)

**Q: What is Hadoop and why do we need it?**

> Apache Hadoop is an open-source framework for **distributed storage and
> distributed processing** of very large datasets across clusters of commodity
> hardware. One machine can't hold/process 14.9M-row files comfortably, so
> Hadoop splits both the *storage* and the *computation* across machines:
>
> - **HDFS** — Hadoop Distributed File System: stores data in large blocks
>   (default **128 MB**) replicated across machines (we use **replication 2**).
> - **YARN** — Yet Another Resource Negotiator: the cluster's resource manager
>   and job scheduler.
> - **MapReduce** — the programming model that YARN executes: computation is
>   moved **to the data** instead of moving data to the computation.

**Q: Explain HDFS architecture.**

> - **NameNode (on our `master`)**: keeps all **metadata** — the namespace
>   (directory tree), the mapping of every file's blocks to DataNodes. It
>   stores this as `fsimage` + an `edits` log. It never stores actual data.
> - **DataNodes (on `worker1`, `worker2`, and master's disk)**: store the
>   actual **blocks** on local disk and send the NameNode a **heartbeat**
>   plus a **block report** every few seconds. A missed heartbeat marks the
>   node dead and HDFS re-replicates its blocks elsewhere.
> - A file is split into blocks; each block is stored on multiple DataNodes
>   (**replication factor 2 in `hdfs-site.xml`**). If one DataNode dies, the
>   other copy still serves reads — that's fault tolerance.
> - **Safe mode**: on startup the NameNode waits for enough DataNodes to
>   report blocks before allowing writes; you should never force it off
>   blindly.

**Q: Explain HDFS read and write paths.**

> *Write*: client asks the NameNode to create a file → NameNode checks
> permissions and picks DataNodes (first replica on the writer's node/rack,
> second on a different rack/node) → client streams the block through a
> pipeline of DataNodes; each acknowledges; when minimum replicas acknowledge,
> the write succeeds.
> *Read*: client asks NameNode for block locations → reads from the **closest**
> replica (same rack first). Clients never talk to the NameNode for data, only
> for metadata — that keeps the NameNode from becoming a bottleneck.

**Q: What is YARN and how does a job run on it?**

> YARN separates **resource management** from **processing**:
> - **ResourceManager (master)**: global scheduler; allocates containers.
> - **NodeManager (each worker)**: launches and monitors **containers** on its
>   machine and reports to the RM.
> - **ApplicationMaster**: per-application process that negotiates containers
>   from the RM and coordinates the job's tasks.
>
> Job flow: client submits job → RM starts the ApplicationMaster in a
> container → AM requests map containers close to the input splits →
> NodeManagers launch map tasks → on completion, AM requests reduce containers
> → reduce tasks pull map outputs (shuffle) → job reported complete to the RM,
> logs go to the **JobHistory Server** (also on our master).

**Q: How many machines does your cluster have? Which roles?**

> Three nodes in `infra/compose.yaml`: **master** (NameNode, ResourceManager,
> MapReduce History Server, HiveServer2), **worker1** and **worker2**
> (DataNode + NodeManager). `workers` file lists the two workers. HDFS
> replication is **2**, each container limited to **4 GB**. I am honest about
> this being a **Docker multi-container simulation** — three containers on one
> laptop share one physical CPU/disk, so it is not the same as three physical
> lab machines unless the assignment run is done on real hosts.

---

## 4. MapReduce — mapper, reducer, and how it all works

**Q: What is the MapReduce programming model?**

> A two-phase model:
> 1. **Map** — run in parallel over independent pieces of input; each map task
>    turns a record into zero or more **key/value** pairs.
> 2. **Reduce** — all values for the **same key** are brought together
>    (shuffle & sort) and aggregated into the final output.
>
> Between them sit: **input splits** (each map task processes one split,
> typically one HDFS block = 128 MB), the **RecordReader** (parses split into
> records), the optional **Combiner** (map-side mini-reducer), the
> **Partitioner** (decides which reducer gets each key: `hash(key) %
> numReducers`), and **shuffle & sort** (HTTP transfer of map outputs to
> reducers, merged in key order). Number of map tasks = number of splits;
> number of reduce tasks is set by the job (we set **2**).

**Q: What is a mapper? Show YOUR mapper.**

> The mapper processes one input record at a time, validates it, and emits a
> keyed partial result. Mine (`mapreduce/mapper.py`) reads the prepared
> `daily.tsv` and emits everything the reducer needs, keyed by
> **request-type + year**:
>
> ```python
> day, sr_type, requests, completed, canceled, resolution = fields
> print(f"{sr_type}|{year}\t{requests}\t{requests}\t{resolution}\t{completed}")
> ```
>
> Input is **6 fields**; output is **5 fields**: `key, requests, requests,
> resolution_days, completed`. I emit `requests` **twice on purpose**: the
> first copy is summed by the reducer, the second copy is fed through a `max`
> to become *max daily requests*. Validation rejects wrong field counts,
> malformed dates, and negative values so bad data fails loudly, not silently.

**Q: What is a reducer? Show YOUR reducer.**

> The reducer receives, for each key, the values **already sorted by key**, and
> aggregates them into the final record. Mine (`mapreduce/reducer.py`) groups
> consecutive identical keys (`itertools.groupby`) and computes:
>
> - `days` — count of daily rows for that type/year
> - `requests` — **sum** of daily request counts
> - `max_daily_requests` — max of the second emitted value
> - `avg_resolution_days` — `sum(resolution_days) / sum(completed)`, guarded
>   to 0 when no requests completed
>
> Output is **7 tab-separated fields**:
> `sr_type, year, days, requests, mean_daily_requests, max_daily_requests,
> avg_resolution_days`, where `mean_daily_requests = requests / days`.

**Q: Walk me through the WHOLE job on the cluster, end to end.**

> 1. `daily.tsv` is uploaded to HDFS under
>    `/user/<user>/chicago311/<run>/`.
> 2. `scripts/run_mapreduce.sh` calls **Hadoop Streaming**:
>    `hadoop jar hadoop-streaming.jar -files mapreduce/mapper.py,mapreduce/reducer.py
>    -mapper 'python3 mapper.py' -reducer 'python3 reducer.py'
>    -D mapreduce.job.name=chicago311-annual-type-summary
>    -D mapreduce.job.reduces=2 -input <HDFS in> -output <HDFS out>`.
> 3. YARN splits the input (~128 MB per map task), each map task runs my
>    Python mapper over its split via **stdin/stdout**.
> 4. Partitioner routes `sr_type|year` keys to **2 reducers**; each reducer
>    receives its keys **sorted**, runs my Python reducer.
> 5. Output lands in the HDFS output dir with `_SUCCESS` — the script
>    explicitly checks `_SUCCESS` exists before declaring victory.

**Q: What is the shuffle and sort phase — in detail?**

> After map tasks finish, each map task's output is written to local disk,
> partitioned by `hash(key) % numReducers`. Each reduce task **copies** its
> partition from every map task over HTTP ("fetch"), then **merges** all those
> runs into one globally key-sorted stream. That is why the reducer can just
> group *consecutive* equal keys — everything for `PHF|2024` arrives together
> and in order. In my **local cross-check** I simulate exactly this with
> `sorted(mapped.stdout.splitlines())` before feeding the reducer.

**Q: What is a combiner? Does your job use one?**

> A combiner is an optional **map-side mini-reducer** that pre-aggregates map
> output to cut shuffle traffic (valid only if the operation is associative
> and commutative). My job doesn't enable one: the input is *already
> pre-aggregated* to one row per type/day, so map output is tiny relative to
> raw data — a combiner would buy almost nothing and a streaming combiner
> would complicate the reducer's "average of averages" correctness.

**Q: What is Hadoop Streaming and why use Python?**

> Streaming lets any executable act as mapper/reducer: Hadoop feeds each task
> **stdin line-by-line** and reads **stdout** lines as `key \t value`. It
> keeps my exact same Python logic runnable **three ways**: inside Hadoop on
> YARN, locally via `subprocess` in `analytics.py`, and by hand in a shell —
> one implementation, three execution modes, results compared.

**Q: How do you KNOW your MapReduce output is correct?**

> `python -m service_requests analyze` computes the annual summary **twice**:
> once with a plain Python reference implementation, once through the actual
> mapper/reducer pair. It then compares group keys and all four metrics with
> `math.isclose(rel_tol=1e-9, abs_tol=1e-9)` and refuses to save results
> unless both agree — the saved `analytics.json` records
> `"mapreduce_crosscheck": "passed"`. With the sample data:
> **33,791 rows → 8,829 daily rows → 39 summaries** (13 types × 3 years).

**Q: Classic trap — why can't you average the yearly means of means?**

> Because groups have different sizes. If type A had 5 requests/day for 10
> days and type B had 1/day for 2 days, the mean of means (3) ≠ true mean
> (total 52 over 12 days ≈ 4.33). My reducer always recomputes
> `sum/count` from **totals** — `mean = total_requests / days`,
> `avg_resolution = Σresolution_days / Σcompleted` — never from pre-averaged
> values. Same rule in the Hive query (`SUM(resolution_days)/SUM(completed)`)
> and the Mongo pipeline (`$divide` of two `$sum`s).

---

## 5. Pig

**Q: What is Pig and what does your Pig script do?**

> Apache Pig is a high-level **dataflow** language (Pig Latin) that compiles
> into MapReduce jobs — good for ETL without writing Java. My
> `pig/clean_daily.pig`:
>
> ```pig
> raw   = LOAD '$INPUT' USING PigStorage('\t') AS (reading_date, sr_type,
>           requests:int, completed:int, canceled:int, resolution_days:double);
> clean = FILTER raw BY reading_date IS NOT NULL AND sr_type IS NOT NULL
>           AND requests >= 0 AND completed >= 0 AND canceled >= 0
>           AND resolution_days >= 0.0;
> STORE clean INTO '$OUTPUT' USING PigStorage('\t');
> ```
>
> It's a distributed data-quality gate: it rejects malformed/negative daily
> rows and keeps everything valid, so downstream Hive/Mongo see clean data.

**Q: Pig vs MapReduce vs Hive — when each?**

> MapReduce = maximum control, most boilerplate. Pig = readable multi-step
> transformations (FILTER/JOIN/GROUP). Hive = SQL for analysts over HDFS
> tables. All three compile down to YARN jobs over the same HDFS data.

---

## 6. Hive

**Q: What is Hive and what tables did you create?**

> Hive provides **SQL (HiveQL)** over files stored in HDFS — schemas are
> metadata; the data stays in place. `hive/tables.hql` creates:
> - `daily_text` — **EXTERNAL** table over the prepared TSV
>   (`ROW FORMAT DELIMITED FIELDS TERMINATED BY '\t'`, `STORED AS TEXTFILE`,
>   `LOCATION '${hivevar:INPUT}'`)
> - `daily_rcfile` — same schema `STORED AS RCFILE` with **gzip output
>   compression**, filled by `INSERT OVERWRITE ... SELECT`
> - `ANALYZE TABLE ... COMPUTE STATISTICS` on both for the optimizer.

**Q: Why EXTERNAL tables?**

> `EXTERNAL` decouples the schema from the data location: dropping the table
> does **not** delete the HDFS files, and multiple table definitions can point
> at the same prepared data. Internal tables would move data into the
> warehouse directory and delete it on drop.

**Q: Text vs RCFile — what's the difference and why compare?**

> TextFile = row-oriented, human-readable, best compression ratio with gzip,
> but a query reading 2 of 6 columns still scans whole rows. RCFile =
> **column-oriented**: rows are stored in stripes column-by-column, so
> column pruning and per-column compression help analytical queries. The
> comparison must be **fair**: identical data, query, and resources; verify
> both engines return **identical results**, then compare logical vs
> replicated bytes (`StorageSummary.java` prints `logical_bytes` vs
> `replicated_bytes`) and query times.

**Q: Show your Hive analytics query.**

> ```sql
> SELECT sr_type, substr(reading_date,1,4) AS year, COUNT(*) AS days,
>        SUM(requests) AS requests, AVG(requests) AS mean_daily_requests,
>        MAX(requests) AS max_daily_requests,
>        SUM(resolution_days)/NULLIF(SUM(completed),0) AS avg_resolution_days
> FROM table GROUP BY sr_type, substr(reading_date,1,4)
> ORDER BY sr_type, year;
> ```
> The year comes from `substr` because `reading_date` is a `YYYY-MM-DD`
> string; `NULLIF` prevents divide-by-zero for types with no completions.
> The results must match the MapReduce and Python summaries.

---

## 7. MongoDB

**Q: Why MongoDB in a Hadoop project?**

> It demonstrates a **document-store** analytics path independent of HDFS:
> flexible JSON-like documents, index-supported point lookups, and a rich
> aggregation pipeline. `python -m service_requests mongo` imports
> `daily.tsv` into collection **`daily_readings`** in a dedicated empty
> database (`service_requests_311`), in batches of **2,000** documents
> (max 10,000).

**Q: What indexes did you create and why?**

> `{sr_type: 1, year: 1}` (compound — serves "one type, one year" and
> type-prefix queries) and `{date: 1}` (day lookups). Indexes let queries
> walk a B-tree instead of scanning the collection — visible in explain as
> `totalKeysExamined ≈ nReturned` instead of `totalDocsExamined = whole
> collection`.

**Q: Explain your aggregation pipeline.**

> `$group` by `{sr_type, year}` with `$sum: 1` (days), `$sum: "$requests"`,
> `$max: "$requests"`, `$sum` of resolution days and completed →
> `$project` computes `mean_daily_requests = requests/days` and
> `avg_resolution_days` with a `$cond` guard (`$gt: completed, 0`) against
> divide-by-zero → `$sort` by type/year. The profiler script
> (`mongo_profile.py`) runs the same pipeline under
> `explain("executionStats")` and records `nReturned`,
> `executionTimeMillis`, `totalKeysExamined`, `totalDocsExamined`.

---

## 8. Dashboard and analytics definitions

**Q: What are your four annual metrics?**

> Per **request type per year**:
> 1. **Total requests** — count of requests created that year
> 2. **Mean requests/day** — total ÷ number of days with data
> 3. **Max daily requests** — busiest single day
> 4. **Avg resolution days** — weighted mean of (closed − created) over
>    completed requests only

**Q: What can a user do in the dashboard?**

> Flask, read-only (serves precomputed `analytics.json`, never starts jobs):
> **Page 1** — look up a type (e.g. *Pothole in Street Complaint*): year table,
> pie chart of any single metric's share by year, bar chart highlighting
> best/worst years. **Page 2** — pick year + metric + Top-K (1…#types): cards
> for the highest/lowest types and a ranked table. **Page 3** — real example
> types (with real volumes) as one-click cards + year-ranking link grid.
> Invalid input (bad year, metric, K) returns 400 — all handled server-side.

---

## 9. Verification, evidence, and honesty points

**Q: What evidence would you show that everything actually ran?**

> - `manifest.json`: source **SHA-256**, row counts, first/last dates
> - `analytics.json`: `"mapreduce_crosscheck": "passed"` + per-type records
> - Cluster: `hdfs dfsadmin -report` (≥2 live DataNodes),
>   `yarn node -list -states RUNNING` (≥2 NodeManagers), a completed YARN
>   application in the History Server, `_SUCCESS` file in the job output
> - Hive: query outputs from both Text and RCFile tables; Pig job counters
> - Mongo: `explain` stats before/after indexing
> - `scripts/verify_cluster.sh` runs the Hadoop **Pi example** as a smoke test

**Q: What does a passed local cross-check NOT prove?**

> It proves mapper+reducer logic matches the reference **on this machine**.
> It does *not* by itself prove the YARN run succeeded — that needs the
> History Server logs and `_SUCCESS`. Similarly, Docker containers are not
> three physical machines; I present Docker as a dev simulation and the
> physical-lab run separately.

**Q: How would your pipeline scale to the full 14.9M rows?**

> `prepare` **streams** the CSV row-by-row and aggregates in memory keyed by
> (day, type) — memory grows with *distinct groups* (~a few hundred thousand
> rows at most), not with 14.9M input rows. Beyond that, the same
> mapper/reducer run on HDFS splits in parallel; Pig/Hive scale out via
> YARN; Mongo sharding would be the next step if needed.

---

## 10. Tricky follow-ups teachers love

| Question | Model answer |
|---|---|
| Why TSV, not CSV, for the prepared file? | Tab needs no quoting; request types/addresses contain commas. One delimiter for Python, Pig, Hive. |
| Number of map tasks? | One per input split ≈ one per 128 MB HDFS block. |
| Number of reduce tasks here? | **2** (`mapreduce.job.reduces=2` in run_mapreduce.sh). |
| What if two rows have the same SR_NUMBER? | Impossible by design (unique key), but prepare never relies on it — it groups by date+type, not by ID. |
| Closed before created — what happens? | The row still counts as a request, but contributes **0** to `resolution_days` (only `CLOSED ≥ CREATED` counts). |
| Case sensitivity? | Status uppercased before matching (`Completed`/`COMPLETED`); dashboard type lookup is case-insensitive (casefold). |
| What's in the manifest? | Dataset name, source file name, **SHA-256**, source rows, daily rows, days, date range, column list. |
| Order of records in daily.tsv? | Sorted by (date, type) — deterministic output regardless of CSV row order. |
| Why `sr_type|year` as mapper key? | One reducer key per summary row; the pipe separates fields and `rsplit("|",1)` recovers both parts safely. |
| Combiner safe for MAX? | Yes (max is associative); for SUM yes; for AVG **no** unless you ship partial sum+count — that's why reducer recomputes from totals. |
| What is speculative execution? | Hadoop re-runs slow straggler tasks in parallel and keeps the first result; on by default, harmless for idempotent tasks like mine. |
| Where do map outputs live? | Local disk of the map task's node (not HDFS), deleted after the job. |
| What does `ANALYZE TABLE ... COMPUTE STATISTICS` do? | Populates row-count/size stats Hive's cost-based optimizer uses to pick better plans. |
| Why is `avg_resolution_days` 0 for some types? | Guard for zero completed requests — division by zero returns 0 by design, documented in code. |
| Biggest limitation of your project? | The 311 data is **event data**: yearly totals mix open/canceled requests and resolution time only exists for completed ones; also Docker ≠ physical cluster for the final evidence run. |

---

## 11. Rapid-fire one-liners

| Question | Answer |
|---|---|
| Dataset rows / columns? | **14.9M rows, 39 columns** |
| Row identifier? | `SR_NUMBER` (unique) |
| 311 system launch? | **18 December 2018** (older rows flagged `LEGACY_RECORD`) |
| Top real request type? | 311 INFORMATION ONLY CALL — **4,921,249** requests |
| Most common origin? | Phone Call (~**57%**) |
| Most common status? | Completed (~**97%**) |
| Daily TSV columns? | **6**: date, sr_type, requests, completed, canceled, resolution_days |
| Mapper emits how many fields? | **5** (key + requests + requests + resolution_days + completed) |
| Reducer emits how many fields? | **7** |
| Key format? | `sr_type|year` |
| Default HDFS block size? | **128 MB** |
| Your HDFS replication? | **2** |
| Cluster size? | **3 nodes** (master + 2 workers) |
| Number of metrics? | **4** |
| Cross-check tolerance? | `rel_tol = abs_tol = 1e-9` |
| Mongo batch size? | **2,000** default, max 10,000 |
| Mongo collection? | `daily_readings` |
| Hive table formats? | TextFile + **RCFile (gzip)** |
| Pig's role? | Validation/cleaning filter (LOAD → FILTER → STORE) |
| Dashboard framework? | Flask, 3 pages, read-only |

---

## 12. What to actually show during the viva

```powershell
# 1. Pipeline + cross-check (MapReduce vs Python)
python -m service_requests prepare --input "data/source/311_Service_Requests.csv" --output "data/prepared/service_requests"
python -m service_requests analyze --daily "data/prepared/service_requests/daily.tsv" --output "results/service_requests"

# 2. Dashboard (three pages)
python -m service_requests dashboard --results "results/service_requests"
#   http://127.0.0.1:5000/                       (page 1)
#   http://127.0.0.1:5000/?page=year&year=2024   (page 2)
#   http://127.0.0.1:5000/?page=examples         (page 3)

# 3. Cluster evidence (inside the cluster environment)
bash scripts/verify_cluster.sh                     # DataNodes, NodeManagers, Pi job
bash scripts/run_mapreduce.sh <HDFS_IN> <HDFS_OUT> 2
hdfs dfs -cat <HDFS_OUT>/part-* | less             # same 7-field rows
hive -f hive/tables.hql -hivevar DATABASE=service_requests_311 -hivevar INPUT=/user/USER/chicago311/RUN -hivevar RC_OUTPUT=/user/USER/chicago311/RUN_RC
hive -f hive/annual_client_summary.hql -hivevar DATABASE=service_requests_311 -hivevar TABLE=daily_text
pig -x mapreduce pig/clean_daily.pig -param INPUT=... -param OUTPUT=...
python -m service_requests mongo --daily data/prepared/service_requests/daily.tsv --database service_requests_311
python -m service_requests.mongo_profile --database service_requests_311 --sr-type "Pothole in Street Complaint"
```

Artifacts to have open: `manifest.json`, head of `daily.tsv`,
`mapreduce.tsv`, `analytics.json` (with `"mapreduce_crosscheck": "passed"`),
dashboard pages 1–3, YARN History Server screen, Hive query output.
