# Compliance Graph Harness - one-command setup (Windows)
# Usage: .\install.ps1 [-NoVenv] [-InstallHook]

param(
    [switch]$NoVenv,
    [switch]$InstallHook
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
Set-Location $Root

function Fail($Message) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit 1
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Fail "Python no encontrado. Instala Python 3.12+ y vuelve a intentar."
}

if ($NoVenv) {
    $Py = $python.Source
} else {
    if (-not (Test-Path ".venv")) {
        Write-Host "Creando .venv..." -ForegroundColor Cyan
        & $python.Source -m venv .venv
        if ($LASTEXITCODE -ne 0) { Fail "No se pudo crear .venv" }
    }
    $Py = Join-Path $Root ".venv\Scripts\python.exe"
    if (-not (Test-Path $Py)) { Fail "No se encontro $Py" }
}

Write-Host "Instalando el paquete en modo editable..." -ForegroundColor Cyan
& $Py -m pip install --upgrade pip
& $Py -m pip install -e ".[dev]"
if ($LASTEXITCODE -ne 0) { Fail "pip install fallo" }

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Creado .env desde .env.example (completa las claves)." -ForegroundColor Yellow
}

if ($InstallHook) {
    & $Py -m src.harness.precommit --install --root $Root
}

Write-Host "`nDoctor:" -ForegroundColor Cyan
& $Py -m src.harness.doctor
if ($LASTEXITCODE -ne 0) { Fail "El doctor reporto fallos" }

Write-Host "`nListo. Proximos pasos:" -ForegroundColor Green
if (-not $NoVenv) { Write-Host "  .\.venv\Scripts\Activate.ps1" }
Write-Host "  python -m pytest tests/harness -q"
Write-Host "  (suite completa: pip install -r requirements.txt -r requirements-dev.txt; luego pytest tests -q)"
Write-Host "  compliance-check --files src/harness/doctor.py"
Write-Host "  harness-antecedentes register --root . --scan src"
Write-Host "  .\harness\install.ps1   # opcional: instalar reglas y skills en el IDE"
