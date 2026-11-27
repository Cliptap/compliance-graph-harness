# INFORME DE AVANCE — HITO 2: CALIBRACIÓN CIEGA, COBERTURA NORMATIVA Y COSTO EN EL CICLO

> **Estado:** segundo incremento funcional del arnés especializado en la Ley N° 21.719. Integra la calibración ciega del detector, la ampliación de la cobertura normativa y la medición del costo que la gobernanza impone al ciclo de desarrollo. Las capacidades indicadas como propuestas, planificadas o futuras no forman parte de la implementación validada.  
**Fecha de corte de esta actualización:** 24 de noviembre de 2026.

### PORTADA

**Proyecto:** Arnés de Supervisión de Software Asistido por IA mediante Grafos de Dependencias y Linaje de Datos bajo la Ley N° 21.719  
**Subtítulo / Caso de Estudio:** Validación experimental de un arnés especializado en la Ley N° 21.719 sobre un banco de comercio electrónico  
**Institución:** Universidad Andrés Bello, Facultad de Ingeniería, Sede Viña del Mar — ITISB  
**Curso:** Portafolio de Proyectos / Proyecto de Título  
**Integrantes:**

- Andrés Tapia

- Bastian Oyanedel

**Profesor Guía:** David Araya  
**Fecha de Entrega del Hito 2:** 24 de noviembre de 2026  
**Fecha de actualización del informe:** 24 de noviembre de 2026


### RESUMEN EJECUTIVO

El proyecto construye un arnés para la Ley N° 21.719, que entra en vigencia el 1 de diciembre de 2026. Los agentes cumplen lo que se les pide, pero no lo que nadie les pidió: una aplicación puede pasar sus pruebas mientras registra el RUT de sus usuarios en una bitácora. El arnés traduce deberes de la ley —no exponer identificadores ni credenciales, no borrar antes del plazo legal— en condiciones verificables sobre el código. Una compuerta las evalúa en cada cambio y bloquea los hallazgos graves; un segundo control exige la evidencia documental que ningún analizador decide, como la evaluación de impacto. De las treinta aristas, quince se detectan, cinco se reportan como riesgo, seis se exigen como evidencia y cuatro las firma una persona.

Para medir si sirve, cuatro tareas de un banco de comercio electrónico se ejecutaron con un agente en tres configuraciones: sin ayuda, con la compuerta sola y con el arnés completo. En la primera medición, la compuerta eliminó las violaciones confirmadas: ocho sin ayuda frente a cero con la compuerta, sobre veinte pares (McNemar, *p* = 0,0078), a 2,3 veces los tokens. La repetición, en un entorno donde el agente no ve las pruebas ni las reglas del banco, confirmó la dirección: seis violaciones sin ayuda, ninguna con la compuerta sola y una con el arnés completo (*p* = 0,031), a 1,7 veces el tiempo y 2,8 veces los tokens. El arnés completo no superó a la compuerta sola.

El detector, medido con 21 rondas de casos escritos sin acceso al repositorio, sostiene 0,955 de precisión y 1,000 de exhaustividad. El efecto se repite con un segundo modelo, con resultados acotados a dos modelos, un banco y muestras pequeñas. El arnés no certifica cumplimiento jurídico: es una red de seguridad.


# 1. INTRODUCCIÓN

La ingeniería de software experimenta una transformación asociada al uso de modelos de lenguaje y agentes capaces de participar activamente en tareas de programación: el desarrollador puede delegar actividades que antes requerían inspección manual, generación de código y modificaciones iterativas del repositorio. Esa autonomía introduce un riesgo concreto: el agente cumple las instrucciones que recibe, pero no garantiza por sí mismo el cumplimiento de obligaciones que nadie le mencionó, como la protección de los datos personales. Frente a esto, el proyecto no busca construir un *harness* de gobernanza general, sino un **arnés especializado en la Ley N° 21.719**, que traduce deberes seleccionados de la norma en controles técnicos ejecutables sobre el código.

El arnés nace de la experiencia del semestre anterior, cuando se desarrolló una aplicación de gestión clínica mediante *prompts* y *skills*: doce procedimientos de desarrollo y reglas permanentes. Sobre esa base se incorporaron análisis estructural del repositorio y linaje de datos, y en esta etapa se agregó la dimensión normativa: un catálogo de controles derivados de la Ley N° 21.719, un motor de políticas y una compuerta de validación que revisa los cambios del agente y cita el artículo que corresponde a cada hallazgo. La ley establece, entre otros deberes, la protección desde el diseño y por defecto (artículo 14 quáter) y la adopción de medidas de seguridad (artículo 14 quinquies); su entrada en vigencia está prevista para el 1 de diciembre de 2026, y el arnés no emite una certificación jurídica de cumplimiento.

En paralelo, el ecosistema de agentes de desarrollo avanzó hacia formatos como *Agent Skills*, que empaquetan procedimientos para cargarse según la tarea, y hacia conceptos de *harness engineering*, que diseñan contexto, herramientas y verificación alrededor del agente. El proyecto toma esas tendencias como referencia, pero delimita su alcance: no construye un *harness* general, sino uno que convierte requisitos seleccionados de la Ley N° 21.719 en chequeos deterministas.

En la fase actual, el arnés se validó experimentalmente sobre un banco de comercio electrónico: 100 ejecuciones que comparan cinco configuraciones —desde el agente solo hasta el arnés con compuerta y revisión externa— sobre cuatro tareas con trampas de privacidad. La configuración con compuerta eliminó las violaciones confirmadas (ocho a cero frente a la línea base; McNemar, *p* = 0,0078) y completó las cuatro tareas, a un costo medible de tokens y tiempo. El resultado es evidencia inicial, acotada a un modelo y un banco, y no equivale a una certificación de cumplimiento jurídico.

**Estructura del informe:** el documento presenta el problema y la pregunta de investigación (sección 2), los objetivos (3), la justificación y el alcance (4), el estado del arte (5), la metodología y el diseño experimental ejecutado (6), la planificación (7), el diseño de la solución (8), los incrementos desarrollados (9), la evaluación y los resultados (10), la discusión y las conclusiones (11) y las referencias (12).

**Convenciones de vocabulario.** Se usa «arnés» como traducción de *harness* y se reserva el término inglés, en cursiva, cuando se nombra el concepto de la literatura. «Compuerta» designa el punto de control que decide si un cambio se bloquea. «Control» es una condición verificable derivada de la ley. «Arista» es un deber identificado en la norma, que puede dar lugar a uno o varios controles. «Brazo» es cada configuración experimental que se compara. Los términos que se usan una sola vez se explican donde aparecen.


# 2. PROBLEMA U OPORTUNIDAD

## 2.1 Situación actual

El uso de modelos de lenguaje para programación permite generar código, modificar archivos, ejecutar pruebas y consultar información del repositorio con una velocidad superior a la interacción manual tradicional. Sin embargo, la utilidad del resultado depende de que el agente reciba contexto suficiente y pertinente, conozca las restricciones del proyecto y disponga de mecanismos que permitan verificar sus cambios.

En el proyecto desarrollado durante el semestre anterior se observaron problemas que motivaron la creación progresiva de instrucciones y skills. Entre ellos se encuentran la incorporación de código no solicitado, la generación de dependencias innecesarias, la modificación de archivos fuera del objetivo original y el aumento de esfuerzo requerido para revisar los cambios generados.

Los problemas que siguen provienen de esa misma experiencia. Solo uno de ellos es el problema central de este proyecto; los demás explican por qué el arnés existe y delimitan lo que se intentó resolver.

Un segundo problema corresponde a la gestión del contexto. En el prototipo actual existe un mecanismo de recorrido BFS (búsqueda en amplitud) sobre un grafo estructural del repositorio, pero el resultado todavía termina concatenando archivos completos. Por lo tanto, el mecanismo actual constituye una primera aproximación a la selección estructural de contexto, pero no una extracción fina a nivel de funciones o símbolos.

Existe además un problema de gobernanza. Las reglas permanentes sirven como instrucciones para el agente, pero no constituyen por sí mismas un mecanismo determinista de enforcement. Esto significa que una regla siempre presente como «mantener el alcance del MVP» puede ser ignorada por el modelo si posteriormente no existe un verificador que compruebe el cambio producido.

Finalmente, y como problema central de este proyecto, está la dimensión normativa: el agente cumple lo que se le pide, pero nadie le pidió respetar la protección de los datos personales y nada verifica que lo haga. Una aplicación puede pasar todas sus pruebas mientras registra RUT, correos o tokens de sesión en bitácoras y respuestas de API, conductas que la Ley N° 21.719 restringe. El problema no es que la IA se equivoque: es que cumple al pie de la letra un pedido incompleto.

## 2.2 Brecha

La oportunidad identificada consiste en estudiar cómo una capa de software alrededor del agente puede combinar:

- Controles técnicos de protección de datos derivados de la Ley N° 21.719;

- Workflows de desarrollo especializados;

- Selección estructural de contexto;

- Políticas explícitas;

- Validación determinista;

- Trazabilidad de las decisiones y resultados.

La brecha que aborda el proyecto no es simplemente la generación de código mediante IA. El foco está en la falta de una forma sistemática de gobernar y evaluar el comportamiento de un agente durante el desarrollo, manteniendo al desarrollador como responsable de la intención y aprobación final.

## 2.3 Pregunta del proyecto y variables de estudio

A partir de la brecha identificada, se formula la siguiente pregunta central de investigación:

> **¿En qué medida un *harness* especializado en la Ley N° 21.719 —con *skills*, reglas y una compuerta de revisión basada en controles de la norma— mejora la incorporación comprobable de requisitos seleccionados de protección de datos personales en una aplicación con repositorio de datos, frente a desarrollarla sin *harness* o con un *harness* básico?**

Para evaluar esta interrogante se consideran las siguientes variables, donde el resultado central es la prevención de violaciones técnicas de privacidad (variable 5) y las demás miden costo y preservación funcional:

1. **Efectividad de gobernanza:** frecuencia de iniciativas no consultadas (*goldplating*), modificaciones fuera de alcance y sugerencias de dependencias inexistentes.

2. **Eficiencia contextual:** volumen de tokens utilizados y tiempo de ciclo por tarea. La contribución específica de la selección mediante grafos deberá evaluarse separadamente, ya que los experimentos formal y de dosis descritos en este informe no aíslan ese factor.

3. **Preservación funcional:** proporción de pruebas automatizadas aprobadas después de la aplicación de cambios o parches.

4. **Trazabilidad de decisiones:** proporción de decisiones técnicas documentadas mediante respuestas del desarrollador y evidencia del pipeline de *skills*.

5. **Capacidad de auditoría normativa:** detección y remediación de violaciones técnicas de privacidad confirmadas mediante pruebas y reglas independientes, sin alterar el comportamiento funcional esperado.


# 3. OBJETIVOS

## 3.1 Objetivo general

Diseñar, implementar y evaluar un arnés de gobernanza **especializado en la Ley N° 21.719** para el desarrollo de software asistido por IA, orientado a traducir deberes seleccionados de la norma en controles técnicos verificables —junto al control del contexto, las restricciones del proyecto y la validación de cambios producidos por agentes de programación—, y medir su impacto frente a una asistencia generativa no gobernada.

## 3.2 Objetivos específicos

- **OE1 — Catálogo de workflows y gobernanza de decisiones:** formalizar un catálogo de workflows de desarrollo asistido por IA basado en las doce *skills* procedimentales (`01-prd` a `12-documentation`) y en las tres *skills* de cumplimiento, incorporando criterios explícitos de activación, ejecución y verificación orientados a la Ley N° 21.719.

- **OE2 — Gestión estructural de contexto:** construir y evaluar un mecanismo de gestión de contexto basado en el análisis de dependencias del repositorio, utilizando grafos estructurales y recorridos de vecindad acotada para seleccionar información pertinente, reducir la incorporación de contexto innecesario y apoyar el análisis de flujos de datos sensibles regulados por la Ley N° 21.719. La evolución hacia selección a nivel de símbolos se mantendrá como objetivo de refinamiento mientras la implementación entregue archivos completos.

- **OE3 — Arquitectura desacoplada y roles especializados:** consolidar la arquitectura modular del arnés, parametrizando los directorios de análisis para operar sobre repositorios Python compatibles. Definir roles especializados —*planner*, *code reviewer*, *security reviewer* y *compliance auditor*— con autonomía acotada y supervisión humana; su orquestación autónoma completa no se considera implementada.

- **OE4 — Catálogo ejecutable de controles de privacidad:** formalizar controles técnicos derivados de la Ley N° 21.719 y de las obligaciones aplicables al caso de estudio en un catálogo ejecutable, utilizando identificadores trazables y motores de detección, validación y remediación supervisada. La evaluación se centrará en violaciones técnicas identificables, sin equiparar el resultado del arnés con una certificación de cumplimiento jurídico.

- **OE5 — Evaluación experimental:** ejecutar y ampliar un protocolo comparativo sobre bancos de prueba controlados, midiendo violaciones de privacidad confirmadas, fallas de comportamiento, pruebas funcionales, consumo de tokens y tiempo de ciclo. El protocolo deberá explicitar las limitaciones de tamaño muestral, adjudicación y generalización de los resultados.

El cumplimiento de cada objetivo se evalúa con los criterios de la sección 6.4 y se traza en la matriz de la sección 7.4.


# 4. JUSTIFICACIÓN Y ALCANCE

## 4.1 Justificación

El valor del proyecto se articula en cuatro ámbitos complementarios:

- **Valor técnico:** el arnés combina análisis estructural del repositorio, selección topológica de contexto, políticas verificables y validación automatizada para comprobar requisitos seleccionados de la Ley N° 21.719. La poda BFS (`k ≤ 2`) busca limitar la vecindad de información considerada para una tarea. Sin embargo, como el contexto todavía puede serializar archivos completos, no se afirma que ya exista selección fina a nivel de símbolos ni que el mecanismo haya reducido por sí solo las dependencias inexistentes o la latencia de inferencia. Esos efectos deben medirse con un protocolo específico.

- **Valor metodológico:** el catálogo de *skills* y las reglas permanentes proporcionan una secuencia de trabajo y un marco explícito de decisiones. La separación entre instrucciones declarativas y controles deterministas permite distinguir lo que el modelo debe seguir de aquello que el arnés puede comprobar mediante software: en este proyecto, los controles derivados de la Ley N° 21.719.

- **Valor normativo y social:** el proyecto utiliza controles técnicos relacionados con protección de datos personales, como la prevención de exposición de información sensible en bitácoras y respuestas de API. La Ley N° 21.719 incorpora al texto de la Ley N° 19.628 la protección desde el diseño y por defecto (artículo 14 quáter) y el deber de adoptar medidas de seguridad (artículo 14 quinquies); a esos artículos se refiere este informe cuando cita la numeración. A la fecha de corte de este informe, 24 de noviembre de 2026, su entrada en vigencia está prevista para el 1 de diciembre de 2026. El artículo 35 contempla sanciones diferenciadas según la gravedad de la infracción, con un máximo de 20.000 UTM para infracciones gravísimas; no corresponde presentar ese máximo como una sanción automática por cualquier fuga de datos \[1\]. Para el caso clínico, la Ley N° 20.584 establece una conservación mínima de quince años de las fichas clínicas, obligación desarrollada también en el artículo 11 del Decreto N° 41 \[3\]\[4\]. El arnés traduce algunos de estos requisitos a controles técnicos; no determina el cumplimiento legal integral ni reemplaza una evaluación jurídica.

- **Valor académico:** el proyecto aporta un artefacto de ingeniería y evidencia experimental sobre el efecto de determinadas capas de gobernanza. Los resultados actuales muestran un efecto estadísticamente significativo de la configuración con compuerta sobre las violaciones confirmadas en el experimento de dosis, junto con un costo de tokens y tiempo. La evidencia no permite generalizar todavía a todos los modelos, dominios ni componentes del arnés.

## 4.2 Alcance del proyecto

El proyecto comprende los siguientes componentes:

1. **Arnés especializado en la Ley N° 21.719 — producto principal:**

   - Doce procedimientos de desarrollo documentados, desde la definición de requerimientos hasta la documentación final.

   - Tres procedimientos de cumplimiento: auditoría, desarrollo con controles y parcheo supervisado.

   - Reglas permanentes de interacción, relacionadas con consulta previa, foco MVP, verificación de dependencias y simplicidad. Estas reglas orientan al agente, pero no se consideran por sí solas un mecanismo determinista de enforcement.

   - Motor de análisis estructural: grafo de archivos, clases, funciones e importaciones, análisis de linaje y de flujos entre origen y destino, con persistencia local.

   - Catálogo de controles y motores de políticas, descritos en la sección 5.3.6.

   - Motor de validación y compuerta de integración, contratos de datos y visualización de resultados.

   - Parametrización de los directorios de análisis, que permite ejecutar los motores sobre distintos repositorios compatibles con el análisis implementado.

   - **Suite propia:** 592 pruebas.

