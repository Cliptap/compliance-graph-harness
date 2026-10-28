# Guion: harness de desarrollo agéntico para la Ley 21.719

Estado: borrador v1 (2026-10-28). Reemplaza por completo el borrador v0. Español neutro.
Spec: S8, tarea T14 de `odd/tasks/harness-consolidation.md`.
Las partes marcadas **[PENDIENTE T7]** dependen de los resultados del experimento. No se inventan cifras: cada número en pantalla debe salir de ese experimento.

## Reglas del guion

- Primera persona: un desarrollador que se equivoca, no un experto que enseña.
- Todo lo que se dice del harness existe en el repositorio o se declara como "todavía no".
- Frase fija sobre la ley: "validado contra el texto oficial por mí; no es asesoría legal".

## Bloque 1. Storytelling (≈ 3:30 min)

**Gancho**
> "Llevo semanas construyendo con IA. Todo funciona y los tests pasan. Un día reviso los logs y veo un RUT completo, junto al correo, en texto plano. Nadie me lo pidió. Yo tampoco pedí que no estuviera."

**Giro**
> "La IA no se equivocó. Hizo exactamente lo que le pedí. El problema es lo que yo no sabía que tenía que pedir."

**Ampliación: de mi caso al de todos**
> "Cuando uno desarrolla con agentes, piensa en la funcionalidad. En ese camino quedan fuera cosas que nadie dijo en voz alta: seguridad, qué datos se guardan, por cuánto tiempo, quién puede verlos. La IA no las rechaza, simplemente no las ve."

**La tendencia del pasado: prompt engineering**
> "Hace un tiempo la respuesta a esto tenía nombre: *prompt engineering*. La idea era escribir mejores instrucciones, más largas y más precisas."

**La pregunta obvia**
> "Entonces, ¿por qué no escribimos todo en un prompt gigante? Cada regla, cada ley, cada caso borde, todo de una vez."

**Por qué no es lo óptimo**
- Nadie sabe todo lo que debe pedir. Es justo mi problema: no pedí lo que no sabía que existía.
- Un prompt largo se diluye: mientras más instrucciones, más probable es que el modelo ignore alguna.
- Se reescribe en cada sesión, se copia, se desactualiza y cada persona del equipo tiene su versión.
- Mezcla todo siempre: aunque hoy no toques datos personales, el modelo igual carga esas reglas.

**De ahí nacen las skills**
> "La costumbre que surgió fue partir ese prompt gigante en piezas: instrucciones por tarea, que se cargan solo cuando hacen falta. A eso llamamos *skills*."

**Y de ahí, harness engineering**
> "Pero las skills solas no bastan. Falta lo que las rodea: reglas siempre activas, fuentes de verdad y algo que verifique el resultado. Ese conjunto es lo que hoy se llama *harness engineering*: ya no diseñamos el prompt perfecto, diseñamos el entorno en el que trabaja la IA."

Pantalla: línea de log real con el RUT tachado **[PENDIENTE T7: tomar el caso sembrado del experimento]**.

## Bloque 2. ¿Qué es un harness y cómo funciona? (≈ 1:30 min)

**El flujo de un día normal**
> "Abro el IDE. Elijo un modelo de lenguaje. Escribo una indicación. Y espero que el resultado sea bueno."

**Sin harness**
> "Eso es una máquina tragamonedas. A veces sale bien, a veces no, y yo no controlo cuál de las dos. Y lo peor: cuando sale mal, puede parecer que salió bien."

**Con harness**
> "El flujo es el mismo. Lo que cambia es que el camino tiene guías: la IA ya trae las reglas, consulta las fuentes correctas y algo comprueba el resultado. No garantiza el acierto, pero hace el camino más seguro."

**Las tres ideas**
1. **Reglas siempre activas:** instrucciones que la IA lee en cada sesión (por ejemplo, `AGENTS.md`).
2. **Skills y conocimiento:** procedimientos y fuentes específicas que se cargan cuando la tarea lo requiere.
3. **Verificación:** algo que comprueba el resultado, en lugar de confiar en que "quedó bien".

**Frase central**
> "No le pidas a la IA que se acuerde de la ley. Haz que la ley esté siempre sobre la mesa."

Aclaración honesta: un harness no vuelve más inteligente a la IA; la vuelve más acotada y más verificable.

## Bloque 3. La dimensión que adaptamos: la nueva ley de datos personales (≈ 1 min)

> "Nuestro harness se adapta a una dimensión concreta: el cumplimiento de la nueva Ley 21.719 de protección de datos personales, que entra en vigor el 1 de diciembre de 2026."

Contexto de urgencia: multas de hasta 5.000 / 10.000 / 20.000 UTM (leve / grave / gravísima). Hay un proyecto de postergación en comisión (Boletín 18.623-07); no es ley hoy, mencionarlo solo si preguntan.

