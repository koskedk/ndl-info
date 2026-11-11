# Planning: National Health Analytics and Intelligence (NHAI)

Working papers for NHAI, prepared on 11 November 2026 ahead of drawing the proposed architecture.

They follow DHA's Data Lake Architecture, which NHAI must keep to and only improve. What is actually staged in S3 Ceph is recorded in `docs/exploration/`.

| Paper | What it settles |
|---|---|
| [01-name-and-terms.md](01-name-and-terms.md) | The confirmed name, what to call the parts, and modern terms to use in place of "dictionary" and "universal semantic layer" |
| [02-components-and-technology.md](02-components-and-technology.md) | Every component, the DHA architecture box it belongs to, and the open-source tool proposed for it; the high-level flow from S3 to dashboard; the Master Patient Index |
| [03-data-layers.md](03-data-layers.md) | Bronze, silver and gold: the canonical model, how Data Vault supports the Master Patient Index, facts and dimensions, and twelve proof-of-concept indicators |

## The proposal in brief

- **Name:** National Health Analytics and Intelligence (NHAI). Confirmed with DHA.
- **Source:** S3 Ceph, where DHA stages data from Taifa Care systems. NHAI reads it and has no control over it.
- **Where NHAI runs:** its own infrastructure, with SeaweedFS as its S3 storage. NHAI picks the data up, stages it there, and builds everything.
- **Flow:** S3 Ceph → pick-up → bronze (staged as picked up) → silver (cleaned, patients linked, one canonical model) → gold (facts and dimensions) → serving database → Indicator Registry → API layer → Programme Intelligence Hubs, the National Health Intelligence Centre, and external systems.
- **Data not in S3 Ceph** arrives through interim source bridges, each temporary, with the advice to DHA that those sources be staged in S3 Ceph.
- **Core stack:** Iceberg, Trino, dbt, Dagster, ClickHouse, with Lakekeeper as the table catalog and Cube as the Indicator Registry.
- **Master Patient Index:** a named component in silver that links one person across systems, built on Data Vault so every match is recorded and reversible.
- **Data Vault:** used only for patients, facilities and encounters. Events go straight to the canonical model.
- **Dashboards:** a custom web application for the designed programme dashboards, Metabase for self-service, Grafana for the Intelligence Centre's screens and alerts. Superset is optional for advanced users.

## Decided

- The name: National Health Analytics and Intelligence (NHAI).
- The source: S3 Ceph.
- Storage and infrastructure: SeaweedFS, on NHAI's own infrastructure.

## To decide before the architecture is drawn

1. Whether dashboards are served from a ClickHouse that NHAI runs (the leaning) or DHA's existing one.
2. Custom-built programme dashboards, or a business-intelligence tool.
3. Cube or dbt MetricFlow for the Indicator Registry.
4. How the Master Patient Index gets an up-to-date Client Registry, and whether DHA will stage names and addresses for KenyaEMR and AMRS.

The detail and a leaning for each are at the end of [02-components-and-technology.md](02-components-and-technology.md).
