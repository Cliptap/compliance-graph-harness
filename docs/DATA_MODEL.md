---
project_id: "catalogo-carrito-web"
project_name: "Sistema Web Básico de Catálogo y Carrito de Compras"
version: 1
status: "APPROVED"
governance_level: "bajo"
persistence_target: "sqlite"
created_at: "2026-10-07"
updated_at: "2026-10-07"
---

# Especificación del Modelo de Datos — Sistema Web Básico de Catálogo y Carrito de Compras

## 1. Contexto e Invariantes Heredadas
- **PRD de Referencia:** `docs/PRD.md` (Versión 1, `status: APPROVED`).
- **Arquitectura de Referencia:** `docs/ARCHITECTURE.md` (Versión 1, `status: APPROVED`).
- **Nivel de Gobernanza:** `bajo` (MVP básico sin esquemas pesados de auditoría forense ni soft-delete obligatorio).
- **Límites de Alcance Heredados:**
  - `IN SCOPE:` Catálogo de productos, búsqueda textual por nombre, estructura del carrito en cliente y cálculo de subtotales.
  - `OUT OF SCOPE:` Cero pasarelas financieras, cero cuentas de acceso y cero algoritmos predictivos.

---

## 2. Entidades de Persistencia del Servidor (Server Data Model)
- **ENT-001 [Product]:**
  - **Componentes Asociados:** COMP-001 (Catálogo de Productos) y COMP-003 (Persistencia Ligera).
  - **Requisitos Soportados:** REQ-001 (Visualización de Catálogo) y REQ-002 (Búsqueda por Nombre).
  - **Tabla en SQLite:** `products`
  - **Propósito:** Almacena los ítems ofertados en el catálogo comercial disponibles para consulta y adición al carrito.
  - **Definición de Columnas y Atributos:**
    - `id`: Integer, Clave Primaria (Primary Key), Autoincremental, Not Null. Identificador numérico único del producto.
    - `name`: String(255), Not Null. Denominación comercial del producto para visualización y búsqueda.
    - `description`: String(1000), Nullable (opcional). Resumen descriptivo de características y detalles.
    - `price`: Numeric(10, 2), Not Null. Precio unitario en moneda base. Sujeto a regla de no-negatividad.
  - **Índices de Soporte:** IDX-001 sobre `name`.

---

## 3. Esquema de Datos del Lado Cliente (Client Storage Model)
Conforme a la decisión arquitectónica vinculante **AD-003**, el estado del carrito no se persiste en tablas de la base de datos de servidor ni genera sesiones en backend, sino que reside íntegramente en el navegador del cliente utilizando Web Storage (`localStorage`).

- **DTO-CART-001 [CartItem]:**
  - **Componente Asociado:** COMP-002 (Carrito de Compras).
  - **Requisitos Soportados:** REQ-003 (Gestión de Carrito) y REQ-004 (Cálculo de Totales).
  - **Medio de Almacenamiento:** Navegador Web Storage (`localStorage`) serializado como JSON.
  - **Estructura del Ítem Individual (`CartItem`):**
    - `product_id`: Integer, Not Null. Referencia al identificador del producto en el catálogo (ENT-001).
    - `name`: String, Not Null. Nombre congelado al momento de añadir para renderizado desacoplado.
    - `unit_price`: Numeric(10, 2), Not Null. Precio unitario al momento de incorporar el ítem.
    - `quantity`: Integer, Not Null, Mayor o igual a 1. Unidades seleccionadas por el comprador.
    - `subtotal`: Numeric(10, 2), Not Null. Monto calculado derivado (`unit_price * quantity`).
  - **Estructura Raíz del Carrito (`CartState`):**
    - `items`: Array de `CartItem`. Lista indexada por `product_id`.
    - `total_items`: Integer. Sumatoria total de unidades de productos.
    - `total_amount`: Numeric(10, 2). Sumatoria consolidada de los subtotales de cada ítem.
    - `updated_at`: String ISO-8601. Marca temporal de última modificación en el almacenamiento local.

---

