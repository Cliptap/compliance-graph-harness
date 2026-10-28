# Guion: harness de desarrollo agéntico para la Ley 21.719

Estado: borrador v0 (2026-10-28). Duración objetivo: 14 min. Spec: S8, tarea T14 de `odd/tasks/harness-consolidation.md`.
Las partes marcadas **[PENDIENTE T7]** dependen de los resultados del experimento. No se inventan cifras: cada número en pantalla debe salir de ese experimento.

## Reglas del guion

- Primera persona, desarrollador que se equivoca, no experto que enseña.
- Cada arista sigue el patrón: dolor (una frase) → pieza → antes/después.
- Todo lo que se dice del harness existe en el repo o se declara como "todavía no".
- Frase fija sobre la ley: "validado contra el texto oficial por mí; no es asesoría legal".

## 1. Gancho (0:00 - 0:45) — el error que cometí yo

Escena: llevo semanas construyendo con IA. Todo funciona. Los tests pasan.
Un día reviso los logs de la tienda y veo un RUT completo, junto al correo, en texto plano. Nadie me lo pidió. Yo tampoco pedí que no estuviera.

Frase de cierre del gancho: "La IA no se equivocó. Hizo exactamente lo que le pedí. El problema es lo que yo no sabía que tenía que pedir."

Pantalla: línea de log real con el RUT tachado (tomar el caso sembrado del experimento **[PENDIENTE T7]**).

## 2. El problema real (0:45 - 2:30) — la IA hace lo que pides, no lo que no sabes que debes pedir

Mensaje: no es culpa de la IA ni tuya, es un fallo de proceso.

Lista de lo que se omite mientras uno piensa en la funcionalidad (todas con artículo verificado en `docs/research/ley-21719-source-map.md`):

| Lo que omito | Qué dice la ley | Artículo |
|---|---|---|
| Base de licitud y consentimiento | libre, informado, específico, previo e inequívoco; revocable con medios equivalentes | Arts. 12-13 |
| Derechos del titular | acceso, rectificación, supresión, oposición, portabilidad, bloqueo; 30 días corridos | Arts. 4-11 |
| Información al titular | qué se trata y para qué | Art. 14 ter |
| Brechas | reportar a la Agencia "sin dilaciones indebidas" (no hay plazo en horas) | Art. 14 sexies |
| Menores | menos de 14 años: niño/niña; 14 a 17: adolescente | Art. 16 quáter |
| Retención | solo el tiempo necesario; boletas 6 años por ley tributaria | Art. 3 c), DL 825 Art. 58 |

Dato para sorprender: la situación socioeconómica es dato sensible (Art. 2 g). Un puntaje de crédito en un e-commerce ya entra ahí.

Contexto de urgencia: la ley entra en vigor el 1 de diciembre de 2026. Multas de hasta 5.000 / 10.000 / 20.000 UTM (leve / grave / gravísima).
Nota: hay un proyecto de postergación en comisión (Boletín 18.623-07). No es ley hoy; mencionarlo solo si preguntan.

## 3. ¿Qué es un harness? (2:30 - 4:00)

Analogía: la IA es el motor; el harness es la carretera, las barreras y el tablero. El motor no cambia, cambia lo que lo rodea.

Frase memorable (candidata): **"No le pidas a la IA que se acuerde de la ley. Hacé que la ley esté siempre en la mesa."** (ajustar el voseo según el público).

Ojo con la honestidad: un harness no hace a la IA más inteligente, la hace más acotada y verificable.

## 4. Las aristas (4:00 - 10:00) — una necesidad, una pieza

Cada bloque de 1 a 1:30 min. Solo aristas que existen hoy.

### 4.1 "Se me olvidó que existía la ley" → reglas permanentes
- Pieza: reglas siempre activas (`AGENTS.md`, `.agents/rules/`) y el pack normativo `.harness/packs/cl-ley-21719.json`.
- Qué mostrar: el pack como fuente única: ley → artículo → control → detección → remediación → evidencia.
- Antes/después: sesión sin reglas vs sesión donde la ley ya está cargada **[PENDIENTE T7: ejemplo real]**.

