# VibeCoding Harness

> **Instalador multi-IDE portable.** Copiá esta carpeta a cualquier proyecto, ejecutá un comando, y la IA empieza a **preguntar en vez de asumir**.

## Requisitos

- Windows (PowerShell 5.1+) o Unix (bash)
- Uno de: OpenCode, Claude Code, o Cursor instalado
- **Nada mas.** Cero dependencias. Puro markdown + scripts.

## Instalacion (10 segundos)

```powershell
# Desde la raiz de tu proyecto:
.\vibecoding-harness\install.ps1
```

El instalador te pregunta:
1. **Que IDE usas?** -> OpenCode / Claude Code / Cursor
2. **Que tipo de proyecto?** -> web-app / api / data-pipeline / cli-tool / mobile
3. **Nivel de gobernanza?** -> bajo / medio / alto

Y genera la estructura **nativa** de tu IDE automaticamente.

## Que incluye

| Componente | Cantidad | Para que sirve |
|-----------|----------|-----------------|
| Reglas always-on | 4 | La IA las carga en cada sesion. La fuerzan a preguntar antes de decidir. |
| Reglas por lenguaje | 3 | Python, TypeScript, Go |
| Skills | 12 + 3 por tipo | Guias paso a paso para cada etapa del desarrollo |
| Agentes | 3 | Planner, Code Reviewer, Security Reviewer |
| Hooks | 4 | Se ejecutan solos: guardan progreso, preservan contexto, miden calidad |

## Como usar

1. Copia la carpeta `vibecoding-harness/` a la raiz de tu proyecto
2. Ejecuta `.\vibecoding-harness\install.ps1`
3. Abri tu IDE
4. Las reglas se cargan solas
5. Decí _"Quiero empezar un proyecto nuevo"_
6. La skill de PRD se activa y te empieza a preguntar
7. **La IA no genera nada sin tu respuesta**

## Enable / Disable / Status

```powershell
.\vibecoding-harness\harness.ps1 status    # Esta activo el harness?
.\vibecoding-harness\harness.ps1 disable   # Desactivar temporalmente (sin desinstalar)
.\vibecoding-harness\harness.ps1 enable    # Reactivar
```

## Desinstalar

```powershell
.\vibecoding-harness\uninstall.ps1
# Requiere escribir DELETE para confirmar
```

## Estructura del harness (lo que llevas a otro proyecto)

```
vibecoding-harness/
├── install.ps1          # Instalador Windows
├── install.sh           # Instalador Unix/Mac
├── harness.ps1          # enable/disable/status
├── uninstall.ps1        # Desinstalador limpio
├── README.md            # Este archivo
├── rules/common/        # 4 reglas always-on
├── rules/stacks/        # Python, TypeScript, Go
├── skills/              # 12 skills base + project_types/
├── agents/              # 3 agentes delegados
├── hooks/               # 4 hooks de sesion
├── contexts/            # Contextos por modo (dev/review/debug)
├── eval/                # Metricas y casos de prueba
└── templates/           # Plantilla AGENTS.md
```

## Estructura nativa que genera en tu proyecto

| IDE | Reglas always-on | Skills | Agentes | Hooks |
|-----|-----------------|--------|---------|-------|
| **OpenCode** | `AGENTS.md` + `opencode.json` | `.opencode/skills/<name>/SKILL.md` | `.opencode/agents/` | `.opencode/hooks/` |
| **Claude Code** | `CLAUDE.md` + `~/.claude/CLAUDE.md` | `~/.claude/skills/vibecoding/<name>/SKILL.md` | `~/.claude/agents/vibecoding/` | `~/.claude/hooks/` |
| **Cursor** | `.cursor/rules/vibecoding.md` | `.cursor/skills/vibecoding/<name>/SKILL.md` | `.cursor/agents/vibecoding/` | `.cursor/hooks/` |

## Las 4 reglas (cargadas siempre)

1. **Ask-dont-assume** — Preguntar, nunca asumir tecnologias ni features
2. **MVP Scope** — Solo implementar lo que el PRD especifica (cero goldplating)
3. **No Hallucinations** — No inventar librerias, APIs, comandos ni versiones
4. **Best Practices** — KISS, YAGNI, codigo limpio, variables de entorno

## Skills disponibles

| # | Skill | Pipeline |
|---|-------|----------|
| 01 | PRD Generation | Definicion |
| 02 | Architecture Design | Arquitectura |
| 03 | Data Modeling | Datos |
| 04 | API Design | API |
| 05 | Backend Implementation | Backend |
| 06 | Frontend Implementation | Frontend |
| 07 | Auth & Security | Auth |
| 08 | Testing Strategy | Testing |
| 09 | CI/CD Pipeline | CI/CD |
| 10 | Deployment | Deploy |
| 11 | Observability | Monitoreo |
| 12 | Documentation | Docs |

## Hooks (que hacen)

| Hook | Cuando | Que hace |
|------|--------|----------|
| **SessionStart** | Al abrir una sesion | Recupera el resumen de la sesion anterior |
| **SessionEnd** | Al cerrar una sesion | Guarda un resumen de lo avanzado |
| **PreCompact** | Cuando la conversacion se alarga | Preserva la informacion critica antes de que la IA "olvide" |
| **EvaluateSession** | Al finalizar | Mide cuantas skills se usaron, en que etapa se avanzo |

## Licencia

MIT