2. **Aplicación clínica — caso de estudio transaccional:**

   - Backend con API REST y persistencia relacional asíncrona para gestionar pacientes, profesionales, citas y registros de auditoría.

   - Lógica de dominio que incluye validación de RUT mediante Módulo-11, prevención de colisiones de agenda y control de acceso basado en roles con tokens firmados.

   - Contratos OpenAPI y 21 pruebas automatizadas. El frontend clínico de usuario final no forma parte del alcance experimental.

   - **Suite propia:** 21 pruebas.

3. **Módulo de cumplimiento normativo — funcionalidad integrada del arnés:**

   - Catálogo de controles en tres niveles: el pack sectorial de la ley (30 aristas), el pack de detectores técnicos (7 controles) y el catálogo consolidado de 37 entradas.

   - Controles técnicos sobre exposición de información sensible en logs y respuestas de API (CWE-532 y CWE-200), protección de datos de pago, control de acceso y retención de información clínica.

   - Rutinas de diagnóstico y remediación asistida con validación posterior. La existencia de procedimientos de cumplimiento no implica orquestación autónoma entre subagentes.

**Bancos de prueba experimentales:**

- La aplicación clínica de demostración.

- Un banco de comercio electrónico («Dumbo») utilizado como sujeto de prueba de los experimentos controlados.

- Un paquete de tareas con pruebas ocultas y reglas Semgrep independientes utilizadas como oráculo.

- Documentación de delimitación de bancos sectoriales, que no constituye un banco ejecutable adicional.

**Perfiles destinatarios:**

- **Ingenieros de software y desarrolladores:** utilizan el arnés desde su entorno de desarrollo y línea de comandos para ejecutar los procedimientos, analizar repositorios y validar cambios.

- **Oficiales de protección de datos y auditores:** constituyen perfiles potenciales de consulta de reportes y visualizaciones para inspeccionar controles y posibles flujos de información sensible. No se afirma que exista una plataforma autónoma de auditoría destinada a estos perfiles.

**Entorno de ejecución y resguardos éticos:**

- Los componentes del arnés requieren Python 3.11 o superior y se validaron en Python 3.13, con una base de datos embebida para persistir estructuras y hallazgos.

- La aplicación clínica utiliza datos sintéticos. Las pruebas emplean RUT ficticios matemáticamente válidos mediante Módulo-11, nombres aleatorios y registros clínicos simulados. No se utilizan fichas ni registros médicos reales de pacientes.

## 4.3 Fuera de alcance

Para preservar el rigor y la viabilidad del proyecto, se establecen las siguientes exclusiones:

1. **Asesoría jurídica formal:** el arnés no reemplaza la consultoría de abogados ni emite certificados vinculantes ante la Agencia de Protección de Datos Personales.

2. **Soporte multi-lenguaje completo:** el análisis estático se concentra en el ecosistema Python. La extensión integral a Java, C\# u otros lenguajes queda fuera de la implementación evaluada.

3. **Orquestación totalmente autónoma:** los roles agénticos están definidos a nivel de especificación y directivas; los ciclos autónomos cerrados entre roles no forman parte del estado implementado.

4. **Frontend clínico de usuario final:** la aplicación clínica se utiliza principalmente como banco de pruebas de API, contratos OpenAPI y persistencia.

5. **Certificación jurídica automática:** los controles detectan condiciones técnicas concretas; no determinan por sí solos el cumplimiento integral de la legislación.

6. **Fine-tuning o entrenamiento de modelos:** no se entrenan ni ajustan modelos de lenguaje como parte del proyecto.

7. **Infraestructura cloud de despliegue:** no se construye una plataforma cloud como producto del arnés.

8. **Sandboxing empresarial o sistema multiagente complejo:** no se implementa una infraestructura de aislamiento ni una arquitectura multiagente de nivel empresarial.


# 5. ESTADO DEL ARTE, MARCO CONCEPTUAL Y BRECHA

## 5.1 Antecedentes del ecosistema

El desarrollo asistido por IA converge en torno a modelos generativos, agentes con capacidad de utilizar herramientas, mecanismos de gestión de contexto y sistemas de verificación.

1. **Herramientas de asistencia al desarrollo:** productos como Copilot, Cursor y Windsurf ofrecen distintas combinaciones de autocompletado, chat contextual y edición asistida. Sus capacidades varían según producto, versión y configuración; por ello, la comparación de este informe se limita a las dimensiones relevantes para el proyecto y no afirma que todas estas herramientas carezcan de mecanismos de gobernanza.

2. **Agentes de ingeniería de software:** enfoques como SWE-agent, Devin y OpenHands permiten que agentes interactúen con repositorios, terminales y herramientas para abordar tareas de desarrollo. Estas soluciones amplían el nivel de acción del modelo, pero hacen relevante la necesidad de permisos, trazabilidad, verificación y supervisión humana \[11\].

3. **Gestión de contexto para LLMs:** las técnicas de recuperación textual y RAG pueden recuperar fragmentos por similitud, mientras que los grafos estructurales representan relaciones explícitas entre archivos, clases, funciones, imports y llamadas. El proyecto explora esta segunda alternativa para seleccionar vecindades del código. No se sostiene que los grafos sean universalmente superiores a RAG: se evalúan como un mecanismo apropiado para preservar determinadas relaciones estructurales del repositorio.

4. **Cumplimiento normativo como código (*Compliance as Code*):** herramientas de análisis estático como Semgrep permiten definir reglas automatizadas sobre patrones de código. En este proyecto se utilizan tanto como apoyo al análisis como parte de un oráculo independiente en los experimentos. Sus resultados requieren adjudicación, pues pueden existir falsos positivos y hallazgos que no constituyan una violación confirmada.

5. **Análisis estático de privacidad:** una línea de trabajo específica aplica análisis de flujo a la protección de datos. Paralegal detecta violaciones de políticas de privacidad en Rust a partir de un grafo de dependencias del programa y de marcadores que los desarrolladores aplican al código, y se compara con CodeQL y con control de flujo de información \[20\]. Tang, Østvold y Bruntink identifican flujos de datos personales para priorizar la revisión de código y reportan una precisión de 0,87 sobre cuatro aplicaciones, sin poder medir exhaustividad por falta de verdad de referencia \[21\]. Ran, Zhang y Tang publican un banco de 1.951 instancias anotadas sobre quince repositorios Android y comparan once métodos, entre ellos modelos de lenguaje, recuperación aumentada y un agente \[22\]. Estos trabajos son el punto de comparación directo de este informe: coinciden en el objeto —detectar tratamiento de datos personales en el código— y difieren en escala y en el mecanismo de evaluación.

6. **Agent Skills y *harness engineering*:** la especificación abierta de Agent Skills define una estructura basada en una carpeta con un archivo de definición, metadatos obligatorios de nombre y descripción, y recursos opcionales como scripts y referencias. También describe un mecanismo de carga progresiva, en el que el agente descubre las *skills* por sus metadatos y carga las instrucciones y recursos cuando corresponde \[12\]\[13\]. Por su parte, OpenAI describe *harness engineering* como el diseño del entorno, las herramientas, la estructura del repositorio y los mecanismos de feedback que permiten a los agentes realizar trabajo de ingeniería de software de manera más confiable \[14\]. Zhong y Zhu proponen además una formulación del *harness* como una capa de ejecución que media entre el modelo, el proyecto y el entorno \[15\].

## 5.2 Análisis crítico y tabla comparativa

La comparación se utiliza para identificar dimensiones de diseño relevantes, no para afirmar que todos los productos de una categoría tengan exactamente las mismas capacidades.

| Criterio | Asistentes de código | Agentes de ingeniería | SAST / linters | Reglas estáticas (archivos de directivas) | Harness propuesto |
| - | - | - | - | :-: | - |
| **Gobernanza del ciclo de vida** | Asistencia centrada en tareas de edición y desarrollo. | Ejecución de tareas mediante herramientas y ciclos agénticos. | Análisis de código y reglas específicas. | Directivas que orientan el comportamiento. | Pipeline documentado de 12 *skills* desde PRD hasta documentación; la validación integral en IDE sigue en progreso. |
| **Soberanía del desarrollador** | Depende del producto, su configuración y los controles disponibles. | Depende de permisos, entorno y supervisión configurados. | El humano revisa y resuelve hallazgos. | Mantienen explícitas las preferencias y restricciones del proyecto. | Directivas permanentes más controles deterministas donde existe una política implementada. |
| **Gestión de contexto** | Contexto del editor, archivos y herramientas disponibles. | Contexto reunido durante la resolución de la tarea. | No constituye su función principal. | Depende de la información suministrada al agente. | Grafo estructural con recorrido BFS acotado (`k ≤ 2`); la serialización todavía puede incorporar archivos completos. |
| **Auditoría de privacidad** | Depende de las funciones y extensiones disponibles. | Depende de las herramientas y políticas configuradas. | Detección mediante reglas estáticas. | Puede documentar restricciones, pero no verifica por sí sola el código. | Catálogo ejecutable de controles de la Ley N° 21.719, motor de políticas y compuerta de validación. |
| **Trazabilidad** | Varía según el historial y los registros disponibles. | Puede registrar acciones, comandos y resultados. | Produce hallazgos de análisis. | Conserva directivas del proyecto. | Vincula workflows, controles, resultados de pruebas y reportes; no se afirma trazabilidad total de toda decisión técnica. |
| **Desacoplamiento** | Suele integrarse en un entorno de desarrollo. | Opera dentro del entorno configurado para el agente. | Puede ejecutarse como herramienta externa o integrada. | Se mantiene en archivos del repositorio. | Núcleo separado de las aplicaciones, con rutas de análisis parametrizables para repositorios Python compatibles. |


## 5.3 Fundamentos técnicos de las decisiones de ingeniería

### 5.3.1 Pipeline de procedimientos (01 a 12) como etapas especializadas

Dividir el ciclo de vida en doce etapas delimitadas (`01-prd` hasta `12-documentation`) permite separar actividades como definición de requerimientos, arquitectura, modelado de datos, diseño de API, backend, frontend, autenticación, pruebas, CI/CD, despliegue, observabilidad y documentación.

Cada *skill* delimita un procedimiento y puede orientar al agente mediante preguntas, pasos y criterios de salida. El pipeline busca que las decisiones relevantes se documenten antes de ejecutar cambios; no se afirma que la secuencia garantice por sí sola que el modelo siga todas las instrucciones. La integridad de las carpetas se comprueba mediante pruebas, mientras que la validación completa del flujo en el entorno del IDE permanece como trabajo pendiente.

### 5.3.2 Reglas permanentes y soberanía del desarrollador

Las reglas permanentes expresan restricciones del proyecto: consultar ante ambigüedades, mantener el alcance MVP, verificar dependencias y privilegiar soluciones simples bajo principios KISS/YAGNI.

Estas reglas son instrucciones dirigidas al agente, no controles deterministas inviolables. Su cumplimiento debe apoyarse en verificaciones independientes cuando exista una condición comprobable, por ejemplo, una política que detecte una dependencia no autorizada o una compuerta que rechace un cambio. La distinción es central para interpretar los experimentos: las reglas declarativas por sí solas no mostraron un efecto estadísticamente detectable en el experimento de dosis.

### 5.3.3 Grafos estructurales frente a recuperación exclusivamente textual

El software contiene relaciones explícitas que pueden representarse mediante un grafo: pertenencia de funciones a archivos y clases, imports, llamadas y posibles relaciones de flujo de datos. El análisis AST permite obtener parte de esa estructura sin ejecutar el programa.

La propuesta utiliza estas relaciones para identificar una vecindad alrededor de un componente de interés. Esto complementa las búsquedas textuales o por similitud semántica cuando la tarea requiere conocer quién invoca a quién o qué módulos están relacionados. No se sostiene que RAG sea innecesario en todos los casos ni que el grafo represente la semántica completa del programa.

### 5.3.4 Poda topológica de vecindad acotada (`k ≤ 2`)

El recorrido BFS limita la selección a nodos cercanos al elemento de interés dentro del grafo. Con ello se busca evitar tanto la incorporación indiscriminada del repositorio como la selección aislada de un único fragmento sin sus relaciones inmediatas.

La implementación actual utiliza la vecindad del grafo, pero la representación entregada al agente puede incluir el contenido completo de los archivos asociados. Por ello, el parámetro `k ≤ 2` expresa una distancia topológica sobre el grafo y no equivale a una extracción de únicamente dos niveles de funciones o símbolos. La selección fina de símbolos constituye una mejora pendiente.

### 5.3.5 Desacoplamiento y parametrización del motor

El núcleo del arnés se organiza como un módulo independiente de las aplicaciones analizadas. Los motores de grafo, de linaje y de auditoría aceptan directorios de escaneo configurables, lo que permite ejecutar el análisis sobre aplicaciones diferentes sin incorporar sus reglas de negocio dentro del motor.

El desacoplamiento se encuentra demostrado en los bancos utilizados por el proyecto. No debe confundirse con soporte universal para cualquier lenguaje o arquitectura: el análisis implementado se concentra en el ecosistema Python y en las estructuras que los extractores actuales reconocen.

### 5.3.6 Catálogo de controles normativos

El catálogo es el aporte normativo del proyecto: una correspondencia explícita entre deberes de la ley y condiciones verificables sobre el código. Cada entrada declara qué se verifica, qué disposición lo exige, qué referencia técnica lo respalda y de qué modo puede comprobarse. El catálogo es un dato del sistema y no una lista escrita dentro del programa: el motor lo lee, de modo que el mismo motor puede servir a otro marco normativo cambiando el catálogo.

**Sobre las citas.** La Ley N° 21.719 no crea un cuerpo legal separado: modifica la Ley N° 19.628, y es en el texto reformado de esta última donde existen los artículos que aquí se citan (14 bis a 16 sexies, entre otros). Por eso la base normativa se expresa como «19.628 art. 14 quáter» y no como «21.719 art. 14 quáter»: la segunda forma remite a un artículo que no está en esa ley. Las normas sectoriales (Ley N° 20.584, Ley N° 19.496, DL 825 y DL 830) se citan del mismo modo.

**Modos de verificación.** «Detectar» significa que una condición del código decide el control y produce un hallazgo con archivo y línea. «Riesgo» significa que el hallazgo se reporta sin bloquear, porque el indicador no prueba por sí solo una violación. «Evidencia» significa que el control exige un artefacto documental con responsable y vigencia. «Manual» significa que lo firma una persona con el artículo a la vista.

**Controles clínicos**

| ID | Qué verifica | Base normativa | Referencia técnica | Modo |
| - | - | - | - | :-: |
| `CL-DATAPROT-001` | Fuga de datos clínicos sensibles o RUT hacia logs del sistema o telemetría | 19.628 art. 14 bis, art. 14 quinquies, art. 34 ter let. i), art. 34 quáter let. d); 20.584 art. 12 | CWE-532; ISO/IEC 27001:2022 A.8.12 | detectar |
| `CL-DATAPROT-002` | Exposición de registros médicos en capas de caché sin cifrado en reposo | 19.628 art. 2 let. g), art. 14 quinquies inc. 2 let. a) | CWE-311; ISO/IEC 27001:2022 A.8.24 | detectar |
| `CL-DATAPROT-003` | Persistencia de entidades de salud sin cifrado a nivel de campo (FLE) en modelo ORM | 19.628 art. 14 quáter, art. 14 quinquies | CWE-312; ISO/IEC 27001:2022 A.8.24 | detectar |
| `CL-DATAPROT-004` | Borrado físico prematuro de fichas clínicas (deber de conservación de 15 años) | 20.584 art. 13; 19.628 art. 7 inc. 2 N° ii, art. 8 ter | CWE-404; ISO/IEC 27001:2022 A.8.10 | detectar |
| `CL-DATAPROT-005` | Exposición de endpoints clínicos sin control de acceso | 19.628 art. 14 quáter, art. 14 quinquies; 20.584 art. 13 inc. 4 | CWE-285; ISO/IEC 27001:2022 A.8.3 | detectar |
| `CL-DATAPROT-006` | Decisión clínica automatizada sin garantías de explicación, intervención humana y revisión | 19.628 art. 8 bis | CWE-693; ISO/IEC 27001:2022 A.8.28 | manual |
| `CL-DATAPROT-007` | Exportación de portabilidad de ficha clínica en formato no estructurado | 19.628 art. 9; 20.584 art. 13 inc. 1; 21.668 art. único | CWE-20; ISO/IEC 27001:2022 A.8.28 | detectar |

**Núcleo de la ley**

