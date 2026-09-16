#!/usr/bin/env bash
# VibeCoding Harness Installer - Unix/Linux/macOS
# Version: 1.0.0
# Uso: chmod +x install.sh && ./install.sh
#       o desde internet: curl -sSL https://... | bash

set -euo pipefail

# --- Colores -------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
GRAY='\033[0;90m'
WHITE='\033[1;37m'
NC='\033[0m'

# --- Banner --------------------------------------------------
echo ""
echo -e "${CYAN}  ==================================================${NC}"
echo -e "${CYAN}       VibeCoding Harness - Instalador v1.0${NC}"
echo -e "${CYAN}       Skills + Reglas + Agentes + Hooks${NC}"
echo -e "${CYAN}  ==================================================${NC}"
echo ""
echo -e "${GRAY}  Un harness para que la IA pregunte en vez de asumir.${NC}"
echo ""

# --- Directorio del script -----------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(pwd)"

# --- Helper: copiar directorios ------------------------------
copy_dir() {
    local src="$1"
    local dest="$2"
    if [ ! -d "$src" ]; then
        return
    fi
    mkdir -p "$dest"
    for f in "$src"/*; do
        if [ -f "$f" ]; then
            cp "$f" "$dest/"
            echo -e "    + ${GRAY}$(basename "$f")${NC}"
        fi
    done
}

# --- Paso 1: Detectar harness --------------------------------
echo -e "${YELLOW}[1/5] Detectando harness de IA...${NC}"

HARNESS=""
HARNESS_BASE=""
TARGET_RULES_DIR=""
TARGET_SKILLS_DIR=""

# Claude Code
if [ -d "$HOME/.claude" ]; then
    HARNESS="claude_code"
    HARNESS_BASE="$HOME/.claude"
    TARGET_RULES_DIR="$HOME/.claude/rules/vibecoding"
    TARGET_SKILLS_DIR="$HOME/.claude/skills/vibecoding"
    echo -e "  Detectado: ${GREEN}Claude Code${NC} ($HARNESS_BASE)"
fi

# OpenCode
if [ -z "$HARNESS" ]; then
    if [ -d "$PROJECT_DIR/.opencode" ]; then
        HARNESS="opencode"
        HARNESS_BASE="$PROJECT_DIR/.opencode"
        TARGET_RULES_DIR="$PROJECT_DIR/.opencode/rules/vibecoding"
        TARGET_SKILLS_DIR="$PROJECT_DIR/.opencode/skills/vibecoding"
        echo -e "  Detectado: ${GREEN}OpenCode${NC} ($HARNESS_BASE)"
    elif [ -d "$HOME/.opencode" ]; then
        HARNESS="opencode"
        HARNESS_BASE="$HOME/.opencode"
        TARGET_RULES_DIR="$HOME/.opencode/rules/vibecoding"
        TARGET_SKILLS_DIR="$HOME/.opencode/skills/vibecoding"
        echo -e "  Detectado: ${GREEN}OpenCode${NC} ($HARNESS_BASE)"
    fi
fi

# Cursor
if [ -z "$HARNESS" ]; then
    if [ -d "$PROJECT_DIR/.cursor" ]; then
        HARNESS="cursor"
        HARNESS_BASE="$PROJECT_DIR/.cursor"
        TARGET_RULES_DIR="$PROJECT_DIR/.cursor/rules/vibecoding"
        TARGET_SKILLS_DIR="$PROJECT_DIR/.cursor/skills/vibecoding"
        echo -e "  Detectado: ${GREEN}Cursor${NC} ($HARNESS_BASE)"
    fi
fi

# Si no se detecto ninguno
if [ -z "$HARNESS" ]; then
    echo -e "  ${YELLOW}No se detecto ningun harness automaticamente.${NC}"
    echo ""
    echo "  Harnesses soportados:"
    echo "  1. Claude Code  (~/.claude)"
    echo "  2. OpenCode      (.opencode/)"
    echo "  3. Cursor        (.cursor/)"
    echo ""
    read -p "  ? Cual usas? (1/2/3): " choice
    choice="${choice:-1}"

    case "$choice" in
        1)
            HARNESS="claude_code"
            HARNESS_BASE="$HOME/.claude"
            TARGET_RULES_DIR="$HOME/.claude/rules/vibecoding"
            TARGET_SKILLS_DIR="$HOME/.claude/skills/vibecoding"
            ;;
        2)
            HARNESS="opencode"
            HARNESS_BASE="$PROJECT_DIR/.opencode"
            TARGET_RULES_DIR="$PROJECT_DIR/.opencode/rules/vibecoding"
            TARGET_SKILLS_DIR="$PROJECT_DIR/.opencode/skills/vibecoding"
            ;;
        3)
            HARNESS="cursor"
            HARNESS_BASE="$PROJECT_DIR/.cursor"
            TARGET_RULES_DIR="$PROJECT_DIR/.cursor/rules/vibecoding"
            TARGET_SKILLS_DIR="$PROJECT_DIR/.cursor/skills/vibecoding"
            ;;
        *)
            HARNESS="custom"
            read -p "  ? Ruta de configuracion del harness: " custom_path
            HARNESS_BASE="$custom_path"
            TARGET_RULES_DIR="$custom_path/rules/vibecoding"
            TARGET_SKILLS_DIR="$custom_path/skills/vibecoding"
            ;;
    esac
fi

echo ""

# --- Paso 2: Tipo de proyecto --------------------------------
echo -e "${YELLOW}[2/5] Tipo de proyecto...${NC}"

echo ""
echo "  Que tipo de proyecto vas a construir?"
echo "  1. web-app       - Full-stack con frontend y backend"
echo "  2. api           - Backend puro, sin interfaz grafica"
echo "  3. data-pipeline - Procesamiento de datos, ETL, reporteria"
echo "  4. cli-tool      - Herramienta de linea de comandos"
echo "  5. mobile        - App movil (React Native / Flutter)"
echo ""
read -p "  ? Opcion (1-5): " pt_choice
pt_choice="${pt_choice:-1}"

case "$pt_choice" in
    1) PROJECT_TYPE="web_app" ;;
    2) PROJECT_TYPE="api" ;;
    3) PROJECT_TYPE="data_pipeline" ;;
    4) PROJECT_TYPE="cli_tool" ;;
    5) PROJECT_TYPE="mobile" ;;
    *) PROJECT_TYPE="web_app" ;;
esac

echo -e "  Seleccionado: ${GREEN}${PROJECT_TYPE}${NC}"
echo ""

# --- Paso 3: Nivel de gobernanza -----------------------------
echo -e "${YELLOW}[3/5] Nivel de gobernanza...${NC}"

echo ""
echo "  Que nivel de gobernanza necesita el proyecto?"
echo "  1. bajo  - sin auth, sin auditoria, validaciones minimas"
echo "  2. medio - auth basica, logs, validaciones"
echo "  3. alto  - RBAC, auditoria completa, trazabilidad, compliance"
echo ""
read -p "  ? Opcion (1-3): " gov_choice
gov_choice="${gov_choice:-1}"

case "$gov_choice" in
    1) GOVERNANCE="bajo" ;;
    2) GOVERNANCE="medio" ;;
    3) GOVERNANCE="alto" ;;
    *) GOVERNANCE="bajo" ;;
esac

echo -e "  Seleccionado: ${GREEN}${GOVERNANCE}${NC}"
echo ""

# --- Paso 4: Copiar archivos ---------------------------------
echo -e "${YELLOW}[4/5] Instalando archivos del harness...${NC}"

BASE_SKILLS=(
    "01_prd.md" "02_architecture.md" "03_data_modeling.md"
    "04_api_design.md" "05_backend_implementation.md" "06_frontend_implementation.md"
    "07_auth_security.md" "08_testing_strategy.md" "09_ci_cd.md"
    "10_deployment.md" "11_observability.md" "12_documentation.md"
)

declare -A PROJECT_TYPE_SKILLS
PROJECT_TYPE_SKILLS["web_app"]="project_types/web_app.md"
PROJECT_TYPE_SKILLS["api"]="project_types/api.md"
PROJECT_TYPE_SKILLS["data_pipeline"]="project_types/data_pipeline.md"

# -- Rules (always-on) --
if [ -n "$TARGET_RULES_DIR" ]; then
    copy_dir "$SCRIPT_DIR/rules/common" "$TARGET_RULES_DIR"
    if [ -d "$SCRIPT_DIR/rules/stacks" ]; then
        copy_dir "$SCRIPT_DIR/rules/stacks" "$TARGET_RULES_DIR/stacks"
    fi
fi

# -- Skills (base + project type) --
if [ -n "$TARGET_SKILLS_DIR" ]; then
    mkdir -p "$TARGET_SKILLS_DIR"
    for skill in "${BASE_SKILLS[@]}"; do
        src="$SCRIPT_DIR/skills/$skill"
        if [ -f "$src" ]; then
            cp "$src" "$TARGET_SKILLS_DIR/"
            echo -e "    + ${GRAY}skills/$skill${NC}"
        fi
    done

    # Skills por tipo de proyecto
    type_skill="${PROJECT_TYPE_SKILLS[$PROJECT_TYPE]:-}"
    if [ -n "$type_skill" ]; then
        mkdir -p "$TARGET_SKILLS_DIR/project_types"
        src="$SCRIPT_DIR/skills/$type_skill"
        if [ -f "$src" ]; then
            cp "$src" "$TARGET_SKILLS_DIR/project_types/"
            echo -e "    + ${GRAY}skills/$type_skill${NC}"
        fi
    fi
fi

# -- Agents (van bajo el base del harness, NO bajo rules/) --
if [ -n "$HARNESS_BASE" ] && [ -d "$SCRIPT_DIR/agents" ]; then
    agents_dir="$HARNESS_BASE/agents/vibecoding"
    mkdir -p "$agents_dir"
    copy_dir "$SCRIPT_DIR/agents" "$agents_dir"
fi

# -- Hooks (van bajo el base del harness, NO bajo rules/) --
if [ -n "$HARNESS_BASE" ]; then
    hooks_dir="$HARNESS_BASE/hooks"
    mkdir -p "$hooks_dir"
    if [ -f "$SCRIPT_DIR/hooks/hooks.json" ]; then
        cp "$SCRIPT_DIR/hooks/hooks.json" "$hooks_dir/"
        echo -e "    + ${GRAY}hooks.json${NC}"
    fi
    if [ -d "$SCRIPT_DIR/hooks/scripts" ]; then
        mkdir -p "$hooks_dir/scripts"
        copy_dir "$SCRIPT_DIR/hooks/scripts" "$hooks_dir/scripts"
    fi
fi

# -- Contexts (van bajo el base del harness, NO bajo rules/) --
if [ -n "$HARNESS_BASE" ] && [ -d "$SCRIPT_DIR/contexts" ]; then
    ctx_dir="$HARNESS_BASE/contexts/vibecoding"
    mkdir -p "$ctx_dir"
    copy_dir "$SCRIPT_DIR/contexts" "$ctx_dir"
fi

echo ""

# --- Paso 5: Crear vibecoding.json ---------------------------
echo -e "${YELLOW}[5/5] Creando vibecoding.json...${NC}"

NOW=$(date +%Y-%m-%d)

# Build base skills JSON array
BASE_SKILLS_JSON=""
for skill in "${BASE_SKILLS[@]}"; do
    name="${skill%.md}"
    if [ -z "$BASE_SKILLS_JSON" ]; then
        BASE_SKILLS_JSON="\"$name\""
    else
        BASE_SKILLS_JSON="$BASE_SKILLS_JSON, \"$name\""
    fi
done

# Build project type skills
PT_NAME=""
type_s="${PROJECT_TYPE_SKILLS[$PROJECT_TYPE]:-}"
if [ -n "$type_s" ]; then
    PT_NAME="$(basename "$type_s" .md)"
fi

cat > "$PROJECT_DIR/vibecoding.json" << EOF
{
  "version": "1.0.0",
  "project": {
    "type": "$PROJECT_TYPE",
    "governance": "$GOVERNANCE",
    "created_at": "$NOW"
  },
  "harness": {
    "type": "$HARNESS",
    "rules_dir": "$TARGET_RULES_DIR",
    "skills_dir": "$TARGET_SKILLS_DIR"
  },
  "skills": {
    "base": [$BASE_SKILLS_JSON],
    "project_type": ["$PT_NAME"]
  },
  "governance_overrides": {}
}
EOF

echo -e "  + ${GREEN}vibecoding.json creado${NC}"
echo ""

# --- Resumen final -------------------------------------------
echo -e "${CYAN}==================================================${NC}"
echo -e "  ${GREEN}INSTALACION COMPLETADA${NC}"
echo -e "${CYAN}==================================================${NC}"
echo ""
echo -e "  ${WHITE}Harness:     ${HARNESS}${NC}"
echo -e "  ${WHITE}Proyecto:    ${PROJECT_TYPE}${NC}"
echo -e "  ${WHITE}Gobernanza:  ${GOVERNANCE}${NC}"
echo -e "  ${GRAY}Reglas:      ${TARGET_RULES_DIR}${NC}"
echo -e "  ${GRAY}Skills:      ${TARGET_SKILLS_DIR}${NC}"
echo -e "  ${GRAY}Config:      ./vibecoding.json${NC}"
echo ""
echo -e "  ${YELLOW}Que sigue?${NC}"
echo -e "  1. Abre tu harness de IA (${HARNESS})"
echo -e "  2. Las reglas 'always-on' se cargaran automaticamente"
echo -e "  3. Di 'Quiero empezar un nuevo proyecto' para activar la skill PRD"
echo -e "  4. La IA te guiara con preguntas, sin asumir nada"
echo ""
echo -e "  ${CYAN}Happy vibe coding!${NC}"
echo ""
