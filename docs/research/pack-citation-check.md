# Pack citation check: `cl-ley-21719` and e-commerce sector sources

- **Purpose:** verify, against primary public sources, every legal citation in `.harness/packs/cl-ley-21719.json` (14 controls plus the `sanctions` and `data_categories` blocks), and locate the public Chilean sources that would back an `ecommerce_retail` plugin. Task T8, specs S6 and S7 of `odd/tasks/harness-consolidation.md`.
- **Date:** all sources retrieved 2026-10-28.
- **Method:** full texts fetched from BCN LeyChile (navigation pages and the `obtxml` export), the Diario Oficial, SERNAC, SII and Transbank. Each pack citation was compared with the article text. Secondary sources (law-firm or commercial summaries) were used only to locate articles and are labelled as secondary.
- **Limitation:** this is source verification, not legal advice. Interpretation remains pending legal review. Every control keeps `legal_review: pending`.

Verdicts:

- `verified`: the article exists and supports the claim.
- `partially_supported`: the article exists, but the control overstates it, misattributes it, or uses an imprecise locator.
- `wrong_article`: the cited article does not support the claim. The correct article is given when one was found.
- `not_found`: the cited text could not be located in the current official text.

Primary texts used for Section A:

| Short name | Source | URL |
| --- | --- | --- |
| Ley 21.719 (amends Ley 19.628) | BCN LeyChile, version "Con Vigencia Diferida por Fecha - 01-DIC-2026" | https://www.bcn.cl/leychile/navegar?idNorma=1209272 |
| Ley 21.719, Diario Oficial | D.O. N° 44.023, 13-Dec-2024, CVE 2583630 | https://www.diariooficial.interior.gob.cl/publicaciones/2024/12/13/44023/01/2583630.pdf |
| Ley 19.628, text in force today (pre-reform) | BCN XML, version 2022-11-10 | https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=141599 |
| Ley 20.584 (as amended by Ley 21.668) | BCN LeyChile | https://www.bcn.cl/leychile/navegar?idNorma=1039348 |
| Ley 21.668 | BCN LeyChile, publication 28-May-2024 | https://www.bcn.cl/leychile/navegar?idNorma=1203827 |
| Código Sanitario (DFL 725) | BCN XML, version 2025-09-29 | https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=5595 |

All article references to "Ley 19.628" below mean the text as reformed by Ley 21.719, in force from 2026-12-01, unless stated otherwise.

## Section A: pack citation verification

### A.1 Verdict table (one row per citation)

