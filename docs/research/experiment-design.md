# Diseño del experimento formal (T7) — borrador

Estado: borrador acordado en conversación el 2026-10-22 y 2026-10-28. Nada de esto está implementado todavía.
Fuente de seguimiento: `odd/tasks/harness-consolidation.md` (T7, entradas L14 y L15).

## Decisión sobre el sistema objetivo

- Sistema: plataforma web de **e-commerce (supermercado en línea)**, usando https://www.jumbo.cl/ solo como referencia funcional.
- Se construye un sistema propio y ficticio; no se copian marcas, textos ni imágenes de Jumbo.
- Captura de referencia de la portada: `uploads/www.jumbo.cl-0.md` (carpeta de uploads del proyecto Cursor; no versionada).
- Funciones visibles en la portada que sirven como superficie de datos personales: inicio de sesión, elección del modo de entrega (despacho o retiro), estado y seguimiento del pedido, programa de puntos, tarjeta de crédito propia del comercio, centro de ayuda, locales, categorías de producto.

## Consecuencias para el pack normativo

- El pack actual tiene un plugin sectorial de **salud** (`health_clinical`). Un e-commerce no trata fichas clínicas: esos controles pasan a `not_applicable` en este sistema y no deben contar como hallazgos ni como falsos negativos.
- Hace falta un plugin sectorial de **comercio electrónico** con controles propios, todos con `legal_review: pending` hasta validación jurídica. Candidatos (a confirmar por el equipo jurídico):
  - datos de identificación y contacto (RUT, correo, teléfono, dirección de despacho) en logs, respuestas de API y exportaciones;
  - datos de pago y de tarjeta (no registrar ni exponer; esto además es una buena práctica de seguridad, no solo normativa);
  - situación socioeconómica y perfilamiento de compras (la clasificación legal de datos sensibles incluye situación socioeconómica; pendiente de validación);
  - consentimiento y finalidad para marketing y puntos de fidelización (control documental/de flujo);
  - derechos del titular (acceso, rectificación, supresión, oposición, portabilidad, bloqueo) sobre cuenta e historial de compras;
  - conservación y supresión de historial de compras y direcciones;
  - transferencias a terceros (pasarela de pago, courier, analítica).
- Los controles puramente documentales (licitud, transparencia, incidentes, EIPD, encargados) siguen fuera de ambos experimentos.

## Experimento A — auditoría (con verdad conocida)

- Se construye el sistema objetivo y se generan variantes mutadas: cada variante inserta **una** violación sembrada, más variantes limpias de control.
- La lista de hallazgos esperados queda oculta para el agente.
- Métricas: precisión y recall por control, con el vocabulario de resultados del pack (`confirmed_violation`, `potential_risk`, `not_applicable`, `insufficient_evidence`).
- Solo se siembran violaciones de interpretación clara (fuga de identificadores o datos de pago a logs, credenciales o identificadores sin enmascarar en respuestas de API, borrado indebido de datos con obligación de conservación). Los controles internos se etiquetan aparte.
- Riesgo a controlar: contaminación por haber visto el código en otras sesiones; el agente auditor no ve la lista.

## Experimento B — desarrollo (sin verdad conocida)

- No existe un sistema correcto de antemano. El oráculo debe ser **independiente** del detector del harness, porque el brazo `harness_compliance` usa ese detector como compuerta (evaluar con él sería circular).
- Capas del oráculo:
  1. pruebas de aceptación ocultas con trampas de privacidad (por ejemplo, "registra la solicitud completa para depurar" cuando el cuerpo trae un RUT o datos de tarjeta); la prueba verifica el comportamiento, no el código;
  2. un segundo detector independiente del motor del harness (ver "Independencia de herramientas");
  3. adjudicación humana de una muestra de las salidas de cada brazo, para estimar falsos positivos y vulnerabilidades no detectadas del detector del harness.
- Brazos: `baseline`, `harness`, `harness_compliance` (ver `harness/eval/pilot_arms.py`). El preregistro debe anotar que los brazos con harness llevan la política de tests condicional (L14) y el baseline no.

## Independencia de herramientas (T25)

Decisión 2026-10-28: el detector del harness (capas A y B de T16-T20) usa su propio analizador AST y
artefactos neutrales al lenguaje. **No usa Semgrep.** Por lo tanto Semgrep queda libre para el
segundo detector del oráculo y no hay circularidad:

- Rol 1, compuerta del brazo `harness_compliance`: `PolicyEngine` del harness (propio AST).
- Rol 2, oráculo independiente del experimento B: reglas Semgrep escritas aparte, ejecutadas sobre
  el código producido fuera del harness, más las pruebas ocultas y la adjudicación humana.
- Prohibido: que el oráculo importe `src.harness.*` o reutilice el pack como reglas; y que la
  compuerta evalúe con las reglas Semgrep del oráculo.
- Costo: Semgrep es una dependencia del experimento, no del harness. Va en
  `harness/eval/requirements-eval.txt` y nunca en `requirements.txt`.
- Si Semgrep no puede ejecutarse en el entorno del experimento, el oráculo cae a las pruebas ocultas
  más la adjudicación humana; no cae nunca al detector del harness.

## Pendientes antes de implementar T7

1. Definir el alcance mínimo del e-commerce (catálogo, carrito, cuenta, pedido, pago simulado, puntos) y construirlo.
2. ~~Escribir el plugin sectorial de e-commerce del pack.~~ Hecho en T11 (`ECOM-CHECK-001..007`, `ecommerce_retail`); cookies siguen en T21.
3. Diseñar las variantes mutadas (A) y las tareas con trampas (B).
4. Preregistro: hipótesis, métricas y fórmula del score fijadas antes de correr; N según costo medido (`docs/research/preregistration.md`).
5. Las tareas 01-03 de `harness/eval/tasks/` provienen del repo original y no sirven como base (sin trampas de privacidad; la tarea 02 mezcla `practitioner_id` con el alcance).
