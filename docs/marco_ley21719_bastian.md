# Requisitos Técnicos y Arquitectónicos de la Ley 21.719 para Sistemas de Salud: Matriz Determinista y Pipeline Agéntico de Análisis Estático (AST) y Taint Tracking

## 1. El Marco Regulatorio Chileno de Protección de Datos y su Impacto en la Arquitectura de Software

La promulgación y publicación de la Ley 21.719 el 13 de diciembre de 2024 reformó integralmente la Ley 19.628 sobre Protección de la Vida Privada, reconfigurando el ecosistema normativo digital chileno bajo los más altos estándares internacionales. Esta transformación legislativa establece un periodo de vacancia legal de veinticuatro meses, fijando su entrada en vigencia general para el 1 de diciembre de 2026. Con esta reforma, Chile abandona un modelo inorgánico de protección civil de baja intensidad para adoptar un esquema estructurado de responsabilidad proactiva y demostrable (*accountability*), convergente con el Reglamento General de Protección de Datos (RGPD) de la Unión Europea.

La gobernanza del nuevo sistema descansa en la Agencia de Protección de Datos Personales (APDP), corporación autónoma de derecho público dotada de facultades exclusivas para instruir fiscalizaciones, dictar resoluciones técnicas vinculantes y sancionar infracciones administrativas. El régimen sancionatorio tipifica las faltas en tres niveles escalonados:

- **Infracciones leves:** Sancionables con amonestación escrita o multas de hasta 5.000 Unidades Tributarias Mensuales (UTM).
- **Infracciones graves:** Tales como el tratamiento de datos personales sin base de licitud o la inobservancia del principio de proporcionalidad, con multas de hasta 10.000 UTM.
- **Infracciones gravísimas:** Aplicables al tratamiento de datos sensibles sin contar con consentimiento explícito o habilitación legal expresa, la exposición masiva por quiebres de seguridad y la cesión no autorizada, con multas que ascienden a 20.000 UTM o hasta el 4% de los ingresos anuales por ventas y servicios en empresas que no califiquen como de menor tamaño.

En el ámbito de la ingeniería de software, los principios consagrados en el artículo 3° reformado de la Ley 19.628 operan como restricciones deterministas del diseño de sistemas. El principio de licitud y lealtad exige que cada operación de lectura, escritura o transferencia cuente con una justificación jurídica demostrable en el código fuente, impidiendo el procesamiento encubierto. El principio de finalidad restringe el tratamiento exclusivamente a los objetivos explícitos declarados al recolectar el dato, prohibiendo su reutilización en subprocesos analíticos o comerciales secundarios. Por su parte, el principio de proporcionalidad y minimización obliga a reducir el volumen de datos capturados al mínimo estrictamente necesario para la funcionalidad requerida. Los principios de seguridad y confidencialidad imponen la preservación ininterrumpida del secreto profesional y de la integridad sistémica, subsistiendo este deber de manera indefinida aun tras extinguirse la relación con el paciente. Finalmente, el principio de responsabilidad comprobada invierte la carga procesal: ante cualquier controversia o incidente de seguridad, corresponde al responsable acreditar empíricamente ante la APDP la existencia y funcionamiento continuo de sus salvaguardas técnicas (artículo 14 quinquies).

| Artículo Legal (Ley 19.628 reformada por Ley 21.719) | Mandato Jurídico Sustantivo | Requisito Arquitectónico / Técnico en Software |
| :--- | :--- | :--- |
| **Art. 2° let. g) y 16° bis** | Definición y régimen de protección especial de datos de salud y perfil biológico humano. | Aislamiento lógico, cifrado a nivel de campo (*Field-Level Encryption*), control de acceso RBAC/ABAC granular. |
| **Art. 2° let. g) y 16° ter** | Regulación y régimen de retención de datos biométricos. | Almacenamiento restringido a representaciones matemáticas hash (*templates*), prohibición de imágenes en crudo y purga periódica. |
| **Art. 3° let. c) y 14° quáter** | Principios de proporcionalidad, minimización y privacidad desde el diseño y por defecto. | Esquemas de persistencia estrictos, eliminación de datos sensibles en URLs, exclusión de parámetros superfluos en APIs. |
| **Art. 7° Ley 19.628 vs Art. 13 Ley 20.584** | Derecho de cancelación frente al deber legal de conservación decenal de historiales médicos. | Implementación de patrones de borrado lógico (*soft-delete*), disociación y bloqueo criptográfico sin destrucción física durante 15 años. |
| **Art. 8° bis** | Garantías frente a decisiones individuales automatizadas y perfilamiento algorítmico. | Pistas de auditoría de inferencia (*audit trail*), explicabilidad de factores diagnósticos y compuertas de validación médica humana. |
| **Art. 9° y Ley 21.668** | Derecho a la portabilidad de datos y mandato de interoperabilidad de la ficha clínica. | Exposición de interfaces de programación interoperables estructuradas bajo el estándar HL7 FHIR R4 (perfil nacional CL Core). |
| **Art. 14° bis y 14° quinquies** | Deber de confidencialidad y medidas obligatorias de seguridad técnica (cifrado y seudonimización). | Forzado de TLS 1.3 en tránsito, cifrado AES-256-GCM en reposo y sanitización previa a la persistencia en cachés y registros de logs. |
| **Art. 14° sexies** | Deber perentorio de registrar y notificar brechas de seguridad ante la APDP y los titulares. | Monitoreo estructurado de accesos no autorizados, detección de anomalías de exfiltración y telemetría inmutable protegida con HMAC. |

---

## 2. Tipología y Clasificación de Datos en Entornos Clínicos: El Backend Médico

En el backend de un consultorio o centro médico asistencial, convergen múltiples flujos de información cuyos atributos presentan sensibilidades jurídicas disímiles. La ley clasifica la información en datos personales ordinarios, regulados bajo la regla general del artículo 12, y categorías especiales —reguladas en los artículos 16, 16 bis y 16 ter— que gozan de una prohibición basal de tratamiento y cesión, salvo excepciones normativas taxativas.

