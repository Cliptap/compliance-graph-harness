# Ley N° 21.719 — public-source map by dimension

**Purpose.** Map every compliance dimension of Ley N° 19.628 as reformed by Ley N° 21.719 to its article, a short verbatim excerpt, and the kind of evidence a code audit can or cannot produce. Feeds T9–T13 of `odd/tasks/harness-consolidation.md` (specs S6, S7).

**Retrieval date.** 2026-10-28 for every source below.

**Method.** Article text was read from the official BCN LeyChile text of Ley 21.719 (version "Con Vigencia Diferida por Fecha De : 01-DIC-2026", last modification Ley 21.806 of 05-FEB-2026), and spot-checked against the Diario Oficial publication (CVE 2583630). No secondary source was used for article content. Article numbers refer to Ley 19.628 **as reformed** (Ley 21.719, "Artículo primero" introduces them).

**Limitation.** This is source verification, not legal advice; interpretation remains pending legal review. Every control derived from this map stays `legal_review: pending`.

## Sources

| ID | Source | URL | Type |
|---|---|---|---|
| P1 | Ley 21.719, BCN LeyChile export (deferred version 2026-12-01, "documento generado el 28-Oct-2026") | https://nuevo.leychile.cl/servicios/Consulta/Exportar?exportar_con_notas_al_pie=False&exportar_con_notas_bcn=False&exportar_con_notas_originales=False&exportar_formato=pdf&hddResultadoExportar=1209272.2026-12-01.0.0%23&nombrearchivo=Ley-21719_13-DIC-2024&radioExportar=Normas | Primary |
| P2 | Ley 21.719, BCN norma page (shows Ley 21.806 annotations) | https://www.bcn.cl/leychile/navegar?idNorma=1209272 | Primary |
| P3 | Diario Oficial N° 44.023, 13-12-2024, CVE 2583630 | https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf | Primary |
| P4 | Ley 19.628, BCN consolidated text (currently shows the **pre-reform** text) | https://www.bcn.cl/leychile/navegar?idNorma=141599 | Primary |
| P5 | Decreto 662 (Hacienda), reglamento of the compliance model (Art. 49), BCN | https://www.bcn.cl/leychile/navegar?idNorma=1227971 | Primary |
| P6 | Decreto 662, Diario Oficial 09-09-2026, CVE 2865940 | https://www.diariooficial.interior.gob.cl/publicaciones/2026/09/09/44546/01/2865940.pdf | Primary |
| P7 | Ley 19.496 Art. 28 B as quoted by SERNAC (official agency) | https://www.sernac.cl/portal/609/w3-propertyvalue-58918.html | Official (not BCN) |
| P8 | Decreto 62 (2020), "No Molestar" reglamento, BCN | https://www.bcn.cl/leychile/Navegar?idNorma=1142343 | Primary |
| P9 | Ley 20.584, BCN consolidated text | https://www.bcn.cl/leychile/navegar?idNorma=1039348 | Primary |

**Entry into force (P1, transitional Art. primero).** "entrarán en vigencia el día primero del mes vigésimo cuarto posterior a la publicación de esta ley en el Diario Oficial." Publication 13-12-2024, so 1-12-2026 (also stated in P5 recital 3).

**Ley 21.806 (05-02-2026).** On P2 its annotations only touch transitional Art. cuarto (appointment of the Agency council). No substantive obligation changed, as far as the annotations show.

---

## 1. Principles (Art. 3°)

- **Article:** Art. 3° letters a)–h). P1.
- **Excerpts:**
  - a) "Los datos personales sólo pueden tratarse de manera lícita y leal. El responsable deberá ser capaz de acreditar la licitud del tratamiento de datos personales que realiza."
  - b) "Los datos personales deben ser recolectados con fines específicos, explícitos y lícitos. El tratamiento de los datos personales debe limitarse al cumplimiento de estos fines."
  - c) "Los datos personales que se traten deben limitarse estrictamente a aquéllos que resulten necesarios, adecuados y pertinentes en relación con los fines del tratamiento."
  - d) "Los datos personales deben ser exactos, completos, actuales y pertinentes"
  - e) "Quienes realicen tratamiento de los datos personales serán legalmente responsables del cumplimiento de los principios"
  - f) "el responsable debe garantizar estándares adecuados de seguridad, protegiéndolos contra el tratamiento no autorizado o ilícito, y contra su pérdida, filtración, daño accidental o destrucción."
  - g) transparency: the policies and practices "deberán encontrarse permanentemente accesibles y a disposición de cualquier interesado de manera precisa, clara, inequívoca y gratuita."
  - h) "El responsable establecerá controles y medidas adecuadas para preservar el secreto o confidencialidad."
