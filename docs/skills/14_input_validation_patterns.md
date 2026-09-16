---
name: input-validation-patterns
version: 1.0.0
depends_on: [prd-generation, frontend-ui, etl-pipeline]
stage: cross-cutting
governance: all
description: Patrón reusable de 7 preguntas para definir comportamiento de cualquier campo regulado (RUT, teléfono, email, fecha, moneda, ID fiscal) en frontend, validación backend y persistencia.
---
# Skill: Patrones de Validación de Inputs Regulados

## Objetivo
Definir el comportamiento completo de cualquier campo de entrada con formato regulado, cubriendo visualización, auto-formato, validación, persistencia y obligatoriedad. Este patrón de 7 preguntas garantiza que ningún detalle de UX, validación o storage quede sin definir.

________________________________________
## Instrucciones
- No generar código al inicio.
- Aplicar las 7 preguntas obligatorias a CADA campo regulado que aparezca en el PRD.
- No avanzar a la implementación hasta que todas las preguntas tengan respuesta para todos los campos.
- Si el usuario no tiene claridad, recomendar la opción más común según el tipo de campo.
- Al final, generar la implementación completa (frontend + backend + DDL).

________________________________________
## Cuándo Usar Esta Skill

Activar esta skill cuando el PRD o el diseño de formularios mencione campos como:
- Identificación personal: RUT (Chile), DNI (Argentina), CPF (Brasil), NIF (España), SSN (EE.UU.)
- Teléfono: nacional, internacional, con/sin código de país
- Email: validación de formato, verificación de dominio
- Fecha: formatos regionales (DD/MM/YYYY vs MM/DD/YYYY), rangos válidos
- Moneda: separadores de miles, decimales, símbolo ($, USD, EUR)
- Códigos postales: formato por país (CP, ZIP, etc.)
- Patentes/placas de vehículos
- CBU/CVU/IBAN (cuentas bancarias)

________________________________________
## Flujo de interacción — Las 7 Preguntas Obligatorias

Para cada campo regulado identificado, responder estas 7 preguntas en orden:

### 1. FORMATO DE VISUALIZACIÓN
¿Cómo debe verse el dato mientras el usuario escribe y una vez guardado?

Ejemplos según tipo:
- **RUT chileno:** a) Con puntos y guión: `12.345.678-9` b) Sin puntos, con guión: `12345678-9` (más común) c) Solo dígitos: `123456789`
- **Teléfono:** a) `+56 9 1234 5678` b) `912345678` c) `(56) 9 1234-5678`
- **Moneda:** a) `$1.234.567,89` b) `1,234,567.89` c) `1234567.89`
- **Fecha:** a) `DD/MM/YYYY` b) `MM/DD/YYYY` c) `YYYY-MM-DD` (ISO 8601)

Regla: El placeholder del campo debe coincidir EXACTAMENTE con el formato acordado.

### 2. CONTROL DE ESCRITURA (Auto-Formato)
¿El usuario escribe todos los caracteres, o alguno se inserta automáticamente?

Opciones:
- a) Guión/separador se auto-inserta — el usuario NUNCA lo digita manualmente (recomendado)
- b) El usuario digita el separador manualmente
- c) Campo libre, validación solo al enviar (submit)
- d) Input enmascarado con librería (ej: `imask`, `cleave.js`)

### 3. CARACTERES PERMITIDOS POR POSICIÓN
¿Qué caracteres son válidos en cada posición del campo?

Definir para cada posición o grupo de posiciones:
- **Cuerpo principal:** solo dígitos `[0-9]`, o también letras `[a-zA-Z0-9]`
- **Dígito verificador / sufijo:** `[0-9]`, `[0-9kK]`, o libre
- **Separadores (puntos, guiones, espacios):** ¿se permiten? ¿se ignoran o se rechazan?
- **Normalización:** ¿se convierte a mayúsculas automáticamente? (ej: `k → K`)

### 4. LONGITUD Y RANGO
¿Mínimo y máximo de caracteres del valor normalizado (sin separadores)?

- **Largo mínimo:** ¿El campo puede estar incompleto mientras el usuario escribe, o debe estar completo para submit?
- **Largo máximo:** Para cada categoría (persona natural vs empresa, si aplica).
- **Validación en tiempo real:** ¿El campo muestra error mientras se escribe (on input) o solo al enviar (on submit)?

### 5. VALIDACIÓN MATEMÁTICA / SEMÁNTICA
¿Se valida solo el formato o también la integridad del dato?

Opciones:
- a) Solo formato (largo y caracteres permitidos)
- b) Formato + algoritmo de verificación (módulo 11 para RUT, Luhn para tarjetas, checksum para IBAN)
- c) Formato + verificación + consulta a servicio externo (API de validación de RUT en SII, verificación de email con SMTP)
- d) Sin validación (campo libre con máscara visual)

### 6. PERSISTENCIA
¿Cómo se almacena en la base de datos?

Opciones:
- a) Tal como lo escribe el usuario (con separadores, puntos, guiones)
- b) Sin separadores — solo cuerpo + dígito verificador (ej: `123456789`) ← recomendado
- c) Con guión sin puntos (ej: `12345678-9`) ← buena opción para RUT, legible y buscable
- d) Formato normalizado ISO (ej: `YYYY-MM-DD` para fechas, `+56912345678` para teléfonos)