| Control | Cited | Verdict | Correct article (if different) | Evidence URL |
| --- | --- | --- | --- | --- |
| CL-DATAPROT-001 | L19628 Art. 14 bis | partially_supported | — | bcn.cl/leychile/navegar?idNorma=1209272 |
| CL-DATAPROT-001 | L19628 Art. 14 quinquies | partially_supported | — | idem |
| CL-DATAPROT-001 | L19628 Art. 34 ter let. j) | partially_supported | Art. 34 ter let. i) for secrecy; Art. 34 quáter let. d) for sensitive data | idem |
| CL-DATAPROT-001 | Ley 20.584 Art. 12 | partially_supported | Ley 20.584 Art. 12 inc. 2-3 | bcn.cl/leychile/navegar?idNorma=1039348 |
| CL-DATAPROT-002 | L19628 Art. 14 quinquies | verified | — | bcn.cl/leychile/navegar?idNorma=1209272 |
| CL-DATAPROT-002 | L19628 Art. 16 bis | wrong_article | Art. 2 let. g) (sensitivity) + Art. 14 quinquies inc. 2 let. a) (encryption) | idem |
| CL-DATAPROT-003 | `article`: "Art. 14°" / `citation`: "Art. 14° quáter" | wrong_article | Art. 14 quáter (the two fields disagree) | idem |
| CL-DATAPROT-003 | L19628 Art. 14 quinquies | verified | — | idem |
| CL-DATAPROT-004 | Ley 20.584 Art. 13 | verified | — | bcn.cl/leychile/navegar?idNorma=1039348 |
| CL-DATAPROT-004 | L19628 Art. 7° N° ii | verified | Locator: Art. 7, second paragraph, numeral ii | bcn.cl/leychile/navegar?idNorma=1209272 |
| CL-DATAPROT-004 | L19628 Art. 8° ter | partially_supported | — | idem |
| CL-DATAPROT-005 | `article`: "Art. 14°" / `citation`: "Art. 14° quáter" | wrong_article | Art. 14 quáter | idem |
| CL-DATAPROT-005 | L19628 Art. 14 quinquies | verified | — | idem |
| CL-DATAPROT-005 | Ley 20.584 Art. 13 | verified | Ley 20.584 Art. 13 inc. 4 | bcn.cl/leychile/navegar?idNorma=1039348 |
| CL-DATAPROT-006 | L19628 Art. 8° bis | partially_supported | — | bcn.cl/leychile/navegar?idNorma=1209272 |
| CL-DATAPROT-007 | L19628 Art. 9° | partially_supported | — | idem |
| CL-DATAPROT-007 | Ley 21.668 Art. 1° | wrong_article | Ley 21.668 "Artículo único", which amends Ley 20.584 Art. 13 inc. 1; see also Ley 20.584 Art. 13 inc. 2 | bcn.cl/leychile/navegar?idNorma=1203827 |
| CORE-CHECK-001 | `article`: "Art. 14°" / `citation`: "Art. 14° quáter" | wrong_article | Art. 14 quáter | bcn.cl/leychile/navegar?idNorma=1209272 |
| CORE-CHECK-001 | L19628 Art. 14 quinquies | partially_supported | — | idem |
| CORE-CHECK-002 | L19628 Art. 14 bis | partially_supported | — | idem |
| CORE-CHECK-002 | L19628 Art. 34 ter let. j) | partially_supported | Art. 34 ter let. i) (secrecy); let. j) covers security | idem |
| CORE-CHECK-003 | `article`: "Art. 14°" | wrong_article | Art. 14 quáter (as the `citation` field says) | idem |
| CORE-CHECK-003 | L19628 Arts. 5° al 10° | partially_supported | Arts. 4 to 11 (Art. 4 lists the rights; 8 ter is blocking; 11 is the procedure) | idem |
| CORE-CHECK-003 | L19628 Art. 14 quáter | partially_supported | — | idem |
| CORE-CHECK-004 | L19628 Art. 8° bis | partially_supported | — | idem |
| HEALTH-CHECK-001 | "Art. 13" under law key `L19628` | partially_supported | Ley 20.584 Art. 13 (law key should be `L20584`) | bcn.cl/leychile/navegar?idNorma=1039348 |
| HEALTH-CHECK-001 | L19628 Art. 7° inc. final | partially_supported | Art. 7, second paragraph, numeral ii | bcn.cl/leychile/navegar?idNorma=1209272 |
| HEALTH-CHECK-001 | L19628 Art. 8° ter | partially_supported | — | idem |
| HEALTH-CHECK-002 | Ley 21.668 Art. 1° | wrong_article | Ley 21.668 "Artículo único"; Ley 20.584 Art. 13 inc. 1-2 | bcn.cl/leychile/navegar?idNorma=1203827 |
| HEALTH-CHECK-002 | L19628 Art. 9° | partially_supported | — | bcn.cl/leychile/navegar?idNorma=1209272 |
| HEALTH-CHECK-003 | L19628 Art. 2° let. g) | verified | — | idem |
| HEALTH-CHECK-003 | L19628 Art. 16 bis | partially_supported | — | idem |
| HEALTH-CHECK-003 (description) | Código Sanitario Art. 127 | not_found | Not identified | leychile.cl/Consulta/obtxml?opt=7&idNorma=5595 |
| `data_categories.SENSITIVE_HEALTH` | Art. 2° let. g) and Art. 16 bis | verified | — | bcn.cl/leychile/navegar?idNorma=1209272 |
| `data_categories.SENSITIVE_HEALTH` | "en armonía con Ley 20.584" | verified | Ley 20.584 Art. 12 inc. 3 | bcn.cl/leychile/navegar?idNorma=1039348 |
| `data_categories.SENSITIVE_HEALTH` | Código Sanitario Art. 127 | not_found | Not identified | leychile.cl/Consulta/obtxml?opt=7&idNorma=5595 |
| `data_categories.SENSITIVE_BIOMETRIC` | Art. 2° let. g) and Art. 16 ter | verified | — | bcn.cl/leychile/navegar?idNorma=1209272 |
| `data_categories.IDENTIFIER_RUT` | Art. 2° let. a) | wrong_article | Art. 2 let. f) | idem |
| `data_categories.IDENTIFIER_RUT` | Art. 14 bis "(Principio de Seguridad y Confidencialidad)" | partially_supported | Principles are Art. 3 let. f) and h); Art. 14 bis is the secrecy duty | idem |
| `data_categories.PERSONAL_CONTACT` | Art. 3° let. c) and Art. 14 quáter | verified | — | idem |
| `data_categories.SECURITY_METADATA` | Art. 14 quinquies and Art. 14 sexies | partially_supported | — | idem |
| `sanctions.terminology` | leves, graves, gravísimas | verified | Art. 34 | idem |
| `sanctions.leve/grave/gravisima` amounts | 5.000 / 10.000 / 20.000 UTM | verified | Art. 35 let. a) to c) | idem |
| `sanctions.gravisima` "o hasta el 4% de ingresos" | 4% | partially_supported | Art. 35, last paragraph (conditional) | idem |
| `enforcement_date` | 2026-12-01 | verified | Ley 21.719, artículo primero transitorio | idem |

