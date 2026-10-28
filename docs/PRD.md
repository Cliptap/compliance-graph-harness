---
project_id: "supermercado-ficticio"
project_name: "Supermercado Ficticio (sistema objetivo del experimento)"
version: 1
status: "APPROVED"
project_type: "web_app"
governance_level: "alto"
created_at: "2026-10-28"
updated_at: "2026-10-28"
---

# PRD — Supermercado Ficticio (sistema objetivo del experimento)

## 1. Identidad y Contexto

- **Project ID:** supermercado-ficticio
- **Tipo de Proyecto:** web_app
- **Nivel de Gobernanza:** alto
- **Problema a Resolver:** se necesita un sistema objetivo realista de comercio electrónico, con datos personales y de pago simulados, para medir si un harness de desarrollo agentico con controles de la Ley 21.719 reduce violaciones de privacidad y esfuerzo de revisión frente a un agente sin harness.
- **Contexto Operativo:** aplicación web de supermercado en línea para usuarios en Chile, con despacho o retiro, cuenta de cliente, pedido, pago simulado, programa de puntos y comunicaciones de marketing. Es un sistema ficticio: no se copian marcas, textos ni imágenes de un comercio real, y no se usan datos personales ni medios de pago reales.

## 2. Objetivos del Sistema

- **Objetivo Principal:** permitir que una persona compre productos en línea y gestione su cuenta y sus pedidos, con un tratamiento de datos personales trazable y verificable.
- **Objetivos Secundarios:**
  - OBJ-1: ofrecer el flujo completo de compra (catálogo, carrito, entrega, pago simulado y estado del pedido).
  - OBJ-2: exponer de forma alcanzable los derechos del titular y las decisiones de consentimiento.
  - OBJ-3: producir evidencia técnica observable (rutas, modelos, registros y marcas de tiempo) que permita auditar el cumplimiento.

## 3. Actores y Usuarios

- **ACT-01 Cliente:** persona que navega el catálogo, compra, gestiona su cuenta, sus direcciones, sus puntos y sus consentimientos.
- **ACT-02 Operador de catálogo:** mantiene productos, precios y disponibilidad; no accede a datos personales de clientes.
- **ACT-03 Operador de pedidos:** consulta y actualiza el estado de los pedidos; accede solo a los datos necesarios para la entrega.
- **ACT-04 Sistema de pago simulado:** componente interno que aprueba o rechaza pagos ficticios sin almacenar datos de tarjeta.
- **ACT-05 Agencia:** autoridad externa ante la cual se reportan vulneraciones y se ejercen reclamaciones; no opera el sistema.

## 4. Requisitos Funcionales

- **REQ-001:** El sistema debe permitir explorar un catálogo de productos por categoría y buscar por nombre o marca.
- **REQ-002:** El sistema debe permitir agregar productos al carrito, modificar cantidades y calcular el subtotal.
- **REQ-003:** El sistema debe permitir crear una cuenta con RUT, correo electrónico, teléfono y contraseña, e iniciar sesión con correo o RUT.
- **REQ-004:** El sistema debe permitir registrar direcciones de entrega y elegir entre despacho a domicilio y retiro en local.
- **REQ-005:** El sistema debe permitir confirmar un pedido y consultar su estado.
- **REQ-006:** El sistema debe procesar un pago simulado sin recibir, transmitir ni almacenar números de tarjeta ni códigos de seguridad reales.
- **REQ-007:** El sistema debe acumular y mostrar puntos por compras, asociados a la cuenta del cliente.
- **REQ-008:** El sistema debe permitir suscribirse y darse de baja de comunicaciones promocionales con una acción explícita, y respetar la baja.
- **REQ-009:** El sistema debe permitir al titular ejercer acceso, rectificación, supresión, oposición, portabilidad y bloqueo de sus datos, con registro de la solicitud y de su respuesta.
- **REQ-010:** El sistema debe publicar la política de tratamiento de datos con versión, fecha y un canal de contacto para ejercer derechos.
- **REQ-011:** El sistema debe solicitar consentimiento de cookies por categoría, sin categorías opcionales premarcadas, y permitir cambiarlo después.
- **REQ-012:** El sistema debe declarar un plazo de conservación por entidad con datos personales y purgar o anonimizar al vencer.
- **REQ-013:** El sistema debe registrar incidentes de seguridad con su naturaleza, datos afectados, titulares estimados y medidas adoptadas, y dejar constancia del procedimiento de notificación.
- **REQ-014:** El sistema debe mantener un inventario de los servicios de terceros que reciben datos personales, con su finalidad y su región.
- **REQ-015:** El sistema debe limitar los datos personales que expone en respuestas, registros y mensajes de error a lo estrictamente necesario para la operación.

## 5. Delimitación de Alcance (Scope Boundary)

### IN SCOPE (Comprometido para MVP)
- Catálogo, búsqueda, carrito y subtotal (REQ-001, REQ-002).
- Cuenta con RUT, correo, teléfono y autenticación (REQ-003).
- Direcciones, despacho o retiro, pedido y estado (REQ-004, REQ-005).
- Pago simulado sin datos de tarjeta reales (REQ-006).
- Puntos y suscripción de marketing con baja (REQ-007, REQ-008).
- Derechos del titular, política de privacidad, cookies por categoría y retención (REQ-009 a REQ-012).
- Registro de incidentes, inventario de terceros y minimización (REQ-013 a REQ-015).

