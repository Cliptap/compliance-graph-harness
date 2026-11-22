INFORME DE AVANCE — HITO 0:
DEFINICIÓN DEL PROYECTO
Estado: definición del proyecto y consolidación del diagnóstico actual.
Las capacidades indicadas como "propuestas", "planificadas" o "futuras" no forman
parte todavía de la implementación validada.
Proyecto: Arnés de Supervisión de Software Asistido por IA mediante Grafos de Dependencias
y Linaje de Datos bajo la Ley N° 21.719
Subtítulo / Caso de Estudio: Validación Experimental sobre un Sistema de Gestión Clínica
Transaccional y Linaje de Datos
Institución: Universidad Andrés Bello, Facultad de Ingeniería, Sede Viña del Mar — ITISB
Curso: Portafolio de Proyectos / Proyecto de Título
Integrantes:
● Andrés Tapia
● Bastian Oyanedel
Profesor Guía: David Araya
Fecha de Entrega: Semana del 28 de septiembre de 2026

Resumen ejecutivo
El desarrollo de software asistido por inteligencia artificial ha evolucionado desde herramientas
de autocompletado hacia agentes capaces de inspeccionar repositorios, utilizar herramientas y
ejecutar cambios sobre un sistema de software. Este cambio aumenta la velocidad potencial de
desarrollo, pero también introduce la necesidad de controlar el contexto entregado al agente, el
alcance de sus modificaciones y la verificación de los resultados.
Este proyecto propone el diseño y evaluación de un arnés de gobernanza para desarrollo de
software asistido por IA. El trabajo se origina en un proyecto desarrollado durante el semestre
anterior, donde se construyó una aplicación de gestión clínica utilizando un conjunto de
instrucciones y skills que fueron aumentando progresivamente según las necesidades de
desarrollo y gobernanza del sistema. A partir de esa experiencia se incorporaron mecanismos de
análisis estático, un grafo estructural de dependencias del repositorio, análisis heurístico de
linaje de datos y controles técnicos asociados a privacidad.
El artefacto actual se encuentra en una etapa de prototipado. Cuenta con doce skills
procedimentales, reglas permanentes de interacción, un motor de extracción de estructura de
código mediante AST y herramientas externas, persistencia SQLite para grafos y hallazgos, un
módulo de análisis de posibles fugas de datos y un visualizador de grafos. Además, existe una
aplicación clínica utilizada como banco de pruebas y una suite de 38 pruebas automatizadas
actualmente aprobadas.
Como resultado preliminar existe un experimento exploratorio anterior que comparó dos
configuraciones de instrucciones mediante OpenCode sobre tres tareas sintéticas. Este piloto
mostró diferencias en tiempo de ciclo y volumen de código generado, pero no evaluó el conjunto
completo del arnés, por lo que sus resultados se consideran evidencia preliminar y no una
validación del artefacto completo.
La investigación se desarrollará mediante un enfoque de ciencia del diseño (DSR)[3], orientado
a construir, demostrar y evaluar progresivamente el artefacto [1]. Como evolución prevista se
plantea mejorar las skills mediante activación y verificación explícitas, avanzar desde la
selección de archivos hacia contexto estructural a nivel de símbolos, formalizar políticas
evaluables por software, establecer compuertas de validación y definir un protocolo
experimental que permita separar el efecto de la gobernanza del efecto de la gestión de contexto.

1. Introducción
La ingeniería de software está experimentando una transformación asociada al uso de modelos
de lenguaje y agentes capaces de participar activamente en tareas de programación. En este
escenario, el desarrollador puede delegar actividades que anteriormente requerían inspección
manual, generación de código, ejecución de pruebas y modificaciones iterativas del repositorio.
El proyecto nace de una experiencia práctica realizada durante el semestre anterior.
Inicialmente, el objetivo era desarrollar una aplicación de gestión clínica utilizando asistencia de
IA mediante un conjunto de prompts y skills organizadas de acuerdo con las distintas etapas del
desarrollo. A medida que el sistema creció, también aumentaron las necesidades relacionadas
con consistencia arquitectónica, persistencia, auditoría, autenticación y tratamiento de
información sensible. Esta evolución llevó a experimentar con reglas permanentes, análisis
estructural del repositorio y mecanismos de auditoría.
A partir de dicha experiencia surge la pregunta de si estos mecanismos pueden organizarse
como un artefacto independiente de una aplicación particular, capaz de proporcionar una capa
de gobernanza alrededor del proceso de desarrollo asistido por IA.
En paralelo, el ecosistema de agentes de desarrollo ha avanzado hacia mecanismos como Agent
Skills, que empaquetan conocimiento y workflows especializados para ser cargados bajo
demanda, y hacia conceptos de harness engineering, donde el trabajo incluye diseñar contexto,
herramientas, verificaciones y mecanismos de feedback alrededor del agente. La especificación
abierta de Agent Skills establece SKILL.md como núcleo de una skill, con scripts, referencias y
recursos como componentes opcionales, y promueve la carga progresiva de información según la
tarea. [2]
El presente proyecto toma estas tendencias como referencia, pero no busca reemplazar de forma
inmediata la implementación existente. El objetivo del Hito 0 es formalizar el problema,
documentar el estado actual del artefacto y establecer una dirección de evolución que
posteriormente pueda ser validada experimentalmente.

