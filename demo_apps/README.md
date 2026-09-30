# Demo Apps / Bancos de Prueba Experimentales

Este directorio aloja las **aplicaciones cliente y sujetos de prueba** utilizados para evaluar y demostrar las capacidades del **VibeCoding Harness**.

> [!IMPORTANT]
> **Delimitación de Alcance de Tesis:**
> El producto principal de este proyecto es el **Harness de Desarrollo** (`harness/` y `src/harness/`), una plataforma de gobernanza agéntica, gestión de contexto y control de calidad. 
> Las aplicaciones dentro de este directorio **no constituyen el objetivo de la investigación**, sino que funcionan como **conejillos de indias o bancos de prueba sectoriales** para validar empíricamente que el harness previene el sobre-código, bloquea alucinaciones y garantiza el cumplimiento normativo.

---

## 1. Banco de Pruebas: Consultorio Clínico (`Clinical Clinic API`)

- **Sector:** Salud / Médico (Chile).
- **Marco Regulatorio Evaluado:**
  - **Ley 21.719:** Nueva Ley de Protección de Datos Personales (APDP, deber de secreto, privacidad desde el diseño y seguridad).
  - **Ley 20.584:** Derechos y Deberes de las Personas en Salud (deber de retención mínima decenal de fichas clínicas / soft-delete).
  - **Ley 21.668:** Modificaciones en interoperabilidad y gestión de fichas clínicas.
- **Stack Técnico:** Python 3.13, FastAPI, SQLAlchemy 2.0 (asíncrono), Pydantic v2, SQLite (`sqlite+aiosqlite`).
- **Módulos:**
  - `patients`: Gestión de pacientes e identificadores nacionales (RUT).
  - `appointments`: Agendamiento de citas médicas con RBAC y filtrado.
  - `practitioners`: Registro y roles de profesionales médicos.
  - `audit`: Registro inmutable de eventos clínicos y accesos a datos sensibles.

---

## 2. Separación de Pruebas

Para mantener la independencia entre el harness y los casos de uso:
- Las pruebas de funcionamiento de esta aplicación se ejecutan con:
  ```powershell
  pytest tests/demo/ -v
  ```
- Las pruebas del motor del harness se ejecutan con:
  ```powershell
  pytest tests/harness/ -v
  ```
