[CmdletBinding()]
param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $SkipTests) {
    python -m pytest -p no:cacheprovider tests
}

python -m PyInstaller --noconfirm --clean packaging\PlantTrace.spec

$Exe = Join-Path $Root "dist\PlantTrace\PlantTrace.exe"
if (-not (Test-Path $Exe)) {
    throw "PlantTrace.exe was not created."
}

Write-Host "PlantTrace build ready:"
Write-Host $Exe
