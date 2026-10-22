$ErrorActionPreference = "Stop"
$repositoryRoot = Split-Path -Parent $PSScriptRoot
$environmentPath = Join-Path $repositoryRoot ".env"
if (-not (Test-Path $environmentPath)) { throw ".env does not exist" }

function New-HexSecret([int]$ByteCount) {
    $bytes = New-Object byte[] $ByteCount
    $generator = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $generator.GetBytes($bytes) } finally { $generator.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace("-", "").ToLowerInvariant()
}

$content = Get-Content -Raw $environmentPath
function Read-Value([string]$Name) {
    $match = [regex]::Match($content, "(?m)^$([regex]::Escape($Name))=(.*)$")
    if (-not $match.Success) { throw "$Name is missing from .env" }
    return $match.Groups[1].Value.Trim()
}

$databaseUser = Read-Value "POSTGRES_USER"
$databaseName = Read-Value "POSTGRES_DB"
if ($databaseUser -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { throw "Unsafe POSTGRES_USER value" }
if ($databaseName -notmatch '^[A-Za-z_][A-Za-z0-9_]*$') { throw "Unsafe POSTGRES_DB value" }

$databasePassword = New-HexSecret 24
$applicationSecret = New-HexSecret 48

Push-Location $repositoryRoot
try {
    docker compose exec -T db psql -v ON_ERROR_STOP=1 -U $databaseUser -d $databaseName -c "ALTER ROLE `"$databaseUser`" PASSWORD '$databasePassword';" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "PostgreSQL password rotation failed" }

    $content = [regex]::Replace($content, '(?m)^POSTGRES_PASSWORD=.*$', "POSTGRES_PASSWORD=$databasePassword")
    $content = [regex]::Replace(
        $content,
        '(?m)^DATABASE_URL=.*$',
        "DATABASE_URL=postgresql+psycopg://$databaseUser`:$databasePassword@localhost:5433/$databaseName"
    )
    if ($content -match '(?m)^SECRET_KEY=') {
        $content = [regex]::Replace($content, '(?m)^SECRET_KEY=.*$', "SECRET_KEY=$applicationSecret")
    } else {
        $content = [regex]::Replace($content, '(?m)^APP_SECRET=.*$', "SECRET_KEY=$applicationSecret")
    }
    [IO.File]::WriteAllText($environmentPath, $content, [Text.UTF8Encoding]::new($false))
    Write-Output "Local database and application secrets rotated. Values remain only in .env."
} finally {
    Pop-Location
}