- **Obligation for the controller:** yes (Art. 33 sanctions infringement of Art. 3° principles).
- **Code evidence:** minimisation (unused personal fields in schemas/DTOs, over-broad API responses), security (encryption, access control), confidentiality (no personal data in logs). **Documentary only:** lawfulness record, purpose register, data-quality procedures, accountability.

## 2. Lawful bases and consent (Arts. 12, 13, 2° p)

- **Art. 12 (consent), P1:** "El consentimiento del titular debe ser libre, informado y específico en cuanto a su finalidad o finalidades. El consentimiento debe manifestarse, además, en forma previa y de manera inequívoca". Withdrawal: "El titular puede revocar el consentimiento otorgado en cualquier momento y sin expresión de causa, utilizando medios similares o equivalentes a los empleados para su otorgamiento." Means "deben ser expeditos, fidedignos, gratuitos y estar permanentemente disponibles". Burden: "Corresponde al responsable probar que contó con el consentimiento del titular".
- **Art. 12, bundling presumption:** "Se presume que el consentimiento para tratar datos no ha sido libremente otorgado cuando el responsable lo recaba en el marco de la ejecución de un contrato o la prestación de un servicio en que no es necesario efectuar esa recolección."
- **Art. 13 (other bases), P1:** a) economic/financial/banking/commercial obligations under Title III; b) legal obligation; c) "necesario para la celebración o ejecución de un contrato entre el titular y el responsable"; d) "intereses legítimos del responsable o de un tercero, siempre que con ello no se afecten los derechos y libertades del titular"; e) legal claims. Closing: "El responsable deberá acreditar la licitud del tratamiento de datos."
- **Art. 2° p) definition:** "toda manifestación de voluntad libre, específica, inequívoca e informada, otorgada a través de una declaración o una clara acción afirmativa".
- **Obligation:** yes.
- **Code evidence:** consent record persisted with timestamp/purpose/version; no pre-ticked consent defaults; a withdrawal path as reachable as the grant path; consent checked before processing for consent-based purposes. **Documentary:** choice and justification of the legal basis per purpose, legitimate-interest balancing.

## 3. Data-subject rights (Arts. 4°–11, 8° bis, 8° ter)

- **Art. 4°, P1:** "tiene derecho de acceso, rectificación, supresión, oposición, portabilidad y bloqueo de sus datos personales". Rights "no pueden limitarse por ningún acto o convención."
- **Art. 5° (acceso):** includes "f) La información significativa sobre la lógica aplicada en el caso de que el responsable realice tratamiento de datos de conformidad con el artículo 8° bis."
- **Art. 6° (rectificación):** "Efectuada la rectificación, no se podrán volver a tratar los datos sin rectificar." Rectified data must be communicated to recipients.
- **Art. 7° (supresión):** grounds a)–f) (unnecessary, consent withdrawn, unlawful, "datos caducos", legal order, opposition). Exceptions i.–vi., e.g. "ii. Para el cumplimiento de una obligación legal o la ejecución de un contrato suscrito entre el titular y el responsable."
- **Art. 8° (oposición):** includes "b) Si el tratamiento se realiza exclusivamente con fines de mercadotecnia o marketing directo de bienes, productos o servicios, incluida la elaboración de perfiles".
- **Art. 8° bis (automated decisions):** "El titular de datos tiene derecho a oponerse y a no ser objeto de decisiones basadas en el tratamiento automatizado de sus datos personales, incluida la elaboración de perfiles, que produzca efectos jurídicos en él o le afecte significativamente." In every case the controller must secure "el derecho a obtener una explicación, a la intervención humana, a expresar su punto de vista y a solicitar la revisión de la decisión."
- **Art. 8° ter (bloqueo):** "derecho a solicitar la suspensión temporal de cualquier operación de tratamiento de sus datos personales cuando formule una solicitud de rectificación, supresión u oposición".
- **Art. 9° (portabilidad):** copy "en un formato electrónico estructurado, genérico y de uso común", when processing is automated **and** consent-based.
- **Art. 10 (means):** "Los responsables de datos deberán implementar mecanismos y herramientas tecnológicas que permitan que el titular ejerza sus derechos en forma expedita, ágil y eficaz." Rectification, erasure and opposition always free; access free at least quarterly.
- **Art. 11 (deadlines):** "pronunciarse a más tardar dentro de los treinta días corridos siguientes a la fecha de ingreso de la solicitud. Este plazo podrá ser prorrogado, por una sola vez, hasta por treinta días corridos." Temporary block: answer "dentro de los dos días hábiles siguientes a su recepción", and "En tanto no resuelva esta solicitud, el responsable no podrá tratar los datos del titular que forman parte del requerimiento." The controller must keep proof of the reply (date and full content).
- **Obligation:** yes.
- **Code evidence:** endpoints/handlers for access, rectification, erasure (or anonymisation), opposition, portability export in a structured format, a `blocked` state honoured by processing paths, request timestamps and SLA tracking (30 + 30 days, 2 business days for blocks), a human-review path for automated decisions. **Documentary:** response templates, denial reasoning, identity-verification procedure (defined by the Agency).

