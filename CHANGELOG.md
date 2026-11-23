# Changelog

Todas las fechas son ISO 8601. El formato sigue Keep a Changelog y el proyecto usa versionado
semántico.

## [Unreleased]

### Agregado

- `harness-doctor` para verificar Python, dependencias, packs, gate y entorno.
- `pyproject.toml` con instalación editable y console scripts (`compliance-check`,
  `harness-antecedentes`, `harness-doctor`).
- `install.ps1` e `install.sh` de un comando, con `.env.example`.
- CI de GitHub Actions (Linux/Windows, Python 3.12/3.13) con doctor, suite y corpus de calibración.
- Templates de issue y pull request.

### Cambiado

- README raíz reescrito para describir el harness, no la aplicación de demostración.
- Referencias de instalación corregidas (`harness/install.ps1`).

### Corregido

- `format_gate_feedback` resolvía el catálogo con el loader del pack normativo y fallaba en la
  primera violación real.
- Register y subject calculaban destinatarios con mecanismos distintos.
- Detectores: `log.*`, contexto admin por clase, `private_key`, máscaras f-string, proyecciones
  booleanas, deletes ORM, intervalos SQL, dumps de objetos, tokens en logs y secretos bajo claves
  genéricas.
- Taint interprocedural intra-archivo: resúmenes de retorno de helpers, `append`/`extend`/`update`,
  fuentes de credenciales (`tokens.create`, `secrets.get_active`, `load_secret`) y truncamientos
  (`api_key[-4:]`) tratados como máscara.
- Efectos por parámetro: posiciones que llegan a un retorno o a un log; listas de campos literales;
  nombres de callee fuera del matcher; deletes de instancia y queries construidas por helpers
  resueltos a su tabla.
- Precisión de flujos: placeholders de formato no cuentan como valores, nombres enmascarados y
  helpers de sufijo no exponen, metadatos de credencial (`_algorithm`, `_at`) no matchean, las
  fuentes de credencial no miran argumentos anidados y los efectos por parámetro cubren keywords.
- Nombres de productores importados (`format_rut_and_email`) aportan sus categorías; los
  enmascaradores y emisores quedan excluidos.
- Efectos por parámetro hacia response y redirect dentro del helper, detectados en el call site.
- Estado de instancia: mutaciones de `self.<attr>` por clase, leídas en el sink; `PlainTextResponse`
  y afines como sinks; defaults keyword-only; argumentos enmascarados no propagan.
- Ramas con flag constante (módulo o clase) resueltas antes de recorrer; asignaciones por clave
  (`body['api_key'] = ...`) contaminan el contenedor; nombres CamelCase no son fuentes de
  credencial; métodos homónimos entre base y subclase unen sus resúmenes; retornos de serializers
  cuentan como payload; modelos pasados a helpers de delete resuelven su tabla.
- Proyecciones `.get('campo')`; enmascarado consistente dentro de comprehensions; delete por método
  con cutoff bajo la política; el campo de retención es compuerta solo si su valor alcanza la
  política.
- Serializers DRF con `source=` y `write_only`; scan de serializers para controles de credenciales;
  constantes de retención prefijadas; modelos dinámicos en `.delete()`; retorno de nombre
  contaminado en endpoints y tareas; decoradores de ruta fuera del scan de borrados.
- Serializers anidados y campos declarados con `Meta.fields` heredado; contexto admin por clase
  `Admin*` o path; `response.data` como payload de error; `HttpResponseRedirect` y `urlencode`;
  dominios y alias de constantes de retención.
- Estado global de módulo sembrado en los scans; cadenas de `SerializerMethodField`; exclusiones por
  `get_fields`/`to_representation`; `adelete`/`hard_delete`/`purge_*`; managers custom con retención
  baja; `.values()`/`.items()`; enlaces de reset.
- Formularios Django con `render_to_response`; tipos GraphQL en controles de credenciales; JWT;
  dependencias async con `yield`; aliases de repositorios y constantes `*_days` de purga.
- Modelos pydantic/dataclass como fuente por sus campos declarados; `model_dump`/`asdict` como
  accesores, no sanitizadores; propagación por `cache.set`/`cache.get` y `request.session`;
  receivers de sesiones de base de datos fuera de la heurística de credenciales.
- Claves de cache normalizadas a su namespace literal; herencia de campos en modelos y en
  anotaciones; campos removidos por `model_dump`; ventanas de retención cacheadas; `__tablename__`
  heredado; deletes de instancia resueltos por el receiver; guardas de retención por retorno
  temprano.
- Exclusión declarada (`model_dump(exclude=...)`, `Field(exclude=True)`, comprehensions filtradas);
  `ORJSONResponse`/`FileResponse`; headers `Location`/`Link`; exports CSV como respuesta admin;
  nombres de tabla SQL con prefijo; registros de modelo fuera de la heurística de credenciales.
- Contextos de template (`render`/`render_template`/`TemplateResponse`); columnas exportadas como
  tuplas; `yield` en generadores de streaming; loggers con nombre propio (`audit.warning`);
  `decode`/`encode` como accesores; claves de dict por sinónimo exacto; helpers de retención
  transitivos.
- Properties y getters accedidos como atributo; `format_map`/`Template.substitute`; contrato de
  `response_model` (campos declarados, herencia y anotaciones) con `response_model_exclude`/`include`;
  `_fingerprint` como metadata; `signing_key` como credencial.
- Literales con `*` como máscara (ramas de un `IfExp`); `_change` como metadata
  (`last_password_change`).
- Fijado en Python 3.13: `pydantic 2.9.2`, `sqlalchemy 2.0.58`, `numpy 2.1.3`, `pandas 2.2.3` y
  `asyncpg 0.30.0` tienen wheels para 3.13; `cursor-sdk 1.0.40` agregado a las dependencias de
  desarrollo.

### Experimentos

- Bloque D (10 trampas) y comparación `baseline` vs `rules_skills_gate`.
- Calibración ciega del gate: rondas 1 a 21 (ronda 20 de convergencia: 42/42; ronda 21 de 84 casos: 82/84 pre-fix); ver
  `docs/research/gate-calibration.md`.

## [0.1.0] - 2026-11-22

- Fundación pública del repositorio: harness, catálogo, gate, evidencia, experimentos y
  documentación.
