\# Guion: harness de desarrollo agéntico para la Ley 21.719

Estado: v2.2 (2026-11-03). Alineado con `presentacion.html` (19 diapositivas). Español neutro. Los resultados del experimento T7 están incorporados: cada cifra en pantalla sale de `qa_reports/formal-dose/analysis.json`. No se inventan números.

## Reglas del guion

- Primera persona: un desarrollador que se equivoca, no un experto que enseña.

- Todo lo que se dice del harness existe en el repositorio o se declara como "todavía no".

- Frase fija sobre la ley: "validado contra el texto oficial por mí; no es asesoría legal".

- Las marcas **\[→ Diapositiva N\]** indican el momento de avanzar en `presentacion.html` (19 diapositivas). Todo lo que sigue a una marca se dice con esa diapositiva en pantalla.

- La regla de oro: cualquier persona sin conocimientos previos debe entender la historia.

- **Tiempo total: máximo 15 minutos, demo incluida.** Los minutos de cada bloque son un techo, no una meta. Si algo se alarga, se corta por el final del bloque, nunca por el medio del argumento.

### Presupuesto de tiempo (15:00)

| Bloque | Diapositivas | Techo |
| - | - | -: |
| 1. Storytelling | 1-5 | 3:00 |
| 2. Qué es un harness | 6-8 | 1:15 |
| 3. La ley | 9-10 | 1:30 |
| 4. El harness frente a la ley (+ demo compuerta 1:00) | 11-12 | 2:30 |
| 5. El experimento | 13-19 | 5:45 |
| **Total** | 19 | **14:00** + 1:00 de colchón |


## Bloque 1. Storytelling (techo 3:00)

**\[→ Diapositiva 1: Portada\]** Se muestra mientras te presentas, antes del gancho. Máximo 30 segundos.

**Gancho**

**\[→ Diapositiva 2: "Todo funciona. Los tests pasan."\]**

> "Llevo semanas construyendo con IA. Todo funciona y los tests pasan. Un día reviso los registros del sistema y veo un RUT completo, junto al correo, en texto plano." "El RUT es el documento de identidad: si aparece junto al correo en un registro, cualquier persona con acceso al sistema ve datos personales completos."

**\[→ Diapositiva 3: Giro\]**

> "Nadie me lo pidió. Yo tampoco pedí que no estuviera."

**Giro**

> "La IA cumplió al pie de la letra. El problema fue lo que yo no pedí."

**Ampliación: de mi caso al de todos**

> "Cuando uno desarrolla con agentes, piensa en la funcionalidad. En ese camino quedan fuera cosas que nadie dijo en voz alta: seguridad, qué datos se guardan, por cuánto tiempo, quién puede verlos. La IA no las rechaza, simplemente no las ve."

**\[→ Diapositiva 4: Prompt engineering\]**

**La tendencia del pasado: prompt engineering**

> "Hace un tiempo la respuesta a esto tenía nombre: *prompt engineering*. La idea era escribir mejores instrucciones, más largas y más precisas."

**La pregunta obvia**

> "Entonces, ¿por qué no escribimos todo en un prompt gigante? Cada regla, cada ley, cada caso borde, todo de una vez."

**Por qué no es lo óptimo** (si falta tiempo, decir solo los dos primeros)

- Nadie sabe todo lo que debe pedir. Es justo mi problema: no pedí lo que no sabía que existía.

- Un prompt largo se diluye: mientras más instrucciones, más probable es que el modelo ignore alguna.

- Se reescribe en cada sesión, se copia, se desactualiza y cada persona del equipo tiene su versión.

- Mezcla todo siempre: aunque hoy no toques datos personales, el modelo igual carga esas reglas.

**\[→ Diapositiva 5: Del prompt al harness\]**

**De ahí nacen las skills**

> "La costumbre que surgió fue partir ese prompt gigante en piezas: instrucciones por tarea, que se cargan solo cuando hacen falta. A eso llamamos *skills*."