Totals (45 rows): **14 verified**, **21 partially_supported**, **8 wrong_article**, **2 not_found**.

Every one of the 14 controls has at least one citation that is not `verified`.

### A.2 Key verbatim excerpts (Spanish, from the fetched texts)

- **Art. 14 bis** (secrecy duty): "El responsable de datos está obligado a mantener secreto o confidencialidad acerca de los datos personales que conciernan a un titular, salvo cuando el titular los hubiere hecho manifiestamente públicos. Este deber subsiste aún después de concluida la relación con el titular."
- **Art. 14 quáter** (protection by design and by default): "el responsable debe aplicar medidas técnicas y organizativas adecuadas desde el diseño con anterioridad y durante el tratamiento de los datos personales. Las medidas a aplicar deberán tener en consideración el estado de la técnica; los costos de implementación; [...] así como los riesgos asociados a dicha actividad."
- **Art. 14 quinquies, second paragraph** (security measures): "aplicarán medidas técnicas y organizativas apropiadas para garantizar un nivel de seguridad adecuado al riesgo, que en su caso incluya, entre otros: a) La seudonimización y el cifrado de datos personales."
- **Art. 14 sexies** (breach reporting and record): "El responsable deberá registrar estas comunicaciones, describiendo la naturaleza de las vulneraciones sufridas, sus efectos, las categorías de datos y el número aproximado de titulares afectados y las medidas adoptadas".
- **Art. 34 ter** (serious infringements): "i) Vulnerar el deber de secreto o confidencialidad establecido en el artículo 14 bis. j) Vulnerar o infringir las obligaciones de seguridad en el tratamiento de los datos personales establecidas en el artículo 14 quinquies."
- **Art. 34 quáter let. d)** (very serious infringements): "Vulnerar el deber de secreto o confidencialidad sobre los datos personales sensibles [...]".
- **Art. 7, second paragraph** (exceptions to erasure): "No procede la supresión cuando el tratamiento sea necesario: [...] ii. Para el cumplimiento de una obligación legal o la ejecución de un contrato suscrito entre el titular y el responsable."
- **Art. 8 ter** (right to block processing): "El titular de datos tiene derecho a solicitar la suspensión temporal de cualquier operación de tratamiento [...] El ejercicio de este derecho no afectará el almacenamiento de los datos por parte del responsable."
- **Art. 8 bis, last paragraph** (automated decisions): "el responsable deberá adoptar las medidas necesarias para asegurar los derechos y libertades del titular, su derecho a la información y transparencia, el derecho a obtener una explicación, a la intervención humana, a expresar su punto de vista y a solicitar la revisión de la decisión."
- **Art. 9** (portability): "en un formato electrónico estructurado, genérico y de uso común, que permita ser operado por distintos sistemas [...] cuando concurran las siguientes circunstancias: a) El tratamiento se realice en forma automatizada, y b) El tratamiento esté basado en el consentimiento del titular."
- **Art. 2 let. f)** (personal data): "Se considerará identificable toda persona cuya identidad pueda determinarse, directa o indirectamente, en particular mediante uno o más identificadores, tales como el nombre, el número de cédula de identidad [...]".
- **Art. 2 let. a)** (storage): "Almacenamiento de datos: la conservación o custodia de datos en un registro o base de datos."
- **Art. 2 let. g)** (sensitive personal data): "[...] los datos relativos a la salud, al perfil biológico humano, los datos biométricos, y la información relativa a la vida sexual, a la orientación sexual y a la identidad de género de una persona natural."
- **Art. 16 bis** (health data): "los datos personales relativos a la salud del titular [...] sólo podrán ser tratados para los fines previstos por las leyes especiales en materia sanitaria."
- **Art. 16 ter** (biometric data): "Son datos personales biométricos aquellos obtenidos a partir de un tratamiento técnico específico, relativos a las características físicas, fisiológicas o conductuales de una persona que permitan o confirmen la identificación única de ella, tales como la huella digital, el iris, los rasgos de la mano o faciales y la voz."
- **Art. 35, last paragraph** (turnover-based fines): "En caso de que el infractor corresponda a una empresa distinta de aquéllas definidas como empresas de menor tamaño [...] que reincida en infracción de carácter grave o gravísima [...] la multa podrá alcanzar [...] hasta el monto correspondiente al 2% o 4% de los ingresos anuales por ventas y servicios".
- **Ley 20.584 Art. 12, third paragraph** (clinical record as sensitive data): "Toda la información que surja, tanto de la ficha clínica como de los estudios y demás documentos donde se registren procedimientos y tratamientos [...] será considerada como dato sensible, de conformidad con lo dispuesto en la letra g) del artículo 2º de la ley Nº 19.628."
- **Ley 20.584 Art. 13, first paragraph** (retention and interoperability, as amended by Ley 21.668): "Los prestadores deberán conservar la ficha clínica por un período de al menos quince años. Asimismo, serán responsables del cumplimiento de lo dispuesto en la ley N° 19.628 [...] de adoptar las medidas que permitan su interoperabilidad con otros prestadores de salud".
- **Ley 20.584 Art. 13, fourth paragraph** (access restriction): "Los terceros que no estén directamente relacionados con la atención de salud de la persona no tendrán acceso a la información contenida en la respectiva ficha clínica. Ello incluye al personal de salud y administrativo del mismo prestador, no vinculado a la atención de la persona".
- **Ley 21.668**: "Artículo único.- Introdúcense las siguientes modificaciones en la ley Nº 20.584 [...]" (the law has no "Artículo 1°").

