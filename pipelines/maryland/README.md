# Maryland SDAT/MDP pipeline

This package implements the first state connector for the property-intelligence system. It uses Maryland Open Data dataset `ed4q-f8tm`, the statewide SDAT assessment data joined with Maryland Department of Planning parcel data.

## Important source limitation

The public dataset is named `Maryland Real Property Assessments_Hidden Property Owner Names`. It intentionally does not expose owner names. This connector therefore builds the property, address, assessment, and sale backbone only. Owner records must come from a separately authorized Maryland dataset or another licensed source and will be handled by a separate connector.

## Flow

1. `connector.py` requests deterministic Socrata pages and never writes to the database.
2. `raw_store.py` writes every HTTP response body byte-for-byte under `data/raw/maryland/<run UUID>/`.
3. `validation.py` rejects records without stable source identity and update metadata.
4. `normalization.py` creates a new typed interpretation without mutating the raw record.
5. `storage.py` maps validated records into canonical tables while retaining source identifiers.
6. `pipeline.py` records batch status and counters in `sync_runs`.

Each raw run includes a manifest containing the source URL, filenames, byte counts, record counts, and SHA-256 hashes.

## Safe first run

From the repository root, with the API dependencies installed:

```powershell
python -m pipelines.maryland.cli --dry-run --limit 10
```

This contacts Maryland Open Data and writes immutable raw pages, but does not touch PostgreSQL. Remove `--dry-run` only after inspecting the raw files and validation output. Full-state ingestion requires the explicit `--all` flag.

Long runs use Maryland account-ID keyset pagination and write `checkpoint.json` after each committed page. Resume an interrupted run with `--resume <run UUID>`. Requests retry rate limits and transient network/server failures with bounded exponential backoff. The loader reserves 2 GB of free disk by default; change the guard explicitly with `--min-free-gb`.

An optional `MARYLAND_APP_TOKEN` can be provided through `.env` for higher Socrata rate limits. No token is required for small public samples.
