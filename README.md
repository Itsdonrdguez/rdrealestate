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
This repository contains the implemented Milestone 1 foundation. The schema and migration must be reviewed before Milestone 2 begins.

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

Not started yet:
- Maryland connector and raw ingestion
- data validation and normalization layer
- matching / deduplication across records
- owner resolution and portfolio aggregation
- RentCast enrichment and queueing
- Search / filter API
- Opportunity scoring engine
- Next.js dashboard and map
- scheduled sync jobs and health monitoring

## Codex handoff plan
Codex should continue in controlled milestones instead of trying to build everything at once.

### Milestone 1 (implemented; awaiting schema approval)
Foundation only.
- app and repo layout
- DB schema foundation
- health endpoint
- Docker startup
- docs and architecture guardrails

### Milestone 2 (in progress)
Maryland connector and ingestion.
Required behavior:
- download from official Maryland data sources via API
- store raw payloads exactly as received
- validate schema and anomalies
- normalize addresses and owner names separately from raw values
- match to existing canonical properties
- upsert into PostgreSQL
- write sync logs and structured status output

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

"Build Milestone 2 for the property intelligence project.

We already have the foundation in place: monorepo, FastAPI app, SQLAlchemy models, Alembic skeleton, Docker Compose stack, and initial health endpoint.

Now implement the Maryland connector and ingestion pipeline in a way that respects the project's rules:
- preserve raw source data exactly as received
- use separate normalized representations for owner names and addresses
- keep source provenance on every imported fact
- use UUIDs for internal IDs and support multiple external IDs per property
- handle sync runs and structured logging
- do not build RentCast, scoring, maps, or UI before the Maryland ingestion foundation is working

Requirements:
1. create the `pipelines/maryland` package with connector, validation, normalization, and storage modules
2. add a local raw-data staging pattern for Maryland API records
3. validate schema and record counts before writing into canonical tables
4. map Maryland records into the existing model layer
5. write tests for schema validation and raw source preservation
6. provide a clear `README` or architecture note describing the pipeline flow
7. do not hard-code credentials; use environment variables only
8. keep the implementation minimal, stable, and reviewable"
