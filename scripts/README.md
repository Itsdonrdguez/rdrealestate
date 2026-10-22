# Operations scripts

Run `powershell -ExecutionPolicy Bypass -File scripts/backup-db.ps1` from the repository root to create a compressed PostgreSQL dump under `backups/`. Backups are excluded from Git.

Test restoration into a separate database before relying on a backup. Restore is intentionally not automated because overwriting the working database is destructive; use `pg_restore --clean --if-exists` only after selecting and verifying an explicit target database.

After taking a verified backup, run `powershell -ExecutionPolicy Bypass -File scripts/rotate-local-secrets.ps1` to generate strong local database and application secrets, update the ignored `.env`, and rotate the PostgreSQL role password. Recreate the database and API containers afterward with `docker compose up -d --force-recreate db api`.