El Rol Único Tributario o Nacional (RUT/RUN), calificado como dato identificador directo conforme al artículo 2° letra a), permite individualizar de forma determinista a un usuario en todo el territorio de la República. En consecuencia, su persistencia y procesamiento exigen validación de dígito verificador, control de acceso autenticado y algoritmos de seudonimización en capas de analítica para evitar reidentificaciones colaterales.

Los datos de salud regulados por el artículo 16 bis abarcan diagnósticos médicos codificados (tales como clasificaciones CIE-10 o CIE-11), notas de evolución clínica, anamnesis, resultados de laboratorio, prescripciones farmacológicas y perfiles biológicos (datos genéticos, proteómicos o metabólicos). Esta categoría demanda la implementación de cifrado a nivel de columna y segregación lógica de esquemas, restringiendo su exposición a profesionales vinculados de forma directa a la atención asistencial del paciente.

Por último, los datos biométricos, regulados en el artículo 16 ter, comprenden la información obtenida a través de tratamientos técnicos específicos relativos a rasgos físicos, fisiológicos o conductuales (como huellas dactilares o patrones de geometría facial empleados para validar identidades en la emisión de licencias médicas o firma de consentimientos). Su tratamiento impone la prohibición absoluta de resguardar imágenes fotográficas o archivos biométricos sin procesar, exigiendo exclusivamente el almacenamiento de plantillas vectoriales irreversibles (*templates hash*) protegidas criptográficamente.

| Categoría de Información | Entidades y Modelos en Backend | Calificación Legal | Requisito Técnico Mandatorio de Arquitectura |
| :--- | :--- | :--- | :--- |
| **Identificadores Civiles Directos** | `rut`, `run`, `numero_documento`, `nombres`, `apellidos`, `fecha_nacimiento` | Dato Personal (Art. 2 let. a) | Validación canónica de formato módulo 11, seudonimización en entornos analíticos y ofuscación en logs de auditoría. |
| **Localización y Contacto** | `email`, `telefono`, `direccion_residencia`, `geolocalizacion_ips` | Dato Personal (Art. 2 let. a) | Minimización de captura (Art. 3 let. c), exclusión de esquemas públicos de API y segregación en tablas secundarias. |
| **Datos Clínicos y Diagnósticos** | `anamnesis`, `evolucion_clinica`, `cie10_code`, `prescripcion_farmaco`, `alergias` | Dato Sensible de Salud (Art. 16 bis) | Cifrado en reposo obligatorio con algoritmo AES-256-GCM, políticas RBAC/ABAC estrictas y trazabilidad inmutable de lecturas. |
| **Perfil Biológico Humano** | `secuencia_genomica`, `biomarcadores`, `perfil_metabolico` | Dato Sensible Crítico (Art. 16 bis) | Cifrado de sobre asimétrico, prohibición de cesión transfronteriza y almacenamiento segregado en bóvedas criptográficas. |
| **Patrones Biométricos** | `huella_template`, `vector_facial_embedding`, `iris_signature` | Dato Sensible Biométrico (Art. 16 ter) | Prohibición de imágenes de mapa de bits sin procesar; persistencia exclusiva de vectores hash matemáticos no reversibles. |
| **Trazabilidad y Auditoría** | `user_id`, `medico_rut`, `target_patient_id`, `ip_address`, `timestamp`, `action` | Metadatos de Seguridad (Art. 14 quinquies y sexies) | Registros de accesos inmutables, firmas criptográficas HMAC-SHA256 y canalización segura hacia sistemas SIEM. |

---

## 3. Obligaciones Técnicas Mandatorias: Seguridad, Retención e Interoperabilidad

### 3.1. Privacidad desde el Diseño, por Defecto y Medidas de Seguridad Técnicas

El artículo 14 quáter instituye la obligación legal de incorporar salvaguardas técnicas y organizativas desde las fases iniciales de diseño arquitectónico y a lo largo de todo el ciclo de desarrollo de software. Esta directriz impone que, de forma predeterminada, los sistemas operen bajo la configuración de privilegios mínimos y contención de datos, limitando el número de variables recolectadas, la extensión temporal de su almacenamiento, su visibilidad interna y los canales de acceso.

El artículo 14 quinquies explicita los estándares técnicos de seguridad obligatorios, vinculando la suficiencia de las medidas implementadas al estado del arte tecnológico y a los riesgos inherentes al procesamiento de categorías especiales. En primer término, la ley prescribe la seudonimización y el cifrado de datos personales como mecanismos prioritarios de mitigación. En almacenamiento en reposo (*data-at-rest*), esto exige que las columnas que albergan historiales y diagnósticos implementen algoritmos simétricos autenticados como AES-256-GCM o esquemas de cifrado de sobre (*envelope encryption*) integrados con sistemas dedicados de gestión de llaves (*Key Management Service*, KMS). En tránsito (*data-in-transit*), la comunicación interna entre microservicios, capas de persistencia y pasarelas de API debe forzar suites criptográficas modernas bajo TLS 1.3 con secreto perfecto hacia adelante (*Perfect Forward Secrecy*).

Asimismo, el artículo 14 quinquies demanda capacidades demostrables para garantizar la confidencialidad, integridad, disponibilidad y resiliencia de los sistemas de tratamiento. Esto se traduce en el endurecimiento contra inyecciones y accesos no autorizados, el resguardo de la inmutabilidad de los historiales clínicos mediante firmas de verificación criptográfica y la habilitación de mecanismos de respaldo continuo y recuperación ante contingencias capaces de restaurar la disponibilidad de la información de forma inmediata.

### 3.2. La Tensión Normativa: Minimización vs. Conservación Decenal de Fichas Clínicas

El análisis de flujo de información en sistemas médicos revela un conflicto regulatorio estructural que debe resolverse mediante un diseño determinista en la capa de persistencia:

