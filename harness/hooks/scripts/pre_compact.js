/**
 * Hook: PreCompact
 * Se ejecuta antes de que OpenCode compacte la ventana de contexto.
 * Sugiere que informacion preservar para mantener continuidad del desarrollo.
 *
 * Identifica:
 * - PRD y decisiones de arquitectura activas
 * - Estado actual del pipeline (que etapa, que skill)
 * - Decisiones pendientes del desarrollador
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const VIBECODING_HOME = process.env.VIBECODING_HOME || path.join(os.homedir(), '.vibecoding');
const SESSION_STATE_FILE = path.join(VIBECODING_HOME, 'sessions', 'last_session.json');

try {
  var contextToKeep = [];

  // 1. Buscar PRD mas reciente en docs/prd/
  var projectRoot = process.env.OPENCODE_PROJECT_ROOT || process.cwd();
  var prdDir = path.join(projectRoot, 'docs', 'prd');
  if (fs.existsSync(prdDir)) {
    var prds = fs.readdirSync(prdDir).filter(function(f) { return f.endsWith('.md'); });
    if (prds.length > 0) {
      contextToKeep.push('PRD activo: docs/prd/' + prds[prds.length - 1]);
    }
  }

  // 2. Estado de la sesion anterior
  if (fs.existsSync(SESSION_STATE_FILE)) {
    var session = JSON.parse(fs.readFileSync(SESSION_STATE_FILE, 'utf-8'));
    contextToKeep.push('Proyecto: ' + session.project_name);
    contextToKeep.push('Etapa pipeline: ' + (session.current_stage || 'No definida'));
    if (session.active_skills && session.active_skills.length > 0) {
      contextToKeep.push('Skills activas: ' + session.active_skills.join(', '));
    }
    if (session.pending_decisions && session.pending_decisions.length > 0) {
      contextToKeep.push('Decisiones pendientes: ' + session.pending_decisions.join(', '));
    }
  }

  // 3. Vibecoding.json
  var vcJson = path.join(projectRoot, 'vibecoding.json');
  if (fs.existsSync(vcJson)) {
    var config = JSON.parse(fs.readFileSync(vcJson, 'utf-8'));
    contextToKeep.push('Tipo proyecto: ' + config.project.type);
    contextToKeep.push('Gobernanza: ' + config.project.governance);
  }

  // 4. AGENTS.md
  var agentsMd = path.join(projectRoot, 'AGENTS.md');
  if (fs.existsSync(agentsMd)) {
    contextToKeep.push('Harness AGENTS.md activo');
  }

  // Output
  console.log('[VibeCoding PreCompact] Contexto a preservar:');
  contextToKeep.forEach(function(item) {
    console.log('  - ' + item);
  });

  // Guardar para que el agente lo use
  if (contextToKeep.length > 0) {
    var compactFile = path.join(VIBECODING_HOME, 'sessions', 'compact_context.json');
    var dir = path.dirname(compactFile);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    fs.writeFileSync(compactFile, JSON.stringify({
      timestamp: new Date().toISOString(),
      preserve: contextToKeep
    }, null, 2), 'utf-8');
  }
} catch (err) {
  // Silencioso: el hook no debe interrumpir la sesion
}
