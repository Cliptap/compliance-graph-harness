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

El desarrollo de software asistido por inteligencia artificial ha evolucionado desde herramientas de autocompletado hacia agentes capaces de inspeccionar repositorios y ejecutar cambios sobre un sistema. Ese cambio aumenta la velocidad, pero el agente cumple lo que se le pide y no garantiza lo que no se le pidió: entre ello, los requisitos de protección de datos personales. Este proyecto no construye un *harness* de gobernanza general, sino un **arnés especializado en la Ley N° 21.719**, que traduce deberes seleccionados de la norma en controles técnicos ejecutables.

El artefacto reúne doce *skills* procedimentales, tres de cumplimiento, reglas permanentes, análisis estructural y de linaje, un catálogo de 37 controles, un motor de políticas, una compuerta de *pre-commit* y un gate de evidencia documental. La suite registra **613 pruebas aprobadas**.

Este incremento evalúa tres dimensiones. Primero, la **calibración ciega del detector**: 21 rondas selladas con autores sin acceso al repositorio, desde 26/36 en la primera hasta 82/84 en la última, con precisión 0,955 [0,849; 0,987] y exhaustividad 1,000 [0,916; 1,000]. Segundo, el **costo en el ciclo de desarrollo**: el arnés no mejoró la completitud funcional (30/30 pruebas ocultas en ambos brazos) y elevó el tiempo de ciclo a 2,5 veces y los tokens a 3,3 veces, con una diferencia estadísticamente significativa (prueba de signos, 10/10, *p* = 0,00195). Tercero, la **cobertura normativa**: 26 de 37 controles tienen detector determinista, 6 se exigen como evidencia documental y 5 quedan como gap declarado con su motivo.

Los resultados están acotados a un modelo, un banco y muestras pequeñas; la verificación de etiquetas usó un evaluador independiente de la misma familia de modelos, no adjudicación humana. El arnés no certifica cumplimiento jurídico: es una red de seguridad especializada: su valor medido es de auditoría, no de corrección funcional.


# 1. INTRODUCCIÓN

La ingeniería de software experimenta una transformación asociada al uso de modelos de lenguaje y agentes capaces de participar activamente en tareas de programación: el desarrollador puede delegar actividades que antes requerían inspección manual, generación de código y modificaciones iterativas del repositorio. Esa autonomía introduce un riesgo concreto: el agente cumple las instrucciones que recibe, pero no garantiza por sí mismo el cumplimiento de obligaciones que nadie le mencionó, como la protección de los datos personales. Frente a esto, el proyecto no busca construir un *harness* de gobernanza general, sino un **arnés especializado en la Ley N° 21.719**, que traduce deberes seleccionados de la norma en controles técnicos ejecutables sobre el código.

El arnés nace de la experiencia del semestre anterior, cuando se desarrolló una aplicación de gestión clínica mediante *prompts* y *skills*: doce procedimientos (`01-prd` a `12-documentation`) y reglas permanentes en `AGENTS.md`. Sobre esa base se incorporaron análisis estructural del repositorio y linaje de datos, y en esta etapa se agregó la dimensión normativa: un catálogo de controles derivados de la Ley N° 21.719, un motor de políticas y una compuerta de validación que revisa los cambios del agente y cita el artículo que corresponde a cada hallazgo. La ley establece, entre otros deberes, la protección desde el diseño y por defecto (artículo 14 quáter) y la adopción de medidas de seguridad (artículo 14 quinquies); su entrada en vigencia está prevista para el 1 de diciembre de 2026, y el arnés no emite una certificación jurídica de cumplimiento.

En paralelo, el ecosistema de agentes de desarrollo avanzó hacia formatos como *Agent Skills*, que empaquetan procedimientos para cargarse según la tarea, y hacia conceptos de *harness engineering*, que diseñan contexto, herramientas y verificación alrededor del agente. El proyecto toma esas tendencias como referencia, pero delimita su alcance: no construye un *harness* general, sino uno que convierte requisitos seleccionados de la Ley N° 21.719 en chequeos deterministas.

En la fase actual, el arnés se validó experimentalmente sobre el banco de comercio electrónico Dumbo (`experiments/supermercado/`): 100 ejecuciones que comparan cinco configuraciones —desde el agente solo hasta el arnés con compuerta y revisión externa— sobre cuatro tareas con trampas de privacidad. La configuración con compuerta eliminó las violaciones confirmadas (ocho a cero frente a la línea base; McNemar, *p* = 0,0078) y completó las cuatro tareas, a un costo medible de tokens y tiempo. El resultado es evidencia inicial, acotada a un modelo y un banco, y no equivale a una certificación de cumplimiento jurídico.

**Estructura del informe:** el documento presenta el problema y la pregunta de investigación (sección 2), los objetivos (3), la justificación y el alcance (4), el estado del arte (5), la metodología y el diseño experimental ejecutado (6), la planificación (7), el diseño de la solución (8), los incrementos desarrollados (9), la evaluación y los resultados (10), la discusión y las conclusiones (11) y las referencias (12).


# 2. PROBLEMA U OPORTUNIDAD

## 2.1 Situación actual

El uso de modelos de lenguaje para programación permite generar código, modificar archivos, ejecutar pruebas y consultar información del repositorio con una velocidad superior a la interacción manual tradicional. Sin embargo, la utilidad del resultado depende de que el agente reciba contexto suficiente y pertinente, conozca las restricciones del proyecto y disponga de mecanismos que permitan verificar sus cambios.

En el proyecto desarrollado durante el semestre anterior se observaron problemas que motivaron la creación progresiva de instrucciones y skills. Entre ellos se encuentran la incorporación de código no solicitado, la generación de dependencias innecesarias, la modificación de archivos fuera del objetivo original y el aumento de esfuerzo requerido para revisar los cambios generados.

Un segundo problema corresponde a la gestión del contexto. En el prototipo actual existe un mecanismo de recorrido BFS (búsqueda en amplitud) sobre un grafo estructural del repositorio, pero el resultado todavía termina concatenando archivos completos. Por lo tanto, el mecanismo actual constituye una primera aproximación a la selección estructural de contexto, pero no una extracción fina a nivel de funciones o símbolos.

Existe además un problema de gobernanza. Las reglas actuales presentes en AGENTS.md sirven como instrucciones para el agente, pero no constituyen por sí mismas un mecanismo determinista de enforcement. Esto significa que una regla siempre presente como «mantener el alcance del MVP» puede ser ignorada por el modelo si posteriormente no existe un verificador que compruebe el cambio producido.

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

# 2.3 PREGUNTA DEL PROYECTO Y VARIABLES DE ESTUDIO

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

# 3.2 OBJETIVOS ESPECÍFICOS

- **OE1 — Catálogo de workflows y gobernanza de decisiones:** formalizar un catálogo de workflows de desarrollo asistido por IA basado en las doce *skills* procedimentales (`01-prd` a `12-documentation`) y en las tres *skills* de cumplimiento, incorporando criterios explícitos de activación, ejecución y verificación orientados a la Ley N° 21.719.

- **OE2 — Gestión estructural de contexto:** construir y evaluar un mecanismo de gestión de contexto basado en el análisis de dependencias del repositorio, utilizando grafos estructurales y recorridos de vecindad acotada para seleccionar información pertinente, reducir la incorporación de contexto innecesario y apoyar el análisis de flujos de datos sensibles regulados por la Ley N° 21.719. La evolución hacia selección a nivel de símbolos se mantendrá como objetivo de refinamiento mientras la implementación entregue archivos completos.

- **OE3 — Arquitectura desacoplada y roles especializados:** consolidar la arquitectura modular del arnés (`src/harness/`), parametrizando los directorios de análisis para operar sobre repositorios Python compatibles. Definir roles especializados —*planner*, *code reviewer*, *security reviewer* y *compliance auditor*— con autonomía acotada y supervisión humana; su orquestación autónoma completa no se considera implementada.

- **OE4 — Catálogo ejecutable de controles de privacidad:** formalizar controles técnicos derivados de la Ley N° 21.719 y de las obligaciones aplicables al caso de estudio en un catálogo ejecutable, utilizando identificadores trazables y motores de detección, validación y remediación supervisada. La evaluación se centrará en violaciones técnicas identificables, sin equiparar el resultado del arnés con una certificación de cumplimiento jurídico.

- **OE5 — Evaluación experimental:** ejecutar y ampliar un protocolo comparativo sobre bancos de prueba controlados, midiendo violaciones de privacidad confirmadas, fallas de comportamiento, pruebas funcionales, consumo de tokens y tiempo de ciclo. El protocolo deberá explicitar las limitaciones de tamaño muestral, adjudicación y generalización de los resultados.


# 4. JUSTIFICACIÓN Y ALCANCE

## 4.1 Justificación

El valor del proyecto se articula en cuatro ámbitos complementarios:

- **Valor técnico:** el arnés combina análisis estructural del repositorio, selección topológica de contexto, políticas verificables y validación automatizada para comprobar requisitos seleccionados de la Ley N° 21.719. La poda BFS (`k ≤ 2`) busca limitar la vecindad de información considerada para una tarea. Sin embargo, como el contexto todavía puede serializar archivos completos, no se afirma que ya exista selección fina a nivel de símbolos ni que el mecanismo haya reducido por sí solo las dependencias inexistentes o la latencia de inferencia. Esos efectos deben medirse con un protocolo específico.

