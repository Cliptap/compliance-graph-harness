---
name: project-type-web-app
version: 2.0.0
depends_on: [prd-generation, architecture-design]
stage: cross-cutting
project_types: [web_app]
governance: all
description: Especificaciones adicionales para proyectos web full-stack. Cubre routing, state management, assets, SEO y PWA.
---

# Skill: Web App Full-Stack

## Objetivo
Refinar la arquitectura y el desarrollo para proyectos web que tienen frontend + backend,
cubriendo aspectos especificos que las skills base no abordan en detalle.

## Instrucciones
- Esta skill **complementa** las skills base, no las reemplaza.
- Activar solo si el tipo de proyecto es `web_app`.
- Hacer preguntas adicionales que son especificas de apps web.

---

## Flujo de Interaccion

### 1. Estrategia de Renderizado

```
? Como se renderizara el frontend?

a) SPA (Single Page Application) — todo el routing en el cliente
   React Router, Vue Router. La API se consume desde el navegador.
   [RECOMENDADO para apps interactivas, dashboards]

b) SSR (Server-Side Rendering) — el servidor renderiza HTML inicial
   Next.js (React), Nuxt (Vue), SvelteKit
   Mejor para: SEO, carga inicial rapida, contenido publico

c) SSG (Static Site Generation) — HTML generado en build time
   Astro, Next.js static export, Hugo
   Mejor para: blogs, landing pages, documentacion

d) MPA (Multi-Page Application) — HTML tradicional con algo de JS
   HTMX + templates del backend
   Mejor para: apps simples, formularios, equipos que prefieren server-side

⏳ Esperando tu respuesta.
```

### 2. Ruteo y Navegacion

```
? Como se estructura el ruteo?

a) File-based routing — archivos determinan las rutas automaticamente
   Next.js: app/ router, Nuxt: pages/, SvelteKit: routes/
   [RECOMENDADO]

b) Programmatic routing — rutas definidas en codigo (React Router)
   Mejor para: control fino sobre las rutas

? Necesitas rutas anidadas? (layout padre + contenido hijo)
  Ej: /dashboard/analytics, /dashboard/users comparten sidebar y header

? Necesitas rutas protegidas? (requieren login)
  Ej: /admin/* solo accesible con rol admin
```

### 3. State Management

```
? Como manejas el estado global de la aplicacion?

a) Sin estado global — props + contexto basico (React Context, Vue provide/inject)
   [RECOMENDADO para MVPs y apps simples]

b) Server state con cache — TanStack Query (React), Vue Query, SWR
   Maneja cache, refetch, estados de carga/error automaticamente
   Mejor para: apps que consumen mucha data de API

c) Store global — Zustand (React), Pinia (Vue), Jotai (React)
   Mejor para: estado de UI global (tema, auth, carrito, filtros)

d) Redux / Vuex — solo para apps muy complejas con mucho estado compartido
   Generalmente overkill para MVPs

⏳ Esperando tu respuesta.
```

### 4. Manejo de Assets Estaticos

```
? Como manejas imagenes, fuentes y otros assets?

a) Import directo — Vite/Webpack procesa y optimiza
   import logo from './logo.png' → hash en filename, cache busting
   [RECOMENDADO]

b) CDN — assets servidos desde CDN (Cloudflare, CloudFront, Vercel)

c) Servidor de assets dedicado — S3 + CloudFront, Cloudinary

d) Optimizacion de imagenes:
   - Formatos modernos (WebP, AVIF)
   - Lazy loading (loading="lazy")
   - Responsive images (srcset)
   ? Necesitas optimizacion automatica?

? Fuentes:
  - Sistema (sin descarga) — mas rapido
  - Google Fonts — facil, buena variedad
  - Self-hosted — mas privacidad, control total
```

### 5. SEO y Metadatos

```
? La app necesita SEO?

a) No — es una app interna/dashboard detras de login
   [COMUN en apps empresariales]

b) Si — necesito meta tags, Open Graph, sitemap
   React: react-helmet-async
   Next.js: Metadata API nativa
   Vue: unhead / vue-meta

c) Si, SEO avanzado — schema.org structured data, canonical URLs, robots.txt

? La app tiene pagina de landing publica?
```

### 6. Progressive Web App (PWA)

```
? Necesitas PWA?

a) No — no necesario para MVP

b) Si — quiero que funcione offline, sea instalable, tenga notificaciones push
   Herramientas: vite-plugin-pwa, workbox, next-pwa

? Que funcionalidades PWA?
  - Service worker para cache offline
  - Manifest.json para instalacion
  - Iconos y splash screen
  - Notificaciones push
```

### 7. Internacionalizacion (i18n)

```
? La app necesita multiples idiomas?

a) No — solo espanol [o idioma unico]

b) Si — necesito i18n
   React: react-i18next, next-intl
   Vue: vue-i18n

? Cuantos idiomas? Cuales?
```

---

## Verificacion Post-Generacion

- [ ] La estrategia de renderizado esta implementada
- [ ] El ruteo funciona con las pantallas definidas en Frontend
- [ ] Los assets se cargan eficientemente
- [ ] SEO basico configurado (title, meta description)
- [ ] Si PWA: service worker y manifest configurados
- [ ] Si i18n: al menos 2 idiomas con traducciones

## Condicion de Cierre

```
Voy a generar la configuracion adicional para web app.
¿Confirmas que estas features adicionales son necesarias?

⏳ Esperando tu confirmacion.
```
