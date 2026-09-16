# VibeCoding Harness — Uninstall
# Elimina completamente el harness del proyecto

param(
    [switch]$Force = $false
)

# En modo standalone, el script esta en vibecoding-harness/uninstall.ps1
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  VibeCoding Harness — Desinstalador" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $Force) {
    $confirm = Read-Host "  ? Estas seguro de desinstalar el harness? (escribe DELETE para confirmar)"
    if ($confirm -ne "DELETE") {
        Write-Host "  Cancelado." -ForegroundColor Yellow
        exit 0
    }
}

$items = @(
    "AGENTS.md",
    "AGENTS.md.disabled",
    "opencode.json",
    "vibecoding.json"
)

$dirs = @(
    ".opencode\rules\vibecoding",
    ".opencode\skills\01-prd",
    ".opencode\skills\02-architecture",
    ".opencode\skills\03-data-modeling",
    ".opencode\skills\04-api-design",
    ".opencode\skills\05-backend",
    ".opencode\skills\06-frontend",
    ".opencode\skills\07-auth",
    ".opencode\skills\08-testing",
    ".opencode\skills\09-cicd",
    ".opencode\skills\10-deployment",
    ".opencode\skills\11-observability",
    ".opencode\skills\12-documentation",
    ".opencode\skills\web-app",
    ".opencode\agents\planner.md",
    ".opencode\agents\code_reviewer.md",
    ".opencode\agents\security_reviewer.md",
    ".opencode\hooks\hooks.json",
    ".opencode\hooks\scripts\session_start.js",
    ".opencode\hooks\scripts\session_end.js",
    ".opencode\hooks\scripts\pre_compact.js",
    ".opencode\hooks\scripts\evaluate_session.js",
    ".opencode\contexts\vibecoding",
    ".opencode\rules\vibecoding\stacks"
)

Write-Host "[*] Eliminando archivos..." -ForegroundColor Yellow
foreach ($item in $items) {
    $path = Join-Path $ProjectDir $item
    if (Test-Path $path) {
        Remove-Item -Force -LiteralPath $path -ErrorAction SilentlyContinue
        Write-Host "  - $item" -ForegroundColor Gray
    }
}

Write-Host "[*] Eliminando directorios del harness..." -ForegroundColor Yellow
foreach ($dir in $dirs) {
    $path = Join-Path $ProjectDir $dir
    if (Test-Path $path) {
        Remove-Item -Recurse -Force -LiteralPath $path -ErrorAction SilentlyContinue
        Write-Host "  - $dir" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "  Harness desinstalado." -ForegroundColor Green
Write-Host "  Los directorios .opencode/ y .agents/ originales no fueron modificados." -ForegroundColor Gray
Write-Host ""