- **Valor metodológico:** el catálogo de *skills* y las reglas permanentes proporcionan una secuencia de trabajo y un marco explícito de decisiones. La separación entre instrucciones declarativas y controles deterministas permite distinguir lo que el modelo debe seguir de aquello que el arnés puede comprobar mediante software: en este proyecto, los controles derivados de la Ley N° 21.719.

- **Valor normativo y social:** el proyecto utiliza controles técnicos relacionados con protección de datos personales, como la prevención de exposición de información sensible en bitácoras y respuestas de API. La Ley N° 21.719 establece protección desde el diseño y por defecto en su artículo 14 quáter, además del deber de adoptar medidas de seguridad en el artículo 14 quinquies. A la fecha de corte de este informe, 24 de noviembre de 2026, su entrada en vigencia está prevista para el 1 de diciembre de 2026. El artículo 35 contempla sanciones diferenciadas según la gravedad de la infracción, con un máximo de 20.000 UTM para infracciones gravísimas; no corresponde presentar ese máximo como una sanción automática por cualquier fuga de datos \[1\]. Para el caso clínico, la Ley N° 20.584 establece una conservación mínima de quince años de las fichas clínicas, obligación desarrollada también en el artículo 11 del Decreto N° 41 \[3\]\[4\]. El arnés traduce algunos de estos requisitos a controles técnicos; no determina el cumplimiento legal integral ni reemplaza una evaluación jurídica.

- **Valor académico:** el proyecto aporta un artefacto de ingeniería y evidencia experimental sobre el efecto de determinadas capas de gobernanza. Los resultados actuales muestran un efecto estadísticamente significativo de la configuración con compuerta sobre las violaciones confirmadas en el experimento de dosis, junto con un costo de tokens y tiempo. La evidencia no permite generalizar todavía a todos los modelos, dominios ni componentes del arnés.

## 4.2 Alcance del proyecto

El proyecto comprende los siguientes componentes:

1. **Arnés especializado en la Ley N° 21.719 — producto principal (`src/harness/`):**

   - Doce *skills* procedimentales documentadas en `.agents/skills/`, desde `01-prd` hasta `12-documentation`.

   - Tres *skills* de cumplimiento: `compliance-audit`, `compliance-dev` y `compliance-patch`.

   - Reglas permanentes de interacción documentadas en `AGENTS.md`, relacionadas con consulta previa, foco MVP, verificación de dependencias y simplicidad. Estas reglas orientan al agente, pero no se consideran por sí solas un mecanismo determinista de enforcement.

   - Motor de grafos y análisis estructural (`graph_engine.py`, `data_lineage.py`, `taint_flow.py`) con persistencia SQLite (`db.py`).

   - Catálogo y motores de políticas (`catalog.py`, `catalog_engine.py`, `policy_engine.py`, `policy_families.py`, `dimension_policy.py`, `exposure_policy.py`, `payment_policy.py`, `normative_pack.py`).

   - Motor de validación y compuerta de *pre-commit* (`validation_engine.py`, `precommit.py`), contratos de datos (`contracts.py`) y visualización (`visualizer.py`).

   - Parametrización de los directorios de análisis mediante argumentos como `scan_dirs`, que permite ejecutar los motores sobre distintos repositorios compatibles con el análisis implementado.

   - **Suite propia:** 592 pruebas en `tests/harness/`.

2. **Aplicación clínica — caso de estudio transaccional (`src/backend/` y `src/database/`):**

   - Backend Python con FastAPI y SQLAlchemy 2.0 asíncrono para gestionar pacientes, profesionales, citas y registros de auditoría.

   - Lógica de dominio que incluye validación de RUT mediante Módulo-11, prevención de colisiones en agenda (*double-booking*) y control de acceso basado en roles (RBAC) mediante JWT.

   - Validación de la API mediante contratos OpenAPI (`/docs`) y pruebas automatizadas. El desarrollo de un frontend clínico de usuario final no forma parte del alcance experimental descrito.

   - **Suite propia:** 21 pruebas en `tests/demo/`.

3. **Módulo de cumplimiento normativo — funcionalidad integrada del arnés:**

   - Catálogo formalizado en `.harness/packs/`, incluyendo `cl-ley-21719.json`, `catalog.v2.json` y `catalog.full.json`.

   - Controles técnicos sobre exposición de información sensible en logs y respuestas de API (CWE-532 y CWE-200), protección de datos de pago, control de acceso y retención de información clínica.

   - Rutinas de diagnóstico y remediación asistida con validación posterior. La existencia de *skills* de cumplimiento no implica que haya una orquestación autónoma completa entre subagentes.

**Bancos de prueba experimentales:**

- `src/backend/` y `src/database/`: aplicación clínica de demostración.

- `experiments/supermercado/`: aplicación de comercio electrónico («Dumbo») utilizada como sujeto de prueba de los experimentos controlados.

- `experiments/tasks/`: paquete de tareas con pruebas ocultas y reglas Semgrep independientes utilizadas como oráculo.

- `demo_apps/`: documentación de delimitación y descripción de los bancos de prueba sectoriales; no se presenta como un banco ejecutable adicional.

**Perfiles destinatarios:**

- **Ingenieros de software y desarrolladores:** utilizan el arnés desde su entorno de desarrollo y línea de comandos para ejecutar *skills*, analizar repositorios y validar cambios mediante el runner `test.ps1`.

- **Oficiales de protección de datos y auditores:** constituyen perfiles potenciales de consulta de reportes y visualizaciones para inspeccionar controles y posibles flujos de información sensible. No se afirma que exista una plataforma autónoma de auditoría destinada a estos perfiles.

**Entorno de ejecución y resguardos éticos:**

- Los componentes del arnés utilizan Python 3.11 o superior, validado en Python 3.13, y SQLite para persistir estructuras y hallazgos.

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

5. **Agent Skills y *harness engineering*:** la especificación abierta de Agent Skills define una estructura basada en una carpeta que contiene `SKILL.md`, con metadatos `name` y `description` obligatorios y recursos opcionales, como scripts, referencias y activos. También describe un mecanismo de carga progresiva, en el que el agente descubre las *skills* por sus metadatos y carga las instrucciones y recursos cuando corresponde \[12\]\[13\]. Por su parte, OpenAI describe *harness engineering* como el diseño del entorno, las herramientas, la estructura del repositorio y los mecanismos de feedback que permiten a los agentes realizar trabajo de ingeniería de software de manera más confiable \[14\]. Zhong y Zhu proponen además una formulación del *harness* como una capa de ejecución que media entre el modelo, el proyecto y el entorno \[15\].

## 5.2 Análisis crítico y tabla comparativa

La comparación se utiliza para identificar dimensiones de diseño relevantes, no para afirmar que todos los productos de una categoría tengan exactamente las mismas capacidades.

| Criterio | Asistentes de código | Agentes de ingeniería | SAST / linters | Reglas estáticas (`AGENTS.md`, `.cursorrules`) | Harness propuesto |
| - | - | - | - | :-: | - |
| **Gobernanza del ciclo de vida** | Asistencia centrada en tareas de edición y desarrollo. | Ejecución de tareas mediante herramientas y ciclos agénticos. | Análisis de código y reglas específicas. | Directivas que orientan el comportamiento. | Pipeline documentado de 12 *skills* desde PRD hasta documentación; la validación integral en IDE sigue en progreso. |
| **Soberanía del desarrollador** | Depende del producto, su configuración y los controles disponibles. | Depende de permisos, entorno y supervisión configurados. | El humano revisa y resuelve hallazgos. | Mantienen explícitas las preferencias y restricciones del proyecto. | Directivas permanentes más controles deterministas donde existe una política implementada. |
| **Gestión de contexto** | Contexto del editor, archivos y herramientas disponibles. | Contexto reunido durante la resolución de la tarea. | No constituye su función principal. | Depende de la información suministrada al agente. | Grafo estructural con recorrido BFS acotado (`k ≤ 2`); la serialización todavía puede incorporar archivos completos. |
| **Auditoría de privacidad** | Depende de las funciones y extensiones disponibles. | Depende de las herramientas y políticas configuradas. | Detección mediante reglas estáticas. | Puede documentar restricciones, pero no verifica por sí sola el código. | Catálogo ejecutable de controles de la Ley N° 21.719, motor de políticas y compuerta de validación. |
| **Trazabilidad** | Varía según el historial y los registros disponibles. | Puede registrar acciones, comandos y resultados. | Produce hallazgos de análisis. | Conserva directivas del proyecto. | Vincula workflows, controles, resultados de pruebas y reportes; no se afirma trazabilidad total de toda decisión técnica. |
| **Desacoplamiento** | Suele integrarse en un entorno de desarrollo. | Opera dentro del entorno configurado para el agente. | Puede ejecutarse como herramienta externa o integrada. | Se mantiene en archivos del repositorio. | Núcleo en `src/harness/` con rutas de análisis parametrizables para repositorios Python compatibles. |


## 5.3 Fundamentos técnicos de las decisiones de ingeniería

### 5.3.1 Pipeline de *skills* (01 a 12) como procedimientos especializados

Dividir el ciclo de vida en doce etapas delimitadas (`01-prd` hasta `12-documentation`) permite separar actividades como definición de requerimientos, arquitectura, modelado de datos, diseño de API, backend, frontend, autenticación, pruebas, CI/CD, despliegue, observabilidad y documentación.

