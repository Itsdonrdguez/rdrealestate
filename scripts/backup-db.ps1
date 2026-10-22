param([string]$OutputDirectory = "backups")

$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$backupDirectory = Join-Path $repositoryRoot $OutputDirectory
New-Item -ItemType Directory -Force -Path $backupDirectory | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = Join-Path $backupDirectory "property-intelligence-$timestamp.dump"
$containerPath = "/tmp/property-intelligence-$timestamp.dump"

Push-Location $repositoryRoot
try {
    docker compose exec -T db sh -c "pg_dump -Fc -U `$POSTGRES_USER -d `$POSTGRES_DB -f $containerPath"
    if ($LASTEXITCODE -ne 0) { throw "pg_dump failed with exit code $LASTEXITCODE" }
    docker cp "property-intelligence-db:$containerPath" $backupPath
    if ($LASTEXITCODE -ne 0) { throw "docker cp failed with exit code $LASTEXITCODE" }
    docker compose exec -T db rm -f $containerPath
    Write-Output "Backup created: $backupPath"
} finally {
    Pop-Location
}
