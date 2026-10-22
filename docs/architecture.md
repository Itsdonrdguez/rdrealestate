# Architecture notes

## Domain model summary
The core schema is intentionally split into operational tables and source-provenance tables.

- `properties`: canonical property records with UUIDs and the primary property facts.
- `addresses`: normalized and raw address representations.
- `owners`: normalized owner identity and portfolio metadata.
- `property_ownership`: the relationship between properties and owners over time.
- `assessments`: value history tied to a source and timestamp.
- `sales`: sale transactions tied to a source and timestamp.
- `property_source_ids`: external IDs mapped to a single internal property.
- `source_records`: preserved raw payloads from every connector.
- `sync_runs`: audit trail for batch runs and scheduler jobs.

## Data flow
1. Extract from source systems.
2. Store raw payloads without mutation.
3. Validate schema and values.
4. Normalize addresses and owner names.
5. Match against existing canonical records.
6. Upsert stable entities.
7. Derive features like years owned and absentee status.
8. Score opportunities and expose them through APIs.

## Why this structure matters
This keeps Maryland, RentCast, and future connectors modular while preserving raw evidence and avoiding brittle single-table ingestion.

## Product direction
The application is owner-centric. Its eventual job is to connect properties to owners and entities, show portfolio and ownership history, combine government and selectively purchased enrichment data, and produce explainable acquisition-opportunity signals. Maryland is the first source implementation, not a permanent boundary in the core schema.

## Foundation boundary
Milestone 1 contains schema, provenance, raw-record storage, migrations, configuration, structured logging, health checks, and local containers. The public Maryland property backbone is now implemented; licensed owner ingestion, broader entity resolution, commercial enrichment, scoring, and full user-interface work remain later milestones.

## Maryland ingestion reliability
The public Maryland loader uses stable account-ID keyset pagination, bounded retry/backoff, append-only raw pages, atomic checkpoints, page-level schema validation before canonical writes, and a free-disk reserve. A normalized fact links back to its `source_records` evidence row and sync run. Interrupted runs resume from their last committed account ID.

## Owner resolution boundary
Public Maryland data hides owner names. The owner schema supports raw and normalized mailing addresses, entity type, resolution status, confidence, and ownership match metadata, but no owner records are fabricated. Automatic matching is limited to exact normalized name plus exact normalized mailing address. Name-only matches remain review candidates.
