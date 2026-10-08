---
project_id: "catalogo-carrito-web"
project_name: "Sistema Web Básico de Catálogo y Carrito de Compras"
version: 1
status: "APPROVED"
project_type: "web_app"
governance_level: "bajo"
created_at: "2026-10-07"
updated_at: "2026-10-07"
---

# PRD — Sistema Web Básico de Catálogo y Carrito de Compras

## 1. Identidad y Contexto
- **Project ID:** catalogo-carrito-web
- **Tipo de Proyecto:** web_app
- **Nivel de Gobernanza:** bajo
- **Problema a Resolver:** Los clientes necesitan consultar productos disponibles, localizarlos por nombre y armar una selección de compra en un carrito sin barreras ni fricción de registro o pago.
- **Contexto Operativo:** Aplicación web interactiva básica orientada a exploración de catálogo y gestión de carrito de compras en entorno local o de demostración.

## 2. Objetivos del Sistema
- **Objetivo Principal:** Proveer una interfaz web que permita a los usuarios explorar productos, buscar ítems por nombre y gestionar un carrito de compras interactivo con actualización dinámica de cantidades.
- **Objetivos Secundarios:**
  - OBJ-1: Presentar el catálogo con visualización clara de atributos básicos de los productos.
  - OBJ-2: Facilitar la localización rápida de artículos mediante búsqueda textual por nombre.
  - OBJ-3: Permitir la gestión de cantidades y productos en el carrito con cálculo automático de subtotales y total acumulado.

## 3. Actores y Usuarios
- **ACT-01 [Usuario Visitante]:** Explora el catálogo, realiza búsquedas por término y gestiona los ítems de su carrito de compras de manera anónima y libre (sin inicio de sesión).

## 4. Requisitos Funcionales
- **REQ-001:** El sistema debe presentar un catálogo de productos con visualización básica de sus datos comerciales (identificador, nombre, descripción básica y precio unitario).
- **REQ-002:** El sistema debe permitir la búsqueda y filtrado de productos del catálogo mediante coincidencia textual ingresada sobre el nombre del producto.
- **REQ-003:** El sistema debe permitir al usuario agregar productos disponibles desde el catálogo hacia el carrito de compras, estableciendo una cantidad inicial.
- **REQ-004:** El sistema debe permitir la modificación interactiva de cantidades de productos en el carrito de compras (incrementar, reducir y eliminar ítems) calculando automáticamente el subtotal por producto y el total general de la selección.

## 5. Delimitación de Alcance (Scope Boundary)

### IN SCOPE (Comprometido para MVP)
- Visualización de catálogo de productos con nombre, descripción básica y precio unitario.
- Búsqueda textual y filtrado en tiempo de consulta por nombre de producto.
- Carrito de compras interactivo: adición de productos, modificación de cantidades y eliminación de ítems.
- Cálculo en tiempo real de subtotales por ítem y monto total acumulado del carrito.
- Manejo de estados básicos de interfaz: carrito vacío y catálogo sin resultados de búsqueda.

### OUT OF SCOPE (Explícitamente Excluido)
- Pasarelas, intermediarios y procesamiento de pagos (tarjetas, billeteras virtuales o transferencias). Prohibida su reintroducción sin Change Request formal.
- Autenticación, inicio de sesión, roles y registro de cuentas de usuario (toda interacción opera bajo modo visitante/anónimo). Prohibida su reintroducción sin Change Request formal.
- Motores de recomendaciones, productos sugeridos o personalización algorítmica. Prohibida su reintroducción sin Change Request formal.

## 6. Criterios de Aceptación (Acceptance Criteria)
- **AC-001** (Vinculado a `REQ-001`): Cuando un usuario accede a la vista de catálogo, el sistema muestra el listado de productos disponibles exhibiendo nombre, descripción básica y precio unitario visible para cada ítem.
- **AC-002** (Vinculado a `REQ-002`): Cuando el usuario ingresa un término en el control de búsqueda, el sistema filtra y exhibe únicamente los productos cuyo nombre contenga la cadena buscada, sin distinguir entre mayúsculas y minúsculas.
- **AC-003** (Vinculado a `REQ-002`): Cuando la búsqueda por texto no coincide con ningún producto existente, el sistema muestra un mensaje informativo indicando que no se encontraron coincidencias, sin producir anomalías en la vista.
- **AC-004** (Vinculado a `REQ-003`): Cuando el usuario agrega un producto disponible al carrito especificando una cantidad $N$ ($N \ge 1$), el carrito refleja dicho ítem con cantidad $N$ y el subtotal correspondiente a $N \times \text{precio unitario}$.
- **AC-005** (Vinculado a `REQ-004`): Cuando el usuario modifica la cantidad de un producto en el carrito a un valor $M$ ($M \ge 1$), el subtotal de esa línea y el total general del carrito se recalculan de forma inmediata.
- **AC-006** (Vinculado a `REQ-004`): Cuando el usuario elimina un producto del carrito o fija su cantidad en 0, el producto desaparece del carrito y el total acumulado descuenta íntegramente su valor.

## 7. Restricciones del Sistema (Constraints)
- **CONST-001:** El sistema no integrará pasarelas ni procesará transacciones financieras o pagos electrónicos.
- **CONST-002:** El sistema no requerirá credenciales, perfiles ni registro de usuarios para operar.
- **CONST-003:** El sistema no incorporará motores de recomendación ni analítica prescriptiva de productos.

## 8. Supuestos de Trabajo (Assumptions)
- **ASSUMP-001:** El catálogo inicial cuenta con un volumen acotado para propósitos de demostración funcional del MVP.
- **ASSUMP-002:** La persistencia del estado del carrito durante la sesión de navegación puede resolverse en memoria o almacenamiento local de cliente sin requerir persistencia de cuenta.
- **ASSUMP-003:** Todos los precios se manejan bajo una única denominación monetaria base predefinida sin conversión de divisas.

## 9. Preguntas Abiertas y Decisiones Pendientes (Open Questions)
- **OPEN-001:** ¿Cuál debe ser el comportamiento esperado del carrito si el usuario cierra el navegador o refresca la página (retener ítems localmente vs reiniciar sesión limpia)?
- **OPEN-002:** Delegación técnica: La selección de patrones arquitectónicos, estrategia de persistencia y contratos de API se resolverá formalmente en `02-architecture` y `03-data-modeling`.