| ID | Qué verifica | Base normativa | Referencia técnica | Modo |
| - | - | - | - | :-: |
| `CORE-CHECK-001` | Privacidad desde el diseño, minimización y seudonimización o cifrado según el riesgo | 19.628 art. 14 quáter, art. 14 quinquies inc. 2 let. a) | — | manual |
| `CORE-CHECK-002` | Deber de secreto y prevención de fugas en logs, consolas y cachés | 19.628 art. 14 bis, art. 34 ter let. i), art. 34 quáter let. d) | — | detectar |
| `CORE-CHECK-003` | Derechos del titular (acceso, rectificación, supresión, oposición, portabilidad y bloqueo) y control de acceso | 19.628 Arts. 4 al 11, art. 14 quáter | — | detectar |
| `CORE-CHECK-004` | Decisiones automatizadas: derecho de oposición y garantías de intervención humana | 19.628 art. 8 bis | — | manual |
| `CORE-CHECK-005` | Licitud del tratamiento y consentimiento | 19.628 art. 12, art. 13, art. 2 let. p) | — | detectar |
| `CORE-CHECK-006` | Atención de los derechos del titular: procedimiento y plazos | 19.628 Arts. 4 al 11 | — | detectar |
| `CORE-CHECK-007` | Deber de información y transparencia (política de tratamiento pública) | 19.628 art. 14 ter, art. 3 let. g) | — | riesgo |
| `CORE-CHECK-008` | Registro y comunicación de vulneraciones de seguridad | 19.628 art. 14 sexies, art. 34 quáter let. f) | — | evidencia |
| `CORE-CHECK-009` | Evaluación de impacto en protección de datos | 19.628 art. 15 ter, art. 34 quáter let. k) | — | evidencia |
| `CORE-CHECK-010` | Encargados del tratamiento y cesión de datos | 19.628 art. 15 bis, art. 15 | — | riesgo |
| `CORE-CHECK-011` | Transferencias internacionales de datos | 19.628 art. 27, art. 28, art. 14 ter let. h) | — | riesgo |
| `CORE-CHECK-012` | Datos personales de niños, niñas y adolescentes | 19.628 art. 16 quáter | — | detectar |
| `CORE-CHECK-013` | Conservación, supresión y limitación de la finalidad | 19.628 art. 3 let. b), art. 3 let. c), art. 14 let. d), art. 7 inc. 2 N° ii | — | riesgo |

**Salud**

| ID | Qué verifica | Base normativa | Referencia técnica | Modo |
| - | - | - | - | :-: |
| `HEALTH-CHECK-001` | Conservación de 15 años de la ficha clínica frente a solicitudes de supresión | 20.584 art. 13; 19.628 art. 7 inc. 2 N° ii, art. 8 ter | — | detectar |
| `HEALTH-CHECK-002` | Interoperabilidad de la ficha clínica bajo HL7 FHIR R4 CL Core (estándar del proyecto) | 20.584 art. 13 inc. 1 y 2; 21.668 art. único; 19.628 art. 9 | — | evidencia |
| `HEALTH-CHECK-003` | Protección reforzada de datos de salud (aislamiento y cifrado según el riesgo) | 19.628 art. 2 let. g), art. 16 bis | — | evidencia |

**Comercio electrónico**

| ID | Qué verifica | Base normativa | Referencia técnica | Modo |
| - | - | - | - | :-: |
| `ECOM-CHECK-001` | Comunicaciones promocionales y oposición al marketing directo | 19.496 art. 28 B; 19.628 art. 12, art. 13, art. 8 let. b) | — | detectar |
| `ECOM-CHECK-002` | Perfilamiento y recomendaciones personalizadas | 19.628 art. 2 let. w), art. 8 let. b), art. 8 bis, art. 15 ter, art. 14 ter let. l) | — | manual |
| `ECOM-CHECK-003` | Datos de tarjetas de pago: secreto, seguridad y comunicación de vulneraciones | 19.628 art. 14 bis, art. 14 quinquies, art. 14 sexies | — | detectar |
| `ECOM-CHECK-004` | Cumplimiento PCI DSS para datos de tarjetas (estándar contractual) | Código Tributario Cláusula 10.9; 19.628 art. 14 quinquies | — | evidencia |
| `ECOM-CHECK-005` | Pasarelas de pago, operadores logísticos y otros encargados | 19.628 art. 15 bis, art. 15 | — | riesgo |
| `ECOM-CHECK-006` | Conservación de documentos tributarios como excepción a la supresión | DL 825 art. 58; DL 830 art. 17, art. 200; 19.628 art. 7 inc. 2 N° ii, art. 3 let. c) | — | evidencia |
| `ECOM-CHECK-007` | Situación socioeconómica y puntajes de crédito como datos sensibles | 19.628 art. 2 let. g), art. 16 | — | detectar |

**Detectores técnicos**

| ID | Qué verifica | Base normativa | Referencia técnica | Modo |
| - | - | - | - | :-: |
| `v2.admin_exposure` | Unmasked personal data in a response | 21.719 art. 14 bis | ISO/IEC 27001:2022 A.8.12; ISO/IEC 27001:2022 A.8.11; CWE-200 | detectar |
| `v2.api_key` | API key or secret returned to the client | 21.719 art. 14 bis | ISO/IEC 27001:2022 A.8.24; CWE-798 | detectar |
| `v2.billing_retention` | Billing records deleted before retention | 21.719 art. 3 c) | ISO/IEC 27001:2022 A.8.10; CWE-404 | detectar |
| `v2.credential_response` | Credential exposed in a response | 21.719 art. 14 bis | ISO/IEC 27001:2022 A.8.12; CWE-200 | detectar |
| `v2.customer_hard_delete` | Customer hard delete inside retention | 21.719 art. 4 y art. 10 | ISO/IEC 27001:2022 A.8.10; CWE-404 | detectar |
| `v2.log_pii` | Personal data written to logs | 21.719 art. 14 bis | ISO/IEC 27001:2022 A.8.12; CWE-532 | detectar |
| `v2.reset_token` | Password-reset token returned to the client | 21.719 art. 14 bis | ISO/IEC 27001:2022 A.8.24; CWE-522 | detectar |

Los 37 controles se distribuyen así: 30 aristas derivadas de la ley —15 detectables, 5 de riesgo, 6 de evidencia y 4 manuales— más 7 detectores técnicos que operan sobre las mismas categorías de datos. De las 15 aristas detectables, 14 tienen detector propio y `CL-DATAPROT-001` queda cubierta por el detector de `CORE-CHECK-002`; junto con las 5 de riesgo y los 7 detectores técnicos suman los 26 controles implementados. Los cinco controles restantes se declaran como gaps con su motivo, no como silencio.

La correspondencia es una derivación técnica revisada contra el texto legal, no una transcripción literal ni una certificación jurídica.

## 5.4 Interoperabilidad mediante Model Context Protocol (MCP)

Una posible evolución consiste en exponer algunas funciones del arnés mediante Model Context Protocol (MCP), sin convertir MCP en el objeto principal de investigación. El protocolo define mecanismos para que servidores expongan herramientas, recursos y *prompts* a clientes compatibles, junto con consideraciones de autorización y participación humana en operaciones sensibles \[17\]\[18\].

En el proyecto, MCP se considera un posible adaptador de integración entre el agente y el arnés. No se presenta como una funcionalidad implementada ni como un requisito para validar los experimentos actuales.

## 5.5 Privacidad y cumplimiento como código

La Ley N° 21.719 incorpora deberes de protección desde el diseño y por defecto, así como medidas de seguridad para el tratamiento de datos personales. Los artículos 14 quáter y 14 quinquies pertenecen al texto reformado de la Ley N° 19.628 y así se citan en el catálogo de la sección 5.3.6; el informe no atribuye al software la capacidad de certificar cumplimiento legal integral \[1\].

En el caso clínico, la conservación de fichas clínicas debe considerar el plazo mínimo de quince años establecido en el artículo 13 de la Ley N° 20.584 y desarrollado en el artículo 11 del Decreto N° 41 \[3\]\[4\]. Este requisito se representa como una restricción técnica de retención y eliminación controlada, no como una obligación de conservar indefinidamente todos los datos.

Entre los escenarios técnicos evaluados se incluyen la exposición de información personal en logs (CWE-532) y la exposición de información sensible a actores no autorizados (CWE-200). Los resultados de análisis se interpretan como hallazgos técnicos sujetos a clasificación y adjudicación.

## 5.6 Brecha identificada

El estado del arte presenta mecanismos de asistencia, agentes, workflows especializados, recuperación de contexto y análisis estático. La brecha que aborda el proyecto se concreta en estudiar cómo integrar esos mecanismos en un flujo de desarrollo gobernado y evaluable, orientado a la prevención de violaciones técnicas de la Ley N° 21.719:

**workflows especializados + contexto estructural + políticas verificables + validación determinista + evidencia experimental.**

La contribución buscada no consiste en afirmar que un componente aislado resuelve los riesgos del desarrollo asistido por IA, sino en evaluar qué efectos produce una combinación concreta de controles sobre tareas reproducibles y bajo qué costos y limitaciones.


# 6. METODOLOGÍA

## 6.1 Enfoque metodológico

Se adopta el paradigma de **Investigación en Ciencia del Diseño** (*Design Science Research*, DSR), complementado con principios de ingeniería de software empírica. DSR se orienta a crear y evaluar artefactos tecnológicos que aborden problemas prácticos. El proceso considera la identificación del problema, definición de objetivos, diseño y desarrollo del artefacto, demostración, evaluación y comunicación de resultados \[7\]\[8\].

El artefacto principal es el arnés de desarrollo asistido por IA especializado en la Ley N° 21.719, compuesto por:

1. Un catálogo de *skills* procedimentales de desarrollo.

2. Reglas permanentes que expresan restricciones y decisiones del proyecto.

3. Un motor de análisis estructural y gestión de contexto.

4. Un catálogo de controles derivados de la Ley N° 21.719 y motores de políticas.

5. Mecanismos de validación, compuerta y registro de resultados.

## 6.2 Diseño experimental ejecutado

Se ejecutaron cuatro experimentos complementarios. Los dos primeros comparan configuraciones del arnés sobre el banco de comercio electrónico y utilizan pruebas ocultas y reglas Semgrep independientes como oráculo. El tercero mide la calidad del detector con corpus ciegos sellados. El cuarto mide el costo y la preservación funcional sobre el paquete de diez trampas de protocolo. En todos los casos el modelo se fijó en `opencode-go/deepseek-v4.1-flash` y la configuración se mantuvo constante dentro de cada comparación.

### Etapa 1 — Experimento formal de tres brazos

Se compararon las siguientes condiciones:

- **`baseline`:** aplicación sin reglas ni *skills* del arnés.

- **`harness`:** las reglas permanentes más los doce procedimientos de desarrollo.

- **`harness_compliance`:** configuración anterior más las tres *skills* de cumplimiento, compuerta y rondas de retroalimentación.

Se ejecutaron **12 tareas × 3 brazos × 3 repeticiones = 108 ejecuciones**. Las 108 ejecuciones finalizaron.

### Etapa 2 — Experimento de dosis de cinco brazos

Para observar el efecto incremental de los componentes de gobernanza, se compararon cinco configuraciones sobre cuatro tareas, con cinco repeticiones por condición:

- **`baseline`:** sin reglas ni *skills*.

- **`rules`:** solamente las reglas permanentes.

- **`rules_skills`:** las reglas permanentes más los doce procedimientos de desarrollo.

- **`rules_skills_gate`:** reglas y *skills* más las *skills* de cumplimiento y la compuerta.

- **`rules_skills_gate_enforced`:** configuración anterior con hasta tres rondas externas de corrección.

Se ejecutaron **5 brazos × 4 tareas × 5 repeticiones = 100 ejecuciones**. Las 100 ejecuciones finalizaron.

### Etapa 3 — Calibración ciega del detector

Los dos experimentos anteriores miden el efecto del arnés sobre el agente; ninguno mide la calidad del detector que la compuerta ejecuta. Esa calidad condiciona cualquier conclusión: una compuerta imprecisa produce falsos positivos que el desarrollador aprende a ignorar, y una compuerta incompleta produce falsos negativos silenciosos. El corpus curado del Hito 1 no podía responder la pregunta, porque sus 22 casos los escribió el mismo autor del detector: ese corpus mide memoria, no generalización.

Por eso cada ronda la escribió un autor sin acceso al repositorio, se selló con `sha256` antes de la corrida, se evaluó una sola vez y se reportó el número **previo** a cualquier corrección. Los fallos se corrigieron después y los casos pasaron al corpus de regresión, de modo que las corridas posteriores sobre ese conjunto son regresión y no evidencia de generalización. Se ejecutaron 21 rondas entre 36 y 84 casos, cubriendo los siete controles `v2.*`.

### Etapa 4 — Preservación funcional y costo

La calibración mide el detector; esta etapa mide el arnés completo en el ciclo de desarrollo. Su pregunta es distinta: ¿el arnés cambia el resultado funcional del trabajo, o solamente lo encarece?

- **Trampas:** diez tareas de protocolo (D01–D10), cada una con una prueba oculta independiente, una verificación de evidencia y la suite propia del objetivo.
- **Brazos:** `baseline` (solo la aplicación, sin reglas, procedimientos ni compuerta) y `rules_skills_gate` (reglas permanentes con el protocolo de ejecución, los doce procedimientos de desarrollo, los tres de cumplimiento, el catálogo, la compuerta y el enganche de integración).
- **Ejecución:** 10 trampas × 3 repeticiones × 2 brazos = **60 ejecuciones**, más 6 repeticiones adicionales de D03 tras unificar la fuente de destinatarios en la capa de evidencia.
- **Instrumento:** mismo modelo, mismo entorno, un *workspace* nuevo por ejecución. Las corridas no se aleatorizaron: el brazo con compuerta se ejecutó el 20 de noviembre y el de línea base el 21.

### Oráculo y clasificación de resultados

Los resultados se clasificaron con dos señales independientes:

|  | Semgrep encontró una violación | Semgrep no encontró una violación |
| - | - | - |
| **La prueba oculta falla** | `confirmed_violation` | `behavioral_failure`: tarea no implementada (404), test demasiado estricto o privacidad que el oráculo no cubre; requiere adjudicación |
| **La prueba oculta pasa** | `latent_risk`: hallazgo que requiere revisión | `clean` |


La compuerta del experimento es una herramienta de línea de comandos que evalúa los archivos cambiados con el motor de políticas (`PolicyEngine` + `CatalogEngine`): parsea el código con AST, aplica las familias y consulta el catálogo. No es el hook de `pre-commit`, que se describe en la sección 8.2 y opera sobre el índice de git; tampoco ve las pruebas ocultas ni el oráculo. El experimento no usa el grafo estructural para seleccionar contexto.

Las métricas consideradas incluyen violaciones confirmadas, pruebas ocultas aprobadas, hallazgos Semgrep, llamadas a la compuerta, rondas externas, tokens utilizados, tiempo de ciclo y fallas de comportamiento.

**Límite del diseño ejecutado:** los brazos de ambos experimentos varían reglas, *skills* y compuertas de cumplimiento. No incorporan una condición independiente de selección de contexto mediante grafos. Por tanto, estos experimentos no permiten atribuir causalmente a la gestión estructural de contexto los cambios observados.

### Diseño factorial proyectado para contexto

Se mantiene como línea experimental posterior la separación de dos factores:

- **Factor A — Gobernanza:** sin políticas del arnés / con políticas del arnés.

- **Factor B — Gestión estructural de contexto:** contexto convencional / contexto seleccionado mediante el grafo estructural.

Esto produciría cuatro condiciones: A (sin gobernanza y sin contexto estructural), B (sin gobernanza y con contexto estructural), C (con gobernanza y sin contexto estructural) y D (con gobernanza y con contexto estructural). Este diseño no debe describirse como ejecutado en los resultados actuales.

## 6.3 Datos utilizados, fuentes y resguardos éticos

- **Datos sintéticos:** las entidades transaccionales de los bancos de prueba se generan programáticamente. Se utilizan RUT ficticios válidos bajo el algoritmo Módulo-11, nombres aleatorios y registros clínicos simulados.

- **Sin registros reales:** el proyecto no utiliza fichas clínicas reales, historiales hospitalarios ni identificadores personales reales. Las pruebas se limitan a código, estructuras y datos sintéticos.

- **Resguardo de resultados:** las pruebas ocultas y los reportes de ejecución se utilizan para comparar las configuraciones, manteniendo la distinción entre detecciones automáticas y violaciones confirmadas mediante la clasificación definida.

## 6.4 Criterios de éxito y amenazas a la validez

### Criterios de éxito

1. **Reducción de violaciones de privacidad:** observar una disminución de violaciones confirmadas respecto de la línea base, reportando la prueba estadística y el tamaño de la muestra.

2. **Preservación funcional:** mantener aprobada la suite de regresión del repositorio. Al cierre de esta actualización, la suite consolidada registra 613 pruebas aprobadas.