**CRÍTICO:** Si el campo es FK de otra tabla, verificar que el formato almacenado sea idéntico en ambas entidades. Advertir si el formato de display difiere del de almacenamiento (evita bugs en búsquedas y JOINs).

### 7. OBLIGATORIEDAD
¿El campo es requerido para guardar el registro, o puede estar vacío?

- **Requerido:** No se puede guardar sin este campo → `NOT NULL` en BD + validación frontend + validación backend.
- **Opcional:** Puede estar vacío → nullable en BD.
- **Condicional:** Requerido solo si otro campo tiene cierto valor (ej: razón social requerida solo si tipo de persona = "empresa").

________________________________________
## Reglas OBLIGATORIAS

- **NUNCA asumir formato sin confirmación explícita.** Lo que es obvio para un país es extraño para otro (ej: fechas DD/MM/YYYY vs MM/DD/YYYY).
- **El placeholder del input debe coincidir EXACTAMENTE con el formato acordado en pregunta 1.** Si se eligió `12345678-9`, el placeholder es `12345678-9`, nunca `12.345.678-9`.
- **Validación SIEMPRE en backend**, incluso si hay validación frontend. La validación client-side es UX, no seguridad.
- **El formato de almacenamiento (pregunta 6) debe estar documentado en el esquema DB.** Si se almacena sin guiones, poner un comentario en el SQL.
- **Consistencia cross-entidad:** Si el mismo campo aparece en múltiples tablas (ej: `patient_rut` en pacientes y en citas), el formato de almacenamiento DEBE ser idéntico.

________________________________________
## Ejemplos de Respuestas para Campos Comunes

### RUT Chileno (Caso más común)
| # | Pregunta | Respuesta recomendada |
|---|----------|----------------------|
| 1 | Visualización | Sin puntos, con guión: `12345678-9` |
| 2 | Auto-formato | Guión auto-insertado, usuario no lo digita |
| 3 | Caracteres | Cuerpo: `[0-9]`, DV: `[0-9kK]` → normalizar K a mayúscula |
| 4 | Longitud | Mín 7, máx 9 dígitos en cuerpo. Validación on submit |
| 5 | Validación | Formato + módulo 11 estricto |
| 6 | Persistencia | Con guión sin puntos: `12345678-9` |
| 7 | Obligatoriedad | Requerido (NOT NULL) |

### Teléfono Internacional (Caso más común)
| # | Pregunta | Respuesta recomendada |
|---|----------|----------------------|
| 1 | Visualización | `+56 9 1234 5678` |
| 2 | Auto-formato | Input enmascarado con librería |
| 3 | Caracteres | `[0-9]` y `+` solo al inicio |
| 4 | Longitud | Mín 8, máx 15 dígitos (E.164) |
| 5 | Validación | Solo formato |
| 6 | Persistencia | Solo dígitos con `+`: `+56912345678` |
| 7 | Obligatoriedad | Requerido |

### Fecha (Caso más común)
| # | Pregunta | Respuesta recomendada |
|---|----------|----------------------|
| 1 | Visualización | `DD/MM/YYYY` (Latam/Europa) |
| 2 | Auto-formato | Input type="date" nativo o datepicker |
| 3 | Caracteres | `[0-9/]` |
| 4 | Longitud | Exactamente 10 caracteres con formato |
| 5 | Validación | Fecha válida + rango (no futura para fecha de nacimiento, no pasada para cita) |
| 6 | Persistencia | ISO 8601: `YYYY-MM-DD` (formato de almacenamiento difiere del display) |
| 7 | Obligatoriedad | Requerido |

________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar para cada campo regulado:
- [ ] Las 7 preguntas tienen respuesta explícita
- [ ] El placeholder coincide con el formato de visualización acordado
- [ ] La validación existe tanto en frontend (UX) como en backend (seguridad)
- [ ] El formato de almacenamiento está documentado en el DDL (comentario SQL)
- [ ] Si el campo es FK, el formato de almacenamiento es idéntico en todas las tablas
- [ ] Se advirtió si el formato de display difiere del de almacenamiento

________________________________________
## Condición de cierre
Antes de generar la implementación:
"He definido las 7 propiedades para cada campo regulado. Voy a generar el código de validación (frontend + backend) y el DDL con el formato de almacenamiento acordado. ¿Confirmas antes de continuar?"

________________________________________
## Formato de salida

1. Tabla de Decisiones por Campo
Para cada campo regulado, una tabla con las 7 respuestas (como en los ejemplos arriba).

2. Implementación Frontend
- Función de auto-formato (ej: `formatRut()`, `formatPhone()`).
- Función de validación (ej: `validarRut()`, `isValidEmail()`).
- Componente de input con placeholder correcto, eventos `@input` y `@blur`.
- Mensajes de error específicos por tipo de fallo (formato, longitud, dígito verificador).

3. Implementación Backend
- Pydantic validator o validación en servicio ETL con las mismas reglas que el frontend.
- Normalización antes de insertar en BD (limpiar separadores, mayúsculas, etc.).

4. DDL / Esquema
- Columna con tipo correcto (`TEXT`, `NUMERIC`, `DATE`), restricción `NOT NULL` si aplica.
- Comentario SQL documentando el formato de almacenamiento elegido.
- Índice si el campo se usa en búsquedas frecuentes.