Estructura del informe

| Bloque / Fase  | Sección  | Contenido Principal  |
| -------------- | -------- | -------------------- |
I. Fundamentación
| ❖   | Sección 2  | • Definición del problema y    |
| --- | ---------- | ------------------------------ |
| ❖   | .          | oportunidad de investigación.  |
❖
| ❖   | Sección 3  • Objetivos generales y específicos  |                |
| --- | ----------------------------------------------- | -------------- |
| ❖   |                                                 | del proyecto.  |
❖
| ❖   | Sección 4  • Justificación técnica/regulatoria  |                              |
| --- | ----------------------------------------------- | ---------------------------- |
| ❖   | .                                               | y delimitación del alcance.  |
❖
| ❖   | Sección 5  | • Estado del arte, marco  |
| --- | ---------- | ------------------------- |
conceptual y brecha identificada.
II. Metodología y Plan
❖
|     | Sección 6  | • Enfoque de Design Science  |
| --- | ---------- | ---------------------------- |
| ❖   | .          | Research (DSR) y diseño      |
❖
|     |     | experimental.  |
| --- | --- | -------------- |
❖
| ❖   | • Planificación por hitos, backlog  |     |
| --- | ----------------------------------- | --- |
Sección 7
MoSCoW y gestión de riesgos.
III. Solución Técnica
❖
|     | Sección 8                          | • Arquitectura actual,  |
| --- | ---------------------------------- | ----------------------- |
| ❖   | .  componentes del arnés y diseño  |                         |
❖
|     |     | en evolución.  |
| --- | --- | -------------- |
❖
| ❖   |     | • Incrementos desarrollados,  |
| --- | --- | ----------------------------- |
Sección 9
estado actual y deuda técnica.

IV. Evaluación y Cierre
❖
|     | Sección 10  • Batería de pruebas y resultados  |                                   |
| --- | ---------------------------------------------- | --------------------------------- |
| ❖   | .                                              | del estudio piloto exploratorio.  |
❖

| ❖   | Sección 11  • Discusión crítica, conclusiones  |                                 |
| --- | ---------------------------------------------- | ------------------------------- |
| ❖   |                                                | preliminares y trabajo futuro.  |
.
❖
| ❖   |     | • Referencias bibliográficas y  |
| --- | --- | ------------------------------- |
Sección 12
anexos previstos.

2. Problema u oportunidad
2.1 Situación actual
El uso de modelos de lenguaje para programación permite generar código, modificar archivos,
ejecutar pruebas y consultar información del repositorio con una velocidad superior a la
interacción manual tradicional. Sin embargo, la utilidad del resultado depende de que el agente
reciba contexto suficiente y pertinente, conozca las restricciones del proyecto y disponga de
mecanismos que permitan verificar sus cambios.
En el proyecto desarrollado durante el semestre anterior se observaron problemas que
motivaron la creación progresiva de instrucciones y skills. Entre ellos se encuentran la
incorporación de código no solicitado, la generación de dependencias innecesarias, la
modificación de archivos fuera del objetivo original y el aumento de esfuerzo requerido para
revisar los cambios generados.
Un segundo problema corresponde a la gestión del contexto. En el prototipo actual existe un
mecanismo de recorrido BFS(búsqueda en amplitud) sobre un grafo estructural del repositorio,
pero el resultado todavía termina concatenando archivos completos. Por lo tanto, el mecanismo
actual constituye una primera aproximación a la selección estructural de contexto, pero no una
extracción fina a nivel de funciones o símbolos.
Finalmente, existe un problema de gobernanza. Las reglas actuales presentes en AGENTS.md
sirven como instrucciones para el agente, pero no constituyen por sí mismas un mecanismo
determinista de enforcement. Esto significa que una regla siempre presente como "mantener el
alcance del MVP" puede ser ignorada por el modelo si posteriormente no existe un verificador
que compruebe el cambio producido.
2.2 Brecha
La oportunidad identificada consiste en estudiar cómo una capa de software alrededor del
agente puede combinar:
❖ Workflows de desarrollo especializados;
❖ Selección estructural de contexto;
❖ Políticas explícitas;
❖ Validación determinista;
❖ Trazabilidad de las decisiones y resultados.
La brecha que aborda el proyecto no es simplemente la generación de código mediante IA. El
foco está en la falta de una forma sistemática de gobernar y evaluar el comportamiento de