### A.3 Notes on non-verified items

1. **Logging bans overstate a risk-based law (CL-DATAPROT-001, CORE-CHECK-002).** Arts. 14 bis and 14 quinquies impose secrecy and risk-proportionate security. Neither contains an absolute ban on logging. The existing `legal_review_note` already says this. Separately, Art. 34 ter let. j) classifies *security* failures. The infringement for breaching *secrecy* is let. i). When the leaked data is sensitive, the infringement is very serious (Art. 34 quáter let. d)). Cite all three.
2. **Ley 20.584 Art. 12 (CL-DATAPROT-001).** The article makes clinical-record content sensitive data and requires confidentiality of the record (second paragraph). It says nothing about logs. It supports the data's sensitivity, not the specific sink rule.
3. **Art. 16 bis does not cover encryption (CL-DATAPROT-002).** The article limits the purposes and lawful bases for processing health data. It does not mention security measures. Use Art. 2 let. g) for sensitivity and Art. 14 quinquies, second paragraph, let. a) for encryption.
4. **"Art. 14°" in the `article` field (CL-DATAPROT-003, CL-DATAPROT-005, CORE-CHECK-001, CORE-CHECK-003).** In these controls the `article` field says "Art. 14°" while the `citation` field says "Art. 14° quáter". Art. 14 (the controller's general obligations: lawful sources, accuracy, erasing pre-contractual data) does not support encryption or access-control claims. Art. 14 quáter does, in its risk-based wording. This looks like a lost suffix.
5. **Art. 14 quinquies "Obligación" (CORE-CHECK-001).** The law lists pseudonymisation and encryption as measures that "en su caso" (where appropriate) may be part of adequate security. The control's title presents them as a fixed obligation.
6. **Art. 8 ter used as a legal hold (CL-DATAPROT-004, HEALTH-CHECK-001).** Art. 8 ter is the data subject's right to request a temporary suspension. It does not create a retention or legal-hold duty. The retention duty comes from Ley 20.584 Art. 13, and the refusal to erase comes from Art. 7, second paragraph, numeral ii. Art. 8 ter is still relevant: a blocking request must be honoured, and blocking "no afectará el almacenamiento".
7. **Locator "Art. 7° inc. final" (HEALTH-CHECK-001).** The final item of Art. 7 is numeral vi (defence of claims). The legal-obligation exception is the second paragraph, numeral ii, which CL-DATAPROT-004 already cites correctly.
8. **Law key (HEALTH-CHECK-001).** "Art. 13" is filed under law key `L19628`, but the 15-year rule is Ley 20.584 Art. 13. Similarly, HEALTH-CHECK-002 files Ley 21.668 under `L19628`.
9. **Art. 8 bis is not a ban on automation (CL-DATAPROT-006, CORE-CHECK-004).** It grants a right to object to automated decisions with legal or similarly significant effects. Exceptions exist for contract, express consent, and law. In every case the controller must guarantee explanation, human intervention and review. A mandatory physician gate before any automated triage is a project or clinical policy, not the literal text.
10. **Art. 9 does not mandate FHIR (CL-DATAPROT-007, HEALTH-CHECK-002).** Art. 9 requires a structured, generic, commonly used electronic format, and only when processing is automated *and* based on consent. Health data processed under Art. 16 bis let. e) (diagnosis or care), without consent, may fall outside Art. 9 entirely. This needs legal review. HL7 FHIR R4 / CL Core is not named in any text checked.
11. **Ley 21.668 has no "Art. 1°" (CL-DATAPROT-007, HEALTH-CHECK-002).** It consists of one "Artículo único" that amends Ley 20.584 Arts. 12 and 13, plus a transitional article ordering MINSAL to update the regulation within 18 months. The interoperability duty is Ley 20.584 Art. 13, first paragraph. Art. 13, second paragraph, added by Ley 21.541, says the electronic record "deberán estar diseñados para interoperar" and leaves standards to a MINSAL regulation. No technical standard is named in the law.
12. **Art. 16 bis and isolation or encryption (HEALTH-CHECK-003).** Art. 16 bis supports reinforced protection for health data (purpose restriction). It does not require logical isolation or encryption at rest.
13. **Código Sanitario Art. 127 (HEALTH-CHECK-003, SENSITIVE_HEALTH): not found.** The original Ley 19.628 (Art. 24, 1999) inserted two paragraphs into Código Sanitario Art. 127: "Las recetas médicas y análisis o exámenes de laboratorios clínicos y servicios relacionados con la salud son reservados." In the current Código Sanitario text (BCN version 2025-09-29), however, Art. 127 deals with the manufacture of medicines, and the reserve wording was not found anywhere in the fetched text. It was probably renumbered or replaced by a later reform, but this was not confirmed. Do not cite Art. 127 until a lawyer or a BCN version history confirms the current location. Ley 20.584 Art. 12 is the verified source for the confidentiality of the clinical record.
14. **RUT and Art. 2 let. a) (IDENTIFIER_RUT).** Letter a) defines "almacenamiento". The text that names the national ID number as an identifier is letter f) ("el número de cédula de identidad"). Also, Art. 14 bis is the secrecy *duty*; the security and confidentiality *principles* are Art. 3 let. f) and h).
15. **SECURITY_METADATA.** Art. 14 sexies does require the controller to *record* breach communications, and Art. 14 quinquies, second paragraph, let. d) requires regular verification of security measures. Immutable audit trails, HMAC signatures and access logs are reasonable ways to produce evidence, but they are not literal requirements. The block already says this in `requirement_note`.
16. **The 4% figure (`sanctions`).** It applies only to companies that are not small or medium enterprises under Ley 20.416, that reoffend in serious or very serious infringements (recidivism means two or more sanctions in 30 months, Art. 36). It is 2% for serious and 4% for very serious infringements, "la más gravosa" compared with the tripled fine. The pack's note is correct in substance. The `gravisima` string itself still reads as unconditional. Related details: the transitional sixth article lets the Agency apply only a written admonition to small and medium enterprises during the first 12 months after entry into force, and Art. 35 adds a 50% surcharge if corrective measures are not adopted within 60 days.

