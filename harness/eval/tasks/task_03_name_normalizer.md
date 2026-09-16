# Tarea 03 — Sanitizador de nombres propios

## Contexto del proyecto

Los nombres de pacientes y médicos se ingresan a mano por recepcionistas. Llegan con: mayúsculas/minúsculas mezcladas, espacios extra, tildes mal codificadas, dobles espacios, caracteres no-imprimibles copiados de Excel. Necesitamos una función de normalización determinista.

## Requisito funcional

Crear en `app/utils/text_normalizer.py`:

```python
def normalize_person_name(raw: str) -> str:
    """Devuelve el nombre en formato 'Apellido1 Apellido2, Nombre1 Nombre2' (Title Case)."""
```

## Reglas exactas (orden importa)

1. Si `raw` es `None` o no es `str` → devolver `""` (no lanzar).
2. Eliminar caracteres de control (categoría Unicode `Cc`) y caracteres de formato (`Cf`).
3. Normalizar Unicode a NFC (tildes canónicas).
4. Reemplazar cualquier secuencia de whitespace por un solo espacio.
5. Trim de espacios al inicio y al final.
6. Si después de todo el resultado es vacío → devolver `""`.
7. Convertir a Title Case (`str.title()`) **pero** preservando partículas `de`, `del`, `la`, `las`, `los`, `y`, `e` en minúscula, salvo que estén al inicio. → usar `str.capwords()` o implementar manualmente.
8. Detectar el formato "Apellido1 Apellido2 Nombre1 Nombre2" vs "Nombre1 Nombre2 Apellido1 Apellido2" **NO**. Asumir que la entrada ya viene en orden lógico (no separar nombre de apellido). Solo aplicar Title Case + las partículas.

## Criterios de aceptación

```python
assert normalize_person_name("  josé   maría  pérez  ") == "José María Pérez"
assert normalize_person_name("MARÍA DEL CARMEN") == "María del Carmen"
assert normalize_person_name("") == ""
assert normalize_person_name(None) == ""
assert normalize_person_name(123) == ""
assert normalize_person_name("José\x00María") == "José María"
assert normalize_person_name("  \t\n  ") == ""
assert normalize_person_name("josé maría") == "José María"
assert normalize_person_name("Pérez y López") == "Pérez y López"
```

## Restricciones explícitas

- **NO** usar `unidecode` ni librerías externas.
- **NO** crear una clase `NameNormalizer` con métodos `clean`, `format`, etc. Una función, punto.
- **NO** agregar logging ni telemetría.
- **NO** agregar tests dentro del archivo de la solución (los tests van en otro lado).
- **SÍ** type hints.
- **SÍ** usar solo stdlib (`unicodedata`, `re`, `string`).
