# Property Intelligence

A private, local-first property + owner + opportunity intelligence platform for Maryland, focused on low cost, automation, and a modular architecture that Codex can extend without rebuilding the system.

## Goal
This is not a Zillow clone. It is a private intelligence system for:

- Maryland property search and filtering
- owner portfolio analysis
- absentee and out-of-state detection
- ownership-duration and equity-oriented opportunity scoring
- enrichment from public data and eventually commercial sources
- durable provenance tracking so every imported fact keeps its source

## What we want to accomplish
The long-term end state is a local web app that lets you search and analyze Maryland properties using filters such as:

- County
- Property type
- Owner occupied / absentee
- Years owned
- Last sale date and price
- Assessed value
- Owner portfolio size
- Active / inactive listing status
- Estimated value, rent, and equity
- Opportunity score

The property profile should show:

- address and property details
- owner identity and mailing details
- years owned and portfolio metrics
- listing history and failed seller signals
- estimated rent and AVM value
- mortgage / equity estimates (when available)
- opportunity score with explainable factors

## Current status: where we are
The foundation and public Maryland ingestion engine are complete through baseline commit `e7748ae`. The Charles County capacity, recovery, and data-quality pilot is complete; see [the pilot report](docs/pilots/charles-county-2026-10-22.md). Accurate owner intelligence remains blocked on obtaining an authorized owner-name source.

Completed:
- monorepo structure
- Docker Compose local dev stack
- FastAPI app scaffold
- PostgreSQL/PostGIS configuration foundation
- SQLAlchemy models for properties, addresses, owners, ownership, assessments, sales, external IDs, raw source records, and sync logs
- initial Alembic migration for the foundation schema
- required provenance metadata on imported domain records
- structured JSON application logging
- health check endpoint and basic tests
- .env handling and local startup scripts
- README and AGENTS instructions for Codex guardrails
- official Maryland public-data connector, validation, normalization, and canonical upserts
- append-only raw snapshots and source-record lineage
- checkpoint/resume ingestion with sync-run tracking
- PostGIS property geometry
- conservative owner-resolution fields and matching foundation
- Charles County checkpoint/recovery and capacity benchmark
- responsive workspace navigation and Charles County property browser
- live system/data-health dashboard backed by sync and storage metrics
- property profiles with characteristics, assessment and sale history, coordinates, and provenance

Next / blocked:
- increase statewide storage headroom and optimize canonical upsert throughput (next)
- add the PostGIS map with bounded and clustered property queries
- authorized Maryland owner-name data acquisition (blocks meaningful owner intelligence)
- owner portfolio aggregation after owner-name access
- RentCast enrichment and queueing
- Search / filter API
- Opportunity scoring engine
- PostGIS map and marker summaries
- scheduled sync jobs and health monitoring

## Codex handoff plan
Codex should continue in controlled milestones instead of trying to build everything at once.

### Milestone 1 (complete)
Foundation only.
- app and repo layout
- DB schema foundation
- health endpoint
- Docker startup
- docs and architecture guardrails

### Milestone 2 (public property backbone complete)
Maryland connector and ingestion.
Required behavior:
- download from official Maryland data sources via API
- store raw payloads exactly as received
- validate schema and anomalies
- normalize addresses and owner names separately from raw values
- match to existing canonical properties
- upsert into PostgreSQL
- write sync logs and structured status output

### County ingestion pilot (complete)
- preflight host, Docker, PostgreSQL, and raw-data capacity
- benchmark Charles County throughput and storage
- deliberately pause and resume from a checkpoint
- verify canonical and provenance records are not duplicated
- project statewide runtime and storage before a scale test in Prince George's County

### Milestone 3
Owner resolution + portfolio aggregation.
- normalize owner names
- match owner records conservatively
- aggregate counts, years owned, and county distribution
- identify absentee and out-of-state owners

### Milestone 4
RentCast connector + enrichment queue.
- add connector abstraction for third-party sources
- pull AVMs, rents, listings, and owner metadata
- add caching and freshness checks
- queue enrichments for property pages and shortlist processing

### Milestone 5
Search + filter API.
- endpoint for properties, owners, and opportunities
- filters for county, value, equity, years owned, absentee, score, and listing status
- ranking and query planning for local use

### Milestone 6
Opportunity scoring.
- deterministic rules first
- explain each score increment with reasons
- score based on ownership length, absentee status, portfolio size, listing behavior, and equity signals

### Milestone 7
Next.js dashboard and property profile UI.
- home search and filters
- property cards and detail pages
- map and owner portfolio pages

### Milestone 8+
Automation and distress sources.
- daily / weekly jobs
- sync-run health tracking
- mortgages, deeds, tax delinquency, foreclosures, and other enrichment modules

## Architecture principles
- Raw source data is preserved and never overwritten.
- All imported facts keep source provenance.
- Internal IDs use UUIDs; external IDs are tracked separately.
- Data connectors stay pluggable and do not mutate the database directly.
- Matching and normalization are explicit and conservative.
- Opportunity scoring is deterministic before AI is introduced.

## Repository layout
```text
property-intelligence/
├── apps/
│   ├── api/
│   └── web/
├── pipelines/
│   ├── maryland/
│   ├── rentcast/
│   └── enrichment/
├── packages/
│   └── shared/
├── data/
│   ├── raw/
│   ├── staging/
│   └── exports/
├── scripts/
├── tests/
├── docs/
├── docker-compose.yml
├── .env.example
├── .env
├── .gitignore
├── README.md
├── AGENTS.md
├── start-local.bat
├── stop-local.bat
└── .dockerignore
```

## Stack
- Python 3.12
- FastAPI
- PostgreSQL 16 + PostGIS
- SQLAlchemy 2
- Alembic
- Pydantic
- Next.js + TypeScript
- Docker Compose
- Pytest

## Local development
Windows users can start everything by double-clicking:

- [start-local.bat](start-local.bat)

This script:
- creates a local `.env` if needed
- opens the health check and web app in the browser
- runs `docker compose up --build`

Command-line alternative:
```bash
docker compose up --build
```

Then open:
- API: http://localhost:8000/health
- Web: http://localhost:3000
- PostgreSQL: localhost:5433

To stop the stack:
- [stop-local.bat](stop-local.bat)

Stopping the stack preserves the PostgreSQL volume. To deliberately remove local database data, run `docker compose down -v` manually.

Before using real data, create a verified database backup with `scripts/backup-db.ps1` and rotate the generated local credentials with `scripts/rotate-local-secrets.ps1`. Both scripts keep secrets and database archives outside Git.

## Important design principles
- Raw source data is preserved, never overwritten.
- Internal IDs are UUIDs, not source IDs.
- Multiple external identifiers per property are supported.
- Search, scoring, and enrichment are implemented after the data model is stable.

## Double-click workflow
For a fast local start on Windows:

1. Ensure Docker Desktop is running.
2. Double-click [start-local.bat](start-local.bat).
3. The app opens at http://localhost:3000.
4. The API health check opens at http://localhost:8000/health.

## Copilot / Codex handoff prompt
Use this as the next prompt for the next coding session:

"Use commit `e7748ae` or newer as the baseline. The foundation, Maryland public ingestion, raw lineage, checkpoint/resume, PostGIS, and owner-matching foundation are complete. Finish and review the Charles County pilot report, then address its measured bottlenecks before the Prince George's County scale test. Do not build portfolio scoring from incomplete public owner data; authorized owner-name access is a separate dependency."
