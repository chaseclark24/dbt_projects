# QDB dbt Project

This project models a local, read-only snapshot of QuantumDB data with dbt and
DuckDB. It standardizes company and financial source data, selects the latest
financial record for each company, and produces a tested company dimension
enriched with current financial-health measures.

The SQLite source database is intentionally excluded from Git. It is a local
development input, not part of the repository.

## Model lineage

```text
qdb_source.financials
        |
        v
stg_financials
        |
        v
mart_latest_financial_health ---------+
                                       |
                                       v
                                mart_company_dim
                                       ^
                                       |
qdb_source.company_metadata            |
        |                              |
        v                              |
stg_company_metadata -----------------+
```

### `stg_financials`

The staging model selects the financial fields needed downstream and casts
source text values to useful DuckDB date and timestamp types.

Grain: one row per company symbol and financial reporting period.

Important transformations include:

- Casting `period_end`, `cash_as_of`, and `operating_cash_flow_as_of` to dates.
- Casting `updated_at` to a timestamp.
- Preserving source financial values without calculating business metrics.

### `mart_latest_financial_health`

This mart uses `row_number()` to select the latest financial record for each
symbol. `updated_at` breaks ties when records have the same reporting-period
end date.

Grain: one row per company symbol with available financial data.

The mart calculates:

- `revenue_growth_pct`: percentage change from source-provided comparison revenue.
- `net_margin_pct`: net income as a percentage of revenue.
- `net_cash`: total cash minus total debt.
- `has_negative_cash_flow`: `1` for negative operating cash flow, `0` for
  nonnegative cash flow, and `NULL` when cash flow is unavailable.
- `going_concern`: the source-provided going-concern flag.

The mart preserves the financial period, cash and operating-cash-flow
measurement dates, operating-cash-flow basis, and source update timestamp.

### `stg_company_metadata`

The staging model selects the company reference fields, casts `ipo_date` to a
date, and casts `updated_at` to a timestamp.

Grain: one row per company symbol.

Employee count and IPO date remain nullable because the source does not always
provide them.

### `mart_company_dim`

This mart starts with `stg_company_metadata` and left joins each company's
latest available financial record from `mart_latest_financial_health`.

Grain: one row per company symbol in the company metadata source.

The left join preserves companies that do not yet have financial data. For
those companies, the financial columns are legitimately `NULL`. Separate
company-metadata and financial update timestamps retain the provenance of each
side of the joined record.

## Data-quality tests

The project tests that:

- Required identifiers, classifications, reporting dates, and source values
  are populated.
- `stg_financials` is unique at the symbol and reporting-period grain.
- The financial-health and company-dimension marts contain one row per symbol.
- Cash-flow and going-concern flags contain only `0` or `1` when populated.
- Every symbol in `mart_latest_financial_health` exists in
  `stg_company_metadata`.

Some values may legitimately be `NULL`. Revenue growth is unavailable when
comparison revenue is missing or zero. Employee count and IPO date may be
missing in company metadata, and the financial side of `mart_company_dim` may
be missing because that model uses a left join.

## Local setup

The project was developed with:

- Python 3.12
- dbt Core 1.12.3
- dbt-duckdb 1.11.0
- DuckDB as the dbt target
- A read-only SQLite attachment named `qdb_source`

Create a dbt profile named `qdb` in your local `~/.dbt/profiles.yml`. The
profile should point DuckDB at a local development database and attach the
local SQLite snapshot:

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

From the `qdb` directory, build the complete current lineage and run its tests:

```powershell
..\.venv\Scripts\dbt.exe build --select +mart_company_dim
```

The leading `+` selects `mart_company_dim` and all of its upstream dbt models,
including both staging models and `mart_latest_financial_health`.

Preview the final company dimension:

```powershell
..\.venv\Scripts\dbt.exe show --select mart_company_dim --limit 20
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
|   |-- company_dim.yml
|   |-- staging/
|   |   |-- stg_financials.sql
|   |   `-- stg_company_metadata.sql
|   `-- marts/
|       |-- mart_latest_financial_health.sql
|       `-- mart_company_dim.sql
|-- analyses/
|-- macros/
|-- seeds/
|-- snapshots/
`-- tests/
```