## 4. Índices y Optimización de Consultas
- **IDX-001 [idx_product_name]:**
  - **Entidad Afectada:** ENT-001 (`products`).
  - **Columna Indexada:** `name`.
  - **Tipo de Índice:** B-Tree estándar en SQLite (`CREATE INDEX idx_products_name ON products(name)`).
  - **Justificación de Negocio:** Optimiza el filtrado textual insensible a mayúsculas para cumplir con el requisito REQ-002 y el criterio AC-002 sin degradación ante el crecimiento del catálogo.

---

## 5. Invariantes y Reglas de Integridad
- **INV-001 (price_positive):**
  - **Regla:** El precio unitario de un producto debe ser mayor o igual a cero (`price >= 0.0`).
  - **Ámbito:** ENT-001 (Servidor) y DTO-CART-001 (Cliente).
  - **Justificación:** Previene errores de tasación o números negativos en operaciones comerciales.
- **INV-002 (quantity_positive):**
  - **Regla:** La cantidad de unidades de un ítem en el carrito debe ser un entero estrictamente positivo (`quantity >= 1`). Si la cantidad se reduce a 0, el ítem se elimina de la lista.
  - **Ámbito:** DTO-CART-001 (Cliente).
  - **Justificación:** Satisface REQ-003 y AC-003 garantizando consistencia en el estado del carrito.
- **INV-003 (name_required):**
  - **Regla:** El nombre del producto no puede ser nulo ni una cadena vacía tras eliminar espacios (`LENGTH(TRIM(name)) > 0`).
  - **Ámbito:** ENT-001.
  - **Justificación:** Garantiza la viabilidad de visualización y búsqueda en el catálogo (AC-001, AC-002).
- **INV-004 (subtotal_consistency):**
  - **Regla:** Para cada ítem del carrito, `subtotal == unit_price * quantity`. El `total_amount` debe ser idéntico a la suma aritmética de todos los subtotales.
  - **Ámbito:** DTO-CART-001.
  - **Justificación:** Cumplimiento matemático estricto del criterio de aceptación AC-004.

---

## 6. Datos Semilla e Inicialización (Seed Data)
- **SEED-001 [initial_catalog]:**
  - **Entidad Destino:** ENT-001 (`products`).
  - **Propósito:** Precargar el catálogo del MVP con un lote inicial variado y representativo para pruebas locales inmediatas.
  - **Registros Declarativos Semilla:**
    1. `id: 1` | `name: "Cuaderno Universitario"` | `description: "Cuaderno espiral de 100 hojas cuadriculadas"` | `price: 2500.00`
    2. `id: 2` | `name: "Bolígrafo Tinta Negra"` | `description: "Bolígrafo retráctil con tinta gel de secado rápido"` | `price: 800.00`
    3. `id: 3` | `name: "Organizador de Escritorio"` | `description: "Organizador modular de tres compartimentos para papelería"` | `price: 8500.00`
    4. `id: 4` | `name: "Lámpara LED de Mesa"` | `description: "Lámpara de bajo consumo con brazo ajustable y luz cálida"` | `price: 15000.00`
    5. `id: 5` | `name: "Mochila Urbana Multiuso"` | `description: "Mochila resistente con compartimento interior acolchado"` | `price: 22000.00`

---

## 7. Matriz de Linaje Contractual y Trazabilidad

| Identificador Requisito (PRD) | Componente Arquitectura | Identificador de Datos | Destino de Persistencia | Invariantes Aplicadas |
| :--- | :--- | :--- | :--- | :--- |
| **REQ-001** (Catálogo) | `COMP-001`, `COMP-003` | `ENT-001` [Product] | Base de Datos SQLite (Servidor) | `INV-001`, `INV-003` |
| **REQ-002** (Búsqueda) | `COMP-001`, `COMP-003` | `ENT-001` [Product], `IDX-001` | Base de Datos SQLite (Servidor) | `INV-003` |
| **REQ-003** (Carrito) | `COMP-002` | `DTO-CART-001` [CartItem] | Web Storage LocalStorage (Cliente) | `INV-002` |
| **REQ-004** (Totales) | `COMP-002` | `DTO-CART-001` [CartItem] | Web Storage LocalStorage (Cliente) | `INV-001`, `INV-002`, `INV-004` |
