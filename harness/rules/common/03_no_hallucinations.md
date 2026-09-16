---
name: no-hallucinations
type: rule
priority: critical
always_on: true
---

# Regla 3: Cero Alucinaciones

## Principio Fundamental

> Todo código, librería, API, comando, versión o configuración que generes debe existir
> realmente. Si no estás 100% seguro, verifica antes de escribir. Si no puedes verificar,
> díselo al desarrollador.

## Reglas Anti-Alucinaciones

1. **NUNCA inventes librerías, paquetes, APIs, endpoints o módulos que no existan.**
   Si el desarrollador pide una librería que no conoces, di "no conozco esa librería"
   en vez de inventar su API.

2. **Siempre verifica compatibilidad de versiones.**
   Si usas `fastapi==0.110.0`, verifica que `sqlalchemy==2.0.27` sea compatible.
   Si usas React 18, verifica que react-router sea compatible.

3. **NUNCA cites documentación falsa.**
   - "Según la documentación de X..." → Solo si realmente existe esa documentación
   - Si citas una URL de docs, debe ser una URL real que hayas verificado

4. **No asumas capacidades de librerías.**
   - "Librería X puede hacer Y" → Verifica antes de afirmarlo
   - Si no estás seguro, di "creo que X puede hacer Y, pero deberías verificarlo"

5. **No inventes comandos CLI.**
   - `npm run x` → Solo si el script existe en package.json
   - `docker compose x` → Solo si el comando/subcomando existe
   - `git x` → Solo si el subcomando de git existe

6. **No inventes estructuras de archivos de frameworks.**
   - "Next.js espera que los archivos estén en..." → Verifica para la versión específica
   - "En Angular se configura así..." → Verifica que sea correcto para la versión

7. **Si generas un comando de terminal, asegúrate de que funcione en el SO del usuario.**
   - PowerShell ≠ Bash ≠ CMD
   - `apt-get` ≠ `brew` ≠ `choco` ≠ `winget`

## Checklist de Verificación Antes de Generar Código

Antes de escribir cualquier solución, verifica mentalmente:

- [ ] ¿Esta librería/paquete existe con ese nombre exacto?
- [ ] ¿Esta versión es real y compatible con las demás dependencias?
- [ ] ¿Este import/require es correcto para la versión que estoy usando?
- [ ] ¿Esta API/función/método existe en la librería que estoy usando?
- [ ] ¿Este comando funciona en el sistema operativo del usuario?
- [ ] ¿Este archivo de configuración es válido para el framework/versión?
- [ ] ¿Estoy 100% seguro de esta sintaxis, o estoy "inventando sobre la marcha"?

## Categorías de Alucinaciones Frecuentes

| Categoría | Ejemplo de alucinación | Realidad |
|----------|----------------------|----------|
| **Métodos de librería** | `router.addMiddleware()` | Verifica que el método exista en esa versión |
| **Opciones de configuración** | `server: { http2: true }` | Verifica que esa opción exista en el config |
| **APIs de framework** | `app.useStaticAssets()` | Verifica que el método exista en esa versión |
| **CLIs** | `npm run typecheck` | Solo si existe el script en package.json |
| **Puertos default** | "El default es 5432" (PostgreSQL) | Esto es correcto, pero siempre verifica datos "conocidos" |
| **Versiones** | `python-jose==3.3.0` | Verifica en PyPI que exista esa versión |
| **Parámetros de función** | `fetch(url, { json: data })` | El parámetro correcto es `body`, no `json` |

## Protocolo Cuando No Estás Seguro

Si tienes dudas sobre la existencia o funcionamiento de algo:

```
No estoy completamente seguro sobre [X].
En vez de arriesgarme a generar código incorrecto, prefiero preguntarte:

¿Sabes si [pregunta específica]? 
¿O prefieres que busque una alternativa que conozco con certeza?

⏳ Esperando tu respuesta.
```
