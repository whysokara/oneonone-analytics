# dbt Core & Cloud Syllabus — Analytics With Sushil

> Source: https://analyticswithsushil.com/syllabus (captured 2026-06-26)
> "The full curriculum covered across the cohort, from fundamentals to dbt Cloud's newest AI-powered capabilities."

This is the master list of topics we are working through, **one at a time**. Progress is tracked in [PROGRESS.md](./PROGRESS.md). Each topic gets its own notes file in `topics/`.

---

## 1. Fundamentals (Core/Cloud)
| Topic | Description |
|---|---|
| Role of dbt | dbt's place in the modern data stack, ELT vs ETL, and analytics engineering. |
| Core vs Cloud | Difference between dbt Core (open source CLI) and dbt Cloud (SaaS platform). |

## 2. Project Setup (Core/Cloud)
| Topic | Description |
|---|---|
| Project | Basic structure of a project. |
| Environments | Configuring multiple environments (Development, Staging, Production) in dbt Cloud. |
| Connections | Setting up data warehouse connections (Snowflake) in dbt Cloud. |
| Repositories | Integrating dbt Cloud with GitHub for version control. |

## 3. Modeling (Core)
| Topic | Description |
|---|---|
| Models | Defining models using SQL; materializations (view, table, incremental, ephemeral, dynamic table). |
| Sources | Declaring sources with YAML; ensuring lineage from raw to curated data. |
| Seeds | Loading CSV files into the warehouse as seed data for transformations. |
| Snapshots | Implementing slowly changing dimensions (SCDs) using dbt snapshots. |

## 4. Templating & Macros (Core)
| Topic | Description |
|---|---|
| Jinja | Using Jinja templating to parameterize SQL models with loops and conditionals. |
| Custom Macros | Writing reusable SQL logic with custom macros. |
| Packages | Installing and using community packages for common transformations. |

## 5. Testing (Core)
| Topic | Description |
|---|---|
| Built-in Tests | Schema tests (unique, not_null, accepted_values, relationships). |
| Custom Tests | Defining custom tests in SQL or YAML for specific business logic. |

## 6. Documentation (Core)
| Topic | Description |
|---|---|
| Docs Generation | Auto-generating docs with model descriptions, lineage, and schema info. |
| Exposure | Defining exposures to track downstream dependencies like BI dashboards. |

## 7. Orchestration (Core)
| Topic | Description |
|---|---|
| Jobs | Using Airflow or similar orchestration to schedule dbt model executions. |

## 8. Advanced (Core)
| Topic | Description |
|---|---|
| Performance Tuning | Optimizing incremental models; indexes, clustering/partitioning strategies. |
| Hooks | Pre- and post-run hooks to manage warehouse tasks (grants, auditing). |

## 9. Access Management (Cloud)
| Topic | Description |
|---|---|
| RBAC | Users, Groups, Permission sets, Project and Account permissions, Licenses. |

## 10. Management (Cloud)
| Topic | Description |
|---|---|
| Profile | User profile, credentials, Password Security, Email and Slack notifications, Audit log. |

## 11. Orchestration (Cloud)
| Topic | Description |
|---|---|
| Jobs | Creating jobs in dbt Cloud to run transformations on a schedule. |
| Job Triggers | Configuring run triggers (manual, schedule-based). |
| Job Settings | Managing concurrency, threads, and run ordering in dbt Cloud jobs. |

## 12. Deployment (Cloud)
| Topic | Description |
|---|---|
| CI/CD | Setting up continuous integration pipelines with Git-based workflows. |

## 13. Advanced (Cloud)
| Topic | Description |
|---|---|
| dbt Cloud CLI | Local development against dbt Cloud with secure creds, deferral, Mesh support, fast builds. |
| dbt mesh | Multi-project deployments. |
| Release tracks | Automatic application of bug fixes, features, updates — no manual version upgrades. |

## 14. Capabilities (Cloud / Core)
| Topic | Area | Description |
|---|---|---|
| dbt Wizard | Cloud | AI assistant that generates SQL, docs, tests, and metrics inside dbt Studio, Canvas, and Insights via natural language. |
| dbt Canvas | Cloud | Drag-and-drop visual modeling for analysts to build transformations without SQL, fully Git-governed. |
| dbt Studio | Cloud | Cloud-based IDE to develop, test, and run dbt projects with integrated Git. |
| dbt Insights | Cloud | AI-assisted ad-hoc data exploration, query generation, and lightweight visualization. |
| dbt Catalog | Cloud | Centralized catalog with lineage (incl. column-level) and execution metadata for discovery and triage. |
| dbt Fusion engine | Core | Next-gen engine: faster parsing, live error detection, richer dev experiences across Studio and VS Code. |

## 15. API (Cloud)
| Topic | Description |
|---|---|
| Discovery API | Programmatic access to project metadata (DAG/lineage, resources) for catalogs, governance, tooling. |
| Semantic Layer and APIs | GraphQL/JDBC (and SDK) interfaces over the dbt Semantic Layer to serve governed metrics to BI & apps. |

## 16. Advanced (Cloud/Core)
| Topic | Description |
|---|---|
| Best practices and features | Fusion-compatible code writing and best practices. |