## 4. Duty of information and transparency (Art. 14 ter, Art. 3° g)

- **Art. 14 ter, P1:** the controller "debe facilitar y mantener permanentemente a disposición del público, en su sitio web o en cualquier otro medio de información equivalente, al menos, la siguiente información:" a) policy with date and version; b) controller identity and "encargado de prevención, si existiere"; c) contact channel for requests; d) data categories, recipients, purposes, "la base de legitimidad del tratamiento" and the legitimate interests relied on; e) security policy and measures; f) ARCOP rights; g) right to complain to the Agency; h) international transfers and adequacy/guarantees; i) "El periodo durante el que se conservarán los datos personales."; j) data source; k) right to withdraw consent; l) "La existencia de decisiones automatizadas, incluida la elaboración de perfiles. En tales casos, información significativa sobre la lógica aplicada".
- **Obligation:** yes; failure is a leve infraction (Art. 34 bis a).
- **Code evidence:** a privacy-policy route/page exists and is linked, with version/date fields; contact channel exposed. **Documentary:** the policy content against items a)–l).

## 5. Sensitive data and special categories (Arts. 2° g, 16, 16 bis, 16 ter, 16 quáter, 16 quinquies, 16 sexies)

- **Full legal list, Art. 2° g), P1:** "datos personales que se refieren a las características físicas o morales de las personas o a hechos o circunstancias de su vida privada o intimidad, que revelen el origen étnico o racial, la afiliación política, sindical o gremial, la situación socioeconómica, las convicciones ideológicas o filosóficas, las creencias religiosas, los datos relativos a la salud, al perfil biológico humano, los datos biométricos, y la información relativa a la vida sexual, a la orientación sexual y a la identidad de género de una persona natural."
  - Note for controls: **"la situación socioeconómica"** is in the sensitive list, which matters for e-commerce (income, credit scoring).
