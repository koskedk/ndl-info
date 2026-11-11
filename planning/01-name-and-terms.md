# What to call it, and the terms to use

## The name

**National Health Analytics and Intelligence (NHAI).** Confirmed with DHA on 11 November 2026.

- **It is DHA's own name.** DHA's architecture document is titled "National Health Analytics & Intelligence — Data Lake Architecture", and the RMNCAH-N mock-ups already carry "National Health Analytics & Intelligence (NHAI)" in the header.
- **Write it with "and"** in running text: National Health Analytics and Intelligence. Use **NHAI** after the first mention.

One-line description to use in slides:

> National Health Analytics and Intelligence (NHAI) picks up the health data staged in DHA's S3 Ceph and turns it into trusted indicators, programme dashboards and alerts, following the DHA Data Lake Architecture.

## Names for the parts

| Part | Name | What it is |
|---|---|---|
| Where the data comes from | **S3 Ceph** | DHA's object store, where data from Taifa Care systems is staged. NHAI's source, and the source of truth. NHAI reads it and has no control over it. |
| What is being built | **NHAI** | Everything from picking the data up to the dashboards, on NHAI's own infrastructure |
| A programme's workspace | **Programme Intelligence Hub** (Malaria Intelligence Hub, RMNCAH-N Intelligence Hub, later HIV, TB, Supply Chain) | Dashboards, maps, self-service analysis and line-list extracts for one programme |
| The big-screen monitoring view | **National Health Intelligence Centre view** | Key indicators and alerts for the centre's situation room |
| Temporary connectors | **Interim source bridges** | Short-lived feeds for data not yet staged in S3 Ceph, each with a stated condition for retiring it |

## Modern terms for the ideas discussed

Two different ideas have been travelling together under "dictionary" and "universal semantic layer". Separating them makes the design much easier to explain.

- **The shape of the data:** one set of tables that every source system is mapped into. This is a *canonical data model*.
- **The meaning of the numbers:** one place where each indicator is defined. This is a *semantic layer*, also called a *metrics layer*.

| What has been said | Term to use | What it means here |
|---|---|---|
| "A dictionary with all the patients from all Taifa Care EMRs", "universal layer" | **Canonical Health Data Model** | One set of tables (patient, encounter, diagnosis, lab test, prescription and so on) that KenyaEMR, AMRS and Tiberbu are all mapped into. It is shaped by what the indicators need, and it extends to non-clinical subjects such as commodities and facilities. |
| "Universal semantic layer" | **Indicator Registry** (the semantic or metrics layer) | Each indicator defined once (numerator, denominator, target, colour bands) and served to every dashboard from that one definition |
| "Data dictionary" | **Data catalog** and **business glossary** | A searchable inventory of every table and column with its origin, plus plain-language definitions of terms |
| "Agreed structure of a table" | **Data contract** | The written promise for a table: what one row means, its keys, its columns, and the quality rules it must pass |
| "Code mapping", "terminology dictionary" | **Terminology service** and **concept maps** | Lookups that translate each system's codes to national code sets |
| "Deduplication", "single patient" | **Identity resolution**, giving a **unified patient identity** | Recognising one person across systems. DHA's architecture calls the component the Master Patient Index; keep that name for the component. |
| "Golden record" | **Derived patient record** | The best-known details for a person, computed from all their source records and recomputable when rules change |
| "DV modelling" | **Integration layer** (Data Vault) | The part of silver that links records from different systems and keeps their full history |
| "Programme platforms", "dedicated platforms" | **Data products**, delivered through **Programme Intelligence Hubs** | A packaged, documented set of tables and dashboards owned by a programme |
| "Data marts" | **Data marts** | Keep DHA's term. A data mart is the tables behind one data product. |
| "Indicator cubes" | **Indicator tables** (pre-aggregated) | Keep DHA's term in diagrams; it means indicator values already totalled by month, place and group |
| "Pick up and stage" | **Pick-up** into **bronze** | Copying source data, unchanged, from S3 Ceph into NHAI's own storage |
| "Temporary boxes" | **Interim source bridges** | See above |
| "Line list downloads" | **Governed extracts** | Patient-level downloads that are scoped to the user's role, de-identified by default and logged. DHA's architecture calls this Query & Export Services. |
| "Incident room with big screens" | **Situation room displays** with **signals and alerts** | A signal is an indicator crossing a threshold or behaving unusually; an alert is a signal sent to someone |
| "Bronze, silver, gold" | **Bronze, silver, gold** | Keep DHA's terms. The general name for this pattern is medallion architecture. |
