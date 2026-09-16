---
name: frontend-implementation
version: 2.0.0
depends_on: [prd-generation, architecture-design, api-design]
stage: 4
project_types: [web_app]
governance: all
description: Implementacion del frontend. Define framework, estructura de componentes, estados UI, navegacion y consumo de API.
---

# Skill: Implementacion Frontend

## Objetivo
Implementar la interfaz de usuario del proyecto siguiendo la API y arquitectura definidas.

## Instrucciones
- Cargar PRD, Arquitectura y API Design como contexto.
- **NO escribir codigo sin definir estructura, componentes y estados.**
- Preguntar por seccion.
- Al final, generar el codigo del frontend.

---

## Flujo de Interaccion

### 1. Framework Frontend

```
? Que framework usaremos?

a) React — [RECOMENDADO] El mas popular, ecosistema enorme, flexibilidad total
   Con: Vite (build tool), React Router, TanStack Query (antes React Query)

b) Vue 3 — Curva de aprendizaje suave, SFC (Single File Components), reactividad
   Con: Vite, Vue Router, Pinia (state management)

c) Svelte / SvelteKit — Menos boilerplate, compilado, rapido

d) Solo HTML + CSS + vanilla JS — sin framework, maximo control

e) No necesito frontend — el proyecto es solo API/CLI

⏳ Esperando tu respuesta.
```

### 2. Estilos y CSS

```
? Como manejaremos los estilos?

a) Tailwind CSS — utility-first, rapido de prototipar, consistente [RECOMENDADO]

b) CSS Modules — estilos con scope por componente, sin dependencias

c) Styled Components / CSS-in-JS — estilos dentro del componente React/Vue

d) Framework de componentes (Material UI, Ant Design, PrimeVue)
   Mejor para: dashboards, apps empresariales con muchos formularios

e) CSS plano — sin librerias, maximo control

⏳ Esperando tu respuesta.
```

### 3. Estado de Carga y Estados UI (OBLIGATORIO)

```
TODA pagina o componente que consuma datos debe manejar 3 estados minimos:

1. Estado VACIO (Empty)
   ?Que muestra cuando no hay datos?
   Ej: "No hay productos registrados" + boton "Crear primer producto"

2. Estado CARGA (Loading)
   ?Que muestra mientras se cargan los datos?
   Ej: Skeleton, spinner, barra de progreso

3. Estado ERROR (Error)
   ?Que muestra cuando falla la carga?
   Ej: "Error al cargar productos" + boton "Reintentar"

? Necesitas algun estado adicional?
  - Estado de exito post-accion (toast "Producto creado exitosamente")
  - Estado de confirmacion ("?Seguro que quieres eliminar este producto?")
```

### 4. Pantallas y Navegacion

```
Segun los casos de uso del PRD, las pantallas principales serian:

[Listar pantallas inferidas de los casos de uso]

? Que pantallas necesita el MVP?
  Ej: Login, Dashboard, Listado de productos, Formulario de producto

? Como se navega entre ellas?
  a) Sidebar + contenido principal [RECOMENDADO para apps]
  b) Top navbar + contenido
  c) Wizard / steps (para flujos secuenciales como registro)
  d) Single page (una sola pantalla)

? Necesitas rutas protegidas? (requieren autenticacion)
```

### 5. Consumo de API

```
? Como se conectara el frontend con la API?

a) Fetch API nativa o Axios + hooks/composables personalizados
   [RECOMENDADO para MVPs]

b) TanStack Query (React) / Vue Query — cache, refetch, estados automaticos
   Mejor para: apps con muchos datos y actualizaciones frecuentes

c) GraphQL client (Apollo, urql) — solo si la API es GraphQL

d) tRPC — typesafe API sin REST, solo para stacks full-stack TypeScript

? Necesitas manejo de errores global?
  Ej: interceptor que muestre toast en errores 401/403/500

? Necesitas refresh token automatico cuando expira el JWT?
```

### 6. Responsive Design

```
? La aplicacion debe ser responsive?

a) Si, mobile-first — disenar para movil primero, luego desktop [RECOMENDADO]
   Tailwind: sm:, md:, lg:, xl:

b) Si, desktop-first — disenar para desktop y adaptar a movil

c) Solo desktop — no necesito version movil

d) Solo mobile — es una app exclusivamente para telefonos
```

### 7. Accesibilidad

```
? Que nivel de accesibilidad necesitas?

a) Basica — HTML semantico, labels en formularios, texto alternativo en imagenes

b) Intermedia — roles ARIA, navegacion por teclado, contraste de colores

c) WCAG 2.1 AA — cumplimiento formal, testeable con herramientas como axe-core

d) Sin requerimientos especificos de accesibilidad

⏳ Esperando tu respuesta.
```

### 8. Assets y Recursos

```
? La aplicacion necesita assets estaticos?

- Imagenes / iconos: ?libreria de iconos? (Heroicons, Lucide, Font Awesome)
- Fuentes: ?fuente del sistema o fuente web? (Inter, Roboto, etc.)
- Favicon / metadatos para SEO?
- Logo / branding?

⏳ Esperando tu respuesta.
```

---

## Verificacion Post-Generacion

- [ ] El framework esta correctamente configurado (Vite, Tailwind, etc.)
- [ ] Cada pantalla tiene implementados los 3 estados (empty, loading, error)
- [ ] La navegacion entre pantallas funciona
- [ ] El consumo de API esta implementado segun lo acordado
- [ ] El diseno es responsive (si se solicito)
- [ ] Los formularios tienen validaciones frontend
- [ ] Los componentes estan organizados segun la estructura acordada
- [ ] No se usaron librerias no solicitadas

## Condicion de Cierre

```
Voy a generar el codigo del frontend con las pantallas definidas.
¿Confirmas que el diseno y estructura son correctos?

⏳ Esperando tu confirmacion.
```
