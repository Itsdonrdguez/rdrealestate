# Charles County ingestion pilot — 2026-10-22

## Decision

The county pilot **passes** validation, provenance, idempotent checkpoint recovery, and API resilience. A statewide import is currently **no-go on capacity**: the measured raw plus database footprint projects to 50.31 GB, while the required 2× operating allowance is 100.62 GB and the host had 63.85 GB free.

Before the Prince George's scale test or statewide import, increase available storage and profile the growing per-page database write time.

## Preflight

| Measurement | Value |
| --- | ---: |
| Charles County source records | 75,796 |
| Statewide source records | 2,434,005 |
| Host disk free | 63.85 GB |
| Configured minimum free threshold | 2.00 GB |
| Raw-data directory before import | 184,565 bytes |
| PostgreSQL before import | 20,165,091 bytes |
| Docker images | 3.388 GB |
| Docker volumes | 3.215 GB |
| Docker build cache | 5.330 GB (4.814 GB reclaimable) |

## Run results

Run ID: `0da8b3cc-4e20-4059-aa25-84eafb137077`

| Measurement | Result |
| --- | ---: |
| Records requested / received | 75,796 / 75,796 |
| Records validated | 75,796 |
| Inserted / updated / skipped / failed | 75,796 / 0 / 0 / 0 |
| API pages fetched | 76 |
| API retries | 1 transient transport retry |
| HTTP 429 / 5xx responses | 0 / 0 |
| Total elapsed time | 950.62 seconds (15m 50.62s) |
| Average throughput | 79.73 records/second |
| Raw bytes written | 1,015,694,843 bytes (1.016 GB) |
| PostgreSQL after import | 571,183,587 bytes |
| PostgreSQL growth | 551,018,496 bytes (551.02 MB) |
| Raw bytes/property | 13,400.38 |
| Database growth/property | 7,269.76 bytes |
| Checkpoints | 76 |

The importer was deliberately paused after page 2 at 2,000 records. Restarting the same run resumed after account ID `0901026542`, completed the remaining records, and retained the original run and raw directory.

## Data-quality and recovery checks

- Schema anomalies that stopped ingestion: 0
- Record validation/normalization failures: 0
- Canonical Maryland source IDs: 75,796 total and 75,796 distinct
- Duplicate canonical source-ID rate: 0%
- Raw provenance rows for the run: 75,796 total and 75,796 distinct source IDs
- Resume-created duplicate canonical records: 0
- Final run status: `succeeded`

## Statewide projection

These are linear planning estimates based on the measured county average. They do not include WAL retention, backups, future snapshots, owner data, listing enrichment, or normal operating headroom.

| Projection for 2,434,005 records | Estimate |
| --- | ---: |
| Raw storage | 32.62 GB |
| PostgreSQL storage growth | 17.69 GB |
| Combined raw + database | 50.31 GB |
| Required capacity at 2× | 100.62 GB |
| Runtime at measured throughput | 30,527 seconds (8h 28m 47s) |

The runtime estimate is optimistic if the observed increase in database write time continues at statewide scale. The next engineering work should profile and batch the canonical upserts, then rerun a representative benchmark before Prince George's County.

## Owner intelligence dependency

The public pilot does not change the owner-data constraint. Authorized Maryland owner-name data is still required before portfolio aggregation, absentee analysis, entity grouping, or meaningful opportunity scoring can be evaluated.