un agente durante el desarrollo, manteniendo al desarrollador como responsable de la
intención y aprobación final.
2.3 Pregunta del proyecto
¿Cómo impacta la incorporación de mecanismos de gobernanza enfocados en
controles técnicos de privacidad derivados de la Ley 21.719 y gestión estructural de
contexto en la eficiencia, calidad y control del desarrollo de software asistido por
IA frente a una asistencia generativa no gobernada?
-La pregunta será refinada durante los siguientes hitos a partir del estado del arte y del diseño
experimental definitivo.-
3. Objetivos
3.1 Objetivo general
Diseñar, implementar y evaluar un arnés de gobernanza para el desarrollo de software asistido
por IA, orientado a controlar el contexto, las restricciones del proyecto y la validación de
cambios producidos por agentes de programación—considerando controles técnicos de
protección de datos personales asociados a la Ley N° 21.719—, y medir su impacto frente a una
asistencia generativa no gobernada.
3.2 Objetivos específicos
1. Diseñar un catálogo de workflows de desarrollo asistido por IA, basado
inicialmente en las doce skills construidas durante el semestre anterior, incorporando
criterios explícitos de activación, ejecución y verificación.
2. Construir un mecanismo de gestión estructural de contexto, utilizando el
análisis de dependencias del repositorio para seleccionar información relevante para una
tarea de desarrollo y disminuir la incorporación de contexto innecesario.
3. Formalizar políticas de gobernanza evaluables por software, separando las
instrucciones dirigidas al modelo de los controles deterministas utilizados para detectar
violaciones de alcance, arquitectura, dependencias y privacidad asociadas a
normativas de la Ley N° 21.719.
4. Implementar un mecanismo de validación y feedback, capaz de ejecutar pruebas
y políticas sobre cambios propuestos y entregar evidencia estructurada para su
aceptación, rechazo o corrección.
5. Desarrollar y ejecutar un protocolo experimental, utilizando el sistema clínico
como banco de pruebas, que permita medir eficiencia, corrección, comportamiento del
agente, cumplimiento de políticas y efectos de la gestión de contexto.

4. Justificación y alcance
4.1 Justificación
Justificación técnica
Los agentes de programación introducen una diferencia respecto del desarrollo asistido por
autocompletado: pueden tomar múltiples acciones sobre el repositorio y producir cambios de
mayor alcance. Esto vuelve relevante contar con mecanismos que permitan controlar el contexto
que reciben, limitar las operaciones permitidas y comprobar los resultados.
La propuesta busca transformar controles actualmente declarativos en mecanismos que puedan
generar evidencia verificable. De esta forma, el agente puede encargarse de proponer y ejecutar
cambios dentro de un entorno controlado, mientras que el harness comprueba las condiciones
definidas para el proyecto.
Justificación académica
El proyecto permite estudiar un problema contemporáneo de ingeniería de software: la
interacción entre modelos generativos, agentes, herramientas, contexto y mecanismos de
verificación. La contribución esperada se centra en diseñar un artefacto de ingeniería y evaluar
empíricamente cómo distintos mecanismos de gobernanza afectan su comportamiento.
El enfoque es compatible con Design Science Research, la metodología orientada a identificar un
problema, definir objetivos para una solución, diseñar y desarrollar un artefacto, demostrarlo,
evaluarlo y comunicar los resultados.
Justificación regulatoria
El sistema utiliza información clínica como caso de estudio porque permite trabajar con una
gobernanza de datos con complejidad, requisitos de protección de datos y auditoría. La Ley N°
21.719 introduce, entre otros aspectos, el deber de protección desde el diseño y por defecto [4] y
medidas de seguridad para el tratamiento de datos personales. Su entrada en vigencia está
prevista para el 1 de diciembre de 2026.[5]
El proyecto no pretende certificar legalmente el cumplimiento de la Ley N° 21.719. En cambio,
estudia la traducción de determinados requisitos técnicos derivados de protección de datos a
reglas verificables mediante software, utilizando como caso inicial la prevención de exposición
de información sensible en registros y mecanismos de auditoría.

4.2 Alcance
El proyecto contempla:
1. Un arnés de gobernanza para desarrollo asistido por IA;
2. Un catálogo inicial de doce workflows basados en las skills existentes;
3. Mecanismos de análisis estructural del repositorio;
4. Selección de contexto para tareas de desarrollo;
5. Políticas técnicas de alcance, arquitectura y privacidad;
6. Mecanismos de validación mediante pruebas y análisis estático;
7. Un banco de pruebas basado en el sistema de gestión clínica desarrollado previamente;
8. Un runner experimental para comparar distintas configuraciones de gobernanza y
contexto;
9. Trazabilidad de resultados y evidencia de ejecución.
4.3 Fuera de alcance
En esta etapa se mantendrán fuera del alcance:
1. El fine-tuning de modelos de lenguaje;
2. El uso de modelos de lenguaje locales;
3. El desarrollo de una plataforma cloud de despliegue;
4. Un sistema multiagente complejo;
5. Una base de datos de grafos distribuida como requisito;
6. Certificación jurídica automática de cumplimiento;
7. Automatización completa de decisiones clínicas;
8. Una infraestructura de sandboxing de nivel empresarial.

