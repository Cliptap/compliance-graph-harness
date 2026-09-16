---
name: etl-pipeline
version: 1.0.0
depends_on: [prd-generation, db-schema-design]
stage: 3
governance: all
description: Pipeline ETL con validación según nivel de gobernanza, carga chunked, logging estructurado y transaccionalidad completa.
---
# Skill: Definición de Pipeline ETL (Carga, Transformación y Validación)

## Objetivo
Construir un script/pipeline en el Backend que extraiga, valide (con niveles de gobernanza y aseguramiento de calidad), transforme los datos de los usuarios o fuentes de origen y los ingrese de manera limpia y estandarizada a la base de datos.

________________________________________
Instrucciones
• No generar el código del ETL al inicio.
• Hacer preguntas por sección siguiendo el flujo de interacción.
• Evaluar cada requerimiento aplicando las reglas de calidad (ver "Reglas OBLIGATORIAS").
• No avanzar si falta información crítica.
• Al final, generar el código del Pipeline.

________________________________________
Flujo de interacción

1. Fuentes y Volumenes
Solicitar de dónde entrarán los datos (ej: lectura de CSV masivo, stream de datos, o datos directos desde un endpoint). Preguntar por el volumen de la carga.

2. Criterios de Limpieza y Estandarización
Preguntar por todas las operaciones necesarias (Transformación):
• Campos de texto: Mayúsculas/minúsculas, recorte de espacios.
• Campos numéricos/fechas: Transformación de strings a datetime, moneda, unidades.
• Datos faltantes: ¿Se imputan, se eliminan filas nulas o se insertan como nulos (NULL)?

3. Gobernanza, Validación y Calidad
Solicitar cómo se gestionará la gobernanza de esta carga:
• Nivel Bajo: Validar formato mínimo. Si falla, descartar, pero no registrar más.
• Nivel Medio/Alto: Registro de logs de la ejecución de carga, rechazo/aceptación y control de quién inició el proceso. Reglas estrictas de validación.

4. Destino
Solicitar el motor o servicio objetivo y la estrategia de inserción (Insert-Heavy masivo, Upserts con ON CONFLICT o Inserción fila por fila).

________________________________________
Reglas OBLIGATORIAS

• Modularidad y Clases de Servicio/Scripts Separados: El proceso ETL no debe existir dentro del de las rutas de la API, debe separarse en funciones unitarias.
• Extracción Inteligente: Si los de datos son masivos, usar chunks o batches, y no saturar memoria RAM cargando todo en variables al mismo tiempo.
• Registro Fiel (Logging): No utilizar "prints" o depuradores genéricos, integrar librerías de logging que permitan rastrear errores críticos (ERROR), alertas (WARNING), o seguimiento (INFO). Para un PRD de gobernanza Media a Alta, se requiere registro en DB del proceso batch.
• Transaccionalidad: O todo entra bien, o se aborta el bloque. Proteger usando BEGIN y COMMIT / ROLLBACK, no tener datos corruptos ni a medias en caso de que ocurra una de error a la mitad de una carga masiva.

________________________________________
## Verificación post-generación

Antes de confirmar el cierre, verificar que el pipeline ETL generado:
- [ ] El proceso ETL está en clases/servicios separados de las rutas API
- [ ] Carga de archivos grandes usa chunks/batches (no carga todo en RAM)
- [ ] Logging con librería `logging` (niveles ERROR, WARNING, INFO) — nunca `print()`
- [ ] Transaccionalidad con `BEGIN/COMMIT/ROLLBACK` explícito
- [ ] Validaciones según nivel de gobernanza: medio/alto registra logs de ejecución en DB
- [ ] Si gobernanza media/alta: registro de quién inició el proceso y resultado
- [ ] Validación de formato para campos regulados (RUT, email, teléfono) en backend, no solo frontend

________________________________________
Condición de cierre
Antes de producir el código:
“Voy a generar el Pipeline / Script de ETL para el backend. ¿Confirmas los criterios de limpieza y validación?”

________________________________________
Formato de salida

1. Resumen de Flujo de Carga
Flujo lógico con los pasos exactos de E -> T -> L y validaciones.

2. Código Completo de Carga y Validaciones
Script de ejemplo / funciones principales e implementación.