1. Los artículos 3° letra c) y 7° de la Ley 19.628 consagran el principio de proporcionalidad y el derecho de cancelación o supresión, facultando al titular a exigir la destrucción inmediata de sus datos cuando estos carezcan de fundamento de uso. No obstante, el inciso final del artículo 7° delimita taxativamente las excepciones donde no procede la eliminación, destacando de manera expresa los tratamientos necesarios para *"el cumplimiento de una obligación legal"* (numeral ii) y *"por razones de interés público en el área de la salud pública"* (numeral iv).
2. Esta excepción legal se vincula armónicamente con la regulación sanitaria sectorial: el artículo 13 de la Ley 20.584 (que regula los derechos y deberes que tienen las personas en relación con acciones vinculadas a su atención de salud) y el Decreto Supremo N° 41 del Ministerio de Salud ordenan que el prestador de salud está legalmente obligado a conservar la ficha clínica por un periodo mínimo de quince años, computados desde la fecha del último registro asistencial del paciente.

Por consiguiente, los controladores del backend médico tienen prohibido ejecutar sentencias de borrado físico destructivo (`DELETE`) sobre tablas de historiales clínicos ante una solicitud de supresión formulada por un usuario. La solución técnica consiste en implementar un estado de bloqueo legal (artículo 8° ter de la Ley 19.628): el registro pasa a estado archivado restringido (`status: "BLOCKED_LEGAL_HOLD"`), se remueve de las interfaces operativas cotidianas del consultorio y sus llaves de descifrado se aíslan en almacenamiento frío. Solamente al expirar el umbral de quince años desde la última interacción médica, el sistema debe disparar procedimientos automatizados de destrucción criptográfica irreversibles para materializar el mandato de caducidad.

### 3.3. Portabilidad e Interoperabilidad Clínica: Ley 21.668 y Estándar HL7 FHIR

El artículo 9° de la Ley 19.628 establece el derecho de portabilidad, facultando al titular a requerir una copia de sus antecedentes en un formato electrónico estructurado, genérico, interoperable y de uso común que le permita transferirlos a otro proveedor de servicios sin interferencias técnicas.

En el ecosistema sanitario chileno, este mandato confluye con la Ley 21.668, publicada el 28 de mayo de 2024, que modifica la Ley 20.584 introduciendo la interoperabilidad técnica y universal de las fichas clínicas entre prestadores públicos y privados. En consonancia con las disposiciones técnicas emitidas por el Ministerio de Salud (MINSAL), el estándar arquitectónico exigible es HL7 FHIR R4 (*Fast Healthcare Interoperability Resources*), complementado por la Guía de Implementación local CL Core. Un backend médico que implemente la portabilidad clínica recurriendo a volcados propietarios en JSON planos, archivos CSV o reportes PDF sin estructurar contraviene la normativa vigente, configurando una restricción indebida al ejercicio de este derecho.

### 3.4. Decisiones Automatizadas y Supervisión Humana (Art. 8° bis)

El artículo 8° bis consagra el derecho del titular a no ser objeto de decisiones adoptadas de forma exclusivamente automatizada —incluyendo la formulación de perfiles algorítmicos— que generen efectos jurídicos o le afecten de manera significativa. En plataformas clínicas que incorporen motores de inteligencia artificial para triaje de urgencia, clasificación sintomática o priorización de consultas médicas, los pipelines de backend deben implementar obligatoriamente salvaguardas arquitectónicas de gobernanza algorítmica:

- Registro y entrega de explicabilidad técnica sobre las variables determinantes utilizadas por el modelo (artículo 14 ter letra l).
- Compuertas de supervisión profesional humana (*Human-in-the-Loop*), impidiendo que la inferencia algorítmica adquiera carácter resolutivo o vinculante sin la validación previa de un médico habilitado.
- Interfaces dedicadas a registrar impugnaciones y revisiones técnicas del juicio algorítmico.

### 3.5. Trazabilidad y Gestión de Brechas de Seguridad (Art. 14 sexies)

El artículo 14 sexies estipula la obligación de notificar a la APDP y a los titulares toda vulneración a las medidas de seguridad que produzca la destrucción, alteración, pérdida, filtración o acceso no autorizado a los datos, en la medida que configure un riesgo razonable para sus derechos. Tratándose de información sensible de salud o patrones biométricos, el reporte a los pacientes afectados adquiere carácter mandatorio. La norma prescribe que la notificación debe cursarse por los canales más expeditos y sin dilaciones indebidas. Para que una organización satisfaga dicho umbral probatorio, los sistemas de software deben generar registros de eventos estructurados que auditen de forma inmutable la temporalidad exacta, los actores intervinientes, los volúmenes de datos expuestos y las medidas de contención ejecutadas.

---

## 4. Arquitectura del Harness Agéntico: Modelado Formal de AST, Flujo de Datos y Taint Analysis

Para transformar las disposiciones de la Ley 21.719 en comprobaciones verificables de manera autónoma en un pipeline de ingeniería, el código fuente del backend médico debe abstraerse en estructuras matemáticas de análisis estático. El motor agéntico construye el Árbol de Sintaxis Abstracta (AST), el Grafo de Flujo de Control Interprocedural (ICFG) y el correspondiente Grafo de Flujo de Datos (*Data Flow Graph*, DFG).

Formalmente, el programa se define como un grafo de dependencias de flujo:

$$G = (V, E)$$

donde $V$ representa el conjunto de nodos del AST asociados a sentencias de asignación, parámetros, accesos a propiedades y llamadas a métodos, y $E$ corresponde a las aristas dirigidas que representan la propagación de datos o restricciones de control. El motor de análisis de contaminación (*Taint Analysis*) se formula mediante la cuádrupla determinista:

$$\mathcal{T} = (\mathcal{S}, \mathcal{P}, \mathcal{K}, \mathcal{R})$$

- **Fuentes contaminadas ($\mathcal{S}$ - Sources):** Agrupa las llamadas que extraen atributos de salud o identificadores directos desde la base de datos o desde los puntos de entrada HTTP (por ejemplo, llamadas a modelos ORM sobre tablas de pacientes, consultas SQL a historiales clínicos o lecturas del cuerpo de solicitudes con campos `rut` o `cie10`).
- **Propagadores ($\mathcal{P}$ - Propagators):** Define las relaciones de transmisión del estigma de contaminación a través del código. Se formaliza indicando que para cualquier arista $(u, v) \in E$, si el nodo $u$ está marcado como contaminado por datos sensibles, el estado se propaga invariablemente hacia $v$:

$$orall (u, v) \in E, \quad u \in 	ext{Tainted} \implies v \in 	ext{Tainted}$$

- **Puntos de fuga prohibidos ($\mathcal{K}$ - Sinks):** Abarca las funciones y destinos donde la persistencia o emisión del dato en claro configura un quiebre normativo: llamadas a funciones de logging en consola o archivos, persistencia en memorias caché compartidas sin cifrar, inyección de variables en cadenas de consulta (*query parameters*) o serializaciones directas en respuestas de API hacia redes externas.
- **Funciones sanitizadoras ($\mathcal{R}$ - Sanitizers):** Reúne las transformaciones de seguridad que cancelan la condición de contaminación al eliminar el riesgo de exposición indebida. Esto incluye invocaciones a funciones de encriptación simétrica autenticada (AES-GCM), derivaciones mediante algoritmos HMAC con sal de alta entropía, rutinas formales de disociación y enmascaramiento de RUT, o transformadores de serialización certificados bajo el estándar HL7 FHIR:

$$orall v \in V, \quad v \in \mathcal{R} \implies 	ext{Clean}(v)$$

El arnés agéntico identifica una vulnerabilidad legal en el repositorio si y solo si existe una trayectoria dirigida acíclica $\pi = \langle v_0, v_1, \dots, v_k angle$ en el grafo de flujo:

$$\exists \, \pi = \langle v_0, v_1, \dots, v_k angle \subseteq G$$

tal que:

$$v_0 \in \mathcal{S} \quad \land \quad v_k \in \mathcal{K} \quad \land \quad orall i \in \{0, \dots, k\}, \, v_i 
otin \mathcal{R}$$

| Componente Taint | Mapeo en Backend Médico | Patrones de Sintaxis Abstracta (AST) | Disposición Legal Infringida |
| :--- | :--- | :--- | :--- |
| **Source ($\mathcal{S}$)** | Consultas ORM a entidades de salud | `Patient.findOne(...)`, `MedicalRecord.find(...)`, `Biometrics.query(...)` | Acceso a categorías especiales de salud y biometría (Arts. 16 bis y 16 ter). |
| **Source ($\mathcal{S}$)** | Entradas no validadas de red | `req.body.rut`, `req.body.diagnostico`, `req.body.huella` | Captura de datos personales sensibles (Art. 3 let. a). |
| **Sink ($\mathcal{K}$)** | Emisión a librerías de logging | `logger.info(...)`, `console.log(...)`, `winston.error(...)`, `pino.debug(...)` | Quiebre del deber de secreto y confidencialidad (Arts. 14 bis y 14 quinquies). |
| **Sink ($\mathcal{K}$)** | Persistencia en caché distribuida | `redisClient.set(...)`, `cacheManager.put(...)`, `memcached.set(...)` | Almacenamiento no seguro de datos personales (Art. 14 quinquies). |
| **Sink ($\mathcal{K}$)** | Borrado físico destructivo | `repository.delete(...)`, `prisma.medicalRecord.delete(...)`, `DROP/DELETE SQL` | Infracción al deber de custodia de 15 años de la ficha médica (Ley 20.584 Art. 13). |
| **Sink ($\mathcal{K}$)** | Serialización sin anonimizar | `res.status(200).json(patient)` sin DTO de exclusión de datos clínicos | Vulneración al principio de minimización y proporcionalidad (Art. 3 let. c). |
| **Sanitizer ($\mathcal{R}$)** | Cifrado a nivel de campo | `crypto.encryptAesGcm(data, key)`, `kms.encryptField(...)` | Medida de seguridad conforme al Art. 14 quinquies. |
| **Sanitizer ($\mathcal{R}$)** | Enmascaramiento y hash seguro | `maskRut(rut)`, `crypto.createHmac('sha256', salt).update(rut)` | Seudonimización conforme al Art. 2 let. l). |
| **Sanitizer ($\mathcal{R}$)** | Transformación interoperable | `fhirSerializer.toPatientResource(data)`, `fhirCLCore.serialize(...)` | Cumplimiento del formato estructurado (Art. 9 y Ley 21.668). |

---

## 5. Matriz Determinista de Reglas de Detección y Reparación Automatizada (YAML)

Las siguientes reglas en formato Semgrep formalizan los patrones de búsqueda AST y de flujo contaminado que el subagente de auditoría evalúa sobre el código fuente del consultorio médico. Cada bloque YAML traduce un artículo específico de la Ley 19.628 reformada por la Ley 21.719 a una regla de detección y corrección automatizable.

### Regla 1: Fuga de Datos Clínicos Sensibles o RUT hacia Logs del Sistema

Esta regla audita el cumplimiento de los artículos 14 bis (deber de confidencialidad) y 14 quinquies (medidas de seguridad), tipificada como infracción grave bajo el artículo 34 ter letra j). Rastrea mediante Taint Analysis si campos clínicos protegidos alcanzan librerías de registro sin un método previo de sanitización o enmascaramiento.

```yaml
rules:
  - id: cl-privacy-health-data-leak-logging
    mode: taint
    languages: [javascript, typescript]
    severity: ERROR
    metadata:
      law: "Ley 19.628 reformada por Ley 21.719"
      article: "Art. 14 bis, Art. 14 quinquies, Art. 34 ter let. j)"
      cwe: "CWE-532: Insertion of Sensitive Information into Log File"
      remediation_action: "Inyectar función de enmascaramiento o remover variable sensible del logger"
    message: >-
      Se detectó la propagación de datos clínicos sensibles o identificadores (RUT) hacia los logs de la aplicación
      sin sanitización previa. Esto vulnera el deber de secreto y confidencialidad (Art. 14 bis) y constituye una
      infracción grave sancionable con hasta 10.000 UTM.
    pattern-sources:
      - patterns:
          - pattern-either:
              - pattern: $RECORD.$FIELD
              - pattern: $RECORD.get($FIELD)
          - metavariable-regex:
              metavariable: $FIELD
              regex: (?i)^(rut|run|diagnostico|anamnesis|receta|prescripcion|cie10|ficha_clinica|biometria|huella)$
      - patterns:
          - pattern: $DB.medical_records.findUnique(...)
          - pattern: $DB.patients.findMany(...)
    pattern-sanitizers:
      - patterns:
          - pattern-either:
              - pattern: maskRut(...)
              - pattern: redactMedicalData(...)
              - pattern: hashIdentifier(...)
              - pattern: crypto.createHmac(...)
    pattern-sinks:
      - patterns:
          - pattern-either:
              - pattern: console.log(...)
              - pattern: console.error(...)
              - pattern: console.warn(...)
              - pattern: logger.$METHOD(...)
              - pattern: winston.$METHOD(...)
              - pattern: pino.$METHOD(...)
```

