# VibeCoding Harness Installer — Multi-IDE Native
# Version: 2.1.0
# Soporta: OpenCode, Claude Code, Cursor
# Uso: .\install.ps1

param(
    [string]$Ide = "",
    [string]$ProjectType = "",
    [string]$Governance = ""
)

$ErrorActionPreference = "Stop"

# --- Banner --------------------------------------------------
Write-Host ""
Write-Host "  ==================================================" -ForegroundColor Cyan
Write-Host "       VibeCoding Harness v2.1 — Multi-IDE" -ForegroundColor Cyan
Write-Host "  ==================================================" -ForegroundColor Cyan
Write-Host ""

# --- Directorios --------------------------------------------
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $ScriptDir) { $ScriptDir = Get-Location }
$ProjectDir = Split-Path -Parent $ScriptDir

# --- Helper: copiar directorios ------------------------------
function Copy-DirContents {
    param($Source, $Dest)
    if (-not (Test-Path $Source)) { return }
    if (-not (Test-Path $Dest)) {
        New-Item -ItemType Directory -Force -Path $Dest | Out-Null
    }
    Get-ChildItem -Path $Source -File | ForEach-Object {
        Copy-Item $_.FullName -Destination $Dest -Force
        Write-Host "    + $($_.Name)" -ForegroundColor Gray
    }
}

# --- Paso 1: Elegir IDE -------------------------------------
Write-Host "[1/5] Seleccionando IDE..." -ForegroundColor Yellow

if ($Ide -eq "") {
    Write-Host ""
    Write-Host "  Que IDE / harness de IA usas?" -ForegroundColor White
    Write-Host "  1. OpenCode      — reglas via AGENTS.md + opencode.json" -ForegroundColor Gray
    Write-Host "  2. Claude Code   — reglas via CLAUDE.md + ~/.claude/" -ForegroundColor Gray
    Write-Host "  3. Cursor        — reglas via .cursor/rules/" -ForegroundColor Gray
    Write-Host ""
    $choice = (Read-Host "  ? Opcion (1-3)").Trim()
} else {
    $choice = $Ide
}

# Configuracion nativa por IDE
$skillMap = @{
    "prd-generation" = "01_prd.md"
    "architecture-design" = "02_architecture.md"
    "data-modeling" = "03_data_modeling.md"
    "api-design" = "04_api_design.md"
    "backend-implementation" = "05_backend_implementation.md"
    "frontend-implementation" = "06_frontend_implementation.md"
    "auth-security" = "07_auth_security.md"
    "testing-strategy" = "08_testing_strategy.md"
    "ci-cd-pipeline" = "09_ci_cd.md"
    "deployment" = "10_deployment.md"
    "observability" = "11_observability.md"
    "documentation" = "12_documentation.md"
}

$ptSkills = @{ web_app = "web_app.md"; api = "api.md"; data_pipeline = "data_pipeline.md" }

switch ($choice.Trim()) {
    "1" {
        $IdeName = "OpenCode"
        $IdeId = "opencode"
        # OpenCode: skills en .opencode/skills/<nombre>/SKILL.md, agents en .opencode/agents/, reglas via AGENTS.md
        $ConfigBase = Join-Path $ProjectDir ".opencode"
        $SkillsDir = Join-Path $ConfigBase "skills"
        $AgentsDir = Join-Path $ConfigBase "agents"
        $RulesDir = Join-Path $ConfigBase "rules\vibecoding"
    }
    "2" {
        $IdeName = "Claude Code"
        $IdeId = "claude_code"
        $ConfigBase = "$env:USERPROFILE\.claude"
        $SkillsDir = Join-Path $ConfigBase "skills\vibecoding"
        $AgentsDir = Join-Path $ConfigBase "agents\vibecoding"
        $RulesDir = Join-Path $ConfigBase "rules\vibecoding"
    }
    "3" {
        $IdeName = "Cursor"
        $IdeId = "cursor"
        $ConfigBase = Join-Path $ProjectDir ".cursor"
        $SkillsDir = Join-Path $ConfigBase "skills\vibecoding"
        $AgentsDir = Join-Path $ConfigBase "agents\vibecoding"
        $RulesDir = Join-Path $ConfigBase "rules\vibecoding"
    }
    default {
        $IdeName = "OpenCode"
        $IdeId = "opencode"
        $ConfigBase = Join-Path $ProjectDir ".opencode"
        $SkillsDir = Join-Path $ConfigBase "skills"
        $AgentsDir = Join-Path $ConfigBase "agents"
        $RulesDir = Join-Path $ConfigBase "rules\vibecoding"
    }
}

Write-Host "  IDE seleccionado: $IdeName" -ForegroundColor Green
Write-Host ""

