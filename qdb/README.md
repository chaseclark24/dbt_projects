# QDB Financial Health dbt Project

This project models a local, read-only snapshot of QuantumDB financial data with dbt and DuckDB. It turns source financial records into a tested mart containing the latest financial-health metrics for each company.

The SQLite source database is intentionally excluded from Git. It is a local development input, not part of the repository.

## Model lineage

```text
qdb_source.financials
        |
        v
stg_financials
        |
        v
mart_latest_financial_health
```

### `stg_financials`

The staging model reads `qdb_source.financials`, selects the fields needed downstream, and casts source text fields to useful DuckDB types.

Grain: one row per company symbol and financial reporting period.

Important transformations include:

- Casting `period_end`, `cash_as_of`, and `operating_cash_flow_as_of` to dates.
- Casting `updated_at` to a timestamp.
- Preserving the source values without applying business-level filters or metrics.

### `mart_latest_financial_health`

The mart uses `row_number()` to select the latest financial record for every symbol. `updated_at` is used as a tie-breaker when records have the same reporting-period end date.

Grain: one row per company symbol.

The mart calculates:

- `revenue_growth_pct`: percentage change from the source-provided previous revenue value.
- `net_margin_pct`: net income as a percentage of revenue.
- `net_cash`: total cash minus total debt.
- `has_negative_cash_flow`: `1` when operating cash flow is negative, `0` when it is nonnegative, and `NULL` when cash flow is unavailable.
- `going_concern`: the source-provided going-concern flag.

The mart also preserves the cash and operating-cash-flow measurement dates, calculation basis, and source update timestamp so consumers can understand the provenance of each metric.

## Data-quality tests

The project uses dbt data tests to verify that:

- Required staging identifiers and dates are populated.
- The mart contains exactly one row per symbol.
- Required mart fields are populated.
- Cash-flow and going-concern flags contain only accepted values.

Some calculated values may legitimately be `NULL`. For example, revenue growth cannot be calculated when the previous revenue value is unavailable or zero.

## Local setup

The project was developed with:

- Python 3.12
- dbt Core 1.12.3
- dbt-duckdb 1.11.0
- DuckDB as the dbt target
- A read-only SQLite attachment named `qdb_source`

Create a dbt profile named `qdb` in your local `~/.dbt/profiles.yml`. The profile should point DuckDB at a local development database and attach your local SQLite snapshot:

```yaml
qdb:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "C:/path/to/dbt_projects/qdb/dev.duckdb"
      schema: main
      threads: 4
      attach:
        - path: "C:/path/to/quantumdb.sqlite"
          type: sqlite
          alias: qdb_source
          read_only: true
```

Neither `profiles.yml` nor the local database files should be committed.

## Running the project

From the `qdb` directory, run the financial-health pipeline and its tests:

```powershell
..\.venv\Scripts\dbt.exe build --select +mart_latest_financial_health
```

The leading `+` selects the mart and its upstream dbt models, ensuring `stg_financials` is built before the mart.

Preview the completed mart:

```powershell
..\.venv\Scripts\dbt.exe show --select mart_latest_financial_health --limit 20
```

Generate and view the dbt documentation and lineage graph:

```powershell
..\.venv\Scripts\dbt.exe docs generate
..\.venv\Scripts\dbt.exe docs serve
```

Stop the documentation server with `Ctrl+C`.

## Repository structure

```text
qdb/
|-- dbt_project.yml
|-- models/
|   |-- sources.yml
|   |-- financial_health.yml
|   |-- staging/
|   |   `-- stg_financials.sql
|   `-- marts/
|       `-- mart_latest_financial_health.sql
|-- analyses/
|-- macros/
|-- seeds/
|-- snapshots/
`-- tests/
```