3. **Costo de gobernanza:** medir y reportar tokens y tiempo de ciclo, de modo que cualquier mejora de privacidad se interprete junto con el costo de ejecución.

4. **Remediación verificable:** acompañar los cambios de privacidad con resultados de pruebas y evidencia del análisis estático.

5. **Reproducibilidad:** documentar modelo, configuración, tareas, repeticiones, reglas de clasificación y limitaciones.

### Amenazas a la validez

- **Validez interna — variabilidad de los LLMs:** las salidas pueden cambiar entre ejecuciones. Se mitigó fijando el modelo y la configuración y realizando repeticiones.

- **Potencia estadística:** el experimento formal tuvo solamente tres pares discordantes para el resultado binario y no alcanzó significancia estadística (McNemar, *p* = 0,25). El experimento de dosis mostró un contraste de ocho pares discordantes a favor de `rules_skills_gate` (*p* = 0,0078), pero sigue limitado a veinte pares por contraste y cuatro tareas.

- **Validez de constructo — oráculo:** las pruebas ocultas y Semgrep no son una representación completa de todas las violaciones posibles. Se han documentado falsos positivos en reglas relacionadas con pseudonimización y retención.

- **Adjudicación:** las tareas, pruebas, detector y oráculo comparten autoría. En esta etapa se incorporó un evaluador independiente sobre una muestra estratificada de 30 casos, que reprodujo las 30 etiquetas (kappa de Cohen 1,000); sin embargo, se trata de un modelo de la misma familia en un rol distinto, no de adjudicación humana. La limitación persiste.

- **Autoría del corpus ciego:** los autores de las rondas ciegas no acceden al repositorio ni al corpus, pero son instancias del mismo modelo que el detector. La independencia es de información, no de sesgo inductivo. Un corpus derivado de vulnerabilidades reales (CVE) o de otro modelo reduciría esta amenaza.

- **Validez externa:** los resultados principales corresponden a un solo modelo y a un banco de comercio electrónico. La generalización a otros modelos, dominios y repositorios requiere nuevas ejecuciones.

- **Alcance de los factores:** los experimentos actuales no aíslan el efecto causal del componente de contexto estructural.


# 7. PLANIFICACIÓN Y GESTIÓN

## 7.1 Cronograma general e hitos institucionales

La planificación se alinea con el calendario del curso Portafolio de Proyectos (ITISB, UNAB). A la fecha de corte de este informe, 24 de noviembre de 2026, las fases asociadas a los hitos 0, 1 y 2 se consideran completadas; la fase de consolidación del producto y evaluación integral se encuentra en curso.

```
gantt
    title Cronograma de Hitos y Fases de Trabajo del Harness
    dateFormat YYYY-MM-DD
    axisFormat %d-%b

    section Hitos oficiales (2026)
    Hito 0: Definición y producto As-Is (25%) :done, milestone, h0, 2026-09-28, 0d
    Hito 1: Primer incremento funcional (15%) :done, milestone, h1, 2026-10-12, 0d
    Hito 2: Segundo incremento y calibración (15%) :done, milestone, h2, 2026-11-24, 0d
    Hito 3: Entrega final y defensa :milestone, h3, 2026-12-01, 0d

    section Fases de desarrollo
    Fase 0: As-Is, desacoplamiento y suite modular :done, p0, 2026-09-01, 2026-09-28
    Fase 1: Catálogo, políticas y validación :done, p1, 2026-09-29, 2026-10-12
    Fase 2: Experimentos formal y de dosis :done, p2, 2026-10-13, 2026-11-02
    Fase 3: Calibración ciega, cobertura normativa y gate de evidencia :done, p3, 2026-11-03, 2026-11-24
    Fase 4: Consolidación del informe final y defensa :p4, 2026-11-25, 2026-12-01
```

| Hito | Semana de referencia | Peso | Entregable y alcance |
| - | - | :-: | - |
| **Hito 0** | Semana del 28 de septiembre | 25% | Definición formal del proyecto, estado del arte inicial, alcance, metodología y presentación del producto As-Is. |
| **Hito 1** | Semana del 12 de octubre | 15% | Primer incremento funcional: catálogo de controles derivados de la Ley N° 21.719, motor de políticas, motor de validación y compuerta de *pre-commit*. |
| **Hito 2** | 24 de noviembre | 15% | Segundo incremento: calibración ciega del detector, ampliación de la cobertura normativa, gate de evidencia y medición del costo en el ciclo de desarrollo. |
| **Hito 3** | Primera semana de diciembre | 15% + 30% | Entrega final: producto consolidado, memoria formal, validación de objetivos, conclusiones y defensa ante comisión evaluadora. |

> **Nota de cronograma:** la versión vigente del curso consolida la entrega final en el Hito 3; no se rinde un Hito 4 separado. Los pesos se mantienen según el calendario original (15 % del Hito 3 y 30 % de la instancia final).

> **Nota de alcance:** este informe corresponde a la entrega del Hito 2 del curso e incluye los resultados de calibración ciega, el experimento de preservación funcional y costo, y la ampliación de cobertura ejecutados antes del cierre de esta actualización.


## 7.2 Backlog priorizado, responsabilidades y dependencias

El equipo opera bajo un régimen de responsabilidad compartida. Ambos integrantes participan en el diseño del arnés, la implementación y revisión de pruebas, el análisis de grafos, la evaluación experimental y la redacción técnica.

| Identificador | Tarea / incremento | Prioridad | Estado |
| - | - | :-: | - |
| **TK-01** | Consolidación y desacoplamiento de la aplicación clínica | Alta | Completado |
| **TK-02** | Parametrización y modularización del motor del arnés | Alta | Completado |
| **TK-03** | Suite modular: 592 pruebas del arnés y 21 de la aplicación clínica | Alta | Completado |
| **TK-04** | Integridad y adaptación documental del pipeline de *skills* (01 a 12) | Alta | Completado |
| **TK-05** | Catálogo de controles y motor de políticas de privacidad | Alta | Completado |
| **TK-06** | Motor de validación y compuerta de *pre-commit* | Alta | Completado |
| **TK-07** | Experimento formal (108 ejecuciones) y experimento de dosis (100 ejecuciones) | Alta | Completado |
| **TK-08** | Refinamiento del visualizador y dashboard de resultados | Media | Pendiente |
| **TK-09** | Segundo adjudicador ciego y repetición experimental con otro modelo | Media | Pendiente |
| **TK-10** | Validación formal del pipeline de *skills* en el entorno del IDE | Media | En progreso |


## 7.3 Gestión de riesgos

| Código | Riesgo identificado | Prob. | Impacto | Nivel | Estrategia de mitigación |
| :-: | - | :-: | :-: | :-: | - |
| **R01** | **Saturación por grafos extensos:** repositorios grandes pueden generar vecindades densas y aumentar el contexto. | Media | Alto | Alto | Mantener límites topológicos (`k ≤ 2`) y medir los tokens del contexto generado. |
| **R02** | **Regresiones por intervenciones de agentes:** los cambios pueden alterar contratos funcionales existentes. | Media | Crítico | Crítico | Ejecutar las pruebas pertinentes después de cada cambio y la suite integral antes de integrar o entregar; utilizar reversión cuando falle la validación. |
| **R03** | **Variabilidad no determinista de los LLMs:** las respuestas pueden variar entre repeticiones. | Alta | Medio | Alto | Fijar modelo y configuración, registrar condiciones y repetir tareas bajo un protocolo documentado. |
| **R04** | **Acoplamiento entre arnés y aplicación:** el motor puede depender indebidamente de rutas o lógica de un banco de prueba. | Baja | Crítico | Alto | Mantener el núcleo del arnés separado, parametrizar los directorios de análisis y documentar los lenguajes soportados. |
| **R05** | **Adjudicación única y falsos positivos:** la clasificación de hallazgos puede depender de una única persona o de reglas imperfectas. | Alta | Alto | Alto | Incorporar un segundo adjudicador ciego y documentar falsos positivos del oráculo sin modificar retroactivamente los resultados. |
| **R06** | **Baja generalización estadística:** pocos modelos y tareas limitan el alcance de las conclusiones. | Alta | Alto | Alto | Ampliar tareas, repeticiones y modelos, y reportar tamaños de efecto, pruebas y limitaciones. |


## 7.4 Matriz de trazabilidad

| Objetivo específico | Requerimiento técnico | Hito de consolidación | Evidencia verificable |
| - | - | :-: | - |
| **OE1 — Pipeline de *skills*** | RF-H01: catálogo de doce procedimientos y directivas permanentes. | Hito 0 | Los doce procedimientos, las reglas permanentes y la prueba de integridad de los procedimientos. |
| **OE2 — Gestión de contexto** | RF-H03 y RF-H04: extracción AST, persistencia local y recorrido BFS (`k ≤ 2`). | Hito 0 / evolución | El motor de grafos, el análisis de linaje y sus pruebas. |
| **OE3 — Arquitectura desacoplada y roles** | RF-H05: motor parametrizable y especificaciones de roles. | Hito 0 | El módulo del arnés y sus 592 pruebas. |
| **OE4 — Catálogo y políticas de privacidad** | RF-H06 a RF-H08: catálogo, detección CWE-532/CWE-200, validación y compuerta. | Hito 1 | El catálogo de controles, los motores de políticas, el motor de validación y la compuerta. |
| **OE5 — Evaluación experimental** | RNF-01 a RNF-03: protocolo comparativo, métricas y ejecución empírica. | Hito 2 | Los cuatro experimentos, sus reportes y la suite de 613 pruebas. |



# 8. DISEÑO DE LA SOLUCIÓN

## 8.1 Requerimientos del sistema

### Requerimientos funcionales del arnés (RF-H)

| ID | Nombre | Descripción operativa | Criterio de aceptación |
| - | - | - | - |
| **RF-H01** | Pipeline de *skills* | Catálogo de directivas procedimentales (`01-prd` a `12-documentation`). | Las doce carpetas están disponibles y mantienen su integridad; la validación completa del flujo en IDE permanece en curso. |
| **RF-H02** | Directivas *Always-On* | Reglas permanentes que expresan consulta previa, foco MVP, verificación de dependencias y simplicidad. | Las directivas están documentadas y disponibles para el agente; las condiciones objetivamente comprobables se verifican mediante políticas independientes. |
| **RF-H03** | Indexación estática y grafos estructurales | Extracción AST de archivos, clases, funciones, imports y llamadas, con persistencia SQLite. | Se construye y persiste el grafo estructural sobre los directorios configurados. |
| **RF-H04** | Poda topológica acotada (`k ≤ 2`) | Recorrido BFS para seleccionar la vecindad de un nodo de interés. | Se obtiene un conjunto acotado de nodos; el volumen de contexto serializado se mide y se documenta que puede incluir archivos completos. |
| **RF-H05** | Motor parametrizable | Análisis sobre directorios configurables sin rutas de aplicación fijas. | El arnés opera sobre los repositorios Python compatibles utilizados en los bancos de prueba sin modificar la lógica central del motor. |
| **RF-H06** | Auditoría de controles de privacidad | Evaluación estática de controles del catálogo sobre patrones de exposición de datos. | Se identifican y reportan hallazgos relacionados con CWE-532 y CWE-200, sujetos a revisión y clasificación. |
| **RF-H07** | Validación y remediación supervisada | Validación de cambios mediante políticas y pruebas automatizadas. | El cambio se acepta únicamente cuando cumple los controles y pruebas configurados; ante fallas se utiliza el mecanismo de reversión disponible. |
| **RF-H08** | Compuerta de *pre-commit* | Inspección del contenido preparado para *commit* antes de permitir su confirmación. | El *commit* se rechaza cuando la compuerta detecta una violación bloqueante y entrega evidencia estructurada. |


### Requerimientos funcionales de la aplicación clínica (RF-C)

| ID | Nombre | Descripción operativa | Criterio de aceptación |
| - | - | - | - |
| **RF-C01** | Gestión transaccional clínica | Operaciones sobre pacientes, profesionales, citas y eventos de auditoría mediante FastAPI. | Respuestas REST tipificadas mediante esquemas Pydantic y contratos OpenAPI. |
| **RF-C02** | Validación canónica de RUT | Verificación del identificador mediante el algoritmo Módulo-11. | Rechazo de identificadores con formato o dígito verificador inválido. |
| **RF-C03** | Prevención de colisiones de agenda | Control de cruces de horario para profesionales o pacientes. | Rechazo de reservas incompatibles y preservación de la consistencia transaccional. |
| **RF-C04** | Control de acceso basado en roles (RBAC) | Autenticación JWT y permisos diferenciados para operaciones sensibles. | Denegación de operaciones cuando el token no posee los permisos requeridos. |


### Requerimientos no funcionales y de seguridad (RNF / RS)

| ID | Tipo | Descripción | Criterio de verificación |
| - | - | - | - |
| **RNF-01** | Reproducibilidad | Mantener constantes y registrar las condiciones de las ejecuciones experimentales. | Registro de modelo, configuración, tareas, repeticiones y resultados. |
| **RNF-02** | Modularidad de pruebas | Ejecutar suites por área y en forma integral. | Selección por área y ejecución completa con el ejecutor de pruebas o Pytest. |
| **RNF-03** | Preservación funcional | Evitar alteraciones no deseadas en contratos existentes. | Suite completa aprobada al cierre de la integración y resultados de regresión documentados. |
| **RS-01** | Confidencialidad (CWE-532 / CWE-200) | Evitar emisión no autorizada de datos personales, clínicos o credenciales en logs y respuestas. | Análisis estático de fuentes y sumideros, más pruebas y adjudicación de hallazgos. |
| **RS-02** | Retención de fichas clínicas | Considerar el plazo mínimo de conservación de quince años desde el último ingreso de información. | Impedir la eliminación irreversible antes de cumplirse el plazo y el proceso de revisión aplicable; permitir, cuando corresponda, una eliminación posterior segura y confidencial \[3\]\[4\]. |


## 8.2 Arquitectura del sistema

El sistema se organiza en tres dominios diferenciados: el arnés de desarrollo, la aplicación clínica de demostración y el banco experimental de comercio electrónico.

```
graph TD
    subgraph HARNESS ["ARNÉS DE DESARROLLO"]
        SKILLS["Doce procedimientos de desarrollo"]
        RULES["Reglas permanentes"]
        ROLES["Roles definidos<br/>Planner, Reviewer, Security, Compliance"]

        subgraph ENGINE ["Motor parametrizable de análisis"]
            AST["Grafo estructural (AST)"]
            TAINT["Linaje y flujo de datos"]
            SLICER["Selección topológica<br/>BFS k ≤ 2"]
            CATALOG["Catálogo y políticas"]
            GATE["Validación y compuerta"]
            AST --> SLICER
            TAINT --> CATALOG
            CATALOG --> GATE
        end

        KNOWLEDGE["Persistencia local"]
        ENGINE <--> KNOWLEDGE
    end

    subgraph CLINIC ["APLICACIÓN CLÍNICA"]
        API["API REST y control de acceso"]
        SVC["Servicios de dominio<br/>Pacientes, citas y profesionales"]
        PERSIST["Persistencia relacional"]
        EVENTS["Eventos y auditoría"]
        API --> SVC --> PERSIST --> EVENTS
    end

    subgraph BENCH ["BANCO EXPERIMENTAL"]
        SHOP["Aplicación de comercio electrónico<br/>Dumbo"]
        PACK["Paquete de tareas<br/>Pruebas ocultas + Semgrep"]
        SHOP --> PACK
    end

    subgraph TESTS ["SUITE MODULAR DE PRUEBAS (613 tests)"]
        THARNESS["Pruebas del arnés (592)"]
        TDEMO["Pruebas de la aplicación clínica (21)"]
    end

    HARNESS -.->|Escaneo parametrizable| CLINIC
    HARNESS -.->|Escaneo y auditoría| BENCH
    THARNESS -.->|Valida motores, catálogo y políticas| HARNESS
    TDEMO -.->|Valida API y persistencia| CLINIC
```

- **Módulo del arnés:** contiene los motores AST, análisis de linaje y taint, catálogo de controles, políticas, validación, compuerta de *pre-commit*, persistencia SQLite y visualización. Los roles agénticos se encuentran definidos, pero su orquestación autónoma completa sigue bajo supervisión humana.

- **Aplicación clínica:** aplicación transaccional validada mediante API REST, contratos y pruebas automatizadas.

- **Banco experimental:** aplicación de comercio electrónico utilizada como sujeto de prueba de los experimentos controlados, junto con el paquete de tareas y el oráculo.

- **Suite modular:** 592 pruebas del arnés y 21 pruebas de la aplicación clínica, ejecutables por separado o en conjunto.

## 8.3 Reproducibilidad y configuración del entorno

El entorno validado utiliza Python 3.13, Pytest 9.0.3 y SQLite embebido. Los componentes del backend utilizan FastAPI, SQLAlchemy 2.0 y las dependencias definidas en `requirements.txt`.