5. Estado del arte, marco conceptual y
brecha
5.1 Desarrollo de software asistido por IA y
agentes de programación
El uso de modelos generativos en ingeniería de software ha evolucionado hacia agentes capaces
de inspeccionar repositorios, invocar herramientas y realizar ciclos de modificación y validación.
Esta evolución desplaza parte del trabajo del desarrollador desde escribir directamente el código
hacia especificar objetivos, proporcionar contexto y revisar los resultados.
El concepto de harness engineering surge precisamente en este contexto. OpenAI describe el
harness como el conjunto de entorno, estructura, herramientas y mecanismos de feedback[6]
que permiten a los agentes realizar trabajo de ingeniería de software de manera confiable.
Trabajos recientes también han propuesto modelos formales del harness como una capa que
media entre agente, proyecto y entorno[7], incluyendo responsabilidades como selección de
contexto, acceso a herramientas, memoria, observabilidad, permisos y verificación.
5.2 Agent Skills y workflows especializados
Agent Skills se ha consolidado como un formato abierto para proporcionar capacidades y
workflows especializados a agentes. La especificación establece como elemento mínimo una
carpeta con SKILL.md, cuyo frontmatter (bloque de metadatos situado al inicio) incluye name y
description; scripts, referencias y recursos son opcionales. El mecanismo contempla una carga
progresiva: descubrimiento mediante metadatos [2], activación del contenido completo cuando
la tarea corresponde y carga adicional de recursos solamente cuando son necesarios.
El repositorio agent-skills de Addy Osmani, referente destacado en la materia[8], propone una
anatomía práctica que incluye descripción de uso, workflow, señales de alerta y verificación
mediante criterios de salida.
Estas características presentan una relación directa con las doce skills desarrolladas en el
proyecto. Sin embargo, las skills actuales fueron diseñadas inicialmente como cuestionarios y
directivas de desarrollo, por lo que se plantea estudiarlas y evolucionarlas hacia workflows con
criterios de verificación.

5.3 Contexto estructural
Una dificultad del desarrollo con agentes es determinar qué parte del repositorio es pertinente
para una tarea concreta. El proyecto utiliza actualmente un grafo estructural compuesto por
archivos, clases, funciones, imports y llamadas, almacenado mediante SQLite y generado
parcialmente mediante AST y herramientas externas.
La implementación actual realiza un recorrido de vecinos sobre el grafo, pero el contexto
seleccionado todavía termina incluyendo los archivos completos para representar cada nodo.
Por ello, la siguiente etapa considera evolucionar hacia selección a nivel de símbolos y
componentes relevantes.
En esta etapa se evita asumir que una solución basada en embeddings o un RAG vectorial es
necesaria. La hipótesis inicial es que la estructura de dependencias del repositorio puede aportar
una forma determinista de seleccionar contexto para tareas de programación.
5.4 Gobernanza, políticas y verificación
La gobernanza propuesta diferencia las instrucciones entregadas al agente de las políticas
evaluables mediante software.
La primera corresponde a mecanismos como AGENTS.md o SKILL.md, cuyo propósito es
orientar el comportamiento. La segunda corresponde a reglas que pueden verificar
objetivamente un cambio, por ejemplo:
● Archivos modificados o creados fuera del alcance;
● Dependencias no autorizadas;
● Violaciones de arquitectura;
● Emisión de datos sensibles hacia sinks de logging;
● Fallas de pruebas.
La diferencia es relevante porque una instrucción puede ser ignorada por un modelo, mientras
que una validación determinista puede emitir un resultado PASS/FAIL independientemente de
la interpretación del agente.

