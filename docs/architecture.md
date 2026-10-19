# Architecture

Sentinel answers license questions from a checked-in snapshot. A later deps.dev export can replace that file. The job interfaces stay the same.

## Snapshot

`fixtures/snapshot.json` is the registry extract. Each package version is keyed by system, name, and version. The file also holds dependency edges and the team roots.

## Spark

`sentinel licenses` and `sentinel squats` run Spark SQL on that snapshot. Licenses emits a row only when the SPDX license changes. Squats pairs a new name with a popular name in the same first-letter block.

## Scanners

`sentinel scan` opens the checked-in tarballs for those license changes. It records the deps.dev label, the LICENSE file label, and the package.json label.

## dbt

`dbt build` in `dbt/` loads the parquet files into DuckDB. The tables are package_version, license_change, lookalikes, scanner_disagreement, and tenant_exposure.

## Policy

Team rules live in `policies/*.yml`. The exposure SQL joins those rules to license_change. The SQL does not contain a team name.

## Ask

`sentinel ask` prints a claim, the SQL, and the row ids. The SQL reads only license_change, lookalikes, scanner_disagreement, and tenant_exposure.