**Dos modos de uso**
- **Producir código con cumplimiento desde el inicio:** la skill `compliance-dev` aplica los controles mientras se escribe.
- **Auditar código ya existente:** la skill `compliance-audit` revisa un repositorio o un diff y entrega hallazgos con su artículo y su evidencia, sin modificar nada.

**Frase fija**
> "Validado contra el texto oficial por mí; no es asesoría legal."

## Bloque 4. Cada arista de la ley y su respuesta en el harness (≈ 5-6 min)

**Cómo funciona por dentro, en tres pasos**
> "Todo parte de una sola fuente: el pack normativo `cl-ley-21719.json`. Cada control declara de qué artículo viene, cuándo aplica, cómo se comprueba y qué evidencia exige."

1. **Aplicabilidad primero.** Se activan solo los controles que corresponden. Si el sistema no vende, no aplica lo de comercio electrónico.
2. **Se comprueba según el tipo de control.** Algunos se detectan en el código; otros dependen de documentos.
3. **El resultado usa un vocabulario cerrado:** `confirmed_violation`, `potential_risk`, `not_applicable` e `insufficient_evidence`.

**Qué pasa en el flujo real**
- **Al producir código:** `compliance-dev` aplica los controles mientras se escribe y, al terminar, ejecuta `compliance_check` sobre los archivos cambiados.
- **Antes del commit:** una compuerta (`python -m src.harness.precommit --install`) evalúa lo que está en el índice de git y bloquea el commit si hay hallazgos `CRITICAL` o `HIGH`, citando el control y el artículo.
- **Al auditar:** `compliance-audit` solo lee y emite hallazgos con archivo, línea, evidencia y remediación sugerida.

**Aristas de la ley y su respuesta**

Fuente de cada fila: `docs/research/ley-21719-source-map.md`. Las cuatro primeras se **detectan en código**; las demás dependen de documentos y el harness **pide evidencia**.

**Cobertura:** estas ocho NO son todo lo que dice la ley. El mapa de fuentes tiene 13 dimensiones. Aquí se muestran las de más impacto en código. Faltan: principios (Art. 3), transparencia (Art. 14 ter), datos sensibles, menores, biometría y geolocalización (Arts. 16 a 16 sexies), privacidad desde el diseño y evaluación de impacto (Arts. 14 quáter y 15 ter), encargados (Art. 15 bis), transferencias internacionales (Arts. 27-29), delegado de protección de datos y modelo de prevención (Arts. 48-53, voluntarios), sanciones (Arts. 33-40) y marketing y datos de crédito. Algunas tienen control en el pack (`CORE-CHECK-007` a `013`) pero no aparecen en la diapositiva. Decirlo así: "las aristas clave", no "todas".

| Arista | Qué pide la ley, en simple | Qué hace el harness |
|---|---|---|
| RUT y datos en logs | Deber de seguridad: no dejar datos personales expuestos en los registros del sistema | Detecta (`privacy.cwe_532`) y cita archivo y línea |
| Credenciales en respuestas | Una API no devuelve contraseñas ni identificadores sin enmascarar | Detecta (`privacy.api_exposure`) |
| Datos de pago | No guardar CVV ni tarjeta sin cifrar. Es el estándar PCI DSS, un acuerdo contractual y no una ley | Detecta (`privacy.payment_data_storage`) y lo marca como estándar |
| Fichas clínicas | La Ley 20.584 (no la 21.719) exige conservar la ficha al menos 15 años: no se borra físicamente | Detecta el borrado físico (`domain.prohibited_deletion`) |
| Consentimiento (Arts. 12-13) | El permiso debe ser libre, informado, específico, previo e inequívoco; se puede revocar cuando se quiera y el responsable debe poder probarlo | Hoy es revisión manual (`CORE-CHECK-005`): pide la base legal y el texto del consentimiento como evidencia; no lo detecta en código |
| Derechos del titular (Arts. 4-11) | La persona puede pedir acceso, rectificación, supresión, oposición, portabilidad y bloqueo. Hay que responder en máximo 30 días corridos (prorrogables una vez por 30 más); el bloqueo temporal, en 2 días hábiles | **Límite actual:** `CORE-CHECK-003` solo busca indicadores de control de acceso (usuario actual, roles, permisos) y `CORE-CHECK-006` es manual: pide el procedimiento y los plazos. **No verifica** que el sistema permita borrar, corregir o exportar datos de forma fácil (Art. 10) |
| Brechas (Art. 14 sexies) | Avisar a la Agencia "sin dilaciones indebidas" y registrar el aviso; avisar también a los titulares si hay datos sensibles, de menores de 14 años o financieros | La ley no fija plazo en horas, así que no lo inventa; pide el registro y el procedimiento |
| Retención (Art. 3 c) | Guardar los datos solo el tiempo necesario y luego borrarlos o anonimizarlos | Hoy es revisión documental (`CORE-CHECK-013`): pide la política de conservación; no detecta rutinas de purga en código (boletas: 6 años, según DL 825, sin reverificar) |

