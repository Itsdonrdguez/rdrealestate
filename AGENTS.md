# AGENTS.md

## Mission
Build a private property + owner + opportunity intelligence system for Maryland using a modular, extensible architecture. Keep the first milestone small, stable, and reviewable.

## Core rules
- Never hard-code credentials or API keys.
- Read environment variables from `.env` and `.env.example` only.
- Preserve raw source data exactly as received. Never overwrite or normalize raw records in place.
- Keep source provenance on all imported facts.
- Use UUIDs as internal primary keys; external IDs are stored in a separate mapping table.
- Prefer explicit source tables and normalized internal tables over a single giant table.
- Do not rewrite working data as a side effect of enrichment.
- Separate connectors, normalization, matching, enrichment, and application concerns.
- Use structured logging and status tracking for every pipeline run.
- Prototype in small milestones. Do not build pricing, scraping, or scoring before the foundation is approved.

## Repository conventions
- Keep the monorepo split between `apps/`, `pipelines/`, `packages/`, `data/`, `docs/`, and `tests/`.
- Use `apps/api` for FastAPI backend and `apps/web` for Next.js frontend.
- Database migrations are managed through Alembic.
- Every table should include `created_at` and `updated_at` timestamps when practical.
- Every imported fact should track `source`, `source_identifier`, and `observed_at`.

## Raw data rule
If the source system gives a value like `SMITH JOHN A & MARY J`, store the original raw value unchanged in `source_records` or an equivalent raw table. Only create normalized representations in separate fields or tables. Raw data is evidence; normalized data is interpretation.

## Implementation policy
- Build the foundation first: models, schema, Alembic, health endpoint, configuration, and local Docker setup.
- Only move to Maryland ingestion after the schema and data provenance model are approved.
- Treat external data connectors as pluggable modules that output standardized records, not direct database mutations.
