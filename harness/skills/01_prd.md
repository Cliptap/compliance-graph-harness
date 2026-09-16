---
name: prd-generation
version: 2.0.0
depends_on: []
stage: 1
project_types: [web_app, api, data_pipeline, cli_tool, mobile]
governance: all
description: Generacion interactiva de PRD para cualquier tipo de repositorio. Define proposito, usuarios, stack, arquitectura y nivel de gobernanza.
---

# Skill: Generacion de PRD

## Objetivo
Construir un PRD claro y accionable para el repositorio, sin asumir nada.

## Instrucciones
- **NO generar el PRD al inicio.** Primero recopila toda la informacion.
- Hacer preguntas por seccion, en orden.
- **NO avanzar a la siguiente seccion** si falta informacion en la actual.
- Si el desarrollador dice "no se" o "no tengo preferencia", recomendar la opcion mas comun y pedir confirmacion.
- Al final, generar el PRD completo y pedir confirmacion antes de cerrar.

---

## Flujo de Interaccion

### 0. Tipo de Proyecto (OBLIGATORIO — preguntar primero)

Preguntar que tipo de proyecto se va a construir. Esto condiciona todo el resto del pipeline:

```
? Que tipo de proyecto quieres construir?

a) Web App — aplicacion full-stack con frontend y backend
b) API — backend puro, sin interfaz grafica (REST, GraphQL, gRPC)
c) Data Pipeline — procesamiento de datos, ETL, reporteria
d) CLI Tool — herramienta de linea de comandos
e) Mobile App — aplicacion movil (iOS, Android o cross-platform)

⏳ Esperando tu respuesta.
```

No avanzar sin respuesta.

### 1. Problema y Proposito

Solicitar:
- ?Que problema resuelve este proyecto?
- ?Cual es el objetivo principal? (una frase)
- ?Que funcionalidad es la mas critica para el MVP?
- ?Que NO va a hacer este proyecto? (limites explicitos)

### 2. Usuarios y Casos de Uso

Solicitar:
- ?Quienes usaran el sistema? (roles, perfiles)
- ?Que necesita hacer cada tipo de usuario? (casos de uso principales)
- ?Cuantos usuarios esperas? (escala: 10, 100, 10k, 1M)
- ?Hay usuarios anonimos o todos estan autenticados?

### 3. Stack Tecnologico Preferido

Preguntar si el desarrollador tiene preferencias o restricciones:

```
? Tienes restricciones de stack tecnologico?

a) No tengo preferencia — recomiendame lo mas adecuado
b) Debe ser en [lenguaje] — ej: Python, TypeScript, Go
c) Debe usar [framework/base de datos especifica]
d) Tengo un stack definido: [frontend] + [backend] + [db]

Si el desarrollador no tiene preferencia, preguntar por el ecosistema conocido
para recomendar algo que su equipo pueda mantener.
```

### 4. Datos y Persistencia

Solicitar:
- ?El proyecto necesita guardar datos? ?De que tipo?
  - Estructurados (tablas, relaciones)
  - Semi-estructurados (JSON, documentos)
  - No estructurados (archivos, imagenes, logs)
  - Mixto
- ?Que volumen de datos esperas? (MB, GB, TB)
- ?Los datos requieren integridad transaccional (ACID) o priorizas escalabilidad?
- ?Necesitas busquedas de texto completo, geolocalizacion u otro indice especial?

### 5. Infraestructura

Solicitar:
- ?Donde se ejecutara el proyecto?
  - Cloud (AWS, GCP, Azure, otro)
  - On-premise (servidores propios)
  - Local (solo en la maquina del desarrollador)
  - No lo se aun

### 6. Contexto Normativo y Regulatorio

Preguntar si el sistema maneja datos sensibles o regulados:

```
? El sistema manejara datos sensibles sujetos a regulacion?

a) No — sin restricciones regulatorias
b) Datos personales (GDPR, LGPD, leyes locales de proteccion de datos)
c) Datos de salud (HIPAA, Ley 20.584, regulacion sanitaria)
d) Datos financieros (PCI-DSS, SOX, regulacion bancaria)
e) Otro tipo de regulacion (especificar)

Si el desarrollador no sabe, preguntar el pais de operacion y el tipo de datos
para inferir la regulacion aplicable.
```

### 7. Gobernanza del Proyecto (OBLIGATORIO)

```
? Que nivel de gobernanza necesita el proyecto?

a) Bajo — validaciones minimas, sin control de acceso, sin logs ni auditoria.
   Ideal para: prototipos, MVPs internos, herramientas personales.

b) Medio — validaciones de datos, logs de actividad, control de acceso basico.
   Ideal para: aplicaciones con multiples usuarios, datos moderadamente sensibles.

c) Alto — validaciones completas, RBAC, auditoria completa, trazabilidad.
   Ideal para: datos regulados, entornos corporativos, sistemas en produccion.
```

### 8. Restricciones Especiales

Preguntar:
- ?Hay restricciones de presupuesto? (costo maximo mensual de infraestructura)
- ?Hay deadline? ?Cuando necesita estar listo el MVP?
- ?Hay restricciones de licencias? (debe ser open source, MIT, propietario)
- ?Hay requerimientos de accesibilidad? (WCAG 2.1, lectores de pantalla)

---

## Verificacion Post-Generacion

Antes de confirmar el cierre, verificar que el PRD generado:

- [ ] Incluye tipo de proyecto explicitamente
- [ ] Incluye problema y objetivo en una frase
- [ ] Define usuarios y sus casos de uso principales
- [ ] Especifica stack tecnologico (o deja claro que esta pendiente)
- [ ] Define tipo de datos y necesidad de persistencia
- [ ] Indica infraestructura objetivo
- [ ] Incluye contexto normativo/regulatorio si aplica
- [ ] Establece nivel de gobernanza (bajo/medio/alto)
- [ ] Define limites explicitos (que NO hara el proyecto)
- [ ] No contiene informacion inventada ni asumida

---

## Condicion de Cierre

Antes de generar el PRD final:

```
Voy a generar el PRD con la informacion recopilada.
¿Confirmas que todo es correcto? ¿Quieres ajustar algo?

⏳ Esperando tu confirmacion.
```

Solo generar el PRD tras confirmacion explicita del desarrollador.

---

## Formato de Salida

```markdown
# PRD — [Nombre del Proyecto]

## 0. Tipo de Proyecto
- Tipo: [web_app | api | data_pipeline | cli_tool | mobile]
- Justificacion: [razon]

## 1. Proposito
- Problema: [descripcion]
- Objetivo MVP: [una frase]
- No incluye: [limites explicitos]

## 2. Usuarios
- Roles: [lista]
- Casos de uso principales: [lista]
- Escala esperada: [numero]

## 3. Stack Tecnologico
- Frontend: [framework o "No aplica"]
- Backend: [lenguaje + framework]
- Base de datos: [motor + tipo]
- Otros: [colas, cache, storage]

## 4. Datos
- Tipo: [estructurados / semi / no estructurados / mixto]
- Volumen estimado: [tamano]
- Requisitos especiales: [ACID, busquedas, etc.]

## 5. Infraestructura
- Entorno: [cloud / on-premise / local]
- Servicios cloud: [si aplica]

## 6. Contexto Normativo
- Regulacion aplicable: [ninguna / GDPR / HIPAA / etc.]
- Requisitos especificos: [lista]

## 7. Gobernanza
- Nivel: [bajo / medio / alto]
- Implicaciones: [auth, auditoria, validaciones]

## 8. Restricciones
- Presupuesto: [monto o "sin limite"]
- Deadline MVP: [fecha o "sin fecha"]
- Licencias: [MIT / propietario / etc.]
- Otras: [accesibilidad, compliance, etc.]
```
