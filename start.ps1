param(
    [string]$Database = "$PSScriptRoot\data\lacan.db"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
New-Item -ItemType Directory -Force (Split-Path -Parent $Database) | Out-Null

Write-Host "Starting Hermeneut interactive CLI..." -ForegroundColor Cyan
Write-Host "Database: $Database" -ForegroundColor DarkGray
python -m hermeneut --db $Database interactive
if ($LASTEXITCODE -ne 0) {
    Write-Host "Hermeneut exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
