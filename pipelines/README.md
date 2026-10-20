# Pipelines

This directory holds the source-specific ETL modules.

Planned modules:
- `maryland/`
- `rentcast/`
- `enrichment/`

Each pipeline should follow a common pattern:
extract -> raw store -> validate -> normalize -> match -> upsert -> derive -> log

The first implemented connector is [`maryland/`](maryland/README.md). It targets the public statewide SDAT/MDP property backbone and intentionally excludes owner names because they are hidden in the public dataset.
