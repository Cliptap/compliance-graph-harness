/**
 * Hook: SessionEnd
 * Se ejecuta al finalizar una sesion del agente.
 * Guarda un resumen del estado actual para continuidad en la siguiente sesion.
 *
 * Guarda en: ~/.vibecoding/sessions/last_session.json
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const VIBECODING_HOME = process.env.VIBECODING_HOME || path.join(os.homedir(), '.vibecoding');
const SESSIONS_DIR = path.join(VIBECODING_HOME, 'sessions');
const SESSION_STATE_FILE = path.join(SESSIONS_DIR, 'last_session.json');

function saveSession(summary, projectName, activeSkills, currentStage, pendingDecisions) {
  try {
    if (!fs.existsSync(SESSIONS_DIR)) {
      fs.mkdirSync(SESSIONS_DIR, { recursive: true });
    }

    var session = {
      project_name: projectName || 'sin-nombre',
      last_updated: new Date().toISOString(),
      active_skills: activeSkills || [],
      current_stage: currentStage || 'No definida',
      pending_decisions: pendingDecisions || [],
      summary: summary || 'Sin resumen'
    };

    fs.writeFileSync(SESSION_STATE_FILE, JSON.stringify(session, null, 2), 'utf-8');
    console.log('[VibeCoding] Sesion guardada en ' + SESSION_STATE_FILE);
  } catch (err) {
    console.error('[VibeCoding] Error al guardar sesion: ' + err.message);
  }
}

// Este script espera recibir parametros del agente al finalizar la sesion
// Los parametros se pasan como variables de entorno o argumentos
var summary = process.env.VIBECODING_SESSION_SUMMARY || process.argv[2] || '';
var projectName = process.env.VIBECODING_PROJECT_NAME || process.argv[3] || '';
var activeSkills = process.env.VIBECODING_ACTIVE_SKILLS ? process.env.VIBECODING_ACTIVE_SKILLS.split(',') : [];
var currentStage = process.env.VIBECODING_CURRENT_STAGE || process.argv[4] || '';

if (summary) {
  saveSession(summary, projectName, activeSkills, currentStage, []);
} else {
  console.log('[VibeCoding] No hay resumen para guardar. El agente debe llamar a session_end con el resumen.');
}