### Regla 2: Exposición de Registros Médicos en Capa de Caché sin Cifrado en Reposo

Esta directriz fiscaliza el artículo 14 quinquies, el cual impone la exigencia de cifrado y disociación técnica para evitar filtraciones masivas de datos de carácter reservado. Detecta la escritura de registros de pacientes en servidores de caché sin aplicar criptografía autenticada.

```yaml
rules:
  - id: cl-privacy-unencrypted-cache-health-data
    mode: taint
    languages: [javascript, typescript]
    severity: ERROR
    metadata:
      law: "Ley 19.628 reformada por Ley 21.719"
      article: "Art. 14 quinquies, Art. 16 bis"
      cwe: "CWE-311: Missing Encryption of Sensitive Data"
      remediation_action: "Encapsular el valor serializado en un módulo de cifrado AES-256-GCM antes de escribir en caché"
    message: >-
      Almacenamiento de datos clínicos de salud o perfiles biológicos en la capa de caché sin cifrado previo.
      El artículo 14 quinquies exige el uso explícito de cifrado y seudonimización para prevenir filtraciones.
    pattern-sources:
      - patterns:
          - pattern-either:
              - pattern: $PRISMA.medicalRecord.findUnique(...)
              - pattern: $PRISMA.patient.findUnique(...)
              - pattern: $REPOSITORY.getClinicalHistory(...)
    pattern-sanitizers:
      - patterns:
          - pattern-either:
              - pattern: $CRYPTO.encryptAesGcm(...)
              - pattern: encryptEnvelope(...)
              - pattern: kms.encrypt(...)
    pattern-sinks:
      - patterns:
          - pattern-either:
              - pattern: $REDIS.set($KEY, $DATA, ...)
              - pattern: $REDIS.setex($KEY, $TTL, $DATA, ...)
              - pattern: $CACHE.put($KEY, $DATA, ...)
```

### Regla 3: Persistencia de Entidades de Salud sin Cifrado a Nivel de Campo (FLE) en el Modelo ORM

Esta regla ejecuta una verificación estática del principio de privacidad por diseño del artículo 14 quáter y de las medidas de seguridad del artículo 14 quinquies. Audita que las entidades que gestionan diagnósticos y evoluciones incluyan conversores o transformadores de cifrado en su definición estructural.

```yaml
rules:
  - id: cl-privacy-orm-missing-encryption-transformer
    mode: search
    languages: [typescript]
    severity: WARNING
    metadata:
      law: "Ley 19.628 reformada por Ley 21.719"
      article: "Art. 14 quáter, Art. 14 quinquies"
      cwe: "CWE-312: Cleartext Storage of Sensitive Information"
      remediation_action: "Inyectar EncryptionTransformer en la columna del modelo ORM"
    message: >-
      La entidad clínica almacena datos sensibles de salud (diagnóstico/anamnesis) sin un transformador de cifrado
      a nivel de columna. El principio de protección desde el diseño impone que la persistencia en base de datos
      esté cifrada en reposo mediante transformadores deterministas o probabilísticos según el caso.
    patterns:
      - pattern: |
          class $ENTITY {
            ...
            @Column(...)
            $FIELD: string;
            ...
          }
      - metavariable-regex:
          metavariable: $FIELD
          regex: (?i)^(diagnostico|anamnesis|cie10|receta|observacionesMedicas)$
      - pattern-not: |
          class $ENTITY {
            ...
            @Column({ ..., transformer: $TRANSFORMER, ... })
            $FIELD: string;
            ...
          }
```

### Regla 4: Borrado Físico Prematuro de Fichas Clínicas (Infracción a Ley 20.584 y Art. 7° Ley 19.628)

Esta verificación estática previene la destrucción prematura de registros asistenciales sujetos a la custodia obligatoria mínima de quince años establecida en el artículo 13 de la Ley 20.584, salvaguardando la excepción a la supresión del artículo 7° numeral ii de la Ley 19.628.

```yaml
rules:
  - id: cl-privacy-illegal-hard-delete-medical-record
    mode: search
    languages: [javascript, typescript]
    severity: ERROR
    metadata:
      law: "Ley 20.584 Art. 13; Ley 19.628 Art. 7° N° ii"
      article: "Art. 13 Ley 20.584 y Art. 7° Ley 19.628"
      cwe: "CWE-404: Improper Resource Shutdown or Release"
      remediation_action: "Reemplazar hard-delete por bloqueo temporal (soft-delete) con verificación de antigüedad > 15 años"
    message: >-
      Se detectó una operación destructiva de borrado físico (DELETE) sobre registros de la Ficha Clínica.
      El Art. 13 de la Ley 20.584 exige la custodia y conservación obligatoria por al menos 15 años. La supresión
      debe transformarse en un bloqueo de tratamiento (Art. 8° ter) o soft-delete archivado hasta agotar el término legal.
    patterns:
      - pattern-either:
          - pattern: $DB.medicalRecord.delete(...)
          - pattern: $DB.medicalRecord.deleteMany(...)
          - pattern: $REPO.remove($RECORD)
          - pattern: $REPO.delete($RECORD_ID)
          - pattern: $QUERYBUILDER.delete().from($TABLE).where(...).execute()
      - metavariable-regex:
          metavariable: $TABLE
          regex: (?i)^(medical_records|fichas_clinicas|atenciones|clinical_logs)$
```