La instalación del entorno se realiza mediante:

```
pip install -r requirements.txt
```

El ejecutor de pruebas del proyecto permite correr áreas por separado —análisis estructural, cumplimiento, linaje, procedimientos, persistencia, aplicación clínica y motor del arnés— o la suite completa.

La ejecución directa de la suite completa puede realizarse con:

```
python -m pytest -q
```

Resultado registrado al cierre de esta actualización: **613 pruebas aprobadas**. Los resultados corresponden al estado del repositorio etiquetado como `hito-2` (24 de noviembre de 2026); el historial de cambios conserva cada versión intermedia.


# 9. DESARROLLO E INCREMENTOS

El Hito 0 consolidó el estado *As-Is* del arnés y de los bancos de prueba; el incremento del Hito 1 agregó el catálogo normativo, las políticas, la compuerta de validación y la evaluación experimental; el incremento del Hito 2 agrega la calibración ciega del detector, la ampliación de la cobertura normativa y el gate de evidencia documental. Los componentes se describen según su estado verificable, distinguiendo los mecanismos operativos de las capacidades que permanecen en desarrollo.

## 9.1 Objetivo y alcance del incremento As-Is

El Incremento 0 tiene como objetivo establecer una línea base técnica: separar el motor del arnés de las aplicaciones analizadas, modularizar las pruebas, formalizar el catálogo de controles y construir la infraestructura necesaria para ejecutar experimentos comparativos. También documenta las limitaciones del análisis de contexto, de las reglas declarativas y de la evaluación realizada.

## 9.2 Funcionalidades implementadas y evidencia de integración

| Componente del incremento | Estado | Evidencia |
| - | :-: | - |
| **Backend clínico transaccional** | Operativo | Modelos de datos, endpoints REST y esquemas de validación. |
| **Suite de pruebas modular** | Operativo | 613 pruebas: 592 del arnés y 21 de la aplicación clínica. |
| **Motor de grafos parametrizable** | Operativo | Extracción del grafo estructural sobre directorios configurables. |
| **Analizador de linaje y flujos** | Operativo | Identificación de relaciones y de posibles flujos entre origen y destino. |
| **Persistencia local** | Operativo | Base de datos embebida para estructuras y hallazgos. |
| **Recorrido de poda topológica (`k ≤ 2`)** | Operativo | Selección de vecindades del grafo; el contexto puede serializar archivos completos. |
| **Reglas operativas permanentes** | Operativo como directivas | Cuatro directivas permanentes; su presencia no constituye verificación determinista por sí sola. |
| **Pipeline de procedimientos (01 a 12)** | Documentado y disponible | Doce procedimientos de desarrollo y tres de cumplimiento. |
| **Catálogo normativo y políticas** | Operativo | Catálogo de 37 controles y los motores que lo aplican. |
| **Motor de validación y compuerta** | Operativo | Bloqueo de los hallazgos configurados como bloqueantes. |
| **Mitigación normativa en disco** | Probada en escenarios definidos | Remediación documentada en el código del banco de pruebas, incluido el enmascaramiento en bitácoras. |
| **Ejecutor de pruebas por área** | Operativo | Selección de áreas y ejecución integral. |
| **Infraestructura experimental** | Operativa | Bancos de prueba, paquete de tareas, reportes de ejecución y notas de investigación. |


## 9.3 Decisiones técnicas y alternativas descartadas

1. **Desacoplamiento del arnés y las aplicaciones:** se separó el núcleo del arnés de las aplicaciones evaluadas y se parametrizaron los directorios de escaneo para reducir dependencias de rutas fijas.

2. **Modularización de la suite de pruebas:** se organizó la suite en 613 pruebas distribuidas entre el motor del arnés y la aplicación clínica, con ejecución selectiva por marcadores y el ejecutor de pruebas del proyecto.

3. **Descarte de hooks invasivos:** se evaluó incorporar hooks automáticos de pre-ejecución y se descartaron por la complejidad añadida respecto del beneficio observado.

4. **Descarte de servidores de grafos pesados:** se priorizó SQLite embebido y estructuras ligeras frente a introducir una base de datos de grafos distribuida como requisito.

5. **Modelo híbrido de análisis y remediación:** se utiliza análisis estático para detectar patrones, contexto del repositorio para orientar la propuesta de corrección y Pytest para validar cambios. Los mecanismos de reversión se aplican cuando la validación configurada falla.

6. **Compuerta asesora frente a enforcement externo:** en el experimento de dosis, la configuración `rules_skills_gate` mostró una reducción de violaciones confirmadas. El bucle externo de corrección de `rules_skills_gate_enforced` no se activó en las ejecuciones reportadas. En esta muestra, la compuerta asesora obtuvo un resultado comparable con menor complejidad operativa.

## 9.4 Problemas encontrados y deuda técnica pendiente

Se declara explícitamente el estado de la deuda técnica:

1. **Validación del pipeline de *skills* en el IDE:** las doce *skills* procedimentales están documentadas e íntegras, pero su validación formal en el flujo completo del IDE permanece en curso.

2. **Orquestación autónoma de roles:** los roles (*planner*, *code reviewer*, *security reviewer* y *compliance auditor*) están definidos a nivel de especificaciones y directivas; los ciclos cerrados autónomos todavía operan bajo supervisión humana.

3. **Potencia estadística:** el experimento formal de tres brazos quedó subpotenciado para el resultado binario (tres pares discordantes; *p* = 0,25). El experimento de dosis obtuvo un contraste significativo, pero sigue limitado a un modelo, cuatro tareas y veinte pares por comparación.

4. **Adjudicación única:** las tareas, pruebas, detector y oráculo comparten autoría. Falta incorporar un adjudicador humano; el evaluador independiente descrito en la sección 10.5 es un modelo de la misma familia.

5. **Falsos positivos de Semgrep:** se documentaron falsos positivos relacionados con pseudonimización y borrado con retención. Deben mantenerse registrados como limitaciones del oráculo independiente.

6. **Cobertura de modelos:** los resultados principales corresponden a `opencode-go/deepseek-v4.1-flash`. La corrida con Cursor es provisional y no se agrupa con los resultados principales.

7. **Contexto a nivel de archivo:** aunque el grafo permite seleccionar vecindades topológicas, el contexto puede contener archivos completos. La selección a nivel de símbolos todavía requiere desarrollo y evaluación.

8. **Cobertura del catálogo:** 11 de 37 controles no tienen detector todavía. Seis de ellos se exigen como evidencia documental verificable (`harness-evidence`) y cinco permanecen como gaps declarados (`implemented: false` con `gap_reason`), no como silencio.

## 9.5 Relación con los objetivos del proyecto

El incremento actual proporciona evidencia de avance en los cinco objetivos:

- **OE1:** se dispone del catálogo de doce *skills* y de las reglas estructuradas; la validación integral en IDE sigue en progreso.

- **OE2:** se dispone de un motor de grafos y selección topológica acotada; falta consolidar selección a nivel de símbolos y medir su efecto aislado.

- **OE3:** el núcleo del arnés está desacoplado y cuenta con 592 pruebas propias; la orquestación autónoma de roles sigue bajo supervisión.

- **OE4:** se formalizó el catálogo de controles, el motor de políticas, la validación y la compuerta de *pre-commit*.

- **OE5:** se ejecutaron cuatro experimentos y se documentaron sus resultados, costos y limitaciones. La evidencia de dosis muestra un efecto estadísticamente significativo de la compuerta sobre las violaciones confirmadas en la muestra evaluada; el experimento de preservación funcional y costo muestra que ese efecto no se traduce en mejora funcional y que el costo es sustancial.

## 9.6 Incremento del Hito 2: cobertura normativa, calibración y gate de evidencia

### Objetivo y alcance

El incremento del Hito 2 no agrega funcionalidades al agente: cierra tres preguntas que el Hito 1 dejó abiertas. ¿El detector funciona fuera de los casos para los que fue escrito? ¿Qué aristas de la ley quedan sin control y por qué? ¿Cuánto cuesta la gobernanza en el ciclo de desarrollo?

### Funcionalidades implementadas

| Capacidad | Estado | Evidencia en el repositorio |
| - | :-: | - |
| **Familia `code_hygiene`** | Operativa | Cinco detectores nuevos: caché de datos de salud sin cifrado, campo ORM sin cifrado, ruta clínica sin autenticación, export clínico no estructurado y ruta con datos personales sin autenticación (el motor de políticas). |
| **Cobertura de 30 aristas** | Documentada y verificada | Cada arista de la ley clasificada en detectar, riesgo, evidencia o manual, con su estado. |
| **Gate de evidencia** | Operativo | Manifiesto con artefacto, responsable y vencimiento; seis controles documentales lo exigen desde el catálogo. |
| **Completitud del índice** | Operativa | La ausencia de una ruta de derechos es violación solo cuando el análisis cubre el árbol completo; el conjunto de cambios declara esa condición. |
| **Herramientas de validación** | Operativas | Triage sobre código real, muestreo ciego con kappa de Cohen y comparación con reglas Semgrep. |
| **Corrección del catálogo** | Verificada | `CORE-CHECK-003` declaraba una categoría de dato inexistente, de modo que su detector no podía dispararse; la revisión del catálogo se corrigió respecto del alcance real de la compuerta. |

### Decisiones técnicas y alternativas descartadas

1. **No promover todos los avisos a violación:** los cinco controles en modo riesgo (`privacy.rights_reachability`, `consent_transparency`, `retention_minimization`, `minors_and_sensitive` y `third_party_transfers`) detectan un riesgo potencial, no una violación demostrada. Promoverlos habría bloqueado commits legítimos y entrenado al equipo a saltear la compuerta. La excepción es `rights_reachability`, que sube a violación únicamente con índice completo.

2. **Evidencia en integración continua, no en el hook:** que falte una evaluación de impacto es un estado del repositorio, no una propiedad del commit que se revisa. Bloquear cada commit por eso habría producido el mismo efecto de saturación.

3. **Canales nuevos como funcionalidad con prueba, no como más rondas ciegas:** cerrada la calibración con una sonda de convergencia en 42/42, los tres canales siguientes (modelo de respuesta importado, exclusión calculada, sinks de cookie y cabecera) se incorporaron al corpus de regresión con pruebas, en lugar de repetir rondas de 42 casos.

4. **Sin detección donde no hay prueba posible:** las aristas documentales y semánticas no reciben un detector que simule un juicio jurídico. Se exige el artefacto o se firma una lista de verificación.

### Problemas encontrados y correcciones

1. **Compuerta inutilizable por latencia:** el resumen interprocedural de efectos (`_call_effects`) marcaba progreso en cada acierto en lugar de hacerlo solo cuando el conjunto crecía, de modo que el punto fijo ejecutaba siempre las 146 iteraciones completas. Sobre un módulo de 3 000 líneas implicaba 244 segundos por control y cerca de 15 minutos para el hook de *pre-commit*. Corregida la condición de corte, el costo bajó a 6,5 segundos por control y 76 segundos para el hook completo.

2. **Falso positivo crítico sobre el propio código:** el detector interpretaba la iteración de una lista de nombres de campo como exportación de columnas, lo que producía tres hallazgos `CRITICAL` sobre el módulo de políticas por dimensión y bloqueaba cualquier commit que tocara ese archivo. La corrección exige que la variable del bucle seleccione una columna (`row[c]` o `getattr(row, c)`).

3. **Ruta de salud clasificada como ruta clínica:** un endpoint `/health` se reportaba como endpoint clínico sin control de acceso. Los *healthchecks* se excluyen explícitamente.

4. **Categoría de dato inexistente:** `CORE-CHECK-003` declaraba `PERSONAL_DATA`, que no existe en el catálogo, por lo que su detector no podía dispararse nunca. Es el tipo de defecto que un informe de cobertura puede ocultar: el control figuraba como implementado.

### Relación con los objetivos

- **OE4:** la cobertura pasa de 21 a 26 controles con detector y las 30 aristas de la ley quedan clasificadas con su modo y su estado; las documentales dejan de ser un gap silencioso y pasan a ser un requisito verificable.
- **OE5:** la evaluación se amplía con dos bloques nuevos —calibración ciega y costo en el ciclo— y con una medición de acuerdo entre etiquetas.
- **OE1, OE2 y OE3:** sin cambios de alcance en este incremento.


# 10. PRUEBAS, EVALUACIÓN Y RESULTADOS

## 10.1 Protocolo experimental

Para evaluar el efecto de las reglas, las *skills* y las compuertas de cumplimiento, se ejecutaron cuatro experimentos. Los dos primeros comparan configuraciones sobre el banco de comercio electrónico con pruebas ocultas y reglas Semgrep independientes como oráculo. El tercero mide la calidad del detector con corpus ciegos sellados. El cuarto mide el costo y la preservación funcional sobre el paquete de diez trampas de protocolo. El modelo se fijó en `opencode-go/deepseek-v4.1-flash` y la configuración se mantuvo constante dentro de cada comparación.

- **Experimento formal:** doce tareas × tres brazos (`baseline`, `harness`, `harness_compliance`) × tres repeticiones = **108 ejecuciones**.

- **Experimento de dosis:** cinco brazos (`baseline`, `rules`, `rules_skills`, `rules_skills_gate`, `rules_skills_gate_enforced`) × cuatro tareas × cinco repeticiones = **100 ejecuciones**.

- **Calibración ciega:** 21 rondas selladas con autores independientes, **907 casos** en total, evaluados una sola vez cada uno y reportados antes de cualquier corrección.

- **Preservación funcional y costo:** diez trampas × dos brazos × tres repeticiones = **60 ejecuciones**, más seis repeticiones de control tras unificar la capa de evidencia.

- **Replicación aislada:** tres brazos (`baseline`, `gate_only`, `rules_skills_gate`) × cuatro tareas × seis repeticiones = **72 ejecuciones**, con el repositorio fuera del entorno del agente.

La suite de pruebas del repositorio se ejecutó como verificación de preservación funcional y registró **613 pruebas aprobadas**.

**Definición de las métricas.** Para cada control se cuenta la matriz de confusión sobre los casos etiquetados: verdaderos positivos (VP), falsos positivos (FP), falsos negativos (FN) y verdaderos negativos (VN). Precisión = VP/(VP+FP); exhaustividad = VP/(VP+FN); exactitud = (VP+VN)/total. Los intervalos son de Wilson al 95 %, elegidos porque se comportan mejor que el intervalo normal con muestras pequeñas y con proporciones cercanas a 0 o a 1.

**Alcance de la evaluación:** estos experimentos comparan configuraciones de reglas, *skills* y compuertas de cumplimiento. No aíslan el efecto causal del contexto seleccionado mediante grafos; esa evaluación requiere un diseño factorial posterior.

## 10.2 Resultados obtenidos

### Experimento formal (12 tareas, 3 brazos)

| Brazo | Pruebas ocultas aprobadas | Hallazgos Semgrep | Confirmadas | Comportamiento | Latentes | Limpias | Ciclo medio | Tokens |  |
| - | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| `baseline` | 33/36 | 6 | 3 | 0 | 2 | 31 | 161,8 s | 43,5 M |  |
| `harness` | 32/36 | 5 | 3 | 1 | 2 | 30 | 176,1 s | 47,8 M |  |
| `harness_compliance` | 34/36 | 0 | 0 | 2 | 0 | 34 | 179,4 s | 55,5 M |  |


- **Violaciones confirmadas:** 3 en `baseline`, 3 en `harness` y 0 en `harness_compliance`.

- **Tiempo de ciclo:** la diferencia pareada entre `harness_compliance` y `baseline` fue de +17,56 segundos (DE = 109,26; prueba de signos, *p* = 0,62). No se detectó una diferencia estadísticamente significativa en esta muestra.

- **Tokens:** `harness_compliance` utilizó 55,5 millones frente a 43,5 millones en `baseline` (+28 %).

- **Potencia estadística:** para el resultado binario hubo tres pares discordantes; la prueba de McNemar produjo *p* = 0,25. El experimento formal no permite concluir un efecto estadísticamente significativo sobre ese resultado.

- **Adjudicación de comportamiento:** las dos fallas de comportamiento de `harness_compliance` son T05 (anonimización con solicitud de baja); se adjudicaron como no violaciones y el test se corrigió después.

### Experimento de dosis (4 tareas, 5 brazos)

En la siguiente tabla, **pruebas ocultas aprobadas** indica el número de aprobaciones sobre 20 ejecuciones. Las categorías de clasificación corresponden al resultado por ejecución.

