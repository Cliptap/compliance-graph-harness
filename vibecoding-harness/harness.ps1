# VibeCoding Harness — Enable/Disable

param(
    [ValidateSet("enable", "disable", "status")]
    [string]$Action = "status"
)

# En modo standalone, el script esta en vibecoding-harness/harness.ps1
# $ProjectDir es la raiz del proyecto (padre de vibecoding-harness/)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

$agentsFile = Join-Path $ProjectDir "AGENTS.md"
$agentsDisabled = Join-Path $ProjectDir "AGENTS.md.disabled"

switch ($Action) {
    "enable" {
        if (Test-Path $agentsDisabled) {
            Rename-Item $agentsDisabled "AGENTS.md"
            Write-Host "Harness ACTIVADO." -ForegroundColor Green
        } elseif (Test-Path $agentsFile) {
            Write-Host "El harness ya esta activo." -ForegroundColor Yellow
        } else {
            Write-Host "AGENTS.md no encontrado. Ejecuta el instalador primero." -ForegroundColor Red
        }
    }
    "disable" {
        if (Test-Path $agentsFile) {
            Rename-Item $agentsFile "AGENTS.md.disabled"
            Write-Host "Harness DESACTIVADO." -ForegroundColor Yellow
        } elseif (Test-Path $agentsDisabled) {
            Write-Host "El harness ya esta desactivado." -ForegroundColor Yellow
        } else {
            Write-Host "AGENTS.md no encontrado." -ForegroundColor Red
        }
    }
    "status" {
        if (Test-Path $agentsFile) {
            Write-Host "Harness: ACTIVO" -ForegroundColor Green
            Write-Host "  AGENTS.md presente. Las reglas always-on se cargan en cada sesion."
        } elseif (Test-Path $agentsDisabled) {
            Write-Host "Harness: DESACTIVADO" -ForegroundColor Yellow
            Write-Host "  AGENTS.md.disabled presente. Ejecuta '.\vibecoding-harness\harness.ps1 enable' para reactivar."
        } else {
            Write-Host "Harness: NO INSTALADO" -ForegroundColor Red
            Write-Host "  Ejecuta '.\vibecoding-harness\install.ps1' para instalar."
        }
    }
}