5.5 Interoperabilidad
Una posible evolución consiste en exponer las funciones principales del arnés mediante Model
Context Protocol (MCP), sin convertir MCP en el proyecto. MCP permite a servidores exponer
tools, resources y prompts a clientes compatibles[10], y la especificación vigente contempla
mecanismos de autorización[9] y la necesidad de mantener participación humana en
operaciones sensibles.
En este proyecto MCP se considera inicialmente un posible adaptador de integración entre el
agente y el harness, no una funcionalidad de investigación independiente.
5.6 Privacidad y cumplimiento como código
La Ley N° 21.719 establece un deber de protección desde el diseño y por defecto y contempla
medidas de seguridad para el tratamiento de datos personales. La ley entra en vigencia el 1 de
diciembre de 2026.
En este proyecto, estos requisitos se traducen a controles técnicos concretos. Un ejemplo
corresponde a la prevención de exposición de datos personales en logs, relacionada con
CWE-532. Otro corresponde al diseño de esquemas y DTOs que eviten una exposición
innecesaria de información.
Por tanto, el concepto utilizado será “controles técnicos derivados de la Ley N° 21.719”, en lugar
de afirmar que el software por sí mismo certifica el cumplimiento jurídico.
5.7 Brecha identificada
El estado del arte evidencia una evolución hacia agentes, skills, herramientas, contexto dinámico
y harnesses. Sin embargo, el proyecto busca abordar específicamente la integración de estos
mecanismos bajo una lógica experimental:
workflow especializado + contexto estructural + políticas verificables +
validación determinista + evaluación reproducible.
La investigación buscará determinar si la combinación de estos mecanismos cambia de forma
medible el comportamiento y resultado de un agente de desarrollo.

6. Metodología
6.1 Enfoque de investigación
El proyecto utilizará un enfoque de Design Science Research, debido a que el objetivo principal
es diseñar y evaluar un artefacto tecnológico destinado a resolver un problema concreto.
La metodología considera las actividades de identificación del problema, definición de objetivos,
diseño y desarrollo, demostración, evaluación y comunicación.
Durante el semestre anterior ya se produjo una primera iteración del artefacto, que permitió
identificar necesidades adicionales de gobernanza. El Hito 0 toma ese aprendizaje y establece
una segunda etapa de diseño y evaluación.
6.2 Ciclo de desarrollo
El trabajo se organizará de manera iterativa:
1. Caracterización del problema;
2. Definición de requisitos;
3. Diseño del componente;
4. Implementación;
5. Demostración sobre tareas de desarrollo;
6. Evaluación;
7. Análisis de resultados;
8. Refinamiento del artefacto.
6.3 Diseño experimental proyectado
El experimento validador definitivo todavía no se encuentra implementado.
Como diseño preliminar se propone separar los factores:
Factor A — Gobernanza
● Sin políticas del harness;
● Con políticas del harness.
Factor B — Gestión estructural de contexto
● Contexto convencional;
● Contexto seleccionado mediante el grafo estructural.

Esto produce cuatro condiciones:
Condición Gobernanza Contexto estructural
A No No
B No Sí
C Sí No
D Sí Sí
– La configuración final del experimento será definida después de cerrar el
estado del arte y el protocolo de evaluación. –
6.4 Variables y métricas preliminares
Se consideran inicialmente:
Eficiencia
❖ Tiempo de ciclo;
❖ Latencia;
❖ Número de iteraciones;
❖ Cantidad de tokens utilizados, cuando pueda medirse de forma reproducible.
Calidad
❖ Pruebas aprobadas;
❖ Defectos introducidos;
❖ Cambios no solicitados;
❖ Líneas de código modificadas.

Gobernanza
❖ Violaciones de políticas;
❖ Violaciones de alcance;
❖ Violaciones arquitectónicas;
❖ Hallazgos de privacidad y cumplimiento normativo (Ley N° 21.719 / CWE-532);
❖ Índice o puntaje de cumplimiento (compliance score) alcanzado en el loop agéntico.
Contexto
❖ Cantidad de archivos recuperados;
❖ Cantidad de símbolos recuperados;
❖ Tokens de contexto;
❖ Proporción de contexto considerado relevante.
Esfuerzo de revisión
❖ Cambios manuales posteriores;
❖ Número de correcciones requeridas;
❖ Tiempo humano de revisión.
6.5 Datos y resguardos
El sistema clínico se utilizará como aplicación de demostración y banco de pruebas. Los datos
empleados durante las pruebas serán controlados por el proyecto y no se utilizarán registros
clínicos reales de pacientes.
El análisis de privacidad se centrará en código, estructuras y datos sintéticos necesarios para
reproducir escenarios técnicos.

6.6 Criterios de éxito preliminares
El proyecto considerará éxito técnico cuando:
● El harness pueda analizar un repositorio objetivo sin depender funcionalmente de su
lógica de negocio;
● Las skills puedan activarse y verificarse de manera reproducible;
● El mecanismo de contexto pueda generar conjuntos de información relevantes;
● Las políticas puedan emitir resultados verificables;
● Los cambios puedan someterse a validación automática;
● El experimento permita distinguir los efectos de gobernanza y gestión de contexto.
Los umbrales numéricos finales serán definidos antes del experimento principal.
6.7 Amenazas a la validez
Entre las amenazas identificadas se encuentran:
● Variabilidad entre modelos;
● Variabilidad entre sesiones de agente;
● Variabilidad entre ejecuciones del mismo modelo;
● Tamaño y dificultad de las tareas;
● Dependencia de herramientas externas;
● Sesgo del caso clínico;
● Dificultad para definir objetivamente una "alucinación";
● Posible confusión entre efecto de las instrucciones y efecto de otros componentes del
harness.
Estas amenazas serán incorporadas al diseño experimental.