| Brazo | Confirmadas | Comportamiento | Latentes | Limpias | Pruebas ocultas aprobadas | Hallazgos Semgrep | Llamadas a compuerta | Ciclo medio |
| - | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| `baseline` | 8 | 1 | 2 | 9 | 11/20 | 11 | 0 | 87,2 s |
| `rules` | 7 | 3 | 1 | 9 | 10/20 | 8 | 0 | 65,5 s |
| `rules_skills` | 3 | 4 | 0 | 13 | 13/20 | 3 | 0 | 94,3 s |
| `rules_skills_gate` | **0** | 0 | 3 | 17 | **20/20** | 4 | 25 | 133,6 s |
| `rules_skills_gate_enforced` | **0** | 2 | 0 | 18 | **18/20** | 0 | 25 | 155,0 s |


**Nota:** la tabla usa los conteos corregidos tras el test T34. Los conteos crudos y el desglose por tipo de fallo están en las notas de resultados del experimento de dosis; los 2 T31 404 de `enforced` son completitud, no privacidad.

Los hallazgos Semgrep son conteos de detecciones y no deben interpretarse automáticamente como equivalentes uno a uno a ejecuciones clasificadas: pueden existir varias detecciones en una misma ejecución y falsos positivos que requieren adjudicación.

### Contrastes pareados contra `baseline` (20 pares)

| Brazo | Diferencia de tiempo | Pares discordantes — violaciones confirmadas | McNemar, violaciones confirmadas | Pares discordantes — cualquier falla | McNemar, cualquier falla |
| - | -: | -: | -: | -: | -: |
| `rules` | −21,8 s | 3/2 | *p* = 1,0 | 2/1 | *p* = 1,0 |
| `rules_skills` | +7,1 s | 6/1 | *p* = 0,125 | 4/1 | *p* = 0,375 |
| `rules_skills_gate` | +46,3 s | **8/0** | **p = 0,0078** | **12/0** | **p = 0,0005** |
| `rules_skills_gate_enforced` | +67,8 s | **8/0** | **p = 0,0078** | 9/1 | *p* = 0,021 |


En los contrastes `8/0`, los ocho pares discordantes favorecen a la configuración con compuerta. El resultado de `rules_skills_gate` muestra una reducción de ocho a cero violaciones confirmadas en la muestra evaluada.

**Evidencia de desacoplamiento y remediación en disco:**

- El arnés escaneó la aplicación de forma externa e identificó emisiones de RUT, correo, tokens y datos de tarjeta hacia bitácoras y respuestas de API, relacionadas con CWE-532 y CWE-200.

- La compuerta se invocó 25 veces en cada uno de los dos brazos que la incorporaban.

- La suite consolidada del repositorio registró 613 pruebas aprobadas. Este resultado aporta evidencia de preservación funcional para el estado verificado, sin equivaler a una certificación exhaustiva de ausencia de regresiones en cualquier entorno.

**Nota de adjudicación de T34:** la prueba T34 rechazaba el nombre `api_key` aunque su valor estuviera vacío o enmascarado. Era un artefacto del test, no una violación. Corregido el test, los aprobados corregidos son **20/20** en `rules_skills_gate` y **18/20** en `enforced`; los dos restantes de `enforced` son T31 con 404 (completitud), no privacidad. Las violaciones confirmadas no se re-puntuaron: siguen en **0**. La tabla de dosis usa los conteos corregidos de pruebas ocultas; los conteos crudos y el desglose por tipo de fallo están en las notas de resultados del experimento de dosis.

## 10.3 Calibración del detector: por qué se midió y qué se concluyó

### Por qué

De todos los componentes del arnés, el detector es el único que decide: cada hallazgo que emite bloquea o no bloquea un commit. Su calidad no es un detalle de implementación, sino la condición de posibilidad de todo lo demás. Una compuerta imprecisa produce falsos positivos que el desarrollador aprende a ignorar; una compuerta incompleta produce falsos negativos que nadie ve. En ambos casos el resultado es el mismo: el gate deja de proteger y nadie lo nota.

El Hito 1 no podía responder esta pregunta. Su evidencia eran 22 casos curados escritos por el mismo autor del detector, y un corpus así mide memoria, no generalización. Para medir generalización hace falta un corpus que el autor del detector no haya podido ajustar.

### Qué se concluyó

1. **El detector converge en el alcance actual.** Una sonda con enunciado neutral, sin énfasis en ningún canal, obtuvo 42/42 en la primera corrida. Es la señal que las rondas anteriores no podían dar: sin un canal nuevo que descubrir, el detector se mantuvo.

2. **La calidad medida es alta, pero el intervalo no permite exagerarla.** La ronda de mayor tamaño, con 84 casos, dio 82/84: precisión 0,955 [0,849; 0,987] y exhaustividad 1,000 [0,916; 1,000]. Un 42/42 habría permitido una exhaustividad real de 0,845; un 82/84 permite 0,916. Con muestras de este tamaño, un resultado perfecto sigue siendo compatible con una tasa de fallo no despreciable.

3. **La mejora provino del detector y no de un corpus complaciente.** Las rondas que introdujeron un canal nuevo —plantillas y *streams*, el contrato del modelo de respuesta, la exclusión calculada, los *sinks* de cookie y cabecera— hicieron caer la exhaustividad hasta 0,524 y después recuperarla. Un corpus escrito para agradar al detector no produce ese patrón: produce puntajes estables. La primera ronda, además, reveló diez fallos sobre modismos que el corpus curado no tenía: borrados de ORM, vistas de administración basadas en clases, `log.info`, `private_key` y enmascaramiento manual con f-string.

4. **Los fallos que quedan tienen forma reconocible.** Los dos falsos positivos de la última ronda fueron una rama enmascarada con el literal `'***'` y un campo `last_password_change` leído como credencial. Ambos se corrigieron después de la medición y el conjunto quedó en 84/84 como regresión.

5. **El método tiene un techo que conviene declarar.** 907 casos en 21 rondas cubren siete controles y miden módulos de 20 a 55 líneas. Eso no es un repositorio. La sección 10.6 reporta el primer acercamiento a código real, y ahí aparece el único falso negativo que sigue abierto.

### La serie completa

La tabla siguiente es la evidencia de esas conclusiones. Cada fila es una ronda; el número reportado es el previo a cualquier corrección.

| Ronda | Casos | Aciertos (pre-fix) | Precisión [IC 95 %] | Exhaustividad [IC 95 %] |
| :-: | :-: | :-: | - | - |
| 1 | 36 | 26/36 | 0,867 [0,621; 0,963] | 0,619 [0,409; 0,792] |
| 2 | 42 | 37/42 | 0,944 [0,742; 0,990] | 0,810 [0,600; 0,923] |
| 3 | 38 | 25/38 | 1,000 [0,676; 1,000] | 0,364 [0,197; 0,570] |
| 4 | 35 | 31/35 | 1,000 [0,806; 1,000] | 0,800 [0,584; 0,919] |
| 5 | 42 | 32/42 | 0,824 [0,590; 0,938] | 0,667 [0,454; 0,828] |
| 6 | 42 | 37/42 | 0,944 [0,742; 0,990] | 0,810 [0,600; 0,923] |
| 7 | 42 | 34/42 | 0,741 [0,553; 0,868] | 0,952 [0,773; 0,992] |
| 8 | 42 | 34/42 | 0,842 [0,624; 0,945] | 0,762 [0,549; 0,894] |
| 9 | 42 | 31/42 | 0,708 [0,508; 0,851] | 0,810 [0,600; 0,923] |
| 10 | 42 | 38/42 | 0,947 [0,754; 0,991] | 0,857 [0,654; 0,950] |
| 11 | 42 | 32/42 | 0,789 [0,567; 0,915] | 0,714 [0,500; 0,862] |
| 12 | 42 | 35/42 | 0,889 [0,672; 0,969] | 0,762 [0,549; 0,894] |
| 13 | 42 | 28/42 | 0,765 [0,527; 0,904] | 0,565 [0,368; 0,744] |
| 14 | 42 | 37/42 | 1,000 [0,816; 1,000] | 0,773 [0,566; 0,899] |
| 15 | 42 | 35/42 | 1,000 [0,785; 1,000] | 0,667 [0,454; 0,828] |
| 16 | 42 | 28/42 | 0,733 [0,480; 0,891] | 0,524 [0,324; 0,717] |
| 17 | 42 | 34/42 | 0,842 [0,624; 0,945] | 0,762 [0,549; 0,894] |
| 18 | 42 | 31/42 | 0,917 [0,646; 0,985] | 0,524 [0,324; 0,717] |
| 19 | 42 | 30/42 | 0,680 [0,484; 0,828] | 0,810 [0,600; 0,923] |
| 20 | 42 | 42/42 | 1,000 [0,845; 1,000] | 1,000 [0,845; 1,000] |
| 21 | 84 | 82/84 | 0,955 [0,849; 0,987] | 1,000 [0,916; 1,000] |

**Cómo leer la serie.** Las 21 rondas no son una muestra única: cada una corrigió lo que la anterior expuso, de modo que los 907 casos se reportan como serie y no como muestra agregada. El único conjunto que puede leerse como muestra independiente es el de la última ronda sellada, con 84 casos, y es el que sostiene las cifras de precisión y exhaustividad citadas en el resumen.

### Comparación con reglas Semgrep sobre el mismo corpus

El corpus sellado permite una comparación que la sección 5.2 solo podía plantear en términos cualitativos: qué obtiene un motor de reglas estático sobre los mismos 84 casos y con las mismas etiquetas.

Se ejecutaron las quince reglas Semgrep que el proyecto ya utiliza como oráculo, mapeadas a los siete controles evaluados mediante una herramienta de comparación incluida en el repositorio:

| Control | Aciertos Semgrep | Precisión | Exhaustividad | Detector calibrado |
| - | :-: | - | - | :-: |
| `v2.admin_exposure` | 7/12 | 1,000 | 0,167 | 12/12 |
| `v2.api_key` | 7/12 | 1,000 | 0,167 | 12/12 |
| `v2.billing_retention` | 6/12 | — | 0,000 | 12/12 |
| `v2.credential_response` | 8/12 | 1,000 | 0,333 | 12/12 |
| `v2.customer_hard_delete` | 9/12 | 1,000 | 0,500 | 12/12 |
| `v2.log_pii` | 7/12 | 0,571 | 0,667 | 12/12 |
| `v2.reset_token` | 7/12 | 1,000 | 0,167 | 12/12 |
| **Total** | **51/84** | **0,800 [0,548; 0,930]** | **0,286 [0,172; 0,436]** | **82/84** |

Dos lecturas importan más que el total.

`v2.billing_retention` no acierta ningún caso: la regla reconoce `delete from orders`, pero no puede comparar el plazo de retención contra el umbral, de modo que la condición que define la violación queda fuera de su alcance expresivo.

`v2.log_pii` muestra el patrón inverso: acierta cuatro de las seis violaciones y produce tres falsos positivos sobre los seis casos limpios. Una expresión regular encuentra la palabra sensible, pero no distingue el dato de la variable que lo contiene ni la llamada que lo enmascara.

**Qué mide y qué no.** La comparación mide las reglas, no el techo del motor. Las quince reglas se escribieron contra los modismos del banco Dumbo y no contra este corpus; Semgrep dispone de modo *taint* y de un registro de reglas de la comunidad, y un esfuerzo dedicado elevaría la exhaustividad. Lo que el resultado sostiene es más acotado y más útil: un conjunto de reglas de patrones cubre los casos que anticipa, y el corpus ciego mide exactamente lo que no anticipó. La diferencia observada no proviene del motor —que es maduro y en seis de los siete controles no produjo falsos positivos— sino de la calibración y del análisis de flujo.

## 10.4 Resultados del experimento de preservación funcional y costo

Este experimento responde una pregunta que los experimentos de dosis no responden: si el arnés mejora la privacidad, ¿mejora también el trabajo, o solo lo encarece?

| Métrica agregada (30 corridas por brazo) | Con compuerta | Línea base |
| - | -: | -: |
| Pruebas ocultas aprobadas | 30/30 | 30/30 |
| Verificación de evidencia | 30/30 | 30/30 |
| Mediana de tiempo de ciclo | 274,6 s | 110,0 s |
| Mediana de tokens por corrida | 1.807.683 | 548.913 |
| Mediana de herramientas por corrida | 43,5 | 25,5 |
| Llamadas a la compuerta | 53 | 0 |
| Violaciones de política, alcance o privacidad | 0 | 0 |
| Cambios no solicitados | 0 | 0 |

- **Completitud funcional saturada:** el modelo resolvió las diez trampas sin el arnés. La prueba oculta pasó 30/30 en ambos brazos. El experimento no puede discriminar porque no hay margen de mejora.
- **Sin ventaja de evidencia:** la diferencia inicial en la verificación de evidencia (30/30 frente a 28/30) provenía de una inconsistencia del propio arnés —dos mecanismos distintos calculaban los destinatarios de terceros—, no del agente. Unificada la fuente y repetidas las corridas de D03, ambos brazos quedaron en 30/30. **El experimento corregido no muestra ventaja funcional ni de evidencia para el brazo con compuerta; solo sobrevive la diferencia de costo.**
- **El costo es estadísticamente significativo:** el brazo con compuerta fue más lento en 10 de 10 tareas (prueba de signos bilateral, *p* = 0,00195). El tiempo de ciclo se multiplicó por 2,5 y los tokens por 3,3.
- **Ningún brazo produjo violaciones:** la compuerta no se activó como corrección porque no había nada que corregir en este paquete. Su valor medido aquí es de auditoría, no de prevención.

**Por qué el costo no coincide con el del experimento de dosis.** El experimento de dosis reportó 2,3 veces los tokens y 46,3 segundos adicionales por tarea sobre cuatro tareas del banco de comercio electrónico; este experimento reporta 2,5 veces el tiempo de ciclo y 3,3 veces los tokens sobre diez trampas de protocolo. No son la misma medición: cambian las tareas, el tamaño del cambio pedido y el punto de partida de cada brazo. Lo que se sostiene en ambos es la dirección —la gobernanza cuesta más— y el orden de magnitud; el valor exacto depende de la tarea.

El resultado delimita el aporte del arnés: en tareas donde el modelo ya cumple, la gobernanza cuesta y no mejora el resultado. El beneficio aparece donde el modelo falla por omisión, que es lo que midieron los experimentos de dosis.

## 10.5 Acuerdo entre etiquetas

Para estimar la reproducibilidad de las etiquetas del corpus se extrajo una muestra estratificada de 30 casos —15 violaciones y 15 casos limpios— y se entregó a un segundo evaluador, sin acceso al corpus ni a las etiquetas originales. El evaluador reprodujo **30/30** etiquetas, con un **kappa de Cohen de 1,000**.

El alcance es acotado: ese evaluador es un modelo de la misma familia en un rol distinto, no una persona, y su independencia es de información, no de sesgo inductivo. Respalda que las etiquetas no dependen de una redacción particular del enunciado; no reemplaza la adjudicación humana.

## 10.6 Triage sobre código real

La calibración usa módulos aislados. Para observar el comportamiento sobre código multi-archivo se ejecutó la compuerta sobre una aplicación real del repositorio (nueve módulos, ~61 KB) y sobre trece variantes del paquete de trampas con defectos sembrados y mutaciones documentadas.

- **Aplicación limpia:** **0 hallazgos**. La revisión manual confirmó que es un verdadero negativo y no un fallo por omisión: la aplicación anonimiza en la retención, filtra el marketing por consentimiento y no registra datos personales.
- **Trece variantes:** **13/13** correctas frente a los detectores heredados. Con los controles `v2.*`, las tres variantes limpias no produjeron hallazgos, y se detectaron las dos variantes con defectos `v2` relevantes (exposición en bitácora y credenciales).
- **Un falso negativo confirmado:** una variante envía el RUT a una bitácora a través de una función auxiliar ubicada en otro módulo. El detector no sigue el flujo entre archivos en ese caso. Es el límite *cross-module* ya documentado, ahora con evidencia sobre código real. La escala es la limitación principal de esta medición: los trabajos comparables evalúan entre cuatro y quince aplicaciones \[20\]\[21\]\[22\], y este informe evalúa una.

## 10.7 Cobertura normativa

| Modo | Aristas | Significado |
| - | -: | - |
| Detectar | 15 | Finding con archivo y línea; bloquea si la severidad es alta y el estado es violación. |
| Detectar como riesgo | 5 | Se reporta sin bloquear: un índice parcial no prueba una violación de derechos o de retención. |
| Exigir evidencia | 6 | El merge se bloquea si falta el artefacto (EIPD, registro de incidentes, FHIR, aislamiento de salud, PCI, retención tributaria). |
| Manual | 4 | Lista de verificación firmada por una persona, con el artículo citado. |
| **Total** | **30** | Aristas derivadas de la Ley N° 21.719 en el pack sectorial. |

Sobre el catálogo completo (37 controles), **26 tienen detector determinista**, **6 se exigen como evidencia** y **5 permanecen como gap declarado** con su motivo. La distinción entre detectar y exigir evidencia no es una excusa de cobertura: es la consecuencia de que un detector solo puede afirmar lo que una prueba en el código sostiene.