- **Art. 16 (rule):** sensitive data only "cuando el titular a quien conciernen estos datos manifiesta su consentimiento en forma expresa", plus closed exceptions a)–f).
- **Art. 16 bis (health, biological profile):** health and genetic/proteomic/metabolic data "sólo podrán ser tratados para los fines previstos por las leyes especiales en materia sanitaria". Prohibition: health data collected "en el ámbito laboral, educativo, deportivo, social, de seguros, de seguridad o identificación" cannot be processed or transferred unless a law authorises it.
- **Art. 16 ter (biometrics):** "aquellos obtenidos a partir de un tratamiento técnico específico, relativos a las características físicas, fisiológicas o conductuales de una persona que permitan o confirmen la identificación única de ella, tales como la huella digital, el iris, los rasgos de la mano o faciales y la voz." The controller must inform: the biometric system, the specific purpose, the period of use, and how to exercise rights.
- **Art. 16 quáter (children and adolescents):** "sólo puede realizarse atendiendo al interés superior de éstos y al respeto de su autonomía progresiva." Children's data need parental/guardian consent. Adolescents follow adult rules, except: "Los datos personales sensibles de los adolescentes menores de dieciséis años sólo se podrán tratar con el consentimiento otorgado por sus padres o representantes legales". Thresholds: "se consideran niños o niñas a los menores de catorce años, y adolescentes, a los mayores de catorce y menores de dieciocho años."
- **Art. 16 quinquies (research/statistics):** treated as a legitimate interest if exclusively for those public-interest purposes, with quality/security measures; publish only anonymised results.
- **Art. 16 sexies (geolocation):** yes, regulated: "se podrá realizar bajo las mismas fuentes de licitud establecidas en los artículos 12 y 13." The data subject must be informed "del tipo de datos de geolocalización que serán tratados, de la finalidad y duración del tratamiento y si los datos se comunicarán o cederán a un tercero".
- **Obligation:** yes. Infractions: Art. 34 ter g) (minors), Art. 34 quáter e) (knowingly processing sensitive or minors' data unlawfully).
- **Code evidence:** classification of sensitive fields in schemas; explicit-consent flag before sensitive processing; age/date-of-birth gating with thresholds 14 and 16; geolocation collection guarded by consent/notice; biometric templates not stored raw. **Documentary:** legal-exception justification, best-interest analysis for minors.

## 6. Security and breach notification (Arts. 14 quinquies, 14 sexies, 14 septies, 15 bis)

- **Art. 14 quinquies, P1:** measures "deben asegurar la confidencialidad, integridad, disponibilidad y resiliencia de los sistemas de tratamiento de datos." Includes "a) La seudonimización y el cifrado de datos personales." … "c) La capacidad de restaurar la disponibilidad y el acceso a los datos personales de forma rápida en caso de incidente físico o técnico. d) Un proceso de verificación, evaluación y valoración regulares de la eficacia de las medidas". Burden of proof after an incident lies on the controller.
- **Art. 14 sexies, P1:** report to the Agency "por los medios más expeditos posibles y sin dilaciones indebidas" breaches causing "destrucción, filtración, pérdida o alteración accidental o ilícita" or unauthorised access, "cuando exista un riesgo razonable para los derechos y libertades de los titulares." The controller "deberá registrar estas comunicaciones". Data subjects must also be notified when breaches concern "datos personales sensibles, datos relativos a niños y niñas menores de catorce años o datos relativos a obligaciones de carácter económico, financiero, bancario o comercial".
  - **No fixed hour deadline** (e.g. 72 h) appears in the article text.
- **Art. 14 septies:** differentiated minimum standards for Arts. 14 ter and 14 quinquies "serán determinados por la Agencia mediante instrucción general."
- **Art. 15 bis (processors):** "Tratándose de una vulneración a las medidas de seguridad, el tercero o mandatario deberá reportar este hecho al responsable."
- **Obligation:** yes. Infractions: Art. 34 ter j) and k); Art. 34 quáter f) ("Omitir en forma deliberada la comunicación de las vulneraciones").
- **Code evidence:** encryption at rest/in transit, pseudonymisation, access control, audit logs, backups/restore, an incident register data model. **Documentary:** incident response plan, Agency/titular notification procedure, periodic security testing records.

## 7. Privacy by design/default and impact assessment (Arts. 14 quáter, 15 ter)

- **Art. 14 quáter, P1:** "el responsable debe aplicar medidas técnicas y organizativas adecuadas desde el diseño con anterioridad y durante el tratamiento". By default, "sólo sean objeto de tratamiento los datos personales específicos y estrictamente necesarios para dicha actividad. Para ello, se tendrá en consideración el número de datos recogidos, la extensión del tratamiento, el plazo de conservación y su accesibilidad."
- **Art. 15 ter, P1:** when processing "pueda producir un alto riesgo para los derechos de las personas titulares", an assessment is required "previo al inicio de las operaciones del tratamiento". Always required for: "a) Evaluación sistemática y exhaustiva de aspectos personales … como la elaboración de perfiles"; "b) Tratamiento masivo de datos o a gran escala."; "c) … observación o monitoreo sistemático de una zona de acceso público."; "d) Tratamiento de datos sensibles y especialmente protegidos, en las hipótesis de excepción del consentimiento." The Agency publishes the orientative list and minimum guidelines.
- **Obligation:** yes. Breach of Art. 15 ter is gravísima (Art. 34 quáter k).
- **Code evidence:** privacy-protective defaults (opt-in flags default `false`, minimal default fields, restricted default visibility), detection of profiling/large-scale processing triggers. **Documentary:** the impact assessment itself.

