# Agent notes

## Spark worker Python

Task. Point PySpark at the project virtualenv.
Artifact. `src/sentinel/spark.py`
Correction. The worker was launching the system Python 3.9, which cannot import PySpark 4. Set `PYSPARK_PYTHON` to `sys.executable` before the session starts.

## dbt and Airflow in one environment

Task. Keep `dbt build` working after Airflow is installed.
Artifact. `pyproject.toml`
Correction. Airflow's constraint set downgraded protobuf, and dbt then crashed while printing its resource report. Install protobuf 6 or newer after Airflow.

## Mystery is not a second license change

Task. Show the unknown scanner case without adding a second license row.
Artifact. `fixtures/tarballs/mystery-1.0.0/deps.dev`
Correction. The license command's fixture proof is one widget row. Mystery is scanned from its tarball label file, not from `license_change`.

## dbt model selection

Task. Build a subset of models for one event date.
Artifact. `airflow/dags/sentinel_daily.py`
Correction. A comma-separated `--select` matches nothing. Separate the model names with spaces.