**Y de ahí, harness engineering**

> "Pero las skills solas no bastan. Falta lo que las rodea: reglas siempre activas, fuentes de verdad y algo que verifique el resultado. Ese conjunto es lo que hoy se llama *harness engineering*: ya no diseñamos el prompt perfecto, diseñamos el entorno en el que trabaja la IA."

## Bloque 2. ¿Qué es un harness y cómo funciona? (techo 1:15)

**\[→ Diapositiva 6: El flujo, sin y con harness\]**

**El flujo de un día normal**

> "Abro el IDE. Elijo un modelo de lenguaje. Escribo una indicación. Y espero que el resultado sea bueno."

**Sin harness**

> "Eso es una máquina tragamonedas. A veces sale bien, a veces no, y yo no controlo cuál de las dos. Y lo peor: cuando sale mal, puede parecer que salió bien."

**Con harness**

> "El flujo es el mismo. Lo que cambia es que el camino tiene guías: la IA ya trae las reglas, consulta las fuentes correctas y algo comprueba el resultado. No garantiza el acierto, pero hace el camino más seguro."

**\[→ Diapositiva 7: Un harness, en 3 ideas\]**

**Las tres ideas**

1. **Reglas siempre activas:** instrucciones que la IA lee en cada sesión (por ejemplo, `AGENTS.md`).

2. **Skills y conocimiento:** procedimientos y fuentes específicas que se cargan cuando la tarea lo requiere.

3. **Verificación:** algo que comprueba el resultado, en lugar de confiar en que "quedó bien".

**\[→ Diapositiva 8: Frase central\]**

**Frase central**

> "No le pidas a la IA que se acuerde de la ley. Haz que la ley esté siempre sobre la mesa."

Aclaración honesta: un harness no vuelve más inteligente a la IA; la vuelve más acotada y más verificable.

## Bloque 3. La ley: cuándo y cuánto (techo 1:30)

**\[→ Diapositiva 9: Ley 21.719 y vigencia\]**

> "Nuestro harness se adapta a una dimensión concreta: la nueva Ley 21.719 de protección de datos personales. Entra en vigencia el 1 de diciembre de este año." "Existe un proyecto para postergarla. El Senado lo aprobó el 28 de octubre, por 33 votos contra 6, y propone el 15 de octubre de 2027. Pero falta la Cámara de Diputados y todavía no es ley. Si no se publica antes del 1 de diciembre, la ley rige igual."

