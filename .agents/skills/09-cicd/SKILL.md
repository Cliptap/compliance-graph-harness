---
name: ci-cd-pipeline
version: 2.0.0
depends_on: [prd-generation, backend-implementation]
stage: cross-cutting
project_types: [web_app, api, data_pipeline, cli_tool]
governance: all
description: Configuracion de CI/CD. Define pipelines, stages, quality gates y despliegue automatizado.
---

# Skill: Pipeline CI/CD

## Objetivo
Configurar la integracion y despliegue continuo del proyecto, automatizando
pruebas, linting, build y deploy segun el nivel de gobernanza.

## Instrucciones
- **NO configurar CI/CD sin preguntar si es necesario para el MVP.**
- Si el proyecto es un prototipo o MVP temprano, preguntar si realmente necesita CI/CD ahora.
- Preguntar por seccion.
- Al final, generar los archivos de configuracion del pipeline.

---

## Flujo de Interaccion

### 1. Necesidad de CI/CD

```
? El proyecto necesita CI/CD en esta etapa?

a) Si — quiero automatizar pruebas, linting y build desde el inicio
b) Si, mas adelante — por ahora solo manual, configurar CI/CD en iteracion futura
c) No — es un prototipo o proyecto personal, no necesito CI/CD

⏳ Si la respuesta es B o C, esta skill se pospone. No configures CI/CD.
```

### 2. Plataforma de CI/CD

```
? Que plataforma de CI/CD prefieres?

a) GitHub Actions — [RECOMENDADO] Integrado con GitHub, marketplace de actions,
   minutos gratis en repos publicos

b) GitLab CI — integrado con GitLab, auto DevOps

c) Bitbucket Pipelines — integrado con Bitbucket

d) CircleCI / Travis CI — plataformas independientes

e) Jenkins — self-hosted, maxima personalizacion

⏳ Esperando tu respuesta.
```

### 3. Stages del Pipeline

```
? Que etapas debe tener el pipeline?

a) Pipeline minimo:
   [lint] → [test] → [build]
   [RECOMENDADO para MVP]

b) Pipeline estandar:
   [lint] → [test] → [build] → [deploy staging] → [e2e] → [deploy prod]

c) Pipeline completo (gobernanza alta):
   [lint] → [test unit] → [test integration] → [security scan] →
   [build] → [deploy staging] → [e2e] → [approval gate] → [deploy prod]

? Que etapas necesitas AHORA?

⏳ Esperando tu respuesta.
```

### 4. Linting y Formateo

```
? Que herramientas de calidad de codigo usaremos?

Python:
a) ruff — [RECOMENDADO] Rapido, reemplaza flake8 + isort + docformatter
b) black — auto-formateo
c) mypy / pyright — type checking

TypeScript:
a) eslint + prettier — [RECOMENDADO]
b) biome — alternativa mas rapida a eslint + prettier
c) tsc — type checking del compilador

Go:
a) golangci-lint — [RECOMENDADO] Agrupa multiples linters
b) gofmt / goimports — formateo

? El linting debe pasar para que el pipeline continue? (quality gate)
? O solo warnings sin bloquear?
```

### 5. Build y Artefactos

```
? Que necesita el build?

- Instalar dependencias (npm install, pip install, go mod download)
- Compilar/transpilar (tsc, vite build, go build)
- Generar assets estaticos (CSS, imagenes)
- Construir imagen Docker (si aplica)

? Que artefactos se generan?
  - Imagen Docker
  - Binario compilado
  - Carpeta dist/ o build/
  - Paquete npm/pip

? Donde se almacenan los artefactos?
  - Docker Hub / GitHub Container Registry
  - GitHub Releases
  - S3 / Artifact Registry
```

### 6. Despliegue

```
? Como y donde se despliega?

a) Docker + VPS / cloud VM — docker-compose up en servidor

b) Plataforma cloud gestionada:
   - Railway / Fly.io / Render — simples, ideales para MVP
   - AWS ECS / GCP Cloud Run — serverless containers
   - Vercel / Netlify — frontend estatico

c) Kubernetes — cluster gestionado (EKS, GKE, AKS)
   Solo para equipos con experiencia en K8s

d) Sin deploy automatico — build y artifacts nomas

? Necesitas multiples entornos?
  - Staging (pruebas antes de prod)
  - Production (usuarios reales)

⏳ Esperando tu respuesta.
```

### 7. Secrets y Variables de Entorno

```
? Como manejamos los secrets en CI/CD?

a) Secrets del proveedor CI/CD (GitHub Secrets, GitLab Variables)
   [RECOMENDADO]

b) HashiCorp Vault / AWS Secrets Manager — secrets centralizados

c) .env encriptado en el repo (no recomendado para produccion)

NUNCA hardcodear secrets en los archivos de CI/CD.
Si necesitas secrets para el pipeline, documentarlos en el README.
```

---

## Verificacion Post-Generacion

- [ ] El pipeline se dispara en los eventos correctos (push, PR, schedule)
- [ ] Las etapas estan correctamente secuenciadas
- [ ] Linting y formateo estan configurados
- [ ] Los tests se ejecutan en el pipeline
- [ ] El build genera los artefactos esperados
- [ ] El deploy (si aplica) tiene confirmacion o approval gate
- [ ] Los secrets no estan hardcodeados
- [ ] El pipeline tiene timeout configurado (no infinito)

## Condicion de Cierre

```
Voy a generar los archivos de configuracion del pipeline CI/CD.
¿Confirmas que las etapas y herramientas son correctas?

⏳ Esperando tu confirmacion.
```