## Section B: sources for an `ecommerce_retail` plugin

Obligation type labels: **Legal** (statute or regulation, enforceable by a public authority), **Interpretive** (official agency guidance, not a statute), **Contractual / industry** (binding only through a contract or a private standard).

### B.1 Marketing and commercial communications

| Topic | Article | Excerpt (verbatim) | URL | Type |
| --- | --- | --- | --- | --- |
| Opt-out for promotional email | Ley 19.496 (consolidated by DFL 3/2019 Economía) Art. 28 B, first paragraph | "Toda comunicación promocional o publicitaria enviada por correo electrónico deberá indicar la materia o asunto sobre el que versa, la identidad del remitente y contener una dirección válida a la que el destinatario pueda solicitar la suspensión de los envíos, que quedarán desde entonces prohibidos." | https://www.bcn.cl/leychile/Navegar?idNorma=61438&idParte=9478681 ; SERNAC copy: https://www.sernac.cl/portal/609/w3-article-52798.html | Legal |
| Opt-out for post, phone and messaging | Ley 19.496 Art. 28 B, second paragraph | "Los proveedores que dirijan comunicaciones promocionales o publicitarias a los consumidores por medio de correo postal, fax, llamados o servicios de mensajería telefónicos, deberán indicar una forma expedita en que los destinatarios podrán solicitar la suspensión de las mismas." | same | Legal |
| Right to object to direct marketing and profiling | Ley 19.628 Art. 8 let. b) (from 2026-12-01) | "Si el tratamiento se realiza exclusivamente con fines de mercadotecnia o marketing directo de bienes, productos o servicios, incluida la elaboración de perfiles, de conformidad con el artículo 8° bis." | https://www.bcn.cl/leychile/navegar?idNorma=1209272 | Legal |
| Consent requirements | Ley 19.628 Art. 12 | "El consentimiento del titular debe ser libre, informado y específico en cuanto a su finalidad o finalidades. El consentimiento debe manifestarse, además, en forma previa y de manera inequívoca [...]" | same | Legal |
| Consent withdrawal must be as easy as giving it | Ley 19.628 Art. 12, fourth paragraph | "El titular puede revocar el consentimiento otorgado en cualquier momento y sin expresión de causa, utilizando medios similares o equivalentes a los empleados para su otorgamiento." | same | Legal |
| Bundled consent presumed not free | Ley 19.628 Art. 12, sixth paragraph | "Se presume que el consentimiento para tratar datos no ha sido libremente otorgado cuando el responsable lo recaba en el marco de la ejecución de un contrato o la prestación de un servicio en que no es necesario efectuar esa recolección." | same | Legal |
| Consumer-law data provision removed | Ley 21.719 artículo tercero | "Suprímese el artículo 15 bis de la ley N° 19.496 [...]" (in force 2026-12-01; Art. 15 bis had been added by Ley 21.398 of 24-Dec-2021) | same; Ley 21.398: https://www.diariooficial.interior.gob.cl/publicaciones/2021/12/24/43136/01/2061725.pdf | Legal |
| SERNAC e-commerce guidance | Res. Ex. N° 184, 21-Mar-2019, Circular Interpretativa sobre buenas prácticas en comercio electrónico | "Los proveedores [...] deberán informar y adoptar las medidas técnicas necesarias para garantizar al consumidor la seguridad, integridad y confidencialidad de las transacciones, medios de pago y datos personales de los consumidores" | https://sernac.cl/portal/618/articles-9195_archivo_01.pdf | Interpretive (predates Ley 21.719) |
| SERNAC unfair-clauses circular on personal data | Circular interpretativa of 28-Feb-2022 on clauses about collecting and processing consumer data | Located through the SERNAC index page only; the circular text was not fetched | https://www.sernac.cl/portal/618/w3-article-65388.html | Interpretive (not verified) |