### Regla 5: Exposición de Endpoints de Ficha Clínica sin Middleware de Autorización RBAC

Esta regla analiza la superficie de exposición de APIs para comprobar la implementación de controles de acceso restringido a la información clínica, conforme a los artículos 14 quáter y 14 quinquies de la Ley 19.628 y artículo 13 de la Ley 20.584.

```yaml
rules:
  - id: cl-privacy-unprotected-clinical-endpoint
    mode: search
    languages: [javascript, typescript]
    severity: ERROR
    metadata:
      law: "Ley 19.628 reformada por Ley 21.719"
      article: "Art. 14 quáter, Art. 14 quinquies, Ley 20.584 Art. 13"
      cwe: "CWE-285: Improper Authorization"
      remediation_action: "Inyectar middleware de autorización y verificación de rol médico habilitado"
    message: >-
      Endpoint de atención clínica expuesto sin validación de roles de acceso estrictos (RBAC/ABAC).
      La ley reserva el acceso a la ficha clínica exclusivamente a los profesionales tratantes directamente involucrados.
    patterns:
      - pattern-either:
          - pattern: |
              $ROUTER.get('/medical-records/:id', $HANDLER)
          - pattern: |
              $APP.get('/api/fichas/:id', $HANDLER)
      - pattern-not: |
          $ROUTER.get('/medical-records/:id', $AUTH_MIDDLEWARE, $ROLE_GUARD, $HANDLER)
      - pattern-not: |
          $APP.get('/api/fichas/:id', $AUTH_MIDDLEWARE, $ROLE_GUARD, $HANDLER)
```

### Regla 6: Pipeline de Inferencia Clínica sin Interceptor de Revisión Humana (Human-in-the-Loop)

Esta regla evalúa el cumplimiento del artículo 8° bis, impidiendo que procesos de inferencia predictiva o triaje algorítmico automaticen estados diagnósticos sin una compuerta de validación clínica presencial.

```yaml
rules:
  - id: cl-privacy-automated-decision-missing-human-review
    mode: search
    languages: [typescript, python]
    severity: WARNING
    metadata:
      law: "Ley 19.628 reformada por Ley 21.719"
      article: "Art. 8° bis"
      cwe: "CWE-693: Protection Mechanism Failure"
      remediation_action: "Establecer flag 'requires_human_validation: true' y bloquear transición de estado clínica definitiva"
    message: >-
      Se detectó la asignación automática de diagnósticos o categorización de triaje médico sin requerir
      revisión humana explícita. El artículo 8° bis garantiza el derecho a no ser objeto de decisiones automatizadas
      lesivas y obliga a incorporar intervención humana y explicabilidad de los modelos analíticos.
    patterns:
      - pattern: |
          const $DECISION = $MODEL.predict($PATIENT_DATA);
          ...
          await $DB.triageAssessment.create({
            data: {
              priority: $DECISION,
              status: "COMPLETED",
              ...
            }
          });
      - pattern-not: |
          const $DECISION = $MODEL.predict($PATIENT_DATA);
          ...
          await $DB.triageAssessment.create({
            data: {
              priority: $DECISION,
              status: "PENDING_PHYSICIAN_REVIEW",
              reviewedBy: null,
              ...
            }
          });
```

### Regla 7: Endpoint de Portabilidad de Ficha Clínica en Formato Propietario No Estructurado

Esta regla verifica la conformidad del endpoint de portabilidad con el estándar de entrega estructurada e interoperable fijado por el artículo 9° de la Ley 19.628 y la Ley 21.668 de Interoperabilidad Clínica (HL7 FHIR R4 CL Core).

```yaml
rules:
  - id: cl-privacy-non-fhir-portability-export
    mode: search
    languages: [typescript]
    severity: WARNING
    metadata:
      law: "Ley 19.628 Art. 9°; Ley 21.668 Art. 1°"
      article: "Art. 9° Ley 19.628; Ley 21.668"
      cwe: "CWE-20: Improper Input Validation"
      remediation_action: "Transformar la carga útil de respuesta en un Resource Bundle HL7 FHIR compatible con Guía CL Core"
    message: >-
      El endpoint de portabilidad de ficha clínica exporta un JSON genérico o no estandarizado. La Ley 21.668 y el
      Art. 9° de la Ley 19.628 mandatan la entrega estructurada interoperable mediante el estándar ministerial HL7 FHIR R4.
    patterns:
      - pattern: |
          $ROUTER.get('/api/patients/:id/export', async (req, res) => {
            ...
            const $DATA = await $DB.patient.findUnique(...);
            ...
            return res.json($DATA);
          })
      - pattern-not: |
          $ROUTER.get('/api/patients/:id/export', async (req, res) => {
            ...
            const $FHIR_BUNDLE = await $FHIR_SERVICE.buildPatientBundle($ID);
            ...
            return res.json($FHIR_BUNDLE);
          })
```

---

## 6. Pipeline de Remediación Agéntica: Flujo de Trabajo Autónomo de Parcheo (Harness Engineering)

El sistema agéntico opera como un arnés de ingeniería de software cerrado (*closed-loop harness*) estructurado para auditar, refactorizar y verificar el código sin intervención humana directa, garantizando la inviolabilidad semántica del repositorio y la resolución estricta de las falencias legales identificadas.

La arquitectura operacional del arnés se estructura a través de cinco etapas secuenciales claramente delimitadas en la matriz técnica del flujo de trabajo:

| Etapa del Pipeline Agéntico | Entrada Operacional | Procesamiento y Transformación Técnica | Salida Generada |
| :--- | :--- | :--- | :--- |
| **1. Auditoría y Taint Tracking** | Código fuente del backend (TypeScript / Python) y matriz de reglas Semgrep. | Generación de AST/CFG, mapeo de fuentes de salud ($\mathcal{S}$) y resolución de caminos acíclicos $\pi$ hacia puntos de fuga ($\mathcal{K}$). | Lista canónica de trayectorias vulnerables con metadatos normativos asociados. |
| **2. Síntesis y Representación Intermedia (IR)** | Hallazgos del análisis estático de datos. | Tipificación y contextualización sintáctica: archivo, número de línea, nodo AST, severidad y norma legal violada. | Documento JSON/IR normalizado de infracciones de privacidad. |
| **3. Parcheo y Reescritura AST** | Documento JSON/IR de violaciones y plantillas de mitigación deterministas. | Selección del patrón de reparación: inyección de funciones sanitizadoras, sustitución de métodos de persistencia y envoltura de modelos. | Código fuente refactorizado en una rama (*branch*) de aislamiento temporal. |
| **4. Verificación y Regresión** | Código refactorizado y suite de pruebas del proyecto. | Reanálisis estático formal para verificar la cancelación matemática del camino de contaminación ($\pi = \emptyset$) y ejecución de tests unitarios/integración. | Informe de regresión y certificación estática de eliminación de la vulnerabilidad. |
| **5. Commit y Registro de Control** | Parche validado y matriz de auditoría de seguridad. | Generación de Pull Request atómico con trazabilidad legal y generación del registro probatorio inmutable para la APDP. | Registro formal de cumplimiento (*compliance audit log*) firmado digitalmente. |

En la primera etapa, el arnés procesa los archivos del backend médico, construyendo el Grafo de Flujo de Datos ($G$). Al aplicar la matriz de reglas Semgrep, el motor marca con un estigma de contaminación (*taint*) todas las instancias en que se invocan modelos de datos clínicos o se leen identificadores como el RUT. Los caminos que alcancen funciones de salida como terminales de log, cachés o respuestas HTTP sin pasar por un nodo sanitizador son registrados como vulnerabilidades activas.

En la segunda etapa, las violaciones detectadas se condensan en un esquema intermedio estructurado (IR). Este formato proporciona al subagente de corrección un diagnóstico contextualizado que identifica con precisión el artículo legal vulnerado (por ejemplo, el artículo 14 bis ante una fuga en logging) y la estrategia técnica prescrita en el catálogo de remediación.

Durante la tercera etapa, un subagente LLM especializado en ingeniería de compiladores y transformaciones de AST procede a refactorizar el código fuente. El agente aplica transformaciones restringidas por plantillas formales de ingeniería de software:

- Si se identifica una fuga en logging, inyecta la dependencia de ofuscación correspondiente (`maskRut` o `redactMedicalData`) envolviendo el parámetro expuesto.
- Si detecta un modelo de datos clínicos sin cifrado de columna, introduce el transformador `@Column({ transformer: EncryptionTransformer })`.
- Si halla una operación de borrado físico directo sobre registros médicos, reescribe la sentencia hacia un patrón de bloqueo lógico (*soft-delete*) protegiendo el periodo decenal de quince años exigido por la Ley 20.584.

En la cuarta etapa, el arnés toma el código modificado y reejecuta el motor de análisis estático en la rama de aislamiento. Para certificar la reparación, el motor debe validar formalmente que el grafo ya no exhibe ningún camino hacia el sink no protegido. A continuación, el entorno ejecuta la batería completa de pruebas unitarias y de integración del consultorio médico para asegurar que el parche no haya introducido regresiones de comportamiento o roto la lógica asistencial preexistente.

Finalmente, en la quinta etapa, el pipeline genera un Pull Request atómico documentando el cambio estructural introducido. De manera simultánea, el sistema compila y firma digitalmente un reporte técnico de conformidad que sirve como evidencia auditable para acreditar la debida diligencia de acuerdo con el principio de responsabilidad comprobada del artículo 14 quinquies, permitiendo demostrar ante cualquier inspección de la Agencia de Protección de Datos Personales la efectividad de los controles implementados en el software.

---

## 7. Conclusiones y Hoja de Ruta para la Ingeniería de Privacidad

La entrada en vigor de la Ley 21.719 en diciembre de 2026 redefine la relación entre el ordenamiento jurídico y el diseño de sistemas informáticos en Chile. La conformidad regulatoria deja de ser una declaración formal redactada en manuales corporativos de políticas de privacidad para convertirse en una exigencia operativa que se audita directamente en las estructuras de datos, las configuraciones de los esquemas de persistencia y la topología de los flujos de información en el código fuente.

En los sistemas que gestionan información de salud, convergen de manera transversal las exigencias de cifrado simétrico en reposo a nivel de columna (artículo 14 quinquies), las restricciones de confidencialidad estricta en registros y cachés (artículo 14 bis), la armonización técnica del bloqueo legal frente al deber imperativo de custodia de quince años de las fichas clínicas (Ley 20.584) y la implementación obligatoria de interfaces estructuradas e interoperables bajo la especificación HL7 FHIR R4 CL Core (Ley 21.668).

El despliegue de un arnés agéntico gobernado por reglas deterministas basadas en el análisis del árbol de sintaxis abstracta (AST) y el rastreo de flujos contaminados (*Taint Tracking*) provee un mecanismo riguroso y sistemático para cerrar la brecha entre la ley y el código. Al transformar cada precepto normativo en una propiedad matemática verificable y susceptible de reparación automática, las instituciones de salud y los desarrolladores de plataformas médicas pueden garantizar una adaptación temprana y efectiva frente al régimen sancionatorio de la APDP, haciendo del principio de Privacidad desde el Diseño una realidad arquitectónica inmutable, continua y verificable.

---

## Obras citadas