7. Planificación y gestión
7.1 Hitos académicos
Hito Objetivo principal del proyecto
Hito 0 Definición del problema, estado del arte inicial, alcance, metodología,
planificación y presentación del producto existente.
Hito 1 Primer incremento funcional del harness y reorganización de las
skills/contexto según las decisiones aprobadas.
Consolidación del núcleo del arnés: Integración funcional del
catálogo de skills, motor de grafo de dependencias de contexto y
adaptación del caso de estudio clínico con controles técnicos
derivados de la Ley N° 21.719.
Hito 2 Integración de mecanismos de gobernanza, validación y evaluación
experimental inicial.
Implementación de loops agénticos y gobernanza: Desarrollo de
ciclos iterativos de auditoría y remediación autónoma (refinement
loops) que convergen mediante un sistema de puntuación de
cumplimiento normativo (compliance scoring) y criterios de parada,
junto con interfaces de observabilidad e inspección del grafo.
Hito 3 Producto consolidado, ejecución experimental y análisis crítico.
Validación experimental de escenarios: Ejecución del protocolo
experimental (comparación factorial A/B/C/D sobre escenarios de
prueba), recolección de métricas de eficiencia, calidad y análisis
crítico de resultados.
Hito 4 Informe final, resultados, conclusiones, limitaciones y trabajo futuro.

7.2 Backlog MoSCoW
| MUST  |     |     | SHOULD  |     |
| ----- | --- | --- | ------- | --- |
| ❖     |     |     |         | ❖   |
Definir arquitectura del harness;  Adaptar el harness mediante MCP;
❖  Mantener las doce skills y evolucionar  ❖  Incorporar aislamiento mediante Git
| su estructura;  |     |     |     | Worktrees;  |
| --------------- | --- | --- | --- | ----------- |
❖  Formalizar políticas técnicas;  ❖  Aumentar la cobertura de análisis de
❖
| Mejorar    | selección  | estructural  | de  | privacidad;                             |
| ---------- | ---------- | ------------ | --- | --------------------------------------- |
| contexto;  |            |              |     | ❖  Incorporar telemetría estructurada.  |
❖  Validar cambios mediante pruebas;
❖  Establecer benchmark reproducible;
❖
| Implementar  |     | evaluación  |     |     |
| ------------ | --- | ----------- | --- | --- |
experimental.
| COULD  |     |     | WON ’ T  |     |
| ------ | --- | --- | -------- | --- |
❖  Integrar  herramientas  externas  de  ❖  Multiagentes complejos;
| análisis estático;  |     |     |     | ❖  Entrenamiento de modelos;  |
| ------------------- | --- | --- | --- | ----------------------------- |
❖  Incorporar más tipos de policies.  ❖  Infraestructura cloud;
❖  Sandbox de nivel empresarial;
❖  Certificación jurídica automática.

7.3 Riesgos
|     | Riesgo  |     | Impacto  |     | Mitigación inicial  |
| --- | ------- | --- | -------- | --- | ------------------- |
Alcance excesivo  Alto  Priorizar mecanismos relacionados con la
pregunta de investigación.
Variabilidad de modelos  Alto  Fijar condiciones experimentales y registrar
configuración.
Falta de evidencia causal  Alto  Utilizar comparación factorial/ablación.
Dependencia de una  Medio  Separar físicamente el benchmark de la
| aplicación  |     |     |     |     | herramienta.  |
| ----------- | --- | --- | --- | --- | ------------- |
Complejidad de integración  Medio  Implementación incremental y posible uso de
| con agentes  |     |     |     |     | MCP como adaptador.  |
| ------------ | --- | --- | --- | --- | -------------------- |
Sobreingeniería  Alto  Mantener componentes mínimos y justificar
cada incorporación por una hipótesis.
7.4 Trazabilidad preliminar
| Objetivo  |     | Componente  |     | Evidencia prevista  |     |
| --------- | --- | ----------- | --- | ------------------- | --- |
OE1  Skills Registry  Skills verificables + pruebas de activación/adherencia
OE2  Context Engine  Context packages + métricas de reducción de contexto
OE3  Policy Engine  Findings PASS/FAIL + políticas técnicas de
privacidad (Ley N° 21.719)
| OE4  |     | Validation Engine  |     | Tests + reports + feedback            |     |
| ---- | --- | ------------------ | --- | ------------------------------------- | --- |
| OE5  |     | Evaluator          |     | Dataset de experimentos + resultados  |     |

8. Diseño de la solución
8.1 Arquitectura actual
Este diseño corresponde al estado actual del prototipo y no representa la arquitectura objetivo
del proyecto.

