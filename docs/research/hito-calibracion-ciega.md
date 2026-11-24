# Hito: calibración ciega del gate

Resumen de cierre del hito de calibración. El detalle por ronda, con cada caso y cada corrección,
vive en [`gate-calibration.md`](gate-calibration.md); este documento lo lee desde arriba: qué se
midió, qué se construyó, qué se decidió y en qué estado queda el repositorio.

## 1. Alcance

**Qué se midió.** Siete controles v2 del catálogo, con sus familias de detección:

| Control | Qué detecta |
|---|---|
| `v2.log_pii` | datos personales en logs |
| `v2.admin_exposure` | datos personales sin enmascarar en respuestas admin |
| `v2.credential_response` | credenciales en respuestas |
| `v2.customer_hard_delete` | borrado duro de clientes dentro de retención (730 días) |
| `v2.billing_retention` | borrado de pedidos/facturas antes de retención (2190 días) |
| `v2.reset_token` | token de reseteo devuelto al cliente |
| `v2.api_key` | API key o secreto devuelto al cliente |

**Qué quedó afuera.** Las políticas legacy (`privacy.cwe_532`, `privacy.api_exposure`), otros
lenguajes y stacks (Java/Spring, Node, Go, Rails), y el contenido de archivos generados (PDF,
imágenes, XLSX). El harness es análisis estático de Python sobre AST; no ejecuta la aplicación.

**Qué significa "ciega".** Un autor fresco, sin acceso al repositorio, escribe un set que el harness
nunca vio. El set se sella con SHA-256 antes de correrlo y se corre **una sola vez**. Ese número es
la medición; cualquier corrección posterior lo convierte en regresión, no en medición.

## 2. Qué se construyó

| Pieza | Estado |
|---|---|
| Detector | `src/harness/policy_families.py`: familias de sink exposure, credential exposure y retention deletion, con taint intra-archivo, estado de instancia, summaries de helpers y contrato de `response_model` |
| Corpus curado | `harness/eval/catalog_corpus.json`: 22 casos que definen el comportamiento esperado |
| Corpus de regresión | `harness/eval/catalog_corpus_heldout.json`: **246 casos**, cada uno nacido de una ronda ciega o de un canal nuevo |
| Sets ciegos | `harness/eval/blind/cases_blind_round{1..21}.json`, cada uno con su `.sha256` |
| Validador y sellador | `harness/eval/blind/check_blind_set.py`: estructura, sintaxis, cobertura por control, balance de etiquetas y sello |
| Runner de métricas | `harness/eval/catalog_corpus.py`: TP/FP/FN/TN, precisión, recall, F1 e intervalos de Wilson por control |
| Artefactos | `qa_reports/catalog-corpus/*_metrics.json`: una medición por corpus y por ronda |

## 3. Resultados

Veintiuna rondas, **907 casos ciegos** en total. La columna *pre-fix* es lo que pasó en la primera
corrida; *post-fix* es el estado actual del set sellado como regresión.

| Ronda | Casos | Pre-fix | Post-fix | Tema |
|---:|---:|---:|---:|---|
| 1 | 36 | 26/36 | 36/36 | Django/DRF básico |
| 2 | 42 | 37/42 | 42/42 | correcciones del round 1 |
| 3 | 38 | 25/38 | 38/38 | cobertura de framework: `JsonResponse`, DRF, admin, ORM, CLI |
| 4 | 35 | 31/35 | 35/35 | Flask, SQLAlchemy, FastAPI, GraphQL, Celery |
| 5 | 42 | 32/42 | 42/42 | flujo indirecto: helpers, f-strings, `%` |
| 6 | 42 | 37/42 | 42/42 | taint interprocedural |
| 7 | 42 | 34/42 | 42/42 | keyword args y parámetros que llegan a responses |
| 8 | 42 | 34/42 | 42/42 | estado de instancia y flujos por keyword |
| 9 | 42 | 31/42 | 42/42 | herencia, ramas constantes, DTO → serializer |
| 10 | 42 | 38/42 | 42/42 | async, decoradores, payloads anidados |
| 11 | 42 | 32/42 | 42/42 | serializers DRF y rutas de error |
| 12 | 42 | 35/42 | 42/42 | admin inlines, serializers anidados, middleware |
| 13 | 42 | 28/42 | 42/42 | management commands, signals, managers custom, middleware async |
| 14 | 42 | 37/42 | 42/42 | formularios, GraphQL/JWT, dependencias async |
| 15 | 42 | 35/42 | 42/42 | modelos pydantic/dataclass, cache/sesión, tareas en background |
| 16 | 42 | 28/42 | 41/42 | claves indirectas, productores cross-module, herencia de modelos |
| 17 | 42 | 34/42 | 42/42 | exclusión de campos y respuestas no-JSON |
| 18 | 42 | 31/42 | 42/42 | templates, sets de exclusión y streaming |
| 19 | 42 | 30/42 | 42/42 | properties, `response_model`, payloads firmados |
| 20 | 42 | **42/42** | 42/42 | **prueba de convergencia**: muestra neutral, sin canal nuevo |
| 21 | 84 | 82/84 | 84/84 | muestra neutral de 84 casos para apretar el intervalo |

