# Tarea 01 — Validador de RUT chileno

## Contexto del proyecto

Sistema de gestión clínica con gobernanza media (Ley 20.584 Chile). Los RUT de pacientes se almacenan como string en la tabla `patients.rut`. Necesitamos un módulo de validación reutilizable.

## Requisito funcional

Crear un módulo `app/utils/rut_validator.py` que exporte:

- `def normalize_rut(raw: str) -> str` — recibe un RUT en cualquier formato (`"12.345.678-9"`, `"12345678K"`, `" 12345678-k "`) y devuelve la versión canónica `"12345678K"` (sin puntos, con guión reemplazado por la letra verificador mayúscula, sin espacios).
- `def is_valid_rut(rut: str) -> bool` — devuelve `True` si el RUT es sintácticamente válido (formato + dígito verificador correcto). `False` en caso contrario, **nunca lanza excepción**.

## Reglas del dígito verificador

Algoritmo "módulo 11":

1. Tomar la parte numérica (sin dígito verificador).
2. Recorrer de derecha a izquierda, multiplicando cada dígito por la serie `2,3,4,5,6,7,2,3,4,5,6,7,...` y sumar.
3. `dv_numerico = 11 - (suma % 11)`.
4. Si `dv_numerico == 10` → `K`. Si `dv_numerico == 11` → `0`. Si no → el número.

## Criterios de aceptación (tests que tienen que pasar)

```python
assert is_valid_rut("12.345.678-5") is True
assert is_valid_rut("12345678-5") is True
assert is_valid_rut("123456785") is True
assert is_valid_rut("11111111-1") is True
assert is_valid_rut("12345678-0") is False
assert is_valid_rut("") is False
assert is_valid_rut(None) is False
assert is_valid_rut("abc") is False
assert normalize_rut(" 12.345.678-k ") == "12345678K"
assert normalize_rut(None) == ""
```

## Restricciones explícitas

- **NO** crear clases abstractas, ABC, ni jerarquías de validadores.
- **NO** crear archivos de configuración para este módulo.
- **NO** agregar validaciones de existencia en base de datos (eso es responsabilidad del caller).
- **NO** agregar logging.
- **NO** usar librerías externas (solo `re` y stdlib).
- **SÍ** escribir type hints en las funciones públicas.