8.2 Componentes actuales
Skills y reglas:
La carpeta .agents/skills/ contiene doce workflows organizados por etapas del desarrollo,
desde PRD hasta documentación. AGENTS.md contiene reglas generales de interacción con el
agente.
Grafo estructural:
src/harness/graph_engine.py utiliza análisis AST y datos provenientes de una herramienta
externa para construir una representación de archivos, símbolos y dependencias.
En la evolución del proyecto se propone utilizar el término Grafo Estructural de
Dependencias del Repositorio, debido a que la implementación actual no constituye una
ontología semántica general.
Linaje y privacidad:
data_lineage.py identifica posibles fuentes y sinks relacionados con información sensible
mediante heurísticas sobre el código.
Auditoría:
agentic_audit.py evalúa reglas técnicas y almacena los resultados en SQLite.
Validación:
La suite actual contiene 38 pruebas automatizadas: 21 asociadas al sistema clínico y 17
asociadas a los componentes del harness.

8.3 Arquitectura en evolución
La dirección propuesta para los siguientes hitos consiste en separar:
Esta arquitectura se considera una dirección de diseño, no una funcionalidad ya implementada.
8.4 Reproducibilidad
El proyecto utiliza Python para los componentes del harness, SQLite para la persistencia de sus
análisis y Pytest para pruebas. El sistema clínico utiliza FastAPI, SQLAlchemy y Vue 3.
La configuración, y procedimiento de ejecución serán documentados progresivamente para
permitir que los experimentos sean reproducibles.

9. Desarrollo e incrementos
9.1 Incremento anterior: aplicación clínica
Durante el semestre anterior se desarrolló una aplicación de gestión clínica con backend,
frontend, autenticación, persistencia y mecanismos de auditoría.
La aplicación constituye actualmente el principal banco de pruebas del proyecto.
9.2 Incremento anterior: pipeline de skills
Se desarrolló un conjunto de doce skills destinadas a organizar el desarrollo desde definición de
requerimientos hasta documentación.
Estas skills representan el antecedente directo del componente de workflows del harness.
9.3 Incremento anterior: análisis estructural
Se implementaron componentes para extraer símbolos y relaciones del código, persistir el
resultado en SQLite y visualizar el grafo mediante D3.js.
9.4 Incremento anterior: análisis de privacidad
Se implementó un módulo heurístico de linaje y auditoría para identificar posibles flujos hacia
mecanismos de logging.
9.5 Incremento actual: consolidación del Hito 0
Durante la formulación de este proyecto se detectó que parte de la documentación describe
ciertas capacidades como si ya estuvieran implementadas. Este Hito 0 busca separar
explícitamente:
● Capacidades actuales;
● Capacidades experimentales;
● Capacidades proyectadas.
Esta separación será utilizada como línea base para los siguientes incrementos.

9.6 Deuda técnica identificada
Entre las principales deudas conocidas se encuentran:
● Rutas de pruebas antiguas dentro del pipeline;
● Parcheo basado en reemplazo de texto fijo;
● Dependencia de instrucciones para parte de las restricciones del agente;
● Selección de contexto a nivel de archivo completo;
● Acoplamiento físico entre el benchmark clínico y el harness;
● Heurísticas de linaje que no representan un análisis completo de flujo de datos;
● Diferencias entre algunas afirmaciones documentales y el comportamiento real del
repositorio.
Estas deudas no serían resueltas todas en el Hito 0
10. Pruebas, evaluación y resultados
preliminares
10.1 Pruebas del producto actual
La suite actual contiene 38 pruebas automatizadas y constituye la principal evidencia funcional
disponible:
● 21 pruebas para el sistema clínico;
● 17 pruebas para el motor del harness.
El conjunto cubre, entre otros aspectos, pacientes, citas, validación de RUT, auditoría,
extracción AST, slicing BFS, linaje y persistencia.
10.2 Estudio piloto exploratorio
Antes de este Hito 0 se realizó un experimento exploratorio utilizando OpenCode CLI y el
modelo minimax-m3.
Se utilizaron tres tareas sintéticas:
● T01: Validador de RUT chileno;
● T02: Endpoint de citas con parámetros y RBAC;
● T03: Sanitización de nombres propios.