1. Ley Chile - Ley 21719 - Biblioteca del Congreso Nacional - BCN, https://www.bcn.cl/leychile/Navegar?idNorma=1209272&idVersion=2024-12-13
2. Ley Chile - Ley 21719 - Biblioteca del Congreso Nacional de Chile, https://www.bcn.cl/leychile/navegar?idNorma=1209272
3. Ley 21.719: datos personales en funerarias | SFUN, https://sfun.co/ley-21719-proteccion-de-datos-funerarias-chile/
4. Aprobada Ley de Protección de Datos: ¿De qué trata? - Gob.cl, https://www.gob.cl/noticias/ley-proteccion-datos-personales-aprobacion-eleva-estandar-derechos/
5. Ley 21.719 en Chile: Guía Práctica para Empresas (Dic 2026) I XMS, https://xmslatam.com/ley-21719-proteccion-datos-chile/
6. Ley Nº 21.719 y la Reconstrucción del Derecho Chileno de, https://www.thomsonreuters.cl/es-cl/soluciones-juridicas/biblioteca-contenido-legal/ley-21719-y-la-reconstruccion-del-derecho-chileno-de-proteccion-de-datos-personales
7. Ley 21.719 de Protección de Datos Personales en Chile - Surtika, https://surtika.cl/ley-21719
8. Tratamiento de datos personales - BCN, https://obtienearchivo.bcn.cl/obtienearchivo?id=repositorio/10221/36715/1/Proteccion_datos_personales._Organismos_Publicos_f.pdf
9. Claves de la Ley 21.719: Así cambia la protección de datos en Chile, https://www.globalsuitesolutions.com/es/claves-ley-organica-proteccion-de-datos-personales-chile/
10. Ley 21.719: Nueva Ley de Protección de Datos en Chile - Netsus, https://netsus.com/ley-de-proteccion-de-datos-en-chile/
11. Artículo 34.- Infracciones leves, graves y gravísimas - Ley de Datos, https://ley.leydedatos.com/ley-21719/vk2CTQx4n1jzdJTXFE5f8i/art%C3%ADculo-34--infracciones-leves-graves-y-grav%C3%ADsimas/dmcNXrWKfKEsiKg4US24ft
12. Principios de tratamientos de datos - KLG Technology, https://klgtechnology.com/Soluciones/Ciberseguridad/Ley-de-Proteccion-de-Datos-Personales-en-Chile/Principios-de-tratamientos-de-datos
13. Ley 21.719: obligaciones técnicas para empresas - icaria Technology, https://icariatechnology.com/ley-21719-chile/
14. LEY 19.628 SOBRE PROTECCIÓN DE LOS DATOS PERSONALES, https://bitlaw.cl/ley-19-628-sobre-proteccion-de-los-datos-personales/
15. Artículo 3°: Principios. - Ley de Datos, https://ley.leydedatos.com/ley-21719/vk2CTQx4n1jzdJTXFE5f8i/art%C3%ADculo-3%C2%B0-principios/hg835xYfXfGrBfiDCEiDwQ
16. Ley 21.719 de datos personales, explicada para una empresa chica, https://estoyaldia.cl/ley-21719/
17. Ley Chile - Ley 19628 - Biblioteca del Congreso Nacional - BCN, https://www.bcn.cl/leychile/Navegar/imprimir?idNorma=141599&idParte=10528054&idVersion=2026-12-01
18. Carta abierta a los colegios sobre la Ley 21.719 - Base Segura, https://basesegura.org/cartas/ley-21719-colegios
19. Videovigilancia, control biométrico y seguimiento geolocalizado de, https://rjd.uandes.cl/index.php/rjduandes/article/download/190/213/422
20. ¿Qué es una Ficha Clínica? Guía Completa Chile 2026 | Clinera.io, https://www.clinera.io/blog/que-es-una-ficha-clinica
21. Ley 19.628 sobre Protección de Datos Personales, https://derechocienciaytecnologia.uc.cl/wp-content/uploads/2024/03/LEY-19.628-al-9-de-mayo-de-2023-Programa-de-Derecho-Ciencia-y-Tecnologia-UC-1.pdf
22. IA y protección de datos: Ley 21.719 · AlayIAtrust, https://alayiatrust.com/blog/ia-proteccion-datos-ley-21719
23. Portabilidad de la ficha médica: Ley 21.668 y plazos - Surtika, https://surtika.cl/blog/portabilidad-ficha-medica-ley-21668
24. "Sin dilación indebida": la cláusula que puede complicar a ... - Soyio, https://soyio.id/blog/sin-dilacion-indebida
25. Ley 21.668: diagnóstico de interoperabilidad de fichas clínicas | Fhiron, https://fhiron.cl/ley-21668
26. Surtika: Cumple la Ley 21.719 de protección de datos, https://surtika.cl/
27. Ecommerce para el sector salud en Chile, https://www.milaecommerce.com/ecommerce-sector-salud-chile
28. Ley 20.584 y Ficha Clínica: Marco Legal en Chile - Clinera O.S., https://www.clinera.io/blog/normativa-ficha-clinica-chile-ley-20584
29. La carencia de protección para los datos biométricos, https://repositorio.uchile.cl/bitstream/2250/203923/1/La-privacidad-en-el-ambito-laboral-en-Chile-la-carencia-de-proteccion-para-los-datos-biometricos.pdf
30. ¿cómo afecta la Ley 21.719 a la relación laboral? - CZ Abogados, https://czabogados.cl/proteccion-datos-personales-trabajadores-ley-21719/
31. Ley N° 21.719 que Regula la Protección y el Tratamiento de los, https://soykoda.cloud/herramientas/leyes/Ley%2021.719
32. Protección de datos para psicólogos en Chile: Ley 20.584 y ... - Freud, https://www.heyfreud.com/es/guias/proteccion-datos-psicologos-chile
33. politica-de-privacidad-y-de-proteccion-de-datos-personales - Autentia, https://web.autentia.cl/politica-de-privacidad-y-de-proteccion-de-datos-personales
34. Ley de Interoperabilidad de las Fichas Clínicas en Chile 2024, https://www.encuadrado.com/blog/ley-de-interoperabilidad-de-las-fichas-clinicas
35. Telemedicina en Chile: regulación, avances y perspectivas (2026), https://davix.ai/es/blog/telemedicina-chile-regulacion-avances/
36. Interoperabilidad de Salud en Chile: Estándares, Marco Legal y, https://gestionsaludaps.com/articles/interoperabilidad-salud-chile-aps
37. Ley 21.719 en clínicas privadas: qué exige de verdad, y tres cosas, https://cliniscribe.io/blog/ley-21719-clinicas-privadas-chile
38. Resumen práctico de la Ley 21719: protección de datos personales, https://fcgroup.cl/ley-21719-proteccion-datos-personales-resumen-practico-articulo-por-articulo/