Cada *skill* delimita un procedimiento y puede orientar al agente mediante preguntas, pasos y criterios de salida. El pipeline busca que las decisiones relevantes se documenten antes de ejecutar cambios; no se afirma que la secuencia garantice por sí sola que el modelo siga todas las instrucciones. La integridad de las carpetas se comprueba mediante pruebas, mientras que la validación completa del flujo en el entorno del IDE permanece como trabajo pendiente.

### 5.3.2 Reglas *Always-On* y soberanía del desarrollador

Las reglas consolidadas en `AGENTS.md` expresan restricciones permanentes del proyecto: consultar ante ambigüedades, mantener el alcance MVP, verificar dependencias y privilegiar soluciones simples bajo principios KISS/YAGNI.

Estas reglas son instrucciones dirigidas al agente, no controles deterministas inviolables. Su cumplimiento debe apoyarse en verificaciones independientes cuando exista una condición comprobable, por ejemplo, una política que detecte una dependencia no autorizada o una compuerta que rechace un cambio. La distinción es central para interpretar los experimentos: las reglas declarativas por sí solas no mostraron un efecto estadísticamente detectable en el experimento de dosis.

### 5.3.3 Grafos estructurales frente a recuperación exclusivamente textual

El software contiene relaciones explícitas que pueden representarse mediante un grafo: pertenencia de funciones a archivos y clases, imports, llamadas y posibles relaciones de flujo de datos. El análisis AST permite obtener parte de esa estructura sin ejecutar el programa.

La propuesta utiliza estas relaciones para identificar una vecindad alrededor de un componente de interés. Esto complementa las búsquedas textuales o por similitud semántica cuando la tarea requiere conocer quién invoca a quién o qué módulos están relacionados. No se sostiene que RAG sea innecesario en todos los casos ni que el grafo represente la semántica completa del programa.

### 5.3.4 Poda topológica de vecindad acotada (`k ≤ 2`)

El recorrido BFS limita la selección a nodos cercanos al elemento de interés dentro del grafo. Con ello se busca evitar tanto la incorporación indiscriminada del repositorio como la selección aislada de un único fragmento sin sus relaciones inmediatas.

La implementación actual utiliza la vecindad del grafo, pero la representación entregada al agente puede incluir el contenido completo de los archivos asociados. Por ello, el parámetro `k ≤ 2` expresa una distancia topológica sobre el grafo y no equivale a una extracción de únicamente dos niveles de funciones o símbolos. La selección fina de símbolos constituye una mejora pendiente.

### 5.3.5 Desacoplamiento y parametrización del motor

El núcleo del arnés se organiza en `src/harness/`. Motores como `graph_engine.py`, `data_lineage.py` y `agentic_audit.py` aceptan directorios de escaneo configurables, lo que permite ejecutar el análisis sobre aplicaciones diferentes sin incorporar sus reglas de negocio dentro del motor.

El desacoplamiento se encuentra demostrado en los bancos utilizados por el proyecto. No debe confundirse con soporte universal para cualquier lenguaje o arquitectura: el análisis implementado se concentra en el ecosistema Python y en las estructuras que los extractores actuales reconocen.

### 5.3.6 Catálogo de controles normativos

El catálogo se materializa en `.harness/packs/` y utiliza identificadores de controles presentes en el proyecto. Entre los controles representativos se encuentran:

| Identificador | Propósito técnico | Implicancia práctica |
| - | - | - |
| `CORE-CHECK-002` | Deber de secreto: fugas en bitácoras, consolas y cachés. | Detectar RUT, correo, tokens o datos de tarjeta en `print`, `logger` y salidas de consola. |
| `CORE-CHECK-003` | Control de acceso a datos personales. | Verificar propiedad del recurso y permisos en rutas sensibles. |
| `CORE-CHECK-005` | Consentimiento informado y no preconfigurado. | Detectar configuraciones que presenten el consentimiento como aceptado por defecto. |
| `ECOM-CHECK-003` | Protección de datos de pago. | Evitar la persistencia o emisión indebida de datos de tarjeta, como PAN o CVV. |
| `v2.log_pii` | Detección técnica de datos personales en bitácoras (CWE-532). | Familia `sink_exposure` con sumidero de bitácora. |
| `v2.credential_response` | Credenciales expuestas en respuestas de API (CWE-200). | Familia `sink_exposure` con sumidero de respuesta. |


Los identificadores se presentan como claves del catálogo técnico del proyecto. Su presencia no implica que cada control constituya una transcripción literal de un artículo legal; la correspondencia normativa debe interpretarse como una derivación técnica documentada.

El catálogo completo (`catalog.full.json`) contiene 37 controles: 26 implementados con detector determinista, 6 exigidos como evidencia documental y 5 declarados como gaps (`implemented: false` con `gap_reason`). Los gaps se reportan como cobertura pendiente, no como silencio. El desglose completo de los 37 controles se presenta en el Anexo B.

## 5.4 Interoperabilidad mediante Model Context Protocol (MCP)

Una posible evolución consiste en exponer algunas funciones del arnés mediante Model Context Protocol (MCP), sin convertir MCP en el objeto principal de investigación. El protocolo define mecanismos para que servidores expongan herramientas, recursos y *prompts* a clientes compatibles, junto con consideraciones de autorización y participación humana en operaciones sensibles \[17\]\[18\].

En el proyecto, MCP se considera un posible adaptador de integración entre el agente y el arnés. No se presenta como una funcionalidad implementada ni como un requisito para validar los experimentos actuales.

## 5.5 Privacidad y cumplimiento como código

La Ley N° 21.719 incorpora deberes de protección desde el diseño y por defecto, así como medidas de seguridad para el tratamiento de datos personales. En este informe se consideran especialmente los artículos 14 quáter y 14 quinquies, sin atribuir al software la capacidad de certificar cumplimiento legal integral \[1\].

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

Se ejecutaron cuatro experimentos complementarios. Los dos primeros comparan configuraciones del arnés sobre el banco de comercio electrónico (`experiments/supermercado/`) y utilizan pruebas ocultas y reglas Semgrep independientes como oráculo. El tercero mide la calidad del detector con corpus ciegos sellados. El cuarto mide el costo y la preservación funcional sobre el paquete de diez trampas de protocolo. En todos los casos el modelo se fijó en `opencode-go/deepseek-v4.1-flash` y la configuración se mantuvo constante dentro de cada comparación.

### Etapa 1 — Experimento formal de tres brazos

Se compararon las siguientes condiciones:

- **`baseline`:** aplicación sin reglas ni *skills* del arnés.

- **`harness`:** reglas de `AGENTS.md` más las doce *skills* procedimentales.

- **`harness_compliance`:** configuración anterior más las tres *skills* de cumplimiento, compuerta y rondas de retroalimentación.

Se ejecutaron **12 tareas × 3 brazos × 3 repeticiones = 108 ejecuciones**. Las 108 ejecuciones finalizaron.

### Etapa 2 — Experimento de dosis de cinco brazos

Para observar el efecto incremental de los componentes de gobernanza, se compararon cinco configuraciones sobre cuatro tareas, con cinco repeticiones por condición:

- **`baseline`:** sin reglas ni *skills*.

- **`rules`:** solamente `AGENTS.md`.

- **`rules_skills`:** `AGENTS.md` más las doce *skills* procedimentales.

- **`rules_skills_gate`:** reglas y *skills* más las *skills* de cumplimiento y la compuerta.

- **`rules_skills_gate_enforced`:** configuración anterior con hasta tres rondas externas de corrección.

Se ejecutaron **5 brazos × 4 tareas × 5 repeticiones = 100 ejecuciones**. Las 100 ejecuciones finalizaron.

### Etapa 3 — Calibración ciega del detector

Los dos experimentos anteriores miden el efecto del arnés sobre el agente; ninguno mide la calidad del detector que la compuerta ejecuta. Esa calidad condiciona cualquier conclusión: una compuerta imprecisa produce falsos positivos que el desarrollador aprende a ignorar, y una compuerta incompleta produce falsos negativos silenciosos. El corpus curado del Hito 1 no podía responder la pregunta, porque sus 22 casos los escribió el mismo autor del detector: ese corpus mide memoria, no generalización.

Por eso cada ronda la escribió un autor sin acceso al repositorio, se selló con `sha256` antes de la corrida, se evaluó una sola vez y se reportó el número **previo** a cualquier corrección. Los fallos se corrigieron después y los casos pasaron al corpus de regresión, de modo que las corridas posteriores sobre ese conjunto son regresión y no evidencia de generalización. Se ejecutaron 21 rondas entre 36 y 84 casos, cubriendo los siete controles `v2.*`.

### Etapa 4 — Preservación funcional y costo

La calibración mide el detector; esta etapa mide el arnés completo en el ciclo de desarrollo. Su pregunta es distinta: ¿el arnés cambia el resultado funcional del trabajo, o solamente lo encarece?

