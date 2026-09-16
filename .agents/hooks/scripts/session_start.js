/**
 * Hook: SessionStart
 * Se ejecuta al iniciar una nueva sesion del agente.
 * Carga el resumen de la sesion anterior (si existe) en el contexto.
 *
 * Busca el archivo de estado en: ~/.vibecoding/sessions/last_session.json
 */

const fs = require('fs');
const path = require('path');
const os = require('os');

const VIBECODING_HOME = process.env.VIBECODING_HOME || path.join(os.homedir(), '.vibecoding');
const SESSION_STATE_FILE = path.join(VIBECODING_HOME, 'sessions', 'last_session.json');

function loadLastSession() {
  try {
    if (fs.existsSync(SESSION_STATE_FILE)) {
      const data = fs.readFileSync(SESSION_STATE_FILE, 'utf-8');
      const session = JSON.parse(data);

      console.log('[VibeCoding] Sesion anterior: ' + session.project_name);
      console.log('[VibeCoding] Ultima actividad: ' + session.last_updated);
      console.log('[VibeCoding] Skills activas: ' + (session.active_skills || []).join(', '));
      console.log('[VibeCoding] Etapa del pipeline: ' + (session.current_stage || 'No definida'));

      if (session.summary) {
        console.log('\n--- Resumen de sesion anterior ---');
        console.log(session.summary);
        console.log('--- Fin del resumen ---\n');
      }

      if (session.pending_decisions && session.pending_decisions.length > 0) {
        console.log('Decisiones pendientes:');
        session.pending_decisions.forEach(function(d) { console.log('  - ' + d); });
      }

      return session;
    }
  } catch (err) {
    // Silencioso: si no hay sesion previa o el archivo esta corrupto, se ignora
  }
  return null;
}

// Ejecutar al cargar
const session = loadLastSession();
if (session) {
  process.env.VIBECODING_LAST_SESSION = JSON.stringify(session);
} else {
  console.log('[VibeCoding] No hay sesion previa. Empezando desde cero.');
}