## 8. Processors and data sharing (Arts. 15 bis, 15, 2° x, 2° v)

- **Art. 15 bis, P1:** the processor acts "conforme al encargo y a las instrucciones que le imparta el responsable". Contract contents: "En el contrato se deberá establecer el objeto del encargo, la duración del mismo, la finalidad del tratamiento, el tipo de datos personales tratados, las categorías de titulares a quienes conciernen los datos, y los derechos y obligaciones de las partes." Sub-processing: "El encargado no podrá delegar parte o la totalidad del encargo, salvo que conste una autorización específica y por escrito del responsable." End of service: data "deben ser suprimidos o devueltos al responsable". Processors must comply with Arts. 14 bis and 14 quinquies. The Agency publishes model contracts.
- **Art. 15 (cesión to another controller):** with consent or contract/legitimate interest/law; must be in writing identifying parties, data and purposes; cession without required consent "será nula".
- **Obligation:** yes (controller and processor).
- **Code evidence:** inventory of third-party SDKs/APIs receiving personal data (payment, analytics, email, hosting), data sent per integration. **Documentary:** processor contracts (DPAs) with the listed clauses, sub-processor authorisations.

## 9. International transfers (Arts. 27, 28, 29)

- **Art. 27, P1:** lawful when the recipient country offers adequate protection, or covered by "cláusulas contractuales, normas corporativas vinculantes, u otros instrumentos jurídicos", or a certified compliance model. Without adequacy or guarantees, only a "transferencia específica y que no sea habitual" under exceptions, e.g. "a) Cuando exista consentimiento expreso del titular" or "g) … necesaria para la celebración o ejecución de un contrato entre el titular y el responsable".
- **Art. 28:** the Agency determines adequate countries and publishes "un listado de países adecuados y modelos tipo de cláusulas contractuales". "Corresponderá al responsable de datos que efectuó la transferencia internacional de datos, acreditar ante la Agencia que ésta se practicó de conformidad a las reglas establecidas en esta ley."
- **Obligation:** yes. Infractions: Art. 34 ter m), Art. 34 quáter h).
- **Code evidence:** hosting/region configuration, foreign SaaS endpoints receiving personal data (partial evidence of *where* data goes). **Documentary:** adequacy decision or SCC/BCR, transfer register.

## 10. Retention, storage limitation, deletion (Arts. 3° c, 14 d, 7°, 14 ter i, 17, 18)

- **Art. 3° c), P1:** "Los datos personales pueden ser conservados sólo por el período de tiempo que sea necesario para cumplir con los fines del tratamiento, luego de lo cual deben ser suprimidos o anonimizados, sin perjuicio de las excepciones que establezca la ley. Un período de tiempo mayor requiere autorización legal o consentimiento del titular."
- **Art. 14 d):** "Suprimir o anonimizar los datos personales del titular cuando fueron obtenidos para la ejecución de medidas precontractuales."
- **Art. 2° k) anonymisation:** "procedimiento irreversible"; "Un dato anonimizado deja de ser un dato personal." Art. 2° l) pseudonymised data remain personal data (only re-attributable with separate information).
- **Financial data, Art. 17 (new inciso, Ley 21.719 Art. primero N° 9 c), P1):** "Los responsables deberán suprimir de sus registros o bases de datos, toda aquella información personal relativa a obligaciones prescritas, sin necesidad de mediar solicitud". **Art. 18 (P4, unchanged text):** "En ningún caso pueden comunicarse los datos a que se refiere el artículo anterior … luego de transcurridos cinco años desde que la respectiva obligación se hizo exigible."
- **Obligation:** yes.
- **Code evidence:** TTL/retention jobs, purge or anonymisation routines, retention fields per entity, true anonymisation vs reversible pseudonymisation. **Documentary:** retention schedule per purpose with legal justification.