- **Trampas:** diez tareas de protocolo (D01–D10) en `experiments/tasks/`, cada una con una prueba oculta independiente, una verificación de evidencia y la suite propia del objetivo.
- **Brazos:** `baseline` (solo la aplicación, sin reglas, *skills* ni compuerta) y `rules_skills_gate` (`AGENTS.md` con el protocolo de ejecución, las doce *skills* procedimentales, las tres de cumplimiento, el paquete normativo, la compuerta y el hook de *pre-commit*).
- **Ejecución:** 10 trampas × 3 repeticiones × 2 brazos = **60 ejecuciones**, más 6 repeticiones adicionales de D03 tras unificar la fuente de destinatarios en la capa de evidencia.
- **Instrumento:** mismo modelo, mismo entorno, un *workspace* nuevo por ejecución. Las corridas no se aleatorizaron: el brazo con compuerta se ejecutó el 20 de noviembre y el de línea base el 21.

### Oráculo y clasificación de resultados

Los resultados se clasificaron con dos señales independientes:

|  | Semgrep encontró una violación | Semgrep no encontró una violación |
| - | - | - |
| **La prueba oculta falla** | `confirmed_violation` | `behavioral_failure`: tarea no implementada (404), test demasiado estricto o privacidad que el oráculo no cubre; requiere adjudicación |
| **La prueba oculta pasa** | `latent_risk`: hallazgo que requiere revisión | `clean` |


La compuerta del experimento es un CLI local (`compliance_check.py`) que evalúa los archivos cambiados con el motor de políticas (`PolicyEngine` + `CatalogEngine`): parsea el código con AST, aplica las familias y consulta el catálogo. No es el hook de `pre-commit`, que se describe en la sección 8.2 y opera sobre el índice de git; tampoco ve las pruebas ocultas ni el oráculo. El experimento no usa el grafo estructural para seleccionar contexto.

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
| **TK-01** | Consolidación y desacoplamiento de la aplicación clínica (`src/backend/`, `src/database/`) | Alta | Completado |
| **TK-02** | Parametrización y modularización del motor del arnés (`src/harness/`) | Alta | Completado |
| **TK-03** | Suite modular (592 pruebas del arnés + 21 de la demo) y runner `test.ps1` | Alta | Completado |
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
| **R04** | **Acoplamiento entre arnés y aplicación:** el motor puede depender indebidamente de rutas o lógica de un banco de prueba. | Baja | Crítico | Alto | Mantener `src/harness/` separado, parametrizar directorios de análisis y documentar los lenguajes soportados. |
| **R05** | **Adjudicación única y falsos positivos:** la clasificación de hallazgos puede depender de una única persona o de reglas imperfectas. | Alta | Alto | Alto | Incorporar un segundo adjudicador ciego y documentar falsos positivos del oráculo sin modificar retroactivamente los resultados. |
| **R06** | **Baja generalización estadística:** pocos modelos y tareas limitan el alcance de las conclusiones. | Alta | Alto | Alto | Ampliar tareas, repeticiones y modelos, y reportar tamaños de efecto, pruebas y limitaciones. |


## 7.4 Matriz de trazabilidad

| Objetivo específico | Requerimiento técnico | Hito de consolidación | Evidencia verificable |
| - | - | :-: | - |
| **OE1 — Pipeline de *skills*** | RF-H01: catálogo de doce procedimientos y directivas permanentes. | Hito 0 | `.agents/skills/`, `AGENTS.md` y `tests/harness/test_skills_integrity.py`. |
| **OE2 — Gestión de contexto** | RF-H03 y RF-H04: extracción AST, persistencia SQLite y recorrido BFS (`k ≤ 2`). | Hito 0 / evolución | `src/harness/graph_engine.py`, `data_lineage.py`, `taint_flow.py`, `graphify-out/` y pruebas asociadas. |
| **OE3 — Arquitectura desacoplada y roles** | RF-H05: motor parametrizable y especificaciones de roles. | Hito 0 | `src/harness/`, `tests/harness/` (592 pruebas) y runner `test.ps1`. |
| **OE4 — Catálogo y políticas de privacidad** | RF-H06 a RF-H08: catálogo, detección CWE-532/CWE-200, validación y compuerta. | Hito 1 | `.harness/packs/`, `catalog.py`, `policy_engine.py`, `precommit.py` y `validation_engine.py`. |
| **OE5 — Evaluación experimental** | RNF-01 a RNF-03: protocolo comparativo, métricas y runner empírico. | Hito 2 | `experiments/tasks/`, `qa_reports/formal-dose/`, `qa_reports/catalog-corpus/`, `docs/research/` y suite de 613 pruebas. |



# 8. DISEÑO DE LA SOLUCIÓN

## 8.1 Requerimientos del sistema

### Requerimientos funcionales del *harness* (RF-H)

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
| **RNF-02** | Modularidad de pruebas | Ejecutar suites por área y en forma integral. | Selección mediante `test.ps1` y ejecución completa con el runner o Pytest. |
| **RNF-03** | Preservación funcional | Evitar alteraciones no deseadas en contratos existentes. | Suite completa aprobada al cierre de la integración y resultados de regresión documentados. |
| **RS-01** | Confidencialidad (CWE-532 / CWE-200) | Evitar emisión no autorizada de datos personales, clínicos o credenciales en logs y respuestas. | Análisis estático de fuentes y sumideros, más pruebas y adjudicación de hallazgos. |
| **RS-02** | Retención de fichas clínicas | Considerar el plazo mínimo de conservación de quince años desde el último ingreso de información. | Impedir la eliminación irreversible antes de cumplirse el plazo y el proceso de revisión aplicable; permitir, cuando corresponda, una eliminación posterior segura y confidencial \[3\]\[4\]. |


## 8.2 Arquitectura del sistema

El sistema se organiza en tres dominios diferenciados: el arnés de desarrollo, la aplicación clínica de demostración y el banco experimental de comercio electrónico.

```
graph TD
    subgraph HARNESS ["HARNESS DE DESARROLLO (src/harness/)"]
        SKILLS["Pipeline de Skills (01-12)<br/>.agents/skills/"]
        RULES["Directivas Always-On<br/>AGENTS.md"]
        ROLES["Roles definidos<br/>Planner, Reviewer, Security, Compliance"]

        subgraph ENGINE ["Motor parametrizable de análisis"]
            AST["Graph Engine (AST)<br/>graph_engine.py"]
            TAINT["Data Lineage / Taint<br/>data_lineage.py + taint_flow.py"]
            SLICER["Selección topológica<br/>BFS k ≤ 2"]
            CATALOG["Catálogo y políticas<br/>catalog.py + policy_engine.py"]
            GATE["Validación y Pre-Commit<br/>validation_engine.py + precommit.py"]
            AST --> SLICER
            TAINT --> CATALOG
            CATALOG --> GATE
        end

        KNOWLEDGE["Persistencia SQLite<br/>.harness/harness.db + packs"]
        ENGINE <--> KNOWLEDGE
    end

    subgraph CLINIC ["APLICACIÓN CLÍNICA (src/backend/ + src/database/)"]
        API["API REST (FastAPI)<br/>Controladores y RBAC"]
        SVC["Servicios de dominio<br/>Pacientes, citas y profesionales"]
        PERSIST["Persistencia<br/>SQLAlchemy 2.0"]
        EVENTS["Eventos y auditoría"]
        API --> SVC --> PERSIST --> EVENTS
    end

    subgraph BENCH ["BANCO EXPERIMENTAL (experiments/supermercado/)"]
        SHOP["Aplicación de comercio electrónico<br/>Dumbo"]
        PACK["Paquete de tareas<br/>Pruebas ocultas + Semgrep"]
        SHOP --> PACK
    end

    subgraph TESTS ["SUITE MODULAR DE PRUEBAS (613 tests)"]
        THARNESS["Pruebas del Harness (592)<br/>tests/harness/"]
        TDEMO["Pruebas de la demo clínica (21)<br/>tests/demo/"]
    end

    HARNESS -.->|Escaneo parametrizable| CLINIC
    HARNESS -.->|Escaneo y auditoría| BENCH
    THARNESS -.->|Valida motores, catálogo y políticas| HARNESS
    TDEMO -.->|Valida API y persistencia| CLINIC
```

- **Módulo del arnés (`src/harness/`):** contiene los motores AST, análisis de linaje y taint, catálogo de controles, políticas, validación, compuerta de *pre-commit*, persistencia SQLite y visualización. Los roles agénticos se encuentran definidos, pero su orquestación autónoma completa sigue bajo supervisión humana.

- **Aplicación clínica (`src/backend/`, `src/database/`):** aplicación transaccional validada mediante API REST, contratos y pruebas automatizadas.

- **Banco experimental (`experiments/supermercado/`):** aplicación de comercio electrónico utilizada como sujeto de prueba de los experimentos controlados, junto con el paquete de tareas y el oráculo.

- **Suite modular:** 592 pruebas del arnés y 21 pruebas de la aplicación clínica, ejecutables por separado o en conjunto.

## 8.3 Reproducibilidad y configuración del entorno

El entorno validado utiliza Python 3.13, Pytest 9.0.3 y SQLite embebido. Los componentes del backend utilizan FastAPI, SQLAlchemy 2.0 y las dependencias definidas en `requirements.txt`.

La instalación del entorno se realiza mediante:

```
pip install -r requirements.txt
```

El runner `test.ps1` permite ejecutar las pruebas por área:

| Comando | Alcance / área |
| - | - |
| `.\test.ps1 fast` | Pruebas rápidas |
| `.\test.ps1 ast` | Motor de análisis sintáctico AST |
| `.\test.ps1 compliance` | Auditoría de reglas y cumplimiento |
| `.\test.ps1 lineage` | Análisis de flujo y linaje de datos |
| `.\test.ps1 governance` | Integridad del pipeline de *skills* |
| `.\test.ps1 db` | Persistencia SQLite |
| `.\test.ps1 demo` | Suite de la aplicación clínica |
| `.\test.ps1 harness` | Suite del motor del arnés |
| `.\test.ps1 all` | Suite integral del repositorio: 613 pruebas |


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

| Componente del incremento | Estado As-Is | Evidencia en el repositorio |
| - | :-: | - |
| **Backend clínico transaccional** | Operativo | Modelos SQLAlchemy, endpoints FastAPI y esquemas Pydantic en `src/backend/` y `src/database/`. |
| **Suite de pruebas modular** | Operativo | 613 pruebas aprobadas: 592 en `tests/harness/` y 21 en `tests/demo/`. |
| **Motor de grafos parametrizable** | Operativo | `src/harness/graph_engine.py` acepta directorios de escaneo configurables. |
| **Analizador de linaje y taint** | Operativo | `src/harness/data_lineage.py` y `src/harness/taint_flow.py` identifican relaciones y posibles flujos *source-to-sink*. |
| **Persistencia SQLite** | Operativo | `src/harness/db.py`, `.harness/schema.sql` y base de datos del arnés. |
| **Recorrido de poda topológica (`k ≤ 2`)** | Operativo | Módulo BFS que selecciona vecindades del grafo; el contexto puede serializar archivos completos. |
| **Reglas operativas Always-On** | Operativo como directivas | `AGENTS.md` contiene cuatro directivas permanentes; su presencia no constituye enforcement determinista por sí sola. |
| **Pipeline de *skills* (01 a 12)** | Documentado y disponible | Doce carpetas procedimentales en `.agents/skills/`, además de tres *skills* de cumplimiento. |
| **Catálogo normativo y políticas** | Operativo | `.harness/packs/`, `catalog.py`, `catalog_engine.py`, `policy_engine.py` y `policy_families.py`. |
| **Motor de validación y pre-commit** | Operativo | `validation_engine.py` y `precommit.py` con bloqueo de hallazgos configurados como bloqueantes. |
| **Mitigación normativa en disco** | Probada en escenarios definidos | Remediación documentada en código del banco de pruebas, incluida la mitigación de exposición en bitácoras mediante enmascaramiento. |
| **Runner modular semántico** | Operativo | Script `test.ps1` con marcadores por área de prueba. |
| **Infraestructura experimental** | Operativa | `experiments/tasks/`, `experiments/supermercado/`, `qa_reports/formal-dose/` y reportes en `docs/research/`. |


## 9.3 Decisiones técnicas y alternativas descartadas

1. **Desacoplamiento del arnés y las aplicaciones:** se separó el núcleo del arnés (`src/harness/`) de las aplicaciones evaluadas y se parametrizaron los directorios de escaneo para reducir dependencias de rutas fijas.

2. **Modularización de la suite de pruebas:** se organizó la suite en 613 pruebas distribuidas entre `tests/harness/` y `tests/demo/`, con ejecución selectiva mediante marcadores y el runner `test.ps1`.

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
| **Familia `code_hygiene`** | Operativa | Cinco detectores nuevos: caché de datos de salud sin cifrado, campo ORM sin cifrado, ruta clínica sin autenticación, export clínico no estructurado y ruta con datos personales sin autenticación (`policy_families.py`). |
| **Cobertura de 30 aristas** | Documentada y verificada | `docs/research/ley-21719-coverage.md`: cada arista de la ley clasificada en detectar, riesgo, evidencia o manual, con su estado. |
| **Gate de evidencia** | Operativo | `src/harness/evidence.py` y `harness-evidence`: manifiesto con artefacto, responsable y vencimiento; seis controles documentales lo exigen desde el pack. |
| **Completitud del índice** | Operativa | `ChangeSet.complete`: la ausencia de una ruta de derechos es violación solo cuando el análisis cubre el árbol completo. |
| **Herramientas de validación** | Operativas | `harness/eval/triage.py` (triage sobre código real) y `harness/eval/label_agreement.py` (muestreo ciego y kappa de Cohen). |
| **Corrección del pack** | Verificada | `CORE-CHECK-003` tenía la categoría inexistente `PERSONAL_DATA`; corregida a `IDENTIFIER_RUT` y `PERSONAL_CONTACT`. El audit del pack se corrigió respecto del alcance real del hook. |

### Decisiones técnicas y alternativas descartadas

1. **No promover todos los avisos a violación:** los cinco controles en modo riesgo (`privacy.rights_reachability`, `consent_transparency`, `retention_minimization`, `minors_and_sensitive` y `third_party_transfers`) detectan un riesgo potencial, no una violación demostrada. Promoverlos habría bloqueado commits legítimos y entrenado al equipo a saltear la compuerta. La excepción es `rights_reachability`, que sube a violación únicamente con índice completo.

2. **Evidencia en integración continua, no en el hook:** que falte una evaluación de impacto es un estado del repositorio, no una propiedad del commit que se revisa. Bloquear cada commit por eso habría producido el mismo efecto de saturación.

3. **Canales nuevos como funcionalidad con prueba, no como más rondas ciegas:** cerrada la calibración con una sonda de convergencia en 42/42, los tres canales siguientes (modelo de respuesta importado, exclusión calculada, sinks de cookie y cabecera) se incorporaron al corpus de regresión con pruebas, en lugar de repetir rondas de 42 casos.

4. **Sin detección donde no hay prueba posible:** las aristas documentales y semánticas no reciben un detector que simule un juicio jurídico. Se exige el artefacto o se firma una lista de verificación.

### Problemas encontrados y correcciones

1. **Compuerta inutilizable por latencia:** el resumen interprocedural de efectos (`_call_effects`) marcaba progreso en cada acierto en lugar de hacerlo solo cuando el conjunto crecía, de modo que el punto fijo ejecutaba siempre las 146 iteraciones completas. Sobre un módulo de 3 000 líneas implicaba 244 segundos por control y cerca de 15 minutos para el hook de *pre-commit*. Corregida la condición de corte, el costo bajó a 6,5 segundos por control y 76 segundos para el hook completo.

2. **Falso positivo crítico sobre el propio código:** el detector interpretaba la iteración de una lista de nombres de campo como exportación de columnas, lo que producía tres hallazgos `CRITICAL` sobre `dimension_policy.py` y bloqueaba cualquier commit que tocara ese archivo. La corrección exige que la variable del bucle seleccione una columna (`row[c]` o `getattr(row, c)`).

3. **Ruta de salud clasificada como ruta clínica:** un endpoint `/health` se reportaba como endpoint clínico sin control de acceso. Los *healthchecks* se excluyen explícitamente.

4. **Categoría de dato inexistente:** `CORE-CHECK-003` declaraba `PERSONAL_DATA`, que no existe en el catálogo, por lo que su detector no podía dispararse nunca. Es el tipo de defecto que un informe de cobertura puede ocultar: el control figuraba como implementado.

### Relación con los objetivos

- **OE4:** la cobertura pasa de 21 a 26 controles con detector y las 30 aristas de la ley quedan clasificadas con su modo y su estado; las documentales dejan de ser un gap silencioso y pasan a ser un requisito verificable.
- **OE5:** la evaluación se amplía con dos bloques nuevos —calibración ciega y costo en el ciclo— y con una medición de acuerdo entre etiquetas.
- **OE1, OE2 y OE3:** sin cambios de alcance en este incremento.


# 10. PRUEBAS, EVALUACIÓN Y RESULTADOS

## 10.1 Protocolo experimental

Para evaluar el efecto de las reglas, las *skills* y las compuertas de cumplimiento, se ejecutaron cuatro experimentos. Los dos primeros comparan configuraciones sobre el banco de comercio electrónico (`experiments/supermercado/`) con pruebas ocultas y reglas Semgrep independientes como oráculo. El tercero mide la calidad del detector con corpus ciegos sellados. El cuarto mide el costo y la preservación funcional sobre el paquete de diez trampas de protocolo. El modelo se fijó en `opencode-go/deepseek-v4.1-flash` y la configuración se mantuvo constante dentro de cada comparación.

- **Experimento formal:** doce tareas × tres brazos (`baseline`, `harness`, `harness_compliance`) × tres repeticiones = **108 ejecuciones**.

- **Experimento de dosis:** cinco brazos (`baseline`, `rules`, `rules_skills`, `rules_skills_gate`, `rules_skills_gate_enforced`) × cuatro tareas × cinco repeticiones = **100 ejecuciones**.

- **Calibración ciega:** 21 rondas selladas con autores independientes, **907 casos** en total, evaluados una sola vez cada uno y reportados antes de cualquier corrección.

- **Preservación funcional y costo:** diez trampas × dos brazos × tres repeticiones = **60 ejecuciones**, más seis repeticiones de control tras unificar la capa de evidencia.

La suite de pruebas del repositorio se ejecutó como verificación de preservación funcional y registró **613 pruebas aprobadas**.

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


**Nota:** la tabla usa los conteos corregidos tras el test T34. Los conteos crudos y el desglose por tipo de fallo están en `docs/research/dose-conclusions.md` y `formal-results-dose.md`; los 2 T31 404 de `enforced` son completitud, no privacidad.

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