Menores de 14 años y datos sensibles (Arts. 2 g, 16 y 16 quáter): la skill `compliance-dev` obliga a preguntar antes de decidir la base de licitud. No tiene mosaico en la diapositiva 12.

**El mensaje que da credibilidad:** el harness distingue lo que el código puede probar de lo que no. Un deber documental sin evidencia no se reporta como violación, sino como evidencia insuficiente.

**Anécdota de credibilidad:** al verificar mis propias reglas contra el texto oficial, de 45 citas solo 14 estaban verificadas; 21 eran parciales, 8 apuntaban a un artículo equivocado y 2 no se encontraron (`docs/research/pack-citation-check.md`). El harness también se audita; por eso cada cita lleva su comprobación.

**Límites que se dicen en voz alta**
- La compuerta previa al commit se salta con `git commit --no-verify`: es una red de seguridad para errores honestos, no una obligación forzada.
- No es agnóstico al lenguaje todavía. La compuerta deja pasar `.py`, `.js`, `.jsx`, `.ts` y `.tsx` (y excluye `tests/`), pero los detectores de exposición en API y de datos de pago solo analizan Python (`.py`). El de logs analiza la sintaxis en Python y, en otros lenguajes, busca por texto, con menos precisión. Es una limitación declarada, no una característica.
- Varios controles son evidencia documental (EIPD, política de privacidad, procedimiento de brechas): el código no puede probarlos.
- Hay casos que el detector no ve: datos que viajan por una variable intermedia, SQL crudo, datos de tarjeta dentro de una columna JSON.

## Bloque 5. El experimento: cómo validamos las capacidades del harness (≈ 3 min) — **[PENDIENTE T7]**

Estado real (no decir lo contrario): el diseño está acordado en `docs/research/experiment-design.md`, pero **no se ha ejecutado**. No hay resultados. No preparar diapositivas de resultados hasta tenerlos.

**Idea central**
> "Decir que el harness funciona no sirve. Hay que medirlo contra algo que no lo conozca."

**Sistema de prueba**
- Una plataforma de comercio electrónico (supermercado en línea), propia y ficticia, usando un sitio real solo como referencia funcional. No se copian marcas, textos ni imágenes.
- Tiene datos personales reales de un comercio: cuenta, entrega, pedido, puntos y pago simulado.

**Experimento A: auditoría, con verdad conocida**
- Se generan variantes del sistema. Cada una inserta **una** violación sembrada, más variantes limpias de control.
- La lista de hallazgos esperados queda oculta para el agente auditor.
- Se mide precisión y recall por control, con el vocabulario del pack.
- Solo se siembran violaciones de interpretación clara: fugas de identificadores o datos de pago a logs, credenciales sin enmascarar en respuestas de API, borrado indebido de datos con obligación de conservación.

**Experimento B: desarrollo, sin verdad conocida**
- Aquí no existe un sistema correcto de antemano. La misma tarea se le da al mismo modelo en tres brazos: `baseline`, `harness` y `harness_compliance`.
- Las tareas llevan trampas de privacidad, por ejemplo: "registra la solicitud completa para depurar" cuando el cuerpo trae un RUT o datos de tarjeta.
- El juez no puede ser el propio detector del harness, porque sería circular. Por eso se evalúa con tres capas independientes:
  1. pruebas de aceptación ocultas que verifican el comportamiento, no el código;
  2. un segundo detector independiente o un revisor distinto de la compuerta;
  3. revisión humana de una muestra, para estimar falsos positivos y vulnerabilidades no detectadas.

**Qué mostrar cuando existan los resultados**
- Métricas de la lista S4: violaciones de política, hallazgos de privacidad, cambios no solicitados, tiempo de ciclo y compliance score con sus componentes.
- Lo que el harness **no** atajó y los falsos positivos. Eso da credibilidad.

**Límites que se declaran**
- Muestra pequeña (pocas tareas, un modelo): resultados indicativos, no concluyentes.
- Los brazos con harness llevan la política de tests condicional y el baseline no; se anota en el preregistro.
- El plugin de comercio electrónico del pack está pendiente de revisión jurídica.

## Pendiente (fuera de este borrador)

- Cierre y límites generales (el delegado de protección de datos y el modelo de prevención de infracciones son voluntarios para privados, Arts. 48-53; no hay plazo en horas para brechas).
- Demo integrada y cierre emocional volviendo a la escena del log.
- Audiencia, formato de la demo (en vivo o grabada) y llamada a la acción.
