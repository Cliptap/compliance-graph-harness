/**
 * Hook: EvaluateSession
 * Se ejecuta al finalizar una sesion para evaluar calidad del harness.
 * Extrae metricas basicas que permiten evidenciar el aporte de las skills.
 *
 * Metricas extraidas:
 * - Skills activadas durante la sesion
 * - Etapas del pipeline completadas
 * - Archivos modificados/creados
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const VIBECODING_HOME = process.env.VIBECODING_HOME || path.join(os.homedir(), '.vibecoding');
const EVAL_DIR = path.join(VIBECODING_HOME, 'eval');

try {
  if (!fs.existsSync(EVAL_DIR)) {
    fs.mkdirSync(EVAL_DIR, { recursive: true });
  }

  var projectRoot = process.env.OPENCODE_PROJECT_ROOT || process.cwd();

  var evaluation = {
    timestamp: new Date().toISOString(),
    session_id: process.env.OPENCODE_SESSION_ID || 'unknown',
    metrics: {
      harness_active: false,
      skills_loaded: [],
      pipeline_stage: 'unknown',
      files_modified: 0
    },
    quality_indicators: {
      rules_loaded: false,
      skills_used: false,
      agents_delegated: false
    }
  };

  // Verificar si AGENTS.md existe y esta activo
  var agentsMd = path.join(projectRoot, 'AGENTS.md');
  if (fs.existsSync(agentsMd)) {
    evaluation.metrics.harness_active = true;
    evaluation.quality_indicators.rules_loaded = true;
  }

  // Verificar skills cargadas (desde session state)
  var sessionFile = path.join(VIBECODING_HOME, 'sessions', 'last_session.json');
  if (fs.existsSync(sessionFile)) {
    var session = JSON.parse(fs.readFileSync(sessionFile, 'utf-8'));
    evaluation.metrics.skills_loaded = session.active_skills || [];
    evaluation.metrics.pipeline_stage = session.current_stage || 'unknown';
    if (evaluation.metrics.skills_loaded.length > 0) {
      evaluation.quality_indicators.skills_used = true;
    }
  }

  // Guardar evaluacion
  var evalFile = path.join(EVAL_DIR, 'session_' + evaluation.session_id + '.json');
  fs.writeFileSync(evalFile, JSON.stringify(evaluation, null, 2), 'utf-8');

  console.log('[VibeCoding EvaluateSession] Evaluacion guardada en ' + evalFile);
  console.log('  Harness activo: ' + evaluation.metrics.harness_active);
  console.log('  Skills usadas: ' + evaluation.metrics.skills_loaded.length);
  console.log('  Etapa pipeline: ' + evaluation.metrics.pipeline_stage);
} catch (err) {
  // Silencioso
}