**Nota de adjudicación de T34:** la prueba T34 rechazaba el nombre `api_key` aunque su valor estuviera vacío o enmascarado. Era un artefacto del test, no una violación. Corregido el test, los aprobados corregidos son **20/20** en `rules_skills_gate` y **18/20** en `enforced`; los dos restantes de `enforced` son T31 con 404 (completitud), no privacidad. Las violaciones confirmadas no se re-puntuaron: siguen en **0**. La tabla de dosis usa los conteos corregidos de pruebas ocultas; los conteos crudos y el desglose por tipo de fallo están en `docs/research/dose-conclusions.md` y `formal-results-dose.md`.

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

Se ejecutaron las quince reglas Semgrep que el proyecto ya utiliza como oráculo (`experiments/tasks/oracle/rules.yml`), mapeadas a los siete controles evaluados, mediante `harness/eval/semgrep_bench.py`:

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

La calibración usa módulos aislados. Para observar el comportamiento sobre código multi-archivo se ejecutó la compuerta sobre una aplicación real del repositorio (`experiments/supermercado/app`, nueve módulos, ~61 KB) y sobre trece variantes del paquete de trampas con defectos sembrados y mutaciones documentadas.

- **Aplicación limpia:** **0 hallazgos**. La revisión manual confirmó que es un verdadero negativo y no un fallo por omisión: la aplicación anonimiza en la retención, filtra el marketing por consentimiento y no registra datos personales.
- **Trece variantes:** **13/13** correctas frente a los detectores heredados. Con los controles `v2.*`, las tres variantes limpias no produjeron hallazgos, y se detectaron las dos variantes con defectos `v2` relevantes (exposición en bitácora y credenciales).
- **Un falso negativo confirmado:** una variante envía el RUT a una bitácora a través de una función auxiliar ubicada en otro módulo. El detector no sigue el flujo entre archivos en ese caso. Es el límite *cross-module* ya documentado, ahora con evidencia sobre código real.

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

## 10.8 Análisis e interpretación de resultados

- **Las reglas por sí solas no mostraron un efecto detectable:** la comparación `rules` frente a `baseline` no presentó una diferencia estadísticamente significativa en las violaciones confirmadas (tres frente a dos pares discordantes; *p* = 1,0). Esto indica que documentar reglas en `AGENTS.md` no fue suficiente para modificar el resultado de manera detectable en esta muestra.

- **Las *skills* no bastaron para eliminar las violaciones:** `rules_skills` redujo las violaciones confirmadas de ocho a tres y los hallazgos Semgrep de once a tres. Sin embargo, el contraste pareado no alcanzó significancia estadística (*p* = 0,125) y se observaron fallas de comportamiento.

- **La compuerta fue el componente con el efecto más claro:** `rules_skills_gate` presentó cero violaciones confirmadas frente a ocho en `baseline` (ocho pares discordantes; *p* = 0,0078). El contraste para cualquier falla también favoreció a esta configuración (12/0; *p* = 0,0005). El resultado está acotado a las tareas, el modelo y las condiciones evaluadas.

- **El enforcement externo no aportó una mejora demostrable en esta muestra:** el brazo `rules_skills_gate_enforced` no activó el bucle externo de corrección durante las ejecuciones reportadas. La compuerta asesora presentó un resultado comparable en violaciones confirmadas con menor complejidad operativa.

- **El costo de la compuerta es medible:** `rules_skills_gate` utilizó aproximadamente 2,3 veces los tokens de `baseline` (35,8 M frente a 15,6 M) y requirió 46,3 segundos adicionales por tarea en promedio. El costo debe formar parte de cualquier interpretación del beneficio de privacidad.

- **La calibración ciega cambia el estatus de la afirmación sobre el detector:** antes del Hito 2, "el detector funciona" se sostenía con 22 casos curados por sus propios autores. Después, se sostiene con 907 casos escritos por autores sin acceso al repositorio, sellados antes de la corrida y medidos antes de la corrección. La diferencia no es de cantidad, sino de qué se puede afirmar.

- **La trayectoria importa más que el número final:** el detector pasó de 26/36 a 82/84 porque cada ronda expuso un canal que el corpus anterior no cubría. Un único resultado alto habría sido compatible con un corpus complaciente; una serie con caídas en las rondas que introducen canales nuevos no lo es.

- **La preservación funcional separa auditoría de corrección:** cuando el modelo resuelve la tarea sin ayuda, el arnés no mejora el resultado y cuesta 2,5 veces más tiempo y 3,3 veces más tokens. El beneficio del arnés no está en hacer mejor el trabajo, sino en impedir que un trabajo aparentemente correcto introduzca una violación. Son dos afirmaciones distintas y la evidencia sostiene solo la segunda.

- **El propio arnés resultó ser objeto de auditoría:** en este incremento se encontraron dos defectos que ningún test detectaba —un punto fijo que multiplicaba por 40 la latencia de la compuerta y un falso positivo crítico que bloqueaba commits legítimos sobre el propio motor—, además de una categoría de dato inexistente que impedía que un control declarado como implementado se disparara. La conclusión metodológica es que la cobertura declarada debe verificarse con el mismo rigor que la detección.

### Cobertura de las variables de estudio

| Variable (sección 2.3) | Dónde se mide | Estado |
| - | - | - |
| 1. Efectividad de gobernanza (*goldplating*, alcance, dependencias) | Cambios no solicitados en ambos experimentos | Parcial: se reporta el conteo, no la tasa por tarea |
| 2. Eficiencia contextual (tokens y tiempo de ciclo) | 10.2 y 10.4 | Medida |
| 3. Preservación funcional | 10.2, 10.4 y la suite de 613 pruebas | Medida |
| 4. Trazabilidad de decisiones | — | No medida |
| 5. Capacidad de auditoría normativa | 10.2, 10.3 y 10.6 | Medida |

La variable 4 no se mide en este informe: exigiría observar cómo documenta sus decisiones un desarrollador con y sin el arnés, y eso requiere un estudio con personas. Se declara como pendiente en lugar de sustituirla por un indicador indirecto.

## 10.9 Limitaciones identificadas

1. **Potencia estadística:** el experimento formal quedó subpotenciado para el resultado binario. El experimento de dosis obtuvo contrastes significativos para la compuerta, pero se limita a veinte pares por comparación.

2. **Un solo modelo principal:** los resultados corresponden a `opencode-go/deepseek-v4.1-flash`; la corrida con Cursor es provisional y no se combina con los resultados principales.

3. **Adjudicación única:** las tareas, pruebas, detector y oráculo comparten autoría. El segundo evaluador de la sección 10.5 es un modelo, no una persona: falta un adjudicador humano.

4. **Falsos positivos del oráculo:** existen falsos positivos documentados de Semgrep en escenarios de pseudonimización y retención. Deben mantenerse identificados y no interpretarse automáticamente como violaciones confirmadas.

5. **Trampas explícitas poco discriminantes:** en un paquete de escenarios agresivos que instruían a violar controles, el modelo se negó o implementó una alternativa segura en todos los brazos. Por ello, la evaluación depende de escenarios más sutiles.

6. **Alcance de las tareas:** el experimento formal cubrió doce tareas y el de dosis cuatro. La generalización a otros dominios requiere más evidencia.

7. **Efecto del contexto no aislado:** no se evaluó mediante estos experimentos una condición independiente de selección contextual por grafos.

8. **Completitud vs privacidad:** las dos fallas de T31 en `enforced` son 404 (tarea no implementada), no violaciones; la completitud se mide aparte de la privacidad.

9. **Tamaño de los casos ciegos:** los corpus de calibración son módulos de 20 a 55 líneas, no repositorios completos. La ronda 21 usó 84 casos y permite una exhaustividad real de 0,916; sigue siendo una muestra pequeña para un detector con siete controles.

10. **Saturación del experimento de preservación funcional:** el modelo resolvió las diez trampas sin el arnés, de modo que ese bloque no puede medir mejora funcional. Solo mide costo. Un paquete de trampas más difíciles sería necesario para observar el efecto sobre la completitud.

11. **Independencia del corpus ciego:** los autores no acceden al repositorio, pero son instancias del mismo modelo. La independencia es de información, no de sesgo inductivo.

12. **Acuerdo entre etiquetas como proxy:** el kappa de 1,000 proviene de un modelo de la misma familia en otro rol. Es evidencia de reproducibilidad, no de validez humana.

13. **Naturaleza de la cobertura normativa:** la clasificación de las 30 aristas es una derivación técnica revisada contra el texto legal por los autores del proyecto, no una validación jurídica. La propia revisión encontró citas imprecisas en el pack, que se corrigieron.

14. **Condiciones de medición del costo:** los tiempos son de reloj de pared en un solo equipo, con las corridas en orden fijo y sin aleatorización. La razón de costo puede variar con la carga del equipo o con el orden de ejecución; la prueba de signos controla la dirección, no la magnitud.

15. **El sujeto es un agente, no un desarrollador:** la premisa del proyecto es que un desarrollador puede pasar por alto un hallazgo, pero ningún experimento observa a una persona. Lo medido es el comportamiento del agente y la calidad del detector, no la conducta de revisión humana.

