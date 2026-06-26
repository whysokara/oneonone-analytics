# 1. Role of dbt

**Module:** Fundamentals · **Status:** ✅

## The problem dbt solves
The hard part of analytics isn't *getting* data — it's **transforming** raw data into
trustworthy, business-meaning tables (reconciling definitions, cleaning, joining, shaping).
dbt is built specifically for that transformation step.

## ETL vs ELT (the key idea)
- **ETL = Extract, Transform, Load.** Transform happens *before* loading, in a separate
  engine. Warehouse only sees the polished final product. Done historically because storage
  + compute were expensive — you couldn't afford to dump raw data into the warehouse.
- **ELT = Extract, Load, Transform.** Load raw data into the warehouse *first*, then
  transform *in-place with SQL* using the warehouse's own compute.

**Why the order flipped:** cloud warehouses (Snowflake, BigQuery, Redshift, Databricks)
made storage cheap, compute massive + elastic, and separated compute from storage. Once the
warehouse itself could do the heavy transforming, the separate transform engine became
unnecessary. **dbt is the "T" in ELT.**

**Why ELT wins:**
- Raw data is preserved → you can re-transform later (in ETL the raw was already discarded).
- Transformations are just SQL — the language analysts already know.
- The warehouse does the heavy lifting and scales with the data.

## What dbt actually is
- dbt does **NOT** extract, load, store data, or have its own compute engine.
- dbt **takes your SQL, sends it to the warehouse to run, and manages the engineering
  discipline around it.** Think: a *compiler + orchestrator for SQL transformations*.
- You write a `SELECT`; dbt wraps it in the right `CREATE TABLE/VIEW`, figures out run order,
  runs it against the warehouse, and tests the result.

## Analytics engineering (the role dbt created)
Fills the gap between **data engineers** (software-strong, not deep in business logic) and
**data analysts** (know SQL + business, but no engineering rigor). The **analytics engineer**
owns the transformation layer and brings software best practices:
- Version control (Git) · Modularity (small reusable models) · Testing
- Documentation & lineage · DRY (define logic once, reuse everywhere)

Cultural shift: **treat analytics code like real software.**

## Where dbt sits in the stack
```
Sources → Ingestion (Fivetran/Airbyte/custom) → Warehouse [ raw → dbt transforms → business tables ] → BI / AI
```
dbt owns the **raw → analysis-ready** middle. Not ingestion, not visualization.

## One-paragraph takeaway
dbt is the **transformation layer of the modern ELT stack**. Cheap cloud storage + elastic
warehouse compute made it viable to load raw first and transform in-place with SQL (ELT,
the reversal of ETL). dbt orchestrates those transformations with software-engineering
discipline, enabling the **analytics engineer** role. dbt itself doesn't move, store, or
compute data — it tells the warehouse what to build, in what order, and verifies the result.