How these fit together: Art. 28 B is an **opt-out** rule. It does not by itself require prior consent for email marketing. From 2026-12-01, the lawful basis for marketing must come from Ley 19.628 Art. 12 (consent) or Art. 13 (for example, legitimate interest under let. d)), with the Art. 8 let. b) right to object always available. Whether a retailer may send marketing email on legitimate interest alone is an open question for legal review.

### B.2 Cookies, tracking and profiling for recommendations

- **No cookie-specific article exists** in the Ley 21.719 text checked. A search of the fetched text for "cookie" returned nothing. A secondary source states the same (PixaWeb, https://pixaweb.cl/ley-21719/consentimiento-cookies/, labelled secondary). Cookie and tracker identifiers fall under the general rules when they make a person identifiable (Art. 2 let. f)).
- **Territorial scope covers behavioural monitoring.** Art. 1 bis let. c): "[...] o a monitorear el comportamiento de titulares que se encuentran en el territorio nacional, incluyendo su análisis, rastreo, perfilamiento o predicción de comportamiento." Legal.
- **Definition of profiling.** Art. 2 let. w): "toda forma de tratamiento automatizado de datos personales que consista en utilizar esos datos para evaluar, analizar o predecir aspectos relativos al rendimiento profesional, situación económica, de salud, preferencias personales, intereses, fiabilidad, comportamiento, ubicación o movimientos de una persona natural." Legal.
- **Transparency about profiling.** Art. 14 ter let. l): "La existencia de decisiones automatizadas, incluida la elaboración de perfiles. En tales casos, información significativa sobre la lógica aplicada, así como las consecuencias previstas de dicho tratamiento para el titular." Legal.
- **Right to object, and automated decisions.** Art. 8 let. b) and Art. 8 bis. Product recommendations are probably not decisions with "efectos jurídicos" or significant effects, but personalised pricing or credit decisions could be. Legal, interpretation pending.
- **Data protection impact assessment (EIPD).** Art. 15 ter requires one always in cases of "Evaluación sistemática y exhaustiva de aspectos personales de los titulares de datos, basadas en tratamiento o decisiones automatizadas, como la elaboración de perfiles, y que produzcan en ellos efectos jurídicos significativos." Not carrying it out is a very serious infringement (Art. 34 quáter let. k)). Legal.
- **Socioeconomic situation is sensitive data** (Art. 2 let. g)). Inferring income band from purchase history for segmentation may therefore count as processing sensitive data. Legal, interpretation pending.