16. **La calibración cubre 7 de los 26 controles:** la serie ciega mide la familia `v2.*`. Los cinco detectores incorporados en este incremento cuentan con pruebas unitarias y casos de regresión, pero no con una medición ciega propia.


# 11. DISCUSIÓN, CONCLUSIONES Y TRABAJO FUTURO

## 11.1 Discusión

Los resultados permiten observar una trayectoria de desarrollo coherente: el proyecto comenzó como asistencia mediante *prompts*, evolucionó hacia un pipeline de *skills* y reglas permanentes, e incorporó posteriormente análisis estructural, catálogo de controles, políticas y evaluación experimental.

- **Gobernanza declarativa y determinista:** las reglas permanentes expresan restricciones, pero su presencia no garantiza el cumplimiento. La evidencia del experimento de dosis sugiere que la compuerta de validación tuvo un efecto más claro que las reglas aisladas.

- **Costo del control:** la configuración con compuerta redujo las violaciones confirmadas en la muestra, pero incrementó el consumo de tokens y el tiempo de ciclo. Este costo es parte del resultado y debe considerarse al evaluar su utilidad.

- **Alcance de la evidencia:** los experimentos muestran resultados sobre un banco de comercio electrónico, un modelo principal y un conjunto limitado de tareas. No permiten afirmar que todo el arnés esté validado en cualquier dominio ni que la gestión de contexto por grafos haya causado los resultados observados.

- **Controles normativos:** el proyecto demuestra la viabilidad técnica de representar algunos escenarios de privacidad mediante reglas ejecutables y pruebas. Esto no equivale a demostrar cumplimiento integral de la Ley N° 21.719.

- **Asimetría entre el título y la evidencia:** el proyecto se nombra por dos mecanismos —grafos de dependencias y linaje de datos— y la evidencia de este informe mide el de gobernanza. El componente de grafos está implementado, pero su efecto no se aísla en ningún experimento ejecutado. La asimetría debe leerse como alcance declarado, no como equivalencia de madurez.

- **Madurez del artefacto:** existen componentes operativos y una suite de 613 pruebas aprobadas, además de una medición de calidad del detector sobre 907 casos ciegos; persisten tareas de integración, validación de *skills* en IDE, orquestación supervisada de roles, ampliación experimental sobre código real y adjudicación humana.

## 11.2 Conclusiones

1. **Respuesta a la pregunta del proyecto:** en el banco y las condiciones evaluadas, la configuración `rules_skills_gate` redujo las violaciones de privacidad confirmadas de ocho a cero frente a `baseline` (McNemar, *p* = 0,0078). El resultado se obtuvo con veinte pares y cuatro tareas, y tuvo un costo aproximado de 2,3 veces más tokens y 46,3 segundos adicionales por tarea. El experimento de preservación funcional y costo acota ese resultado: cuando el modelo ya resuelve la tarea sin el arnés, la compuerta no mejora la completitud funcional y el costo sube a 2,5 veces el tiempo de ciclo y 3,3 veces los tokens. No se afirma una reducción general del tiempo de ciclo, la eliminación de alucinaciones ni un efecto causal del contexto estructural.

2. **Consolidación técnica:** el núcleo del arnés se organizó en `src/harness/`, con 592 pruebas propias. La aplicación clínica se organiza en `src/backend/` y `src/database/`, con 21 pruebas propias. La suite consolidada cuenta con 613 pruebas aprobadas.

3. **Catálogo y validación:** se formalizó un catálogo de controles con identificadores del proyecto, motores de políticas, validación y compuerta de *pre-commit*. La cobertura se documenta arista por arista: 15 se detectan, 5 se reportan como riesgo, 6 se exigen como evidencia y 4 quedan a cargo de una persona.

4. **Evidencia experimental:** se ejecutaron cuatro experimentos —108 ejecuciones del experimento formal, 100 del experimento de dosis, 907 casos de calibración ciega y 66 ejecuciones del experimento de preservación funcional y costo—, con sus resultados, costos y limitaciones documentados por separado.

5. **Calidad medida del detector:** la calibración ciega sostiene una precisión de 0,955 [0,849; 0,987] y una exhaustividad de 1,000 [0,916; 1,000] sobre la ronda de mayor tamaño. La serie completa muestra que el detector mejoró porque cada ronda expuso un canal que el corpus anterior no cubría, no porque el corpus se ajustara al detector.

6. **Límites de las conclusiones:** el prototipo demuestra factibilidad técnica, evidencia inicial de la utilidad de una compuerta de cumplimiento y una medición acotada de la calidad del detector. No permite afirmar que todos los componentes formen un *harness* plenamente integrado, que los resultados se generalicen a otros modelos o dominios, ni que el arnés mejore la completitud funcional del trabajo asistido.

## 11.3 Trabajo futuro comprometido

De acuerdo con la planificación vigente al 24 de noviembre de 2026, el Hito 2 es el penúltimo entregable; las siguientes actividades se concentran en la entrega final:

1. **Adjudicación humana:** incorporar al menos un evaluador humano —idealmente con formación jurídica y con formación en desarrollo— sobre una muestra del corpus, para reemplazar el acuerdo entre modelos por un acuerdo entre personas. Es la limitación que más condiciona la interpretación de los resultados.

2. **Código real a mayor escala:** repetir el triage sobre entre tres y cinco repositorios reales, con adjudicación de cada hallazgo, para estimar la precisión fuera de los módulos aislados y medir el ruido que la compuerta introduce en un flujo de revisión. La misma línea debe incluir una comparación con Semgrep en modo *taint*, para separar el efecto de las reglas del efecto del motor.

3. **Piloto de preservación funcional con instrumento completo:** ejecutar los dos brazos de ese experimento con el detector actual y un paquete de trampas más difíciles, dado que el paquete vigente está saturado y no permite medir mejora funcional.

4. **Validación del pipeline de *skills*:** completar las pruebas del flujo de las doce habilidades en el entorno del IDE y documentar sus criterios de activación y salida.

5. **Consolidación documental y del visualizador:** cerrar la trazabilidad entre objetivos, requerimientos, pruebas, experimentos, resultados y limitaciones, incorporar las decisiones de arquitectura como registros formales y completar el visualizador de dependencias, hoy pendiente.

6. **Cobertura de modelos y dominios:** incorporar una segunda configuración de modelo y, si la planificación lo permite, un segundo banco de prueba.


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

### Anexo B: Catálogo de controles normativos

El catálogo formalizado en `.harness/packs/catalog.full.json` reúne **37 controles: 26 implementados con detector, 6 exigidos como evidencia y 5 declarados como gaps**, organizados en cinco familias: clínicos (`CL-DATAPROT`), núcleo (`CORE-CHECK`), salud (`HEALTH-CHECK`), comercio electrónico (`ECOM-CHECK`) y detectores técnicos (`v2.*`). Cada control declara qué verifica, cómo se comprueba y su estado; los gaps se reportan con su motivo y como cobertura pendiente, no como silencio. La correspondencia normativa es una derivación técnica de la Ley N° 21.719 y de las normas sectoriales aplicables, no una transcripción literal ni una certificación jurídica.