**Lectura de la serie.** Los primeros catorce rounds fueron de recall: cada uno agregó una dimensión
del lenguaje o del framework, y el número pre-fix osciló entre 25/38 y 38/42. Los rounds 15 a 19
fueron de canal: almacenamiento indirecto, herencia, exclusión, templates/streams y contrato de
respuesta. Cada uno perdió entre 5 y 14 casos porque el autor ciego encontró una dimensión que el
modelo no tenía. El round 20 fue la prueba de convergencia: misma distribución, sin canal nuevo, y
pasó **42/42 en la primera corrida**. El round 21 duplicó la muestra a 84 casos y encontró dos
falsos positivos residuales de metadata de serializer, corregidos y promovidos.

En agregado, **739 de 907 casos ciegos pasaron en la primera corrida (81,5 %)**; hoy pasan **906 de
907**. El agregado no es una métrica de calidad del detector actual —cada ronda midió un modelo
distinto— sino la evidencia de cuánto costó cada dimensión nueva.

El único fallo ciego que queda es `r16-admin-03`: un productor importado (`build_admin_export`) cuyo
nombre no declara qué devuelve. Es el límite conocido del modelo cross-module por nombre.

## 4. Decisiones

1. **Protocolo de 42 casos (7 controles × 6, 3/3).** Permite medir los siete controles en cada
   ronda sin inflar el costo del autor. Un set con split 4/2 se conserva si las etiquetas son
   consistentes; las métricas se reportan por control.
2. **Sello antes de correr, corrida única.** Sin esto, el número se puede ajustar mirando el
   resultado. El sello vive en el repo y se verifica con `--verify-seal`.
3. **Cada fallo se corrige y se promueve.** Un caso que falló y se arregló entra al corpus de
   regresión. El set ciego queda "quemado": su número es pre-fix para siempre.
4. **El intervalo manda.** Con 42 casos, 38/42 y 34/42 no son estadísticamente distintos. Por eso el
   cierre se hizo con 84 casos: la exactitud post-fix pasa de [0.916, 1.000] a [0.956, 1.000].
5. **El loop se cierra cuando converge, no cuando el número gusta.** El criterio fue una muestra
   neutral que pasa en la primera corrida (round 20).
6. **Los canales nuevos se cultivan en el corpus, no en rondas ciegas.** Una vez estabilizada la
   distribución, otra ronda de 42 rinde menos que agregar el canal como feature con tests.
7. **El hook de pre-commit no se saltea.** Si el detector se marca a sí mismo, se corrige el
   detector; no se usa `--no-verify`.

## 5. Límites

| Límite | Caso que lo expone |
|---|---|
| Productor cross-module con nombre neutro | `r16-admin-03` |
| `response_model` importado resuelto solo con `from X import Name` | canal 1 (documentado) |
| Cookie con nombre neutro que lleva un reset token | canal 3 (documentado) |
| Exclusión calculada en runtime desde configuración | canal 2 (documentado) |
| Stream armado en otro módulo | round 18 |
| Taint intra-archivo: no sigue imports ni tipos por campo | diseño del modelo |
| Contenido de PDF/imagen/XLSX y otros lenguajes | fuera de alcance |

## 6. Estado final verificable

| Verificación | Resultado |
|---|---|
| Suite de tests | **558 passed** |
| Corpus curado | **22/22** |
| Corpus de regresión | **246/246** |
| Sets ciegos 1–21 | todos pasan salvo `r16-admin-03` |
| Doctor | `[PASS]` |
| Self-scan del detector | **0 findings** |
| CI | 3.12 y 3.13, Linux y Windows |

## 7. Cómo reproducirlo

```powershell
# validar un set ciego antes de correrlo
python harness/eval/blind/check_blind_set.py --corpus harness/eval/blind/cases_blind_round21.json

# verificar el sello de un set ya corrido
python harness/eval/blind/check_blind_set.py --corpus harness/eval/blind/cases_blind_round21.json --verify-seal

# medir cualquier corpus y escribir el artefacto
python harness/eval/catalog_corpus.py --corpus harness/eval/catalog_corpus_heldout.json --out qa_reports/catalog-corpus/heldout_metrics.json

# suite completa y doctor
python -m pytest tests -q
python -m src.harness.doctor
```

## 8. Próximos pasos

1. Canales restantes del Tier 1: sets de exclusión desde configuración, reset token bajo cookie
   neutra, streams armados en otro módulo.
2. Tier 2: política de retención desde settings, soft delete + purge en servicios distintos,
   `FileResponse` con PII en el filename, GraphQL subscriptions, admin actions.
3. Extender la calibración a las políticas legacy y a un segundo stack, si el proyecto lo pide.