### 4.2 "Escribí el código y nadie lo revisó contra la ley" → auditoría contra el pack
- Pieza: skills `compliance-dev` y `compliance-audit`, motor de políticas y compuerta de validación (`PolicyEngine`, `ValidationEngine`).
- Resultado tipificado: `confirmed_violation | potential_risk | not_applicable | insufficient_evidence`. Decir que "no aplica" y "sin evidencia suficiente" son resultados legítimos, no fallas.
- Antes/después: hallazgo con artículo y evidencia **[PENDIENTE T7]**.

### 4.3 "Me dijo que cumplía y no sé por qué" → cada control cita su fuente
- Pieza: `source_check` por cita (estado, URL de BCN, fecha) y `validation_note` por control.
- Anécdota de credibilidad real: al verificar mis propias reglas contra el texto, de 45 citas solo 14 estaban bien; 8 apuntaban a un artículo equivocado y 2 a uno que ya no dice eso. El harness también se audita.
- Mensaje: la IA y yo podemos equivocarnos citando la ley; por eso cada cita se comprueba.

### 4.4 "Quién arregla esto sin romper lo demás" → parcheo supervisado
- Pieza: skill `compliance-patch`: cambio mínimo y verificación de que no se rompe comportamiento existente.
- Decir con claridad: el parcheo es asistido y exige prueba; no es magia.

### 4.5 "Perdí por qué decidí eso" → memoria y contexto
- Pieza: CodeGraph para recuperar contexto del código (MCP) y memoria entre sesiones.
- Cuidado: la memoria Engram se usa para **desarrollar** el harness; en el experimento los brazos no la tienen. No mezclar ambos mensajes.
- Cifras del benchmark de contexto (recall 0.63 / precisión 0.61 vs graphify 0.65 / 0.32): son indicativas, 6 tareas. Solo mostrarlas con esa etiqueta, o no mostrarlas.

### 4.6 Lo que todavía no existe (decirlo en voz alta)
- Bloqueo previo al commit: hoy los hooks solo guardan y cargan memoria de sesión. No impiden nada. Es el siguiente paso, no una característica.
- Detección real en muchos controles: varios son evidencia documental (EIPD, política de privacidad, procedimiento de brechas), porque el código no puede probarlos.

## 5. Demo integrada (10:00 - 12:00) — **[PENDIENTE T7]**

Estructura fija ya decidida (`docs/research/experiment-design.md`):
1. Misma tarea, mismo modelo, dos brazos: con harness y sin harness.
2. Mostrar los hallazgos del oráculo independiente del detector del harness, no del propio detector.
3. Mostrar métricas de la lista S4: violaciones de política, hallazgos de privacidad, cambios no solicitados, tiempo de ciclo, compliance score con sus componentes.
4. Mostrar también lo que **el harness no atajó** y los falsos positivos. Eso da credibilidad.

No preparar diapositivas de resultados hasta tenerlos.

## 6. Límites y honestidad (12:00 - 13:00)

Mensaje central, casi literal: "Validé cada control contra el texto oficial de la ley, y dejo anotado cómo. No soy abogado y esto no es asesoría legal; no reemplaza a un delegado de protección de datos."
Puntos concretos:
- El delegado de protección de datos y el modelo de prevención de infracciones son voluntarios para privados (Arts. 48-53). Un harness no los sustituye.
- No hay plazo en horas para notificar brechas; el harness no puede decidir si hay "riesgo razonable".
- Muestra pequeña (N de tareas, un modelo) → resultados indicativos, no concluyentes.
- Varias instrucciones de la Agencia aún no están publicadas.

## 7. Cierre (13:00 - 14:00)

Volver a la escena: el mismo log, ahora sin RUT, y el hallazgo con su artículo.
Frase: "Seguiré equivocándome. La diferencia es que ahora algo me lo dice antes de que lo vea un cliente."
CTA (decidir): repositorio, invitación a probar el pack sobre su propio código, o pedir corrección de los controles (las citas son públicas y verificables).

## Preguntas abiertas para el autor

1. Audiencia: ¿desarrolladores, estudiantes, o gente de cumplimiento? Cambia el ritmo de las secciones 2 y 6.
2. ¿Voseo o español neutro al hablar?
3. ¿La demo se muestra en vivo o con video grabado?
4. ¿Se menciona el nombre de Gentle-AI/Gentleman Programming como inspiración del formato?