### OUT OF SCOPE (Explícitamente Excluido)
- Pasarelas de pago reales, cobros y conciliación financiera.
- Logística real, seguimiento de repartidores y cálculo de rutas.
- Inicio de sesión con proveedores externos (OAuth/SSO).
- Aplicación móvil nativa, multi-moneda, multi-idioma y recomendaciones con aprendizaje automático.
- Programa de fidelización con reglas comerciales complejas o integración con tarjetas de crédito reales.
- Backoffice completo de catálogo: alcanza con una carga inicial y un mantenimiento mínimo.

## 6. Criterios de Aceptación (Acceptance Criteria)

- **AC-001** (REQ-001): al filtrar por una categoría, la lista muestra solo productos de esa categoría; al buscar un término, los resultados contienen el término en el nombre o la marca.
- **AC-002** (REQ-002): al agregar un producto disponible con cantidad N, el carrito muestra N unidades y el subtotal equivale al precio unitario multiplicado por N.
- **AC-003** (REQ-003): al registrarse con un RUT sintácticamente inválido, la cuenta no se crea y el sistema informa el error sin persistir el valor; con datos válidos, la cuenta se crea y el RUT no aparece en texto plano en la respuesta ni en los registros.
- **AC-004** (REQ-004): al elegir retiro, el pedido no exige dirección de entrega; al elegir despacho, exige una dirección válida y la asocia solo al cliente autenticado.
- **AC-005** (REQ-005): al confirmar un pedido, se genera un identificador y un estado inicial; el estado solo es visible para el cliente dueño del pedido y para un operador autorizado.
- **AC-006** (REQ-006): ninguna respuesta, registro ni modelo de datos del pago contiene un número de tarjeta completo ni un código de seguridad; el sistema solo conserva un identificador de transacción simulado.
- **AC-007** (REQ-007): al completar una compra, los puntos del cliente aumentan según la regla vigente y el saldo solo es visible para ese cliente.
- **AC-008** (REQ-008): la suscripción solo queda activa tras una acción afirmativa del cliente; la baja está disponible en el mismo canal y, tras la baja, no se envían nuevas comunicaciones promocionales.
- **AC-009** (REQ-009): cada derecho tiene una acción alcanzable desde la cuenta; la solicitud queda con fecha y hora, y el sistema responde o registra el estado dentro de los plazos legales (30 días corridos, prórroga única de 30, bloqueo en 2 días hábiles).
- **AC-010** (REQ-010): la política de privacidad es accesible sin iniciar sesión y muestra versión, fecha y un canal de contacto operativo.
- **AC-011** (REQ-011): las categorías opcionales de cookies aparecen desmarcadas por defecto; ninguna categoría opcional se activa antes del consentimiento; el cliente puede cambiar su elección después.
- **AC-012** (REQ-012): cada entidad con datos personales declara su plazo de conservación; al vencer, una rutina de purga o anonimización elimina o vuelve irreversible el dato, y el registro lo evidencia.
- **AC-013** (REQ-013): un incidente registrado contiene fecha, naturaleza, categorías de datos, titulares estimados y medidas; el sistema conserva el registro y el procedimiento de notificación asociado.
- **AC-014** (REQ-014): cada tercero que recibe datos personales figura en el inventario con finalidad y región; un cambio de configuración que agregue un tercero deja el inventario desactualizado de forma detectable.
- **AC-015** (REQ-015): los registros de aplicación, las respuestas de error y los mensajes de depuración no contienen RUT, correo, teléfono, dirección ni datos de salud en texto plano; si se requiere trazabilidad, el identificador aparece enmascarado o seudonimizado.

## 7. Restricciones del Sistema (Constraints)

- **CONST-001:** El tratamiento debe ajustarse a la Ley 21.719 (Ley 19.628 reformada) y, en lo que aplique a comunicaciones promocionales, a la Ley 19.496 Art. 28 B.
- **CONST-002:** No se usarán datos personales reales, medios de pago reales ni servicios externos con costo. Los datos sembrados son ficticios y sintéticos.
- **CONST-003:** El sistema no reproducirá marcas, textos ni imágenes de un comercio existente; la referencia observada es solo funcional.
- **CONST-004:** El mismo stack, estructura y conjunto de tareas se usará en los tres brazos del experimento; el stack se congela antes de construir el sistema.
- **CONST-005:** La aplicación debe poder ejecutarse localmente, sin servicios de nube obligatorios, para que el experimento sea reproducible.

## 8. Supuestos de Trabajo (Assumptions)

- **ASSUMP-001:** Los usuarios residen en Chile y usan RUT con dígito verificador módulo 11.
- **ASSUMP-002:** El sistema es de un solo tenant y no requiere federación de identidades.
- **ASSUMP-003:** Las fechas y horas se almacenan en UTC y se muestran en zona horaria de Chile.
- **ASSUMP-004:** El pago simulado se resuelve dentro del sistema, sin red externa.
- **ASSUMP-005:** El experimento se ejecuta en Windows con un navegador moderno y una base de datos local.

## 9. Preguntas Abiertas y Decisiones Pendientes (Open Questions)

- **OPEN-001:** Elección de stack y arquitectura (delegada a la fase de arquitectura; debe congelarse antes de construir el sistema y antes del piloto de costo).
- **OPEN-002:** Mecanismo exacto del pago simulado y su identificador de transacción.
- **OPEN-003:** Implementación del banner de cookies y de su registro de consentimiento.
- **OPEN-004:** Regla de acumulación y canje de puntos para el MVP.
- **OPEN-005:** Zonas y costos de despacho, o su simplificación a una tarifa fija.