## 11. Data protection officer and compliance model (Arts. 48–53; Decreto 662)

- **Art. 48, P1 (mandatory):** controllers "deberán adoptar acciones destinadas a prevenir la comisión de las infracciones establecidas en los artículos 34 bis, 34 ter y 34 quáter."
- **Art. 49 (voluntary model):** "Los responsables de datos podrán voluntariamente adoptar un modelo de prevención de infracciones consistente en un programa de cumplimiento." Minimum elements a)–g): DPO designation, DPO means, data inventory, risk-generating processes, protocols, internal and Agency reporting (Art. 14 sexies), internal sanctions.
- **Art. 50 (DPO):** "El responsable de datos podrá designar un delegado de protección de datos personales." The DPO must have autonomy; SMEs' owners may act as DPO. Functions include "c) Supervisar el cumplimiento de la presente ley" and "h) Cooperar y actuar como punto de contacto de la Agencia."
- **Art. 51:** Agency certifies the model; certificate is a mitigating factor (Art. 36 N° 5). **Art. 52:** certificates valid three years.
- **Decreto 662 (P5/P6), recital 6:** the DPO's "designación es obligatoria en el marco del modelo de prevención de infracciones".
- **Obligation:** Art. 48 is mandatory; the model (Art. 49) and DPO (Art. 50) are **voluntary** for private controllers, except that a DPO is mandatory **inside** an adopted model.
- **Code evidence:** none meaningful (a DPO contact in the privacy policy is the most a repo can show). **Documentary:** program, DPO appointment, annual plan, certificate.

## 12. Infractions and sanctions (Arts. 33–40)

- **Art. 34 bis (leves), P1:** e.g. "a) Incumplir total o parcialmente el deber de información y transparencia, establecido en el artículo 14 ter." and "c) Omitir la respuesta, responder en forma incompleta o fuera de plazo, las solicitudes formuladas por el titular".
- **Art. 34 ter (graves):** e.g. "a) Tratar los datos personales sin contar con el consentimiento del titular de datos o sin un antecedente o fundamento legal"; "c) Efectuar tratamiento de datos personales innecesarios"; "e) Impedir u obstaculizar el ejercicio legítimo de los derechos"; "g) … niños, niñas y adolescentes"; "i) Vulnerar el deber de secreto o confidencialidad establecido en el artículo 14 bis."; "j) Vulnerar o infringir las obligaciones de seguridad … artículo 14 quinquies."; "k) Omitir las comunicaciones o los registros en los casos de vulneración de las medidas de seguridad establecidas en el artículo 14 quinquies."; "m) … transferencia internacional … en contravención".
- **Art. 34 quáter (gravísimas):** e.g. "a) Efectuar tratamiento de datos personales en forma fraudulenta."; "d) Vulnerar el deber de secreto o confidencialidad sobre los datos personales sensibles"; "e) Tratar, comunicar o ceder, a sabiendas, datos personales sensibles o datos personales de niños, niñas y adolescentes"; "f) Omitir en forma deliberada la comunicación de las vulneraciones"; "k) Incumplir la obligación establecida en el artículo 15 ter".
- **Art. 35 (sanctions):** "a) Las infracciones leves serán sancionadas con amonestación escrita o multa de hasta 5.000 unidades tributarias mensuales. b) Las infracciones graves serán sancionadas con multa de hasta 10.000 unidades tributarias mensuales. c) Las infracciones gravísimas serán sancionadas con multa de hasta 20.000 unidades tributarias mensuales." For non-SME reoffenders: up to "2% o 4% de los ingresos anuales por ventas y servicios". Corrective measures within 60 days or a 50% surcharge.
- **Arts. 36–38:** mitigating/aggravating factors (recidivism = two or more sanctions in 30 months); fine criteria including sensitive/minors' data; accessory suspension up to 30 days for repeated gravísimas. **Art. 39:** public Registro Nacional de Sanciones y Cumplimiento. **Art. 40:** actions prescribe in four years.
- **Transitional Art. sexto:** during the first 12 months, SMEs may receive a written warning instead.
- **Use in the harness:** severity mapping for findings (leve/grave/gravísima), not a detector.

