param(
    [string]$Database = "$PSScriptRoot\data\lacan.db"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
$env:PYTHONPATH = $PSScriptRoot
New-Item -ItemType Directory -Force (Split-Path -Parent $Database) | Out-Null

Write-Host "Starting Lacan-Agent interactive CLI..." -ForegroundColor Cyan
Write-Host "Database: $Database" -ForegroundColor DarkGray
python -m lacan_agent --db $Database interactive
if ($LASTEXITCODE -ne 0) {
    Write-Host "Lacan-Agent exited with code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}
