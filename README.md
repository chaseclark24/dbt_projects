# dbt Analytics Portfolio

A portfolio of dbt models built around real application data from Quantum Market Cap. The project demonstrates source modeling, staging conventions, dimensional joins, financial metrics, rolling stock-performance calculations, documentation, and data-quality testing.

## Project

### [QDB](qdb/README.md)

The `qdb` project uses DuckDB as the dbt engine and attaches local SQLite snapshots as read-only sources. It currently models:

- Company metadata.
- Company financial statements and financial-health measures.
- Daily price history.
- Latest price per symbol.
- Daily, seven-row, and 30-row returns.
- Rolling 30-calendar-day volume.

The final models include a company dimension, latest financial-health mart, stock-performance mart, and latest-price mart.

## Repository design

Only reusable project assets belong in Git:

- SQL models.
- Model and source YAML.
- dbt project and package configuration.
- Documentation.
- Dependency declarations.

Local databases, DuckDB output, credentials, virtual environments, logs, dbt build artifacts, and personal planning notes are intentionally excluded through `.gitignore`.

## Technology

- dbt Core
- dbt-duckdb
- DuckDB
- SQLite read-only attachments
- SQL and YAML

## Explore the project

See the [QDB project documentation](qdb/README.md) for model lineage, grain, calculated metrics, data tests, local setup, and build commands.