Las 15 aristas en modo *detectar* incluyen `CL-DATAPROT-001`, que el pack declara como gap porque la fuga la evalúa el detector de `CORE-CHECK-002`. Por eso el pack tiene 19 aristas de la ley implementadas (14 en modo detectar y 5 en modo riesgo) más 7 detectores `v2.*`, que suman los 26 controles con detector.

## 10.8 Replicación del experimento de dosis con el entorno aislado

El contraste de dosis se midió en octubre. Para saber si se sostiene, se repitieron las mismas cuatro tareas con el modelo actual y con el entorno aislado: el agente no puede leer las pruebas ocultas ni las reglas del oráculo. Seis repeticiones por tarea y brazo: 24 corridas por brazo, 72 en total, ninguna contaminada según el registro de comandos.

| Brazo | Corridas | Confirmadas | Tasa [IC 95 %] | Latentes | Limpias | Ciclo mediana | Tokens mediana |
| - | -: | -: | - | -: | -: | -: | -: |
| `baseline` | 24 | 6 | 0,250 [0,120; 0,449] | 1 | 17 | 176,6 s | 986.284 |
| `gate_only` | 24 | 0 | 0,000 [0,000; 0,138] | 3 | 21 | 301,5 s | 2.759.781 |
| `rules_skills_gate` | 24 | 1 | 0,042 [0,007; 0,202] | 5 | 18 | 314,0 s | 2.932.218 |

- **Las seis violaciones de la línea base:** tres en T33, con el token de reseteo en la URL de redirección; dos en T35, con el token de sesión en la bitácora; una en T31, con un borrado dentro de la retención. El arnés completo cometió una, en T31. T34 no falló en ningún brazo.
- **Contra la línea base:** seis pares discordantes a favor de `gate_only` (McNemar, *p* = 0,031) y seis a uno a favor del arnés completo (*p* = 0,125).
- **Entre los dos brazos con compuerta no hay diferencia:** un par discordante (*p* = 1,0). La capa procedural no agrega un efecto medible.
- **El costo es real:** 1,7 veces el tiempo de ciclo y 2,8 veces los tokens para `gate_only`; 1,8 y 3,0 para el arnés completo. Tiempos agotados: cuatro, tres y uno.
- **Ninguna corrida leyó el benchmark:** el registro de comandos de *shell* lo confirma.

**Lectura.** La compuerta reduce las violaciones de forma estadísticamente significativa en la comparación primaria, y la capa procedural no agrega nada medible. La dirección coincide con octubre, que dio ocho de veinte a cero (*p* = 0,0078).

**Sensibilidad.** Excluyendo las ocho corridas que agotaron el tiempo límite, el contraste principal queda en cinco a cero (*p* = 0,0625). La dirección no depende de los tiempos agotados; la significancia sí.

**Qué había pasado antes.** Una corrida previa mostró cero en los tres brazos. La causa fue una fuga: la raíz del repositorio se exportaba al entorno para que la compuerta importara el motor, y el agente podía explorar el benchmark con la *shell*. Se corrigió con un paquete por corrida que contiene solo el motor y el catálogo.

## 10.9 El mismo experimento con un segundo modelo

Para probar si el efecto depende del modelo, se repitió el diseño con `opencode-go/gpt-6-luna`, del mismo proveedor y con un costo por corrida comparable. Tres repeticiones por tarea y brazo: 36 corridas, ninguna contaminada según el registro de comandos.

| Brazo | Corridas | Confirmadas | Comportamiento | Latentes | Limpias | Ciclo mediana | Tokens mediana |
| - | -: | -: | -: | -: | -: | -: | -: |
| `baseline` | 12 | 6 | 0 | 1 | 5 | 96,4 s | 325.034 |
| `gate_only` | 12 | 2 | 0 | 2 | 8 | 267,4 s | 491.378 |
| `rules_skills_gate` | 12 | 2 | **7** | 0 | 3 | 71,3 s | 134.298 |

- **La compuerta vuelve a reducir las violaciones:** de seis a dos, con cuatro pares discordantes (*p* = 0,125). La dirección se repite; la potencia, con doce pares, no alcanza.
- **El arnés completo produjo siete fallas de comportamiento:** en la mayoría de las corridas el agente no escribió código. En T34, las tres repeticiones terminaron con cero archivos modificados y unos 69 mil tokens: exploró, escribió un plan y terminó sin implementar.
- **El contraste entre los dos brazos con compuerta es 0 a 7** a favor de `gate_only` (*p* = 0,0156).

**Lectura.** El efecto de la compuerta no depende de una familia de modelos: se repite en las dos. La capa procedural, en cambio, sí: con el primer modelo fue neutra y con el segundo interfirió con la implementación. Eso convierte "no aporta" en "puede perjudicar", y refuerza que el aporte está en la compuerta y no en el pipeline.

**Límite.** Tres repeticiones por tarea y un solo banco. Las fallas de comportamiento son consistentes entre tareas, pero podrían reflejar un bucle de planificación propio de este modelo.

### La capa procedural estaba escrita para una conversación

Las doce skills y las reglas permanentes piden preguntar y esperar confirmación. En una corrida sin nadie del otro lado eso detiene al agente: seis de las siete fallas de comportamiento terminaron con cero archivos y dos no ejecutaron ninguna herramienta. Para separar redacción de alcance se agregó un brazo idéntico al completo con una cláusula de modo autónomo: sin respuesta del usuario, continuar con la opción más conservadora, dejar el supuesto escrito y no detenerse.

| Brazo | Confirmadas | Comportamiento | Limpias | Cero archivos | Tokens mediana | Ciclo mediana | Timeouts |
| - | -: | -: | -: | -: | -: | -: | -: |
| `rules_skills_gate` | 2 | 7 | 3 | 8 | 145.557 | 73 s | 0 |
| `rules_skills_headless` | 0 | 1 | 8 | 1 | 1.113.521 | 412 s | 3 |

- **Las fallas de comportamiento caen de siete a una:** seis pares discordantes, todos a favor del brazo con la cláusula (*p* = 0,031).
- **El costo se multiplica:** 7,6 veces los tokens y 5,6 veces el ciclo, con tres tiempos agotados.

**Lectura.** Las skills no están mal escritas: están escritas para una sesión con una persona. Con una cláusula de una frase el agente implementa. El problema era de modo, no de redacción. Lo que sigue sin demostrarse es que la capa procedural aporte sobre la compuerta sola: con la cláusula funciona, pero cuesta más del doble que `gate_only` y no reduce las violaciones de forma medible.

## 10.10 Análisis e interpretación de resultados

- **Las reglas por sí solas no mostraron un efecto detectable:** la comparación `rules` frente a `baseline` no presentó una diferencia estadísticamente significativa en las violaciones confirmadas (tres frente a dos pares discordantes; *p* = 1,0). Esto indica que documentar reglas permanentes no fue suficiente para modificar el resultado de manera detectable en esta muestra.

- **Las *skills* no bastaron para eliminar las violaciones:** `rules_skills` redujo las violaciones confirmadas de ocho a tres y los hallazgos Semgrep de once a tres. Sin embargo, el contraste pareado no alcanzó significancia estadística (*p* = 0,125) y se observaron fallas de comportamiento.

- **El escalón que incorporó la compuerta es donde las violaciones llegaron a cero:** `rules_skills` registró tres violaciones confirmadas y `rules_skills_gate` ninguna. El contraste pareado de ese escalón es 3/0 (*p* = 0,25): la dirección es la esperada, pero con veinte pares no alcanza significancia. El único contraste significativo es el del paquete completo frente a la línea base (8/0; *p* = 0,0078).

- **La compuerta fue el componente con el efecto más claro:** `rules_skills_gate` presentó cero violaciones confirmadas frente a ocho en `baseline` (ocho pares discordantes; *p* = 0,0078). El contraste para cualquier falla también favoreció a esta configuración (12/0; *p* = 0,0005). El resultado está acotado a las tareas, el modelo y las condiciones evaluadas.

- **El enforcement externo no aportó una mejora demostrable en esta muestra:** el brazo `rules_skills_gate_enforced` no activó el bucle externo de corrección durante las ejecuciones reportadas. La compuerta asesora presentó un resultado comparable en violaciones confirmadas con menor complejidad operativa.

- **La replicación aísla el componente:** en el entorno limpio, `baseline` cometió seis violaciones, `gate_only` ninguna y el arnés completo una. El contraste principal es 6/0 (*p* = 0,031) y el contraste entre los dos brazos con compuerta es 0/1 (*p* = 1,0): el efecto proviene de la compuerta y la capa procedural no agrega nada medible.

- **La significancia depende de los tiempos agotados:** al excluir las ocho corridas que alcanzaron el límite de 600 segundos, el contraste principal queda 5/0 (*p* = 0,0625). La dirección es robusta; la significancia, limítrofe, y conviene declararlo.

- **El costo se replica:** 1,7 veces el tiempo de ciclo y 2,8 veces los tokens en la corrida limpia, frente a 2,3 veces los tokens en octubre. Dos mediciones separadas dan el mismo orden de magnitud.

- **El segundo modelo separa lo que el primero confundía:** con `gpt-6-luna` la compuerta volvió a reducir las violaciones, de seis a dos, y la capa procedural produjo siete fallas de comportamiento. El beneficio de la compuerta no depende de la familia de modelos; el costo de la capa procedural, sí.

- **El aislamiento del entorno es parte del método:** la primera medición dio cero en todos los brazos porque el agente podía leer el benchmark desde el repositorio. Una fuga así empuja todas las comparaciones hacia "sin efecto" y no se detecta mirando los resultados, solo el entorno.

- **El costo de la compuerta es medible:** `rules_skills_gate` utilizó aproximadamente 2,3 veces los tokens de `baseline` (35,8 M frente a 15,6 M) y requirió 46,3 segundos adicionales por tarea en promedio. El costo debe formar parte de cualquier interpretación del beneficio de privacidad.

- **La calibración ciega cambia el estatus de la afirmación sobre el detector:** antes del Hito 2, "el detector funciona" se sostenía con 22 casos curados por sus propios autores. Después, se sostiene con 907 casos escritos por autores sin acceso al repositorio, sellados antes de la corrida y medidos antes de la corrección. La diferencia no es de cantidad, sino de qué se puede afirmar.

- **La trayectoria importa más que el número final:** el detector pasó de 26/36 a 82/84 porque cada ronda expuso un canal que el corpus anterior no cubría. Un único resultado alto habría sido compatible con un corpus complaciente; una serie con caídas en las rondas que introducen canales nuevos no lo es.

- **La preservación funcional separa auditoría de corrección:** cuando el modelo resuelve la tarea sin ayuda, el arnés no mejora el resultado y cuesta 2,5 veces más tiempo y 3,3 veces más tokens. El beneficio del arnés no está en hacer mejor el trabajo, sino en impedir que un trabajo aparentemente correcto introduzca una violación. Son dos afirmaciones distintas y la evidencia sostiene solo la segunda.

- **El propio arnés resultó ser objeto de auditoría:** en este incremento se encontraron dos defectos que ningún test detectaba —un punto fijo que multiplicaba por 40 la latencia de la compuerta y un falso positivo crítico que bloqueaba commits legítimos sobre el propio motor—, además de una categoría de dato inexistente que impedía que un control declarado como implementado se disparara. La conclusión metodológica es que la cobertura declarada debe verificarse con el mismo rigor que la detección.

### Cobertura de las variables de estudio

| Variable (sección 2.3) | Dónde se mide | Estado |
| - | - | - |
| 1. Efectividad de gobernanza (*goldplating*, alcance, dependencias) | Cambios no solicitados en ambos experimentos | Parcial: se reporta el conteo, no la tasa por tarea |
| 2. Eficiencia contextual (tokens y tiempo de ciclo) | 10.2, 10.4 y 10.8 | Medida |
| 3. Preservación funcional | 10.2, 10.4 y la suite de 613 pruebas | Medida |
| 4. Trazabilidad de decisiones | — | No medida |
| 5. Capacidad de auditoría normativa | 10.2, 10.3, 10.6 y 10.8 | Medida |

La variable 4 no se mide en este informe: exigiría observar cómo documenta sus decisiones un desarrollador con y sin el arnés, y eso requiere un estudio con personas. Se declara como pendiente en lugar de sustituirla por un indicador indirecto.

## 10.11 Limitaciones identificadas

Las limitaciones se organizan según el tipo de validez afectada, siguiendo la clasificación habitual en ingeniería de software empírica.

### Validez de constructo

1. **Adjudicación.** Las tareas, pruebas, detector y oráculo comparten autoría. El segundo evaluador de la sección 10.5 es un modelo de la misma familia: mide reproducibilidad, no validez humana.

2. **Independencia del corpus ciego.** Los autores no acceden al repositorio, pero son instancias del mismo modelo. La independencia es de información, no de sesgo inductivo.

3. **Oráculo.** Las pruebas ocultas y Semgrep no representan todas las violaciones posibles, y existen falsos positivos documentados en escenarios de pseudonimización y retención.

4. **Sujeto del estudio.** La premisa del proyecto es que un desarrollador puede pasar por alto un hallazgo, pero ningún experimento observa a una persona. Se mide el comportamiento del agente y la calidad del detector, no la conducta de revisión humana.

5. **Cobertura normativa.** La clasificación de las 30 aristas es una derivación técnica revisada contra el texto legal por los autores del proyecto, no una validación jurídica.

6. **Alcance de la calibración.** La serie ciega mide siete de los 26 controles. Los cinco detectores incorporados en este incremento cuentan con pruebas unitarias y casos de regresión, pero no con una medición ciega propia.

### Validez interna

7. **Atribución causal.** Los brazos varían reglas, procedimientos y compuerta, pero no incorporan una condición independiente de selección de contexto. Los resultados no permiten atribuir a los grafos los cambios observados.

8. **Trampas explícitas poco discriminantes.** En un paquete de escenarios que instruían a violar controles, el modelo se negó o implementó una alternativa segura en todos los brazos. La evaluación depende de escenarios más sutiles.

9. **Saturación.** En el experimento de preservación funcional el modelo resolvió las diez trampas sin el arnés, de modo que ese bloque no puede medir mejora funcional: solo mide costo.

10. **Condiciones de medición del costo.** Los tiempos son de reloj de pared en un solo equipo, con las corridas en orden fijo y sin aleatorización. La prueba de signos controla la dirección, no la magnitud.

11. **Completitud frente a privacidad.** Las dos fallas de T31 en el brazo con corrección externa son tareas no implementadas, no violaciones; la completitud se mide aparte.

### Validez externa

12. **Un solo modelo principal.** Los resultados corresponden a un modelo; la corrida con otro es provisional y no se combina con los principales.

13. **Alcance de las tareas.** El experimento formal cubrió doce tareas y el de dosis cuatro. La generalización a otros dominios requiere más evidencia.

14. **Tamaño de los casos ciegos.** Los corpus de calibración son módulos de 20 a 55 líneas, no repositorios completos. La ronda de 84 casos permite una exhaustividad real de 0,916.

15. **Escala del código real.** El triage cubre una aplicación y trece variantes; los trabajos comparables evalúan entre cuatro y quince aplicaciones \[20\]\[21\]\[22\].

### Validez de conclusión

16. **Potencia estadística.** El experimento formal quedó subpotenciado para el resultado binario, y el de dosis se limita a veinte pares por comparación.

17. **Intervalos.** Se reportan intervalos de Wilson porque, con muestras pequeñas, un resultado perfecto sigue siendo compatible con una tasa de fallo no despreciable.

18. **Vigencia temporal de la evidencia.** El mismo instrumento dio resultados distintos en octubre y en noviembre. Un resultado sobre comportamiento de modelos no es estable en el tiempo, y esa inestabilidad debe considerarse al interpretar cualquier medición de este tipo.

19. **Contaminación del entorno en corridas previas.** La raíz del repositorio se exportaba para que la compuerta importara el motor, y el agente podía leer el benchmark con la *shell*: 21 de 247 corridas históricas lo hicieron. La medición que se reporta es la del entorno aislado; las anteriores no son interpretables en este punto.
20. **Aislamiento a nivel de variables de entorno.** El entorno aislado impide el acceso por la variable del arnés, pero el perfil del usuario sigue apuntando a la carpeta real: un agente decidido podría llegar al repositorio por ruta absoluta. El registro de comandos lo detectaría; un contenedor lo impediría.


# 11. DISCUSIÓN, CONCLUSIONES Y TRABAJO FUTURO

## 11.1 Discusión

Los resultados permiten observar una trayectoria de desarrollo coherente: el proyecto comenzó como asistencia mediante *prompts*, evolucionó hacia un pipeline de *skills* y reglas permanentes, e incorporó posteriormente análisis estructural, catálogo de controles, políticas y evaluación experimental.

