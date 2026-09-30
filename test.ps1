param(
    [Parameter(Position=0)]
    [string]$Target = "help",
    [switch]$v = $false
)

$vFlag = if ($v) { "-v" } else { "" }

switch ($Target.ToLower().Trim()) {
    "harness" {
        Write-Host "`n[*] Ejecutando suite del HARNESS (Motor, AST, Lineage, Skills, DB)..." -ForegroundColor Cyan
        pytest -m harness $vFlag
    }
    "compliance" {
        Write-Host "`n[*] Ejecutando tests de COMPLIANCE (Ley 21.719 / Salud)..." -ForegroundColor Cyan
        pytest -m compliance $vFlag
    }
    "ast" {
        Write-Host "`n[*] Ejecutando tests de MOTOR AST (Code Graph & Slicing)..." -ForegroundColor Cyan
        pytest -m ast $vFlag
    }
    "lineage" {
        Write-Host "`n[*] Ejecutando tests de DATA LINEAGE (Taint Analysis)..." -ForegroundColor Cyan
        pytest -m lineage $vFlag
    }
    "governance" {
        Write-Host "`n[*] Ejecutando tests de GOBERNANZA (Validacion de 12 Skills)..." -ForegroundColor Cyan
        pytest -m governance $vFlag
    }
    "db" {
        Write-Host "`n[*] Ejecutando tests de PERSISTENCIA SQLITE..." -ForegroundColor Cyan
        pytest -m db $vFlag
    }
    "fast" {
        Write-Host "`n[*] Ejecutando tests RAPIDOS en memoria (< 1s)..." -ForegroundColor Cyan
        pytest -m fast $vFlag
    }
    "demo" {
        Write-Host "`n[*] Ejecutando suite de la DEMO CLINICA (Pacientes, Citas, RBAC)..." -ForegroundColor Green
        pytest -m demo $vFlag
    }
    "all" {
        Write-Host "`n[*] Ejecutando SUITE GLOBAL COMPLETA..." -ForegroundColor Yellow
        pytest $vFlag
    }
    default {
        Write-Host ''
        Write-Host '  =======================================================' -ForegroundColor Cyan
        Write-Host '       VibeCoding Harness - Runner Modular de Tests      ' -ForegroundColor Cyan
        Write-Host '  =======================================================' -ForegroundColor Cyan
        Write-Host ''
        Write-Host '  Uso: .\test.ps1 [rama] [-v]' -ForegroundColor White
        Write-Host ''
        Write-Host '  Ramas del Harness:' -ForegroundColor Yellow
        Write-Host '    harness     - Suite completa del motor del harness (17 tests)' -ForegroundColor Gray
        Write-Host '    ast         - Motor AST, extraccion de codigo y slicing' -ForegroundColor Gray
        Write-Host '    compliance  - Motor de auditoria y reglas Ley 21.719' -ForegroundColor Gray
        Write-Host '    lineage     - Taint analysis y trazabilidad de datos' -ForegroundColor Gray
        Write-Host '    governance  - Integridad y esquema de las 12 skills' -ForegroundColor Gray
        Write-Host '    db          - Persistencia relacional SQLite y logs' -ForegroundColor Gray
        Write-Host '    fast        - Pruebas ultra-rapidas en memoria (< 1s)' -ForegroundColor Gray
        Write-Host ''
        Write-Host '  Ramas de Aplicacion Cliente:' -ForegroundColor Yellow
        Write-Host '    demo        - Tests de la app clinica de demostracion (21 tests)' -ForegroundColor Gray
        Write-Host ''
        Write-Host '  Global:' -ForegroundColor Yellow
        Write-Host '    all         - Ejecutar todos los 38 tests del repositorio' -ForegroundColor Gray
        Write-Host ''
    }
}