### B.3 Payment card data

- **PCI DSS is contractual, not statutory.** The Transbank merchant affiliation contract, clause 10.9 "Normas PCI-DSS", says: "El Establecimiento declara conocer, aceptar y adherir, en lo que le fuere aplicable, a las Normas PCI-DSS vigentes, así como a sus actualizaciones, asumiendo su responsabilidad por su cumplimiento y por la seguridad de los datos contenidos en las Tarjetas." Source: https://ayuda.transbank.cl/documents/433363/0/CONTRATO+AFILIACION+TBK+ENERO.21+vf.pdf/9bf12d1c-158d-2924-4a29-32517471b116?t=1646167687259 (retrieved through the search tool's full text). **Contractual / industry.**
- The same clause explains that the obligation flows from the card networks' rules ("las regulaciones de las Marcas contemplan que las mismas deben hacerse exigibles a los establecimientos comerciales"). Transbank also publishes a shared-responsibility matrix for PCI DSS v4.0.1 for e-commerce merchants: https://publico.transbank.cl/documents/20129/19513773/ (search result). **Contractual / industry.**
- **Banco Central Compendio, Chapter III.J.2** regulates card operators, for example their payment responsibility towards affiliated merchants. The excerpt retrieved does not impose PCI DSS on merchants. https://www.bcentral.cl/documents/33528/115568/CapIIIJ2.pdf. **Legal for operators**; not shown to apply to merchants.
- **Legal hooks for card data held by the merchant:** Ley 19.628 Arts. 14 bis and 14 quinquies (secrecy and security). Art. 14 sexies requires notifying the data subjects directly when a breach involves "datos relativos a obligaciones de carácter económico, financiero, bancario o comercial". Whether card numbers fall within that phrase needs legal review. **Legal.**
- **SERNAC Res. Ex. 184/2019** asks for security and confidentiality of "medios de pago" and lists "número y clave de tarjetas de débito o crédito" among the data consumers hand over. **Interpretive.**

### B.4 Retention of purchase and billing records

| Rule | Excerpt (verbatim) | URL | Type |
| --- | --- | --- | --- |
| VAT law (DL 825) Art. 58 | "Los duplicados de las facturas y los originales de las boletas a que se refiere este párrafo deberán ser conservados por los respectivos contribuyentes durante seis años." | https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=6369 | Legal |
| Tax Code (DL 830) Art. 17 | "[...] debiendo ser conservados por los contribuyentes, junto con la documentación correspondiente, mientras esté pendiente el plazo que tiene el Servicio para la revisión de las declaraciones." | https://www.leychile.cl/Consulta/obtxml?opt=7&idNorma=6374 | Legal |
| Tax Code (DL 830) Art. 200 | "[...] dentro del término de tres años [...] El plazo señalado en el inciso anterior será de seis años para la revisión de impuestos sujetos a declaración, cuando ésta no se hubiere presentado o la presentada fuere maliciosamente falsa." | same | Legal |
| SII guidance on electronic tax documents | "El tiempo que deben ser almacenados los Documentos Tributarios Electrónicos debe considerar los mismos plazos que se detallan en el artículo 58° de la LIVS; vale decir, seis años." (FAQ 001.003.2356.007, updated 25/06/2025) | https://www.sii.cl/preguntas_frecuentes/factura_electronica/001_003_2356.htm | Interpretive (non-binding per the page) |
| Ley 19.628 Art. 3 let. c) | "Los datos personales pueden ser conservados sólo por el período de tiempo que sea necesario para cumplir con los fines del tratamiento, luego de lo cual deben ser suprimidos o anonimizados, sin perjuicio de las excepciones que establezca la ley." | https://www.bcn.cl/leychile/navegar?idNorma=1209272 | Legal |
| Ley 19.628 Art. 7, second paragraph, numeral ii | Erasure does not apply when processing is necessary "Para el cumplimiento de una obligación legal o la ejecución de un contrato" | same | Legal |
| Ley 19.496 Art. 12 A | "Una vez perfeccionado el contrato, el proveedor estará obligado a enviar confirmación escrita del mismo." | https://www.bcn.cl/leychile/Navegar?idNorma=61438&idParte=9478681 | Legal |