Se compararon dos condiciones de instrucciones. El piloto informó diferencias en tiempo de
ciclo, tokens, líneas de código y cantidad de archivos modificados.
La evidencia actualmente disponible indica una reducción de aproximadamente 22,4 % en el
tiempo de ciclo bajo la configuración evaluada. Sin embargo, el experimento no evaluó el
conjunto completo del arnés actual: no intervino el módulo de grafo, no intervino el módulo de
cumplimiento y no representó el pipeline completo de las doce skills.
Por lo tanto, estos resultados se presentan en este informe únicamente como:
Estudio piloto exploratorio preliminar.
No se utilizarán para afirmar todavía que el harness completo produce una mejora causal
determinada.
10.3 Evaluación futura
El experimento principal será diseñado posteriormente para medir por separado los efectos de
gobernanza y contexto estructural.
Se buscará reportar:
1. Protocolo;
2. Condiciones;
3. Tarea;
4. Modelo;
5. Configuración;
6. Número de repeticiones;
7. Resultados;
8. Evidencia;
9. Limitaciones.
Se evitará utilizar "cero alucinaciones" como afirmación general mientras no exista una
definición reproducible del término y un protocolo de detección al respecto

11. Discusión, conclusiones y trabajo
futuro
11.1 Discusión preliminar
El avance realizado hasta el Hito 0 permite observar que el proyecto posee una base tecnológica
y una trayectoria evolutiva coherente: comenzó como desarrollo asistido por IA mediante
prompts, evolucionó hacia un conjunto de skills y posteriormente incorporó mecanismos de
análisis estructural y privacidad.
La principal dificultad identificada corresponde a que actualmente estos mecanismos no se
encuentran todavía integrados en un ciclo único de gobernanza alrededor del agente.
Esto conduce a una distinción central para el desarrollo posterior:
● Skill → Orienta al agente
● Context → Determina qué información necesita
● Policy → Define qué está permitido
● Validator → Determina si el resultado cumple
● Humano → Mantiene la decisión final
La arquitectura futura se desarrollará sobre esta separación, evitando convertir cada
componente nuevo en una dependencia obligatoria.
11.2 Conclusiones preliminares
El proyecto presenta una oportunidad de investigación aplicable al desarrollo de software
asistido por IA, debido al crecimiento de agentes capaces de modificar repositorios y operar
herramientas.
El prototipo existente demuestra factibilidad técnica inicial mediante un conjunto de skills,
análisis estructural, auditoría y pruebas automatizadas. Sin embargo, todavía no permite
afirmar que el conjunto constituye un harness plenamente integrado ni que los resultados piloto
demuestran causalmente el efecto de sus componentes.
Por esta razón, el objetivo del siguiente incremento será convertir las capacidades existentes en
componentes mejor definidos y evaluables, conservando el trabajo previo y evitando
modificaciones arquitectónicas que no tengan una relación directa con la pregunta de
investigación.
La pregunta del proyecto y los objetivos específicos serán revisados después de la
retroalimentación correspondiente al Hito 0.

11.3 Trabajo futuro
El trabajo previsto incluye:
1. Perfeccionar el catálogo de skills con criterios de uso y verificación;
2. Evolucionar el contexto estructural hacia una selección más precisa;
3. Formalizar políticas técnicas;
4. Implementar un ciclo de validación y feedback;
5. Separar el sistema clínico como benchmark;
6. Evaluar la posible integración mediante MCP;
7. Definir un experimento controlado y reproducible;
8. Ejecutar la evaluación principal;
9. Analizar resultados y amenazas a la validez.
12. Referencias y anexos
12.1 Referencias iniciales
[1] Agent Skills. Specification. Formato abierto de Agent Skills. Disponible en:
https://github.com/agentskills/agentskills/blob/main/docs/specification.mdx
[2] Agent Skills. Overview. Formato abierto y modelo de progressive disclosure. Disponible
en: https://github.com/agentskills/agentskills
[3] Peffers, K., Tuunanen, T., Rothenberger, M. A., & Chatterjee, S. (2007). A Design Science
Research Methodology for Information Systems Research. Journal of Management
Information Systems, 24(3), 45–77.
[4] Biblioteca del Congreso Nacional de Chile. Ley N° 21.719: Regula la protección y el
tratamiento de los datos personales y crea la Agencia de Protección de Datos Personales.
Disponible en: https://www.bcn.cl/leychile/navegar?idNorma=1209272

[5] Biblioteca del Congreso Nacional de Chile. Ley N° 21.719 — versión con vigencia diferida
al 1 de diciembre de 2026. Disponible en:
https://www.bcn.cl/leychile/Navegar?idNorma=1209272&idParte=10527471&idVersion=2026-
12-01
[6] OpenAI. (2026). Harness engineering: leveraging Codex in an agent-first world. Disponible
en: https://openai.com/index/harness-engineering/
[7] Zhong, H., & Zhu, S. (2026). AI Harness Engineering: A Runtime Substrate for
Foundation-Model Software Agents. arXiv:2605.13357.
[8] Osmani, A. Agent Skills — Skill Anatomy. Disponible en:
https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md
[9] Model Context Protocol. Specification — Tools. Disponible en:
https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2
026-07-28/server/tools.mdx
[10] Model Context Protocol. Specification — Overview. Disponible en:
https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2
026-07-28/basic/index.mdx