## 13. Direct marketing, commercial communications, credit data (e-commerce)

- **Marketing opposition, Art. 8° b) (P1):** see section 3; opposition to processing "exclusivamente con fines de mercadotecnia o marketing directo … incluida la elaboración de perfiles". Profiling definition Art. 2° w): "evaluar, analizar o predecir aspectos relativos al rendimiento profesional, situación económica, de salud, preferencias personales, intereses, fiabilidad, comportamiento, ubicación o movimientos".
- **Commercial e-mail, Ley 19.496 Art. 28 B (P7 SERNAC; also quoted verbatim in Decreto 62, P8):** "Toda comunicación promocional o publicitaria enviada por correo electrónico deberá indicar la materia o asunto sobre el que versa, la identidad del remitente y contener una dirección válida a la que el destinatario pueda solicitar la suspensión de los envíos, que quedarán desde entonces prohibidos." Decreto 62 creates SERNAC's "No Molestar" system.
- **Ley 21.719 Art. tercero (P1):** "Suprímese el artículo 15 bis de la ley N° 19.496". The content of the deleted article was **not** retrieved (see gaps).
- **Credit/financial data, Arts. 13 a), 17–19 (P1, P4):** processing of financial-obligation data without consent only "de conformidad con las normas del Título III"; Art. 17 now covers "cumplimiento o incumplimiento"; prescribed obligations must be deleted ex officio; five-year communication limit (Art. 18). Breaches involving financial data trigger notice to data subjects (Art. 14 sexies).
- **Payment card data:** no PCI-type rule exists in this law; card data are personal data protected by Arts. 3° f), 14 quinquies. Any PCI-DSS control is an **internal standard**, not a legal obligation.
- **Code evidence:** unsubscribe link + subject + sender in marketing templates; marketing opt-in flag separate from contract processing; suppression list honoured; profiling features gated. **Documentary:** marketing consent records, No Molestar list reconciliation.

---

## Verification of the 14 existing controls' citations (`.harness/packs/cl-ley-21719.json`)

Checked against P1 (Ley 19.628 reformed) and P9 (Ley 20.584). Ley 21.668 itself was not fetched; its role was read from P9's amendment annotations.

| Control / item | Cited | Verdict |
|---|---|---|
| category health (line 31) | Art. 2° g), 16 bis | Verified |
| category biometric (line 50) | Art. 2° g), 16 ter | Verified |
| category RUT (line 63) | Art. 2° **a)**, 14 bis | **Mismatch**: Art. 2° a) defines "Almacenamiento de datos". The identifier ("el número de cédula de identidad") is in **Art. 2° f)**. |
| category contact (line 74) | Art. 3° c), 14 quáter | Verified |
| category audit metadata (line 86) | 14 quinquies, 14 sexies | Verified (14 quinquies last inciso: controller must prove measures; 14 sexies: register of breach communications) |
| CL-DATAPROT-001, CORE-CHECK-002 | 14 bis, 14 quinquies, 34 ter **j)** | **Partial**: confidentiality breach is Art. 34 ter **i)**; j) is security. For sensitive data the confidentiality breach is gravísima, Art. 34 quáter d). |
| CL-DATAPROT-002 | 14 quinquies, 16 bis | Verified |
| CL-DATAPROT-003, -005, CORE-CHECK-001 | `article` "Art. 14°" vs `citation` "Art. 14° quáter" | **Inconsistent fields**: Art. 14° is general controller obligations; the citation (14 quáter) is the correct one. |
| CL-DATAPROT-004 | Ley 20.584 Art. 13; 19.628 Art. 7° N° ii, 8° ter | Verified (Ley 20.584 Art. 13: "conservar la ficha clínica por un período de al menos quince años"; Art. 7° exception ii) |
| CL-DATAPROT-006, CORE-CHECK-004 | Art. 8° bis | Verified |
| CL-DATAPROT-007, HEALTH-CHECK-002 | Art. 9°; Ley 21.668 **Art. 1°** | **Mismatch**: P9 annotations show Ley 21.668 has an "Art. único" that amended Ley 20.584 Arts. 12–13. HEALTH-CHECK-002 also lists "Art. 1°" under law `L19628`. |
| CORE-CHECK-003 | `article` "Art. 14°"; citation Arts. 5°–10°, 14 quáter | **Inconsistent fields**; Art. 11 (procedure and deadlines) is missing and relevant. |
| HEALTH-CHECK-001 | `article` "Art. 13, Art. 7° inc. final, Art. 8° ter" under `L19628` | **Mismatch**: "Art. 13" belongs to Ley 20.584, not Ley 19.628 (whose Art. 13 is "Otras fuentes de licitud"). |
| HEALTH-CHECK-003 | Art. 2° g), 16 bis | Verified; Ley 20.584 Art. 12 (P9) confirms clinical-record data are "dato sensible, de conformidad con lo dispuesto en la letra g) del artículo 2º de la ley Nº 19.628". |
| CL-DATAPROT-001 | Ley 20.584 Art. 12 | Verified (sensitive status of clinical record) |