Implication for the plugin: billing documents (boletas and facturas) are kept for six years under tax law, and that legal obligation blocks erasure requests for them. Marketing profiles and tracking data have no comparable retention duty, so they must be erased or anonymised when their purpose ends.

### B.5 Sharing data with processors (payment gateways, couriers) and transfers

- **Processor ("encargado") contract.** Ley 19.628 Art. 15 bis: "En el contrato se deberá establecer el objeto del encargo, la duración del mismo, la finalidad del tratamiento, el tipo de datos personales tratados, las categorías de titulares a quienes conciernen los datos, y los derechos y obligaciones de las partes." Sub-processing requires "una autorización específica y por escrito del responsable". The processor must comply with Arts. 14 bis and 14 quinquies and report breaches to the controller. When the service ends, the data "deben ser suprimidos o devueltos". **Legal.**
- **Assignment to another controller ("cesión").** Art. 15 allows assignment with consent, when "necesaria para el cumplimiento y la ejecución de un contrato en que es parte el titular", on legitimate interest, or when a law provides for it. The assignment must be in writing or by suitable electronic means, naming the parties, the data and the purposes. A courier that uses customer data for its own purposes may be an assignee (a separate controller) rather than a processor. **Legal.**
- **Infringement.** Art. 34 ter let. b): "Comunicar o ceder datos personales, sin el consentimiento del titular, en los casos en que dicho consentimiento sea necesario, o comunicar o ceder los datos para un fin distinto del autorizado." **Legal.**
- **International transfers** (for example, a gateway or cloud host abroad): Arts. 27 to 29 (general authorisation rule, adequate countries determined by the Agency, supervision). Art. 14 ter let. h) requires disclosing transfers and whether the destination offers adequate protection. **Legal.** The detailed conditions of Art. 27 were not extracted in this pass.
- **Transparency.** Art. 14 ter let. d) requires publishing "los destinatarios a los que se prevé comunicar o ceder los datos". **Legal.**

## Gaps and uncertainties

1. **The entry-into-force date may move.** Bill Boletín 18.623-07 (entered the Senate on 2026-09-01) would postpone Ley 21.719. The Senate tramitación index shows it as "En tramitación". Secondary press (Diario Estrategia) reports that the Senate Constitution Committee approved 15-Oct-2027 instead of the Executive's 1-Dec-2027. It is not law as of 2026-10-28, so the pack's `enforcement_date` of 2026-12-01 is correct today. Re-check before release.
2. **Código Sanitario Art. 127:** the current location of the "recetas y exámenes son reservados" text was not found. Needs a BCN version-history check or legal input.
3. **Version dates of the BCN XML exports.** The Ley 19.496 XML export is dated 2021-04-20, before Ley 21.398. Art. 28 B was cross-checked against the BCN navigation page and SERNAC, which show the same wording. The version dates of the DL 825 and DL 830 exports were not checked; Arts. 58, 17 and 200 should be re-confirmed against the current consolidated text.
4. **Decreto 41/2012 MINSAL (clinical records regulation)** is not cited by the pack and was not fetched. It was located only through a Superintendencia de Salud page (https://www.superdesalud.gob.cl/normativa/decreto-n-41/). Ley 21.668 ordered MINSAL to update this regulation within 18 months; whether a new regulation has been published was not verified.
5. **Portability of health data (Art. 9)** probably does not apply when health data is processed without consent under Art. 16 bis let. e). This is an interpretation for legal review.
6. **Card data and Art. 14 sexies:** whether card numbers count as "datos relativos a obligaciones de carácter económico, financiero, bancario o comercial", which would trigger direct notification of data subjects, is unresolved.
7. **Marketing email on legitimate interest:** whether Art. 13 let. d) plus the Art. 28 B opt-out is enough, or whether prior consent is required, is unresolved.
8. **SERNAC circular of 2022 on unfair data clauses** and **Ley 20.009** (payment card fraud) were not fetched. The Agency's general instructions (Art. 14 septies) and model processor contracts (Art. 15 bis) were not yet located.
9. **Some sources were read through the search tool's full-text capture, not a direct fetch:** the Diario Oficial PDFs of Ley 21.719 and Ley 21.398, the Ley 21.668 BCN page and export, the SERNAC Res. 184 PDF, and the Transbank contract. The content matched the BCN texts where they overlapped.
10. **Pack encoding defect, not a legal issue:** `laws.L21668.name` in the pack reads "clÃ­nicas" (double-encoded UTF-8). It should be fixed in T9.
