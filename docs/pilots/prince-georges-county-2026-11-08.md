# Prince George's County ingestion pilot — 2026-11-08

## Decision

The county scale pilot **passes** throughput, validation, provenance, uniqueness, and checkpoint recovery. Page-oriented database preloading removed the per-record lookup bottleneck and increased sustained throughput from the Charles County baseline of 79.73 records/second to 262.63 records/second at more than four times the record volume.

A statewide import remains **no-go on capacity**. Prince George's measurements project 51.12 GB of raw plus database storage statewide and require 102.24 GB at the 2× operating allowance, while 43.51 GB was free after this pilot.

## Preflight

| Measurement | Value |
| --- | ---: |
| Prince George's source records | 315,586 |
| Statewide source records | 2,434,625 |
| Host disk free before import | 50.65 GB |
| Configured minimum free threshold | 2.00 GB |
| Raw-data directory before import | 1,015,894,058 bytes |
| PostgreSQL before import | 579,924,451 bytes |
| Docker images | 3.437 GB |
| Docker volumes | 4.166 GB |
| Docker build cache | 8.350 GB (6.407 GB reclaimable) |

The Charles County per-property measurements projected approximately 6.5 GB for this county, or approximately 13 GB at the required 2× allowance. The 50.65 GB available before import provided sufficient county-pilot headroom.

## Run results

Run ID: `50ae47b2-336d-4a61-abaa-dc40d3caea1a`

| Measurement | Result |
| --- | ---: |
| Records requested / received | 315,586 / 315,586 |
| Records validated | 315,586 |
| Inserted / updated / skipped / failed | 315,586 / 0 / 0 / 0 |
| API pages fetched | 317 (316 data pages plus terminal empty page) |
| API retries | 0 |
| HTTP 429 / 5xx responses | 0 / 0 |
| Active elapsed time | 1,201.62 seconds (20m 1.62s) |
| Average throughput | 262.63 records/second |
| Database write time | 713.10 seconds |
| Database write throughput | 442.55 records/second |
| Raw bytes written | 4,237,332,643 bytes (4.237 GB) |
| PostgreSQL after import | 2,968,949,219 bytes |
| PostgreSQL growth | 2,389,024,768 bytes (2.389 GB) |
| Raw bytes/property | 13,426.87 |
| Database growth/property | 7,570.12 bytes |
| Checkpoints | 317 |

The importer was deliberately paused after page 2 at 2,000 records. Restarting the same run resumed after account ID `17010021014`, completed the remaining records, and retained the original run and raw directory.

## Optimization and scale findings

The previous implementation issued multiple existence queries and flushes for every property. The optimized storage path preloads source records, canonical source IDs, assessments, and sales once per page, assigns UUIDs before persistence, and performs a single explicit provenance flush before dependent facts.

The controlled two-page run measured 114.02 records/second overall and 507.06 database records/second. At full scale, overall throughput settled at 262.63 records/second and database persistence at 442.55 records/second. This is a 3.29× overall improvement over the Charles baseline despite the larger canonical tables and indexes.

The 4.237 GB raw snapshot exposed a 32-bit overflow in `sync_runs.raw_bytes` during final status persistence. Migration `20261108_0006` widens the field to `BIGINT`. The last checkpoint already contained all 315,586 committed records, so the final resume safely wrote the manifest and successful status without duplicating canonical records.

## Data-quality and recovery checks

- Schema anomalies that stopped ingestion: 0
- Record validation/normalization failures: 0
- Canonical Prince George's properties: 315,586 total and 315,586 distinct source IDs
- Maryland external IDs: 315,586 total and 315,586 distinct source IDs
- Raw provenance rows: 315,586 total, 315,586 distinct source IDs, and 315,586 distinct record hashes
- Resume-created duplicate canonical records: 0
- Final run status: `succeeded`
- Raw manifest present: yes

## Postflight and statewide projection

| Measurement | Value |
| --- | ---: |
| Host disk free after import | 43.51 GB |
| Raw-data directory after import | 5,266,691,314 bytes |
| PostgreSQL after import | 2,968,949,219 bytes |
| Projected statewide raw storage | 32.69 GB |
| Projected statewide database storage | 18.43 GB |
| Projected statewide combined storage | 51.12 GB |
| Required capacity at 2× | 102.24 GB |
| Projected statewide runtime | 9,270 seconds (2h 34m 30s) |

The projection excludes WAL retention, backups, future raw snapshots, owner data, listing enrichment, and subsequent synchronization runs. Increase storage headroom before statewide ingestion; the current 43.51 GB free is 58.73 GB below the 2× projected requirement.

## Owner intelligence dependency

The public scale pilot does not change the owner-data constraint. Authorized Maryland owner-name data remains required before portfolio aggregation, absentee analysis, entity grouping, or meaningful opportunity scoring can be evaluated.