# --- Paso 2: Tipo de proyecto --------------------------------
Write-Host "[2/5] Tipo de proyecto..." -ForegroundColor Yellow
if ($ProjectType -eq "") {
    Write-Host "  1. web-app       — Full-stack frontend + backend"
    Write-Host "  2. api           — Backend puro"
    Write-Host "  3. data-pipeline — ETL / procesamiento de datos"
    Write-Host "  4. cli-tool      — Herramienta CLI"
    Write-Host "  5. mobile        — App movil"
    Write-Host ""
    $pt = (Read-Host "  ? Opcion (1-5)").Trim()
    switch ($pt) {
        "1" { $ProjectType = "web_app" }
        "2" { $ProjectType = "api" }
        "3" { $ProjectType = "data_pipeline" }
        "4" { $ProjectType = "cli_tool" }
        "5" { $ProjectType = "mobile" }
        default { $ProjectType = "web_app" }
    }
}
Write-Host "  $ProjectType" -ForegroundColor Green; Write-Host ""

# --- Paso 3: Gobernanza -------------------------------------
Write-Host "[3/5] Gobernanza..." -ForegroundColor Yellow
if ($Governance -eq "") {
    Write-Host "  1. bajo  — sin auth, validaciones minimas"
    Write-Host "  2. medio — auth basica, logs"
    Write-Host "  3. alto  — RBAC, auditoria, trazabilidad"
    Write-Host ""
    $gv = (Read-Host "  ? Opcion (1-3)").Trim()
    switch ($gv) {
        "1" { $Governance = "bajo" }
        "2" { $Governance = "medio" }
        "3" { $Governance = "alto" }
        default { $Governance = "bajo" }
    }
}
Write-Host "  $Governance" -ForegroundColor Green; Write-Host ""

# --- Paso 4: Instalar archivos (estructura nativa por IDE) ---
Write-Host "[4/5] Instalando harness nativo para $IdeName..." -ForegroundColor Yellow

# 4a. Archivo de reglas always-on (varia segun IDE)
$ruleNames = @("OpenCode", "Claude Code", "Cursor")
Write-Host "  [*] Reglas always-on" -ForegroundColor Gray

$rulesContent = @'
# VibeCoding Harness — Reglas Always-On

Eres un asistente de desarrollo que SIGUE instrucciones, no las inventa.
Trabajas bajo el harness VibeCoding con las siguientes reglas obligatorias.

## Regla 1: Preguntar, Nunca Asumir
1. NUNCA decidas tecnologias, arquitectura, librerias o patrones por tu cuenta.
2. Ante cualquier ambiguedad en el requerimiento, PREGUNTA. No asumas.
3. Si el desarrollador dice "no se", recomenda la opcion mas comun y pedi confirmacion.
4. NUNCA agregues features, endpoints, tablas o componentes no solicitados.
5. Cada decision debe ser trazable a una respuesta explicita del desarrollador.

## Regla 2: Alcance MVP — Sin Goldplating
1. Solo implementa lo que esta en el PRD o fue solicitado explicitamente.
2. No agregues "buenas practicas" no solicitadas.
3. Ante la duda entre simple y complejo, elegi SIMPLE.
4. No optimices prematuramente.

## Regla 3: Cero Alucinaciones
1. NUNCA inventes librerias, paquetes, APIs, endpoints, comandos o versiones.
2. Verifica compatibilidad de versiones antes de sugerir dependencias.
3. Si no estas 100% seguro de que algo existe, decilo.

## Regla 4: Principios Universales
KISS, YAGNI, DRY con cuidado. Codigo limpio, sin numeros magicos.
Nunca hardcodees secrets. Usa variables de entorno.

## Estructura del Harness
- Skills disponibles: .opencode/skills/vibecoding/
- Agentes delegados: .opencode/agents/
- Reglas detalladas: .opencode/rules/vibecoding/
- Hooks de sesion: .opencode/hooks/
'@

switch ($IdeId) {
    "opencode" {
        # OpenCode: AGENTS.md + opencode.json
        $rulesContent | Set-Content (Join-Path $ProjectDir "AGENTS.md") -Encoding UTF8
        Write-Host "    + AGENTS.md (carga automatica en cada sesion)" -ForegroundColor Green
        $ocConfig = [ordered]@{
            schema = "https://opencode.ai/config.json"
            instructions = @(
                ".opencode/rules/vibecoding/01_ask_dont_assume.md"
                ".opencode/rules/vibecoding/02_mvp_scope.md"
                ".opencode/rules/vibecoding/03_no_hallucinations.md"
                ".opencode/rules/vibecoding/04_best_practices.md"
            )
        }
        $ocConfig | ConvertTo-Json -Depth 3 | Set-Content (Join-Path $ProjectDir "opencode.json") -Encoding UTF8
        Write-Host "    + opencode.json (reglas detalladas)" -ForegroundColor Green
    }
    "claude_code" {
        # Claude Code: CLAUDE.md en raiz + CLAUDE.md en ~/.claude/
        $rulesContent | Set-Content (Join-Path $ProjectDir "CLAUDE.md") -Encoding UTF8
        Write-Host "    + CLAUDE.md (proyecto, carga automatica)" -ForegroundColor Green
        Copy-Item (Join-Path $ProjectDir "CLAUDE.md") (Join-Path "$env:USERPROFILE\.claude" "CLAUDE.md") -Force
        Write-Host "    + CLAUDE.md (global ~/.claude/, carga automatica)" -ForegroundColor Green
    }
    "cursor" {
        # Cursor: .cursor/rules/ se lee automaticamente
        $rulesContent | Set-Content (Join-Path $ConfigBase "rules\vibecoding.md") -Encoding UTF8
        Write-Host "    + .cursor/rules/vibecoding.md (carga automatica)" -ForegroundColor Green
    }
}