| ID | Control | Comprobación | Estado |
| - | - | - | :-: |
| `CL-DATAPROT-001` | Fuga de datos clínicos o RUT hacia logs y telemetría | Reemplazado por `v2.log_pii` | Gap |
| `CL-DATAPROT-002` | Registros médicos en caché sin cifrado en reposo | Familia `code_hygiene` (`cache_unencrypted`) | Implementado |
| `CL-DATAPROT-003` | Entidades de salud sin cifrado a nivel de campo en el ORM | Familia `code_hygiene` (`orm_unencrypted`) | Implementado |
| `CL-DATAPROT-004` | Borrado físico prematuro de fichas clínicas (conservación de 15 años) | Política `domain.prohibited_deletion` | Implementado |
| `CL-DATAPROT-005` | Endpoints clínicos sin control de acceso | Familia `code_hygiene` (`route_auth`) | Implementado |
| `CL-DATAPROT-006` | Decisión clínica automatizada sin explicación ni revisión humana | Evaluación manual (evidencia documental) | Gap |
| `CL-DATAPROT-007` | Portabilidad de ficha clínica en formato no estructurado | Familia `code_hygiene` (`export_format`) | Implementado |
| `CORE-CHECK-001` | Privacidad desde el diseño, minimización y seudonimización | Heurística heredada; sin detector en el motor de políticas | Gap |
| `CORE-CHECK-002` | Deber de secreto: fugas en logs, consolas y cachés | Política `privacy.cwe_532` | Implementado |
| `CORE-CHECK-003` | Derechos del titular y control de acceso | Familia `code_hygiene` (`personal_route_auth`) | Implementado |
| `CORE-CHECK-004` | Decisiones automatizadas: derecho de oposición e intervención humana | Revisión humana documental | Gap |
| `HEALTH-CHECK-001` | Conservación de 15 años frente a solicitudes de supresión | Política `domain.prohibited_deletion` | Implementado |
| `HEALTH-CHECK-002` | Interoperabilidad de la ficha bajo HL7 FHIR R4 CL Core | `harness-evidence`: declaración FHIR | Evidencia exigida |
| `HEALTH-CHECK-003` | Protección reforzada de datos de salud (aislamiento y cifrado) | `harness-evidence`: atestación de aislamiento | Evidencia exigida |
| `CORE-CHECK-005` | Licitud del tratamiento y consentimiento | Política `privacy.consent_transparency` | Implementado |
| `CORE-CHECK-006` | Derechos del titular: procedimiento y plazos | Política `privacy.rights_reachability` | Implementado |
| `CORE-CHECK-007` | Deber de información y transparencia | Política `privacy.consent_transparency` | Implementado |
| `CORE-CHECK-008` | Registro y comunicación de vulneraciones de seguridad | `harness-evidence`: registro de incidentes | Evidencia exigida |
| `CORE-CHECK-009` | Evaluación de impacto en protección de datos (EIPD) | `harness-evidence`: evaluación de impacto | Evidencia exigida |
| `CORE-CHECK-010` | Encargados del tratamiento y cesión de datos | Política `privacy.third_party_transfers` | Implementado |
| `CORE-CHECK-011` | Transferencias internacionales de datos | Política `privacy.third_party_transfers` | Implementado |
| `CORE-CHECK-012` | Datos personales de niños, niñas y adolescentes | Política `privacy.minors_and_sensitive` | Implementado |
| `CORE-CHECK-013` | Conservación, supresión y limitación de la finalidad | Política `privacy.retention_minimization` | Implementado |
| `ECOM-CHECK-001` | Comunicaciones promocionales y oposición al marketing directo | Política `privacy.consent_transparency` | Implementado |
| `ECOM-CHECK-002` | Perfilamiento y recomendaciones personalizadas | Evidencia documental | Gap |
| `ECOM-CHECK-003` | Datos de tarjeta de pago: secreto y seguridad | Política `privacy.payment_data_storage` | Implementado |
| `ECOM-CHECK-004` | Cumplimiento PCI DSS para datos de tarjetas | `harness-evidence`: atestación PCI | Evidencia exigida |
| `ECOM-CHECK-005` | Pasarelas de pago, logística y otros encargados | Política `privacy.third_party_transfers` | Implementado |
| `ECOM-CHECK-006` | Conservación de documentos tributarios como excepción | `harness-evidence`: política de retención | Evidencia exigida |
| `ECOM-CHECK-007` | Situación socioeconómica y puntajes de crédito como datos sensibles | Política `privacy.minors_and_sensitive` | Implementado |
| `v2.log_pii` | Datos personales escritos en bitácoras | Familia `sink_exposure` (sink: log) | Implementado |
| `v2.admin_exposure` | Datos personales sin enmascarar en respuestas admin | Familia `sink_exposure` (sink: response, ruta admin) | Implementado |
| `v2.customer_hard_delete` | Borrado físico de cliente dentro del plazo de retención | Familia `retention_deletion` (730 días) | Implementado |
| `v2.billing_retention` | Registros de facturación borrados antes del plazo (6 años) | Familia `retention_deletion` (2190 días) | Implementado |
| `v2.reset_token` | Token de reseteo de contraseña devuelto al cliente | Familia `credential_exposure` | Implementado |
| `v2.api_key` | API key o secreto devuelto al cliente | Familia `credential_exposure` | Implementado |
| `v2.credential_response` | Credenciales expuestas en respuestas de API | Familia `sink_exposure` (sink: response) | Implementado |

Los detectores `v2.*` son los que opera la compuerta del experimento (`compliance_check.py`), agrupados en las familias `sink_exposure`, `retention_deletion`, `credential_exposure` y `code_hygiene`. Los cinco gaps restantes se declaran con su motivo (`gap_reason`) y se reportan como cobertura pendiente; los seis controles documentales se exigen como evidencia verificable mediante `harness-evidence`, que bloquea la integración mientras falte el artefacto, su responsable o su vigencia.

##### Anexo C: Reporte de Verificación de la Suite Modular de Pruebas Unitarias (613 Tests)

Ejecución de la suite completa automatizada sobre el producto al cierre del Hito 2 mediante Pytest:

- **Comando de ejecución:** `pytest` (o bien `.\test.ps1 all`)

- **Entorno de ejecución:** Python 3.13, Pytest 9.0.3, SQLite embebido, SQLAlchemy 2.0 asíncrono.

- **Desglose de pruebas por componente y archivo:**

| Suite Modular | Archivo de Prueba | N° Tests | Área Evaluada | Resultado |
| - | - | :-: | - | :-: |
| `tests/demo/` | `test_appointments.py` | 2 | Citas y colisiones horarias | PASS |
| `tests/demo/` | `test_audit.py` | 11 | Inmutabilidad de registros y eventos | PASS |
| `tests/demo/` | `test_patients.py` | 5 | Pacientes y validación RUT Módulo-11 | PASS |
| `tests/demo/` | `test_practitioners.py` | 3 | Autenticación y facultativos | PASS |
| `tests/harness/` | `test_agentic_audit.py` | 6 | Auditoría de reglas y hallazgos | PASS |
| `tests/harness/` | `test_antecedentes.py` | 17 | Registro de procesamiento y paquete por titular | PASS |
| `tests/harness/` | `test_call_effects.py` | 4 | Resumen interprocedural de efectos | PASS |
| `tests/harness/` | `test_catalog.py` | 6 | Catálogo de controles multi-marco | PASS |
| `tests/harness/` | `test_catalog_corpus.py` | 2 | Corpus del catálogo | PASS |
| `tests/harness/` | `test_code_hygiene.py` | 10 | Higiene de código: cifrado, autorización y export | PASS |
| `tests/harness/` | `test_compliance_skills.py` | 12 | Skills de cumplimiento | PASS |
| `tests/harness/` | `test_context_bench.py` | 5 | Benchmark de contexto | PASS |
| `tests/harness/` | `test_context_semantic.py` | 5 | Contexto semántico | PASS |
| `tests/harness/` | `test_control_matrix.py` | 81 | Matriz de cobertura de los 37 controles | PASS |
| `tests/harness/` | `test_corpus.py` | 7 | Corpus de evaluación | PASS |
| `tests/harness/` | `test_cursor_pilot.py` | 31 | Piloto Cursor | PASS |
| `tests/harness/` | `test_data_lineage.py` | 3 | Linaje de datos sensibles | PASS |
| `tests/harness/` | `test_db_persistence.py` | 3 | Persistencia SQLite | PASS |
| `tests/harness/` | `test_dimension_policy.py` | 23 | Políticas por dimensión de la Ley 21.719 | PASS |
| `tests/harness/` | `test_doctor.py` | 1 | Diagnóstico del entorno | PASS |
| `tests/harness/` | `test_evidence.py` | 11 | Gate de evidencia documental | PASS |
| `tests/harness/` | `test_evidence_check.py` | 3 | Verificación de evidencia | PASS |
| `tests/harness/` | `test_exposure_policy.py` | 12 | Exposición de datos en respuestas de API | PASS |
| `tests/harness/` | `test_flow_bench.py` | 4 | Benchmark de flujo | PASS |
| `tests/harness/` | `test_framework_coverage.py` | 146 | Cobertura de frameworks y canales de detección | PASS |
| `tests/harness/` | `test_graph_engine.py` | 5 | Extracción AST y grafo | PASS |
| `tests/harness/` | `test_label_agreement.py` | 3 | Muestreo ciego y kappa de Cohen | PASS |
| `tests/harness/` | `test_normative_pack.py` | 73 | Paquete normativo Ley 21.719 | PASS |
| `tests/harness/` | `test_opencode_runner.py` | 10 | Runner de OpenCode | PASS |
| `tests/harness/` | `test_payment_policy.py` | 10 | Datos de pago persistidos | PASS |
| `tests/harness/` | `test_policy_engine.py` | 13 | Motor de políticas | PASS |
| `tests/harness/` | `test_policy_families.py` | 18 | Familias de detección | PASS |
| `tests/harness/` | `test_prd_skill.py` | 5 | Skill de PRD | PASS |
| `tests/harness/` | `test_precommit.py` | 18 | Compuerta de pre-commit | PASS |
| `tests/harness/` | `test_render.py` | 9 | Renderizado de artefactos | PASS |
| `tests/harness/` | `test_repo_config.py` | 1 | Configuración del repositorio | PASS |
| `tests/harness/` | `test_semgrep_bench.py` | 6 | Comparación con reglas Semgrep | PASS |
| `tests/harness/` | `test_skills_integrity.py` | 3 | Integridad de las skills | PASS |
| `tests/harness/` | `test_taint_flow.py` | 19 | Flujo de datos a nivel de llamadas | PASS |
| `tests/harness/` | `test_task_pack.py` | 3 | Paquete de tareas | PASS |
| `tests/harness/` | `test_validation_engine.py` | 2 | Motor de validación | PASS |
| `tests/harness/` | `test_variants.py` | 2 | Variantes de prueba | PASS |
| **TOTAL CONSOLIDADO** | **42 archivos** | **613** | **Cobertura de Harness y Aplicación Clínica** | **100% PASS** |

Del total, **592** pruebas corresponden al arnés (`tests/harness/`) y **21** a la aplicación clínica (`tests/demo/`).

**Evidencia de ejecución en consola:**

```
============================= test session starts =============================
platform win32 -- Python 3.13, pytest-9.0.3, pluggy-1.5.0
rootdir: C:\Users\<usuario>\Documents\<proyecto>
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
.....................................                                    [100%]

============================= 613 passed in 85.61s =============================
```