________________________________________
SECCIÓN ADICIONAL: Control de Inputs de Formulario (Frontend)

Esta sección aplica cuando la fuente de datos es un formulario de usuario y no un archivo/stream.
La validación en el frontend no reemplaza la del backend, pero define la UX de entrada.

PREGUNTAS OBLIGATORIAS antes de implementar cualquier campo de identidad nacional u otro
dato con formato regulado (RUT, teléfono, fecha, moneda):

  1. FORMATO DE VISUALIZACIÓN
     ¿Cómo debe verse el dato mientras el usuario escribe y una vez guardado?
     Para RUT — opciones:
       a) Con puntos y guión: 12.345.678-9
       b) Sin puntos, con guión automático antes del último dígito: 12345678-9  ← más común en sistemas modernos
       c) Solo dígitos sin separadores: 123456789

  2. CONTROL DE ESCRITURA (auto-formato)
     ¿El usuario escribe todos los caracteres, o alguno se inserta automáticamente?
       a) El guión (-) se auto-inserta — el usuario NUNCA lo digita manualmente
       b) El usuario digita el guión manualmente
       c) Campo libre con validación solo al enviar

  3. CARACTERES PERMITIDOS POR POSICIÓN
     ¿Qué caracteres son válidos en cada posición?
     Para RUT chileno:
       - Cuerpo (todas las posiciones menos la última): solo dígitos [0-9]
       - Último carácter (dígito verificador): [0-9] o K (¿se normaliza a mayúscula automáticamente?)
       - ¿Se permite ingresar puntos? ¿Se ignoran o se rechazan?

  4. LONGITUD Y RANGO
     ¿Mínimo y máximo de caracteres del cuerpo?
     Para RUT chileno:
       - Persona natural: 7-8 dígitos en el cuerpo
       - Empresa: hasta 9 dígitos en el cuerpo
       - ¿El sistema acepta ambos rangos o solo uno?
       - ¿Validación en tiempo real o solo al submit?

  5. VALIDACIÓN MATEMÁTICA
     ¿Se valida el dígito verificador con el algoritmo módulo 11, o solo el formato?
       a) Solo formato (largo y caracteres permitidos)
       b) Formato + módulo 11 estricto
       c) Sin validación (campo libre con máscara visual)

  6. PERSISTENCIA
     ¿Cómo se almacena en la base de datos?
       a) Tal como lo escribe el usuario
       b) Sin puntos ni guión (solo cuerpo + DV): 123456789
       c) Con guión sin puntos: 12345678-9  ← formato de almacenamiento recomendado

  7. OBLIGATORIEDAD
     ¿El campo es requerido para guardar el registro, o puede estar vacío?

Referencia de implementación — RUT sin puntos, guión automático (caso más común):
  Formato resultante: 12345678-9 | 7654321-K

  ```javascript
  function formatRut(raw) {
    // Limpia todo excepto dígitos y K
    const clean = raw.replace(/[^0-9kK]/g, '').toUpperCase()
    if (clean.length <= 1) return clean
    return clean.slice(0, -1) + '-' + clean.slice(-1)
  }
  // En Vue: @input="model.rut = formatRut($event.target.value)"
  // Placeholder correcto: "12345678-9" — nunca "12.345.678-9" si no se usan puntos
  ```

  Validación módulo 11 (si se requiere):
  ```javascript
  function validarRut(rut) {
    const clean = rut.replace(/[^0-9kK]/g, '').toUpperCase()
    if (clean.length < 2) return false
    const body = clean.slice(0, -1)
    const dv   = clean.slice(-1)
    let sum = 0, mul = 2
    for (let i = body.length - 1; i >= 0; i--) {
      sum += parseInt(body[i]) * mul
      mul = mul === 7 ? 2 : mul + 1
    }
    const r = 11 - (sum % 11)
    return dv === (r === 11 ? '0' : r === 10 ? 'K' : String(r))
  }
  ```

Reglas adicionales:
  • NUNCA asumir formato con puntos (12.345.678-9) sin confirmación explícita del dev.
  • El placeholder del campo debe coincidir EXACTAMENTE con el formato acordado.
  • Si el campo es FK de otro registro, verificar que el formato almacenado sea idéntico en ambas entidades.
  • Advertir si el formato de display difiere del de almacenamiento (evita bugs en búsquedas/joins).