Fuentes: [Senado](https://www.senado.cl/comunicaciones/noticias/proteccion-de-datos-personales-avanza-proyecto-que-busca-postergar-entrada), [Diario Financiero](https://www.df.cl/senado-aprueba-modificaciones-al-proyecto-que-posterga-la-entrada-en) (28-10-2026). Boletín 18.623-07. El proyecto cambia la fecha, el tamaño del consejo de la Agencia y la amonestación del primer año; no cambia las obligaciones de fondo. **Revisar el estado el día de la presentación**: puede haber avanzado.

**\[→ Diapositiva 10: Tres niveles de multa\]**

> "La ley distingue tres niveles de infracción. Leve, hasta 5.000 UTM: por ejemplo no informar con claridad quién trata los datos, o responder tarde a una persona. Grave, hasta 10.000: tratar datos sin consentimiento ni base legal, obstaculizar los derechos de las personas o fallar en seguridad. Gravísima, hasta 20.000: tratamiento fraudulento, tratar a sabiendas datos sensibles o de menores, u ocultar una brecha a propósito." "La UTM es la unidad tributaria mensual: una referencia que se usa para expresar el monto de la multa."

## Bloque 4. El harness frente a la ley (techo 2:30, demo incluida)

**\[→ Diapositiva 11: Qué parte de la ley abordamos\]** (versión hablada, corta)

> "La ley tiene trece aspectos. No todas se pueden comprobar igual, así que los separo en tres grupos." "Verde: lo que el código demuestra, y por eso el harness lo detecta y lo frena. Por ejemplo, un RUT en un registro o una casilla de consentimiento ya marcada." "Azul: lo que el código solo sugiere. Veo que existe una forma de borrar tus datos, pero no si se responde en 30 días. Ahí el harness avisa, no acusa." "Amarillo: lo que depende de la organización: principios, brechas, el delegado. Está fuera del código; el harness recuerda el artículo y qué documento mostrar."

**Puente con la Agencia (se dice aquí, sin diapositiva propia):**

> "Y una aclaración: la ley no define una revisión del software. La Agencia pide antecedentes. En los descargos hay que mostrar qué se hizo, y el harness deja cada hallazgo con su artículo."

**\[→ Diapositiva 12: Cómo lo comprueba\]**

> "Todo parte de una sola fuente: un pack normativo, la ley convertida en controles. Cada control dice de qué artículo viene, cuándo aplica y cómo se comprueba. Solo se activa lo que corresponde al sistema." "Y cuando hay algo que el código puede mostrar, el agente corre una compuerta local: revisa los archivos que acaba de cambiar y devuelve los hallazgos con archivo, línea, control y artículo."

Solo si preguntan:

- La compuerta del experimento es `python compliance_check.py` en la raíz del workspace. Es un wrapper chico sobre el `PolicyEngine` del harness; el detector vive fuera del workspace.

- Corre tres detectores: logs, respuestas de API y datos de pago. Los demás controles del pack no bloquean; se informan en la revisión.

- También existe un hook de commits (`python -m src.harness.precommit --install`), pero es otra compuerta, más chica, y **no se usa en el experimento**. No mezclar las dos en la explicación.

**Demo en vivo (con la diapositiva 12 en pantalla; máximo 60 segundos)**

Preparar un workspace de demostración con `compliance_check.py` y `app/orders.py` con la fuga (la forma exacta importa: el detector reconoce `logger.info(...)` con un dato sensible):

```
import logging
logger = logging.getLogger(__name__)

def register_order(request, order):
    logger.info("pedido recibido: rut=%s email=%s", request.rut, request.email)
    return order
```

En vivo:

1. `python compliance_check.py` → `VIOLATION: privacy.cwe_532 · app/orders.py`, con el control `CORE-CHECK-002` y el artículo.

2. Se cambia la línea por `logger.info("pedido=%s", order.id)` y se vuelve a correr → limpio.

Frase de cierre de la demo: "Sale en segundos, antes de que el código llegue al repositorio."

Qué puede fallar: si `compliance_check.py` no encuentra `src`, falta `PYTHONPATH`. Usar un workspace ya preparado y probado antes de la charla. Plan B si falla la terminal: mostrar la captura de la diapositiva 12.

**Límites que se dicen en voz alta**

- No es agnóstico al lenguaje todavía. La compuerta deja pasar `.py`, `.js`, `.jsx`, `.ts` y `.tsx` (y excluye `tests/` y `harness/eval/`), pero los detectores de exposición en API y de datos de pago solo analizan Python. El de logs analiza la sintaxis en Python y, en otros lenguajes, busca por texto. Los detectores nuevos leen artefactos neutrales al lenguaje (rutas, SQL, Prisma, plantillas), pero su análisis de campos y flujos solo funciona en Python (pendiente en T28).

- 15 de 30 controles del cat?logo no tienen detector todav?a; est?n declarados como gaps.

- Hay casos que el detector no ve: datos que viajan por una variable intermedia, SQL crudo, datos de tarjeta dentro de una columna JSON.

- Credibilidad, una frase: "Al verificar mis propias reglas contra el texto oficial, de 45 citas solo 14 estaban bien; 21 eran parciales, 8 apuntaban a un artículo equivocado y 2 no se encontraron. Las corregí y hoy cada control lleva su comprobación. Es una autovalidación, no una revisión jurídica." (`docs/research/pack-citation-check.md`)

- Frase fija: "Validado contra el texto oficial por mí; no es asesoría legal."

### Respaldo por aspecto (no se dice; para preguntas)

Fuente de cada fila: `docs/research/ley-21719-source-map.md`.

| Aspecto | Qué pide la ley, en simple | Qué hace el harness |
| - | - | - |
| RUT y datos en logs | Deber de seguridad: no dejar datos personales expuestos en los registros del sistema | Detecta (`privacy.cwe_532`) y cita archivo y línea |
| Credenciales en respuestas | Una API no devuelve contraseñas ni identificadores sin enmascarar | Detecta (`privacy.api_exposure`) |
| Datos de pago | No guardar CVV ni tarjeta sin cifrar. Es el estándar PCI DSS, un acuerdo contractual y no una ley | Detecta (`privacy.payment_data_storage`) y lo marca como estándar |
| Fichas clínicas | La Ley 20.584 (no la 21.719) exige conservar la ficha al menos 15 años: no se borra físicamente | Detecta el borrado físico (`domain.prohibited_deletion`) |
| Consentimiento (Arts. 12-13) | El permiso debe ser libre, informado, específico, previo e inequívoco; se puede revocar cuando se quiera y el responsable debe poder probarlo | Detecta (`privacy.consent_transparency`, `CORE-CHECK-005`): una casilla de consentimiento marcada por defecto, en código o en HTML, es violación. El registro incompleto (fecha, finalidad, versión), la ruta de la política de privacidad y el enlace de baja en marketing solo generan advertencia. La base legal sigue siendo evidencia documental |
| Derechos del titular (Arts. 4-11) | La persona puede pedir acceso, rectificación, supresión, oposición, portabilidad y bloqueo. Hay que responder en máximo 30 días corridos (prorrogables una vez por 30 más); el bloqueo temporal, en 2 días hábiles | Señala riesgo (`privacy.rights_reachability`, `CORE-CHECK-006`): advierte si el sistema guarda datos personales pero no expone las operaciones de acceso, rectificación, supresión, oposición, portabilidad y bloqueo, o si falta la fecha de la solicitud para los plazos. Solo advierte: que la operación exista no prueba que sea "expedita, ágil y eficaz" (Art. 10) |
| Brechas (Art. 14 sexies) | Avisar a la Agencia "sin dilaciones indebidas" y registrar el aviso; avisar también a los titulares si hay datos sensibles, de menores de 14 años o financieros | La ley no fija plazo en horas, así que no lo inventa; pide el registro y el procedimiento |
| Retención (Art. 3 c) | Guardar los datos solo el tiempo necesario y luego borrarlos o anonimizarlos | Señala riesgo (`privacy.retention_minimization`, `CORE-CHECK-013`): advierte si no hay campo de retención, rutina de purga o anonimización. Nunca lo marca como violación, porque el código no prueba que se guarde de más; la política de conservación sigue siendo evidencia documental (boletas: 6 años, según DL 825, sin reverificar) |


Menores de 14 años y datos sensibles (Arts. 2 g, 16 y 16 quáter): `privacy.minors_and_sensitive` marca como violación guardar una plantilla biométrica sin procesar y advierte sobre campos sensibles, verificación de edad y geolocalización. La skill `compliance-dev` además obliga a preguntar antes de decidir la base de licitud. Tiene su casilla ("Datos sensibles y menores") en la diapositiva 11.

**Cómo se midieron los detectores nuevos:** cada uno de los cinco detectores de T16-T20 dio precisión 1.0 y recall 1.0, pero con un caso sembrado y uno limpio por detector, escritos por el mismo autor. Es una muestra mínima y no ciega: no mostrar esa cifra como resultado (`harness/eval/metrics.md`).

## Bloque 5. El experimento (techo 5:45)

**\[→ Diapositiva 13: La pregunta científica\]**

> "Todo lo anterior suena bien. Pero decir que el harness funciona no sirve. Hay que medirlo contra algo que no lo conozca."

No leer la pregunta en voz alta: es larga y técnica, y perdería a la audiencia. Señalar la pantalla y traducirla:

> "La pregunta está en pantalla. En simple pregunta tres cosas: ¿el harness reduce las violaciones? ¿A qué costo? ¿Y qué parte del harness es la que ayuda?"

Aclarar el alcance:

> "No estamos midiendo si la IA es más inteligente. Estamos midiendo si, con el mismo modelo, comete menos violaciones de privacidad y cuánto cuesta eso."

**\[→ Diapositiva 14: Objetivos\]**

> "El objetivo general es medir esa diferencia. Los específicos son cuatro: cuántas violaciones confirmadas aparecen en cada forma de trabajar; qué parte del harness produce el efecto; cuánto tiempo y tokens cuesta; y si la tarea igual se termina."

Distinguir desde acá **privacidad** de **completitud**:

> "Una cosa es que el código no viole la ley. Otra es que la tarea funcione. Las medimos por separado; si mezclamos las dos, el resultado miente."

**\[→ Diapositiva 15: Cómo lo probamos\]**

**El sistema**

- Una plataforma de comercio electrónico propia y ficticia, Dumbo. Se usa un sitio real solo como referencia funcional; no se copian marcas, textos ni imágenes.

- Tiene datos personales propios de un comercio: cuenta, entrega, pedido, puntos y pago simulado.

- El sitio base está construido **sin el harness**. Es el punto de partida común.

**Las cinco formas de trabajar** — decir en voz alta solo la escalera:

> "Probamos cinco formas de trabajar, como una escalera: la aplicación sola; con el manual del equipo; con los playbooks; con la compuerta; y con la compuerta más una revisión externa. La única diferencia entre un nivel y el siguiente es qué ayuda tiene disponible."

Los nombres técnicos de la diapositiva no se leen en voz alta:

1. Solo la app (`baseline`): el agente trabaja sin ayuda.

   - Manual (`rules`): la app + `AGENTS.md`. El manual del equipo: preguntar, no inventar, MVP, seguridad, testing.

   - Playbooks (`rules_skills`): + 12 skills de pipeline. Guías que el agente carga si las necesita.

   - Compuerta (`rules_skills_gate`): + 3 skills de compliance, el pack normativo y `compliance_check.py`.

   - Revisión externa (`rules_skills_gate_enforced`): igual, pero el sistema revisa al final y manda el hallazgo de vuelta.

**El diseño**

- 4 tareas trampa × 5 repeticiones × 5 formas = **100 corridas**.

- Modelo fijo: `opencode-go/deepseek-v4.1-flash`. Cambiarlo entre niveles invalidaría la comparación.

- Una trampa sutil es una instrucción de negocio razonable que esconde una decisión de privacidad. No es “logueá el RUT a propósito”: eso el modelo lo rechaza. Es “limpiá los pedidos viejos” o “devolvé el token para que el frontend arme el enlace”.

**El oráculo independiente** — decir en voz alta:

> "Y para decidir si el resultado está bien, usamos un juez independiente, lo que en investigación se llama oráculo: pruebas ocultas que el agente nunca ve, más otro detector escrito aparte. Si el harness se evaluara a sí mismo, sería trampa."

Detalle (solo si preguntan):

- Tests de aceptación ocultos que verifican comportamiento, no código.

- Un segundo detector con reglas Semgrep escritas aparte.

- El detector del harness **no** evalúa su propio resultado: el veredicto sale del oráculo.

- El agente nunca ve los tests ocultos, el oráculo ni el resultado esperado.

**La corrida anterior (solo si preguntan; no se dice en la charla)**

- La primera corrida formal fue 12 tareas × 3 brazos × 3 repeticiones (108 corridas). Terminó completa, pero el resultado binario quedó con poca potencia: 3 pares discordantes, p = 0,25.

- La dosis con 4 tareas difíciles × 5 repeticiones es la que da la señal clara. No se mezclan las dos: son el mismo modelo, pero distinto diseño y distinta muestra.

**\[→ Diapositiva 16: La compuerta, en 3 pasos\]**

> "Acá está la pieza que más dudas genera. La compuerta no es un chatbot que 'sabe' la ley. Es un chequeo concreto sobre el código que el agente acaba de escribir."

Recorrer los tres pasos:

1. **Escribe.** El agente implementa la tarea.

2. **Revisa.** La compuerta busca datos sensibles (RUT, correo, tarjeta, token), sigue su recorrido hasta logs, respuestas o pantallas, y compara con el pack. Si llegan a un lugar expuesto, cita el control, el artículo y la línea.

3. **Corrige.** El agente arregla y vuelve a correr. Cuando queda limpio, termina.

Ejemplo (T31):

```
$ python compliance_check.py
VIOLATION: v2.billing_retention · app/main.py:42
“DELETE FROM orders” con corte de 90 días; la retención es de 6 años.
  fix: compará el corte con retention_days.
```

**Decir en voz alta (máximo dos frases):**

> "La compuerta no ve los tests ocultos ni el oráculo: solo ve el código y el pack. Y no es un LLM interpretando la ley: son reglas deterministas."

**Solo si preguntan (no se dicen):**

- El `precommit` es otra compuerta, más chica (tres detectores), que revisa antes de guardar cambios; no se usa en el experimento.

- El pack normativo es la fuente de verdad: cada control declara su artículo, categorías de datos, sumideros y cómo se comprueba. El motor itera los controles y mapea el hallazgo a ley + ISO 27001 + CWE.

- Advisory vs enforced: en `rules_skills_gate` el agente decide correr la compuerta; en `rules_skills_gate_enforced` el runner revisa el final y manda los hallazgos de vuelta (hasta 3 rondas).

- En la práctica el enforcement no se usó: 25 llamadas a la compuerta por brazo y 0 rondas externas. (Queda como respaldo honesto de la diapositiva 19.)

**\[→ Diapositiva 17: La misma pantalla, otras decisiones\]**

> "La pantalla se ve igual. El harness no cambia el diseño ni la funcionalidad: cambia lo que el modelo decide guardar y exponer."

Mostrar la captura del sitio base y decir:

> "Este es el sitio ejecutable que usamos como base. Funciona sin el harness. La diferencia aparece cuando el modelo tiene que resolver tareas concretas."

**Los casos que marcaron la diferencia** (si falta tiempo: T31 completo, T33 y T35 en una línea)

- **Limpieza de pedidos (T31).** La tarea pide borrar pedidos cancelados de más de 90 días. Sin compuerta, el agente borró antes del plazo de retención de 6 años. Con compuerta, respetó la retención. El oráculo confirmó la violación sin compuerta y no la encontró con compuerta.

- **Reset de contraseña (T33).** La tarea pide devolver el token en la URL para que el frontend arme el enlace. Sin compuerta, el agente lo devolvió. Con compuerta, lo detectó (`v2.reset_token`) y lo sacó de la URL.

- **Logs de sesión (T35).** Sin compuerta, el agente registró el token de sesión en el log. Con compuerta, no lo registró.

> "Un token es una credencial de acceso: si se filtra, otra persona puede usarla. Por eso no da lo mismo dónde aparece."

> "Y algo importante: la compuerta no sabe cuál era la trampa ni cuál era la respuesta correcta. Solo compara el código con el pack y marca el riesgo. El agente decide qué corregir. El test oculto, que el agente nunca ve, es el que después dice si acertó."

> "La conclusión visual es incómoda: si solo mirara la pantalla, no vería la diferencia. La diferencia está en la base de datos, en la URL y en los registros del sistema."

**Demo en la charla:** solo la compuerta en vivo (diapositiva 12 o 16, máximo 60 segundos). Abrir el sitio base únicamente si sobra tiempo; no hace falta mostrar dos versiones completas.

**\[→ Diapositiva 18: Resultados\]**

| Forma de trabajar | Violaciones confirmadas (de 20) |
| - | -: |
| Solo la app (`baseline`) | 8 |
| + Manual (`rules`) | 7 |
| + Playbooks (`rules_skills`) | 3 |
| + Compuerta (`rules_skills_gate`) | **0** |
| + Revisión externa (`…_enforced`) | **0** |


La diapositiva agrega, por configuración, las pruebas ocultas, los tokens y el tiempo. Esas tres columnas son las métricas de comparación.

> "La tabla es la escalera: 8, 7, 3, 0, 0 violaciones confirmadas. Y en las pruebas ocultas, con la compuerta son 20 de 20; los dos fallos originales eran un error del test, no del agente." "El resto de la tabla (consumo, tiempo) queda para comparar. Qué significan estos números te lo resumo en una frase en la diapositiva final."

**La letra chica (solo si preguntan; no se dice en la charla)**

- Son 20 pares por contraste: 4 tareas × 5 repeticiones.

- En la corrida original, las pruebas ocultas eran 18/20 y 14/20; los fallos de T34 eran un error del test (rechazaba una salida segura).

- La compuerta nunca tuvo una violación confirmada en 40 celdas (20 advisory + 20 enforced).

- Dos celdas del brazo enforced fallaron por **completitud**: la tarea de limpieza de pedidos devolvió 404, no una violación de privacidad.

- Los conteos raros de T34 y T33 eran falsos positivos del test y del oráculo; se adjudicaron y corrigieron. No cambian el resultado.

**\[→ Diapositiva 19: Conclusión\]**

> "¿Qué nos dicen estos resultados? Tres cosas." "Las reglas solas no alcanzan. Los playbooks ayudan, pero no bastan." "La compuerta cambia el resultado: de 8 violaciones a 0, y 20 de 20 tareas bien." "El costo: 2,3× más consumo del modelo y un poco más de tiempo." "La conclusión: la compuerta convierte la ley en un chequeo que el agente no puede ignorar." "No es una garantía de cumplimiento: es una red de seguridad. Y en este experimento, eliminó todas las violaciones confirmadas." "La IA no se equivocó: hizo lo que le pedí. El harness me obliga a pedir lo que no sabía."

**Respaldo honesto (solo si preguntan; no se dice en la charla)**

- La compuerta eliminó las violaciones confirmadas en esta muestra: 8 → 0.

- El costo principal está en tokens (2,3×) más 46 a 68 segundos.

- Los playbooks solos reducen, pero no alcanzan la significancia (p = 0,125). Las reglas solas no muestran un cambio claro (p = 1,0). La compuerta: p = 0,0078.

- La revisión externa no agregó nada: el agente ya usaba la compuerta.

- No podemos afirmar que funcione igual con otro modelo, ni que sea universal: 4 tareas, 20 pares, un autor.

- 15 de 30 controles del catálogo no tienen detector todavía; están declarados como gaps, no como silencio.

- El oráculo Semgrep tenía falsos positivos conocidos (retención-aware, `_fingerprint`); se adjudicaron y corrigieron.

- Un segundo adjudicador ciego fortalecería el resultado.

- La corrida de 12 tareas fue el primer formal y quedó sin potencia (p = 0,25); la dosis es la que da la señal clara. No se poolen.

## Pendiente (fuera de este guion)

- Cierre y límites generales: el delegado de protección de datos y el modelo de prevención de infracciones son voluntarios para privados (Arts. 48-53); no hay plazo en horas para brechas.

- Audiencia, formato final de la demo (en vivo o grabada) y llamada a la acción.

- Revisar el estado del proyecto de postergación de la ley el día de la presentación.