# 4b. Reglas detalladas
Write-Host "  [*] Reglas detalladas" -ForegroundColor Gray
if ($RulesDir) {
    $srcRules = Join-Path $ScriptDir "rules\common"
    Copy-DirContents -Source $srcRules -Dest $RulesDir
    $srcStacks = Join-Path $ScriptDir "rules\stacks"
    if (Test-Path $srcStacks) {
        Copy-DirContents -Source $srcStacks -Dest (Join-Path $RulesDir "stacks")
    }
}

# 4c. Skills
Write-Host "  [*] Skills" -ForegroundColor Gray
if ($SkillsDir) {
    foreach ($name in $skillMap.Keys) {
        $src = Join-Path $ScriptDir "skills\$($skillMap[$name])"
        if (Test-Path $src) {
            $skillDir = Join-Path $SkillsDir $name
            New-Item -ItemType Directory -Force -Path $skillDir | Out-Null
            Copy-Item $src (Join-Path $skillDir "SKILL.md") -Force
            Write-Host "    + skills/$name/SKILL.md" -ForegroundColor Gray
        }
    }
    # Skill de tipo de proyecto
    if ($ptSkills.ContainsKey($ProjectType)) {
        $ptSrc = Join-Path $ScriptDir "skills\project_types\$($ptSkills[$ProjectType])"
        if (Test-Path $ptSrc) {
            $ptSkillDir = Join-Path $SkillsDir $ProjectType
            New-Item -ItemType Directory -Force -Path $ptSkillDir | Out-Null
            Copy-Item $ptSrc (Join-Path $ptSkillDir "SKILL.md") -Force
            Write-Host "    + skills/$ProjectType/SKILL.md" -ForegroundColor Gray
        }
    }
}

# 4d. Agentes
Write-Host "  [*] Agentes delegados" -ForegroundColor Gray
if ($AgentsDir) {
    $srcAgents = Join-Path $ScriptDir "agents"
    if (Test-Path $srcAgents) {
        Copy-DirContents -Source $srcAgents -Dest $AgentsDir
    }
}

# 4e. Hooks
Write-Host "  [*] Hooks de sesion" -ForegroundColor Gray
if ($ConfigBase) {
    $hooksDir = Join-Path $ConfigBase "hooks"
    New-Item -ItemType Directory -Force -Path $hooksDir | Out-Null
    Copy-Item (Join-Path $ScriptDir "hooks\hooks.json") -Destination $hooksDir -Force -ErrorAction SilentlyContinue
    Copy-DirContents -Source (Join-Path $ScriptDir "hooks\scripts") -Dest (Join-Path $hooksDir "scripts")
    Write-Host "    + hooks/ (4 hooks activos)" -ForegroundColor Gray
}

Write-Host ""

# --- Paso 5: vibecoding.json ---------------------------------
Write-Host "[5/5] Creando vibecoding.json..." -ForegroundColor Yellow
$now = Get-Date -Format "yyyy-MM-dd"
$config = @{
    version = "2.1.0"
    ide = $IdeId
    project = @{ type = $ProjectType; governance = $Governance; created_at = $now }
    skills = @{ count = $skillMap.Count; names = [string[]]($skillMap.Keys) }
}
$config | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $ProjectDir "vibecoding.json") -Encoding UTF8
Write-Host "  + vibecoding.json" -ForegroundColor Green
Write-Host ""

# --- Resumen -------------------------------------------------
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "  INSTALACION COMPLETADA — $IdeName" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  IDE:         $IdeName" -ForegroundColor White
Write-Host "  Proyecto:    $ProjectType   Gobernanza: $Governance" -ForegroundColor White
Write-Host ""
Write-Host "  Comandos utiles:" -ForegroundColor Yellow
Write-Host "  .\harness.ps1 status    — ver si el harness esta activo" -ForegroundColor Gray
Write-Host "  .\harness.ps1 disable   — desactivar temporalmente" -ForegroundColor Gray
Write-Host "  .\harness.ps1 enable    — reactivar" -ForegroundColor Gray
Write-Host "  .\harness\uninstall.ps1 — desinstalar" -ForegroundColor Gray
Write-Host ""
Write-Host "  Abri $IdeName. Las reglas se cargan solas." -ForegroundColor Cyan
Write-Host ""