## Summary table

| Dimension | Articles | Evidence type | Confidence |
|---|---|---|---|
| Principles | 3° a)–h) | both | verified primary |
| Lawful bases and consent | 2° p), 12, 13 | both | verified primary |
| Data-subject rights and automated decisions | 4°–11, 8° bis, 8° ter | both | verified primary |
| Information and transparency | 14 ter, 3° g) | both (page exists = code; content = documentary) | verified primary |
| Sensitive data, minors, biometrics, geolocation | 2° g), 16, 16 bis–sexies | both | verified primary |
| Security and breach notification | 14 quinquies, 14 sexies, 14 septies, 15 bis | both | verified primary |
| Privacy by design/default, impact assessment | 14 quáter, 15 ter | both (defaults = code; assessment = documentary) | verified primary |
| Processors and data sharing | 15, 15 bis, 2° v), 2° x) | mostly documentary (integration inventory = code) | verified primary |
| International transfers | 27, 28, 29 | mostly documentary | verified primary |
| Retention and deletion | 3° c), 14 d), 2° k)–l), 17, 18 | both | verified primary |
| DPO and compliance model | 48–53; Decreto 662 | documentary | verified primary (Decreto 662: recital only) |
| Infractions and sanctions | 33–40, transitional sexto | n/a (severity mapping) | verified primary |
| Marketing, commercial communications, credit data | 8° b), 2° w), 13 a), 17–19; Ley 19.496 Art. 28 B | both | verified primary (28 B via official SERNAC and BCN Decreto 62, not the BCN Ley 19.496 page) |

## Gaps and uncertainties

1. **Breach deadline.** Art. 14 sexies sets "sin dilaciones indebidas", no hour count. Any 72-hour figure would come from an Agency instruction (not found) or from foreign law; do not encode one as legal.
2. **Art. 34 ter k) cross-reference.** It cites "artículo 14 quinquies" for breach communications/registers, while the duty itself is in Art. 14 sexies. Recorded verbatim; needs legal review before mapping.
3. **Consolidated Ley 19.628 page (P4)** still shows the pre-reform text on 2026-10-28. Reformed article text was taken from the amending law (P1/P3), not from a consolidated post-reform version.
4. **Agency instructions and reglamentos.** Not found: the Agency's minimum security standards (Art. 14 septies), the impact-assessment list (Art. 15 ter), the identity-authentication procedure (Art. 11), model processor contracts (Art. 15 bis), adequate-country list (Art. 28). Only Decreto 662 (compliance model) was located. The official Agency website was not fetched.
5. **Decreto 662** was read only through its recitals (P5/P6); its articles were not reviewed.
6. **Deleted Ley 19.496 Art. 15 bis.** Its content was not retrieved; impact on consumer-law enforcement of data protection is unknown.
7. **Ley 19.496 Art. 28 B** was quoted from SERNAC and Decreto 62, not from the BCN Ley 19.496 page.
8. **Cookies.** No article of Ley 19.628 (reformed) or Ley 21.719 mentions cookies specifically; any cookie control must rest on Arts. 12, 13, 14 ter and 8° b) as an interpretation pending legal review.
9. **Historia de la Ley** was not consulted; no interpretation in this map relies on legislative history.
10. **Ley 21.668** text was not fetched directly; its "Art. único" is inferred from P9 annotations.