- **Gobernanza declarativa y determinista:** las reglas permanentes expresan restricciones, pero su presencia no garantiza el cumplimiento. La evidencia del experimento de dosis sugiere que la compuerta de validación tuvo un efecto más claro que las reglas aisladas.

- **Costo del control:** la configuración con compuerta redujo las violaciones confirmadas en la muestra, pero incrementó el consumo de tokens y el tiempo de ciclo. Este costo es parte del resultado y debe considerarse al evaluar su utilidad.

- **Alcance de la evidencia:** los experimentos muestran resultados sobre un banco de comercio electrónico, un modelo principal y un conjunto limitado de tareas. No permiten afirmar que todo el arnés esté validado en cualquier dominio ni que la gestión de contexto por grafos haya causado los resultados observados.

- **Controles normativos:** el proyecto demuestra la viabilidad técnica de representar algunos escenarios de privacidad mediante reglas ejecutables y pruebas. Esto no equivale a demostrar cumplimiento integral de la Ley N° 21.719.

- **La replicación confirma la dirección y separa los componentes:** con el entorno aislado, la línea base cometió seis violaciones, la compuerta sola ninguna y el arnés completo una. Los dos brazos con compuerta no difieren (*p* = 1,0), de modo que el efecto proviene de la compuerta y no de la capa procedural. El costo es de 1,7 veces el tiempo y 2,8 veces los tokens; la comparación primaria alcanza significancia y queda en el límite al excluir los tiempos agotados. Una corrida previa había dado cero en todos los brazos porque el agente podía leer el benchmark desde el repositorio: sin el aislamiento, el resultado no era interpretable.

- **Contraste con el estado del arte:** la comparación de la sección 5.2 anticipaba que un motor de reglas estático detecta aquello que sus reglas describen. La medición de la sección 10.3 lo confirma con un número: 51 de 84 casos frente a 82 del detector calibrado, y una exhaustividad de 0,286 frente a 1,000. La diferencia no está en la existencia de la herramienta, que es madura, sino en la calibración del instrumento y en el análisis de flujo.

- **Asimetría entre el título y la evidencia:** el proyecto se nombra por dos mecanismos —grafos de dependencias y linaje de datos— y la evidencia de este informe mide el de gobernanza. El componente de grafos está implementado, pero su efecto no se aísla en ningún experimento ejecutado. La asimetría debe leerse como alcance declarado, no como equivalencia de madurez.

- **Madurez del artefacto:** existen componentes operativos y una suite de 613 pruebas aprobadas, además de una medición de calidad del detector sobre 907 casos ciegos; persisten tareas de integración, validación de *skills* en IDE, orquestación supervisada de roles, ampliación experimental sobre código real y adjudicación humana.

## 11.2 Conclusiones

1. **Respuesta a la pregunta del proyecto:** en el banco y las condiciones evaluadas, la configuración `rules_skills_gate` redujo las violaciones de privacidad confirmadas de ocho a cero frente a `baseline` (McNemar, *p* = 0,0078). El resultado se obtuvo con veinte pares y cuatro tareas, y tuvo un costo aproximado de 2,3 veces más tokens y 46,3 segundos adicionales por tarea. La replicación con el entorno aislado confirmó la dirección: la línea base cometió seis violaciones, la compuerta sola ninguna y el arnés completo una, con seis pares discordantes (McNemar, *p* = 0,031) y sin diferencia entre los dos brazos con compuerta, a un costo de 1,7 veces el tiempo y 2,8 veces los tokens. El experimento de preservación funcional y costo acota ese resultado: cuando el modelo ya resuelve la tarea sin el arnés, la compuerta no mejora la completitud funcional y el costo sube a 2,5 veces el tiempo de ciclo y 3,3 veces los tokens. No se afirma una reducción general del tiempo de ciclo, la eliminación de alucinaciones ni un efecto causal del contexto estructural.

2. **Consolidación técnica:** el núcleo del arnés se organizó como módulo independiente, con 592 pruebas propias, y la aplicación clínica con 21. La suite consolidada cuenta con 613 pruebas aprobadas.

3. **Catálogo y validación:** se formalizó un catálogo de controles con identificadores del proyecto, motores de políticas, validación y compuerta de *pre-commit*. La cobertura se documenta arista por arista: 15 se detectan, 5 se reportan como riesgo, 6 se exigen como evidencia y 4 quedan a cargo de una persona.

4. **Evidencia experimental:** se ejecutaron cinco experimentos —108 ejecuciones del experimento formal, 100 del experimento de dosis, 72 de la replicación aislada, 907 casos de calibración ciega y 66 ejecuciones del experimento de preservación funcional y costo—, con sus resultados, costos y limitaciones documentados por separado.

5. **Calidad medida del detector:** la calibración ciega sostiene una precisión de 0,955 [0,849; 0,987] y una exhaustividad de 1,000 [0,916; 1,000] sobre la ronda de mayor tamaño. La serie completa muestra que el detector mejoró porque cada ronda expuso un canal que el corpus anterior no cubría, no porque el corpus se ajustara al detector.

6. **Validez externa y modo de uso:** el efecto de la compuerta se repitió con un segundo modelo, de seis a dos violaciones. Las siete fallas de comportamiento del arnés completo se debían a que las skills piden esperar confirmación: con una cláusula de modo autónomo caen a una (*p* = 0,031), a un costo de 7,6 veces los tokens. La capa procedural no está rota, pero su valor sobre la compuerta sola no se demuestra.

7. **Límites de las conclusiones:** el prototipo demuestra factibilidad técnica, evidencia de que la compuerta reduce las violaciones de privacidad confirmadas en dos mediciones independientes y una medición acotada de la calidad del detector. No permite afirmar que todos los componentes formen un *harness* plenamente integrado, que los resultados se generalicen a otros modelos o dominios, ni que el arnés mejore la completitud funcional. La significancia de la comparación principal desciende a *p* = 0,0625 al excluir las corridas que agotaron el tiempo límite.

## 11.3 Trabajo futuro comprometido

De acuerdo con la planificación vigente al 24 de noviembre de 2026, el Hito 2 es el penúltimo entregable; las siguientes actividades se concentran en la entrega final:

1. **Adjudicación humana:** incorporar al menos un evaluador humano —idealmente con formación jurídica y con formación en desarrollo— sobre una muestra del corpus, para reemplazar el acuerdo entre modelos por un acuerdo entre personas. Es la limitación que más condiciona la interpretación de los resultados.

2. **Código real a mayor escala:** repetir el triage sobre entre tres y cinco repositorios reales, con adjudicación de cada hallazgo, para estimar la precisión fuera de los módulos aislados y medir el ruido que la compuerta introduce en un flujo de revisión. La misma línea debe incluir una comparación con Semgrep en modo *taint*, para separar el efecto de las reglas del efecto del motor.

3. **Pruebas separadas y aislamiento reforzado:** dividir cada prueba oculta en una parte funcional y una de privacidad, para no depender del oráculo, y ejecutar el experimento en un contenedor que impida el acceso por ruta absoluta.

4. **Validación del pipeline de *skills*:** completar las pruebas del flujo de las doce habilidades en el entorno del IDE y documentar sus criterios de activación y salida.

5. **Consolidación documental y del visualizador:** cerrar la trazabilidad entre objetivos, requerimientos, pruebas, experimentos, resultados y limitaciones, incorporar las decisiones de arquitectura como registros formales y completar el visualizador de dependencias, hoy pendiente.

6. **Cobertura de modelos y dominios:** el segundo modelo ya está medido; falta ampliar a otros proveedores y, si la planificación lo permite, a un segundo banco de prueba.


# 12. REFERENCIAS Y ANEXOS

## 12.1 Referencias normativas y bibliográficas

1. Biblioteca del Congreso Nacional de Chile (BCN). (2024, texto vigente con modificaciones posteriores). *Ley N° 21.719: Regula la protección y el tratamiento de los datos personales y crea la Agencia de Protección de Datos Personales*. Versión con vigencia diferida al 1 de diciembre de 2026. [https://www.bcn.cl/leychile/Navegar?idNorma=1209272&idParte=10527471&idVersion=2026-12-01](https://www.bcn.cl/leychile/Navegar?idNorma=1209272&idParte=10527471&idVersion=2026-12-01)

2. Biblioteca del Congreso Nacional de Chile (BCN). (1999). *Ley N° 19.628: Sobre Protección de la Vida Privada*. [https://www.bcn.cl/leychile/navegar?idNorma=141599](https://www.bcn.cl/leychile/navegar?idNorma=141599)

3. Biblioteca del Congreso Nacional de Chile (BCN). (2012, con modificaciones posteriores). *Ley N° 20.584: Regula los derechos y deberes que tienen las personas en relación con acciones vinculadas a su atención en salud*. Artículo 13, conservación de fichas clínicas por un período mínimo de quince años. [https://www.bcn.cl/leychile/navegar?idNorma=1039348](https://www.bcn.cl/leychile/navegar?idNorma=1039348)

4. Biblioteca del Congreso Nacional de Chile (BCN). (2012). *Decreto N° 41, Reglamento sobre Fichas Clínicas*. Artículos 11 y 12, conservación mínima y eliminación segura de fichas clínicas. [https://www.bcn.cl/leychile/navegar?idNorma=1046753](https://www.bcn.cl/leychile/navegar?idNorma=1046753)

5. MITRE Corporation. *CWE-532: Insertion of Sensitive Information into Log File*. Common Weakness Enumeration. [https://cwe.mitre.org/data/definitions/532.html](https://cwe.mitre.org/data/definitions/532.html)

6. MITRE Corporation. *CWE-200: Exposure of Sensitive Information to an Unauthorized Actor*. Common Weakness Enumeration. [https://cwe.mitre.org/data/definitions/200.html](https://cwe.mitre.org/data/definitions/200.html)

7. Hevner, A. R., March, S. T., Park, J., & Ram, S. (2004). *Design Science in Information Systems Research*. MIS Quarterly, 28(1), 75–105.

8. Peffers, K., Tuunanen, T., Rothenberger, M. A., & Chatterjee, S. (2007). *A Design Science Research Methodology for Information Systems Research*. Journal of Management Information Systems, 24(3), 45–77.

9. Wieringa, R. J. (2014). *Design Science Methodology for Information Systems and Software Engineering*. Springer Science & Business Media.

10. Weiser, M. (1984). *Program Slicing*. IEEE Transactions on Software Engineering, (4), 352–357.

11. Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., & Press, O. (2024). *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*. arXiv:2405.15793. [https://arxiv.org/abs/2405.15793](https://arxiv.org/abs/2405.15793)

12. Agent Skills. *Specification*. Formato abierto de Agent Skills. [https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx](https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx)

13. Agent Skills. *Overview*. Formato abierto y modelo de *progressive disclosure*. [https://github.com/agentskills/agentskills](https://github.com/agentskills/agentskills)

14. OpenAI. (2026, 11 de febrero). *Harness engineering: leveraging Codex in an agent-first world*. [https://openai.com/index/harness-engineering/](https://openai.com/index/harness-engineering/)

15. Zhong, H., & Zhu, S. (2026). *AI Harness Engineering: A Runtime Substrate for Foundation-Model Software Agents*. arXiv:2605.13357. [https://arxiv.org/abs/2605.13357](https://arxiv.org/abs/2605.13357)

16. Osmani, A. *Agent Skills — Skill Anatomy*. [https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md](https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md)

17. Model Context Protocol. (2026). *Specification — Tools*. Versión 2026-07-28. [https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx)

18. Model Context Protocol. (2026). *Specification — Overview*. Versión 2026-07-28. [https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/index.mdx](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/index.mdx)

19. Repositorio oficial del proyecto. (2026). *Harness de Desarrollo Asistido por IA y Gobernanza de Software*. [https://github.com/Cliptap/compliance-graph-harness](https://github.com/Cliptap/compliance-graph-harness)

20. Adam, J., Zech, C., Zhu, L., Rajesh, S., Harbison, N., Jethwa, M., Crichton, W., Krishnamurthi, S., & Schwarzkopf, M. (2025). *Paralegal: Practical Static Analysis for Privacy Bugs*. 19th USENIX Symposium on Operating Systems Design and Implementation (OSDI 25), 957–978. [https://www.usenix.org/conference/osdi25/presentation/adam](https://www.usenix.org/conference/osdi25/presentation/adam)

21. Tang, F., Østvold, B. M., & Bruntink, M. (2023). *Helping Code Reviewer Prioritize: Pinpointing Personal Data and its Processing*. 22nd International Conference on Intelligent Software Methodologies, Tools and Techniques (SOMET 2023). [https://doi.org/10.3233/FAIA230228](https://doi.org/10.3233/FAIA230228)

22. Ran, H., Zhang, H., & Tang, X. (2025). *GDPR-Bench-Android: A Benchmark for Evaluating Automated GDPR Compliance Detection in Android*. arXiv:2511.00619. [https://arxiv.org/abs/2511.00619](https://arxiv.org/abs/2511.00619)

## 12.2 Anexos

### Anexo A: Glosario de términos técnicos

- **APDP:** Agencia de Protección de Datos Personales de Chile, creada por la Ley N° 21.719.

- **AST (*Abstract Syntax Tree*):** representación jerárquica de la estructura sintáctica del código fuente.

- **Context Rot:** degradación de la utilidad del contexto de un modelo por saturación o acumulación de información irrelevante.

- **CWE-532:** debilidad relacionada con la inserción de información sensible en archivos de bitácora.

- **CWE-200:** debilidad relacionada con la exposición de información sensible a un actor no autorizado.

- **Goldplating:** incorporación de funcionalidades, dependencias o abstracciones que no fueron solicitadas.

- **Arnés / *harness*:** sinónimos en este informe. Se usa «arnés» en el texto y el término inglés en cursiva cuando se nombra el concepto o el producto.

- **Brazo:** cada configuración experimental que se compara, por ejemplo con compuerta y sin ella.

- **Compuerta (*gate*):** punto de control que evalúa un cambio y decide si bloquea la integración. En este proyecto se materializa en la compuerta de *pre-commit* y en el gate de evidencia.

- **Harness de desarrollo:** entorno estructurado que reúne contexto, herramientas, reglas, políticas y mecanismos de validación alrededor de un agente.

- **Pack:** archivo de catálogo que declara controles, categorías de datos y detectores. El motor no contiene la ley: la lee del pack, de modo que el mismo motor sirve a otro marco normativo cambiando el archivo.

- **Privacy by Design:** principio de protección de datos desde el diseño y por defecto.

- **Sub-graph slicing:** selección de un subconjunto de nodos y aristas de un grafo respecto de un nodo de interés y una distancia máxima.

- **Taint Analysis:** análisis de posibles flujos de datos desde fuentes (*sources*) hacia sumideros (*sinks*).

### Anexo B: Estructura del repositorio

La estructura se incluye para reproducibilidad. El cuerpo del informe describe funciones; este anexo indica dónde encontrarlas.

```
raíz/
├── src/
│   ├── harness/        motor del arnés: grafos, catálogo, políticas, compuerta y evidencia
│   ├── backend/        aplicación clínica de demostración (API)
│   └── database/       persistencia de la aplicación clínica
├── .harness/
│   ├── packs/          catálogos de controles
│   └── evidence.json   manifiesto de evidencia documental
├── .agents/skills/     doce procedimientos de desarrollo y tres de cumplimiento
├── experiments/        bancos de prueba, paquete de tareas y variantes con defectos
├── harness/eval/       evaluación: triage, acuerdo entre etiquetas y comparación con Semgrep
├── tests/              suite automatizada
└── docs/               informe, notas de investigación y evidencias
```

### Anexo C: Verificación de la suite automatizada (613 pruebas)

Ejecución de la suite completa al cierre del Hito 2:

- **Comando:** `pytest`, o el ejecutor de pruebas del proyecto.
- **Entorno:** Python 3.13, Pytest 9.0.3, SQLite embebido, SQLAlchemy 2.0 asíncrono.

| Área evaluada | Pruebas |
| - | -: |
| Análisis estructural, linaje y contexto | 53 |
| Catálogo, políticas y cobertura | 398 |
| Compuerta, evidencia y registro | 52 |
| Evaluación del detector | 15 |
| Procedimientos, persistencia y entorno | 74 |
| Aplicación clínica | 21 |
| **Total** | **613** |

La distribución por archivo no se reproduce aquí: el repositorio conserva el detalle y el comando la regenera.

**Evidencia de ejecución:**

```
============================= test session starts =============================
platform win32 -- Python 3.13, pytest-9.0.3, pluggy-1.5.0
rootdir: <proyecto>
configfile: pytest.ini
collected 613 items

........................................................................ [ 12%]
........................................................................ [ 24%]
........................................................................ [ 36%]
........................................................................ [ 48%]
........................................................................ [ 60%]
........................................................................ [ 72%]
........................................................................ [ 84%]
........................................................................ [ 96%]
....................................                                     [100%]

============================= 613 passed in 85.61s =============================
```
