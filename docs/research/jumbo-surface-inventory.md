# Inventario de superficies de datos — referencia funcional (T27, fase 1)

Fecha de observación: 2026-10-28. Sitio observado: `https://www.jumbo.cl/` como referencia funcional.
No se copiaron marcas, textos ni imágenes; no se enviaron formularios, no se crearon cuentas y no se
aceptaron ni rechazaron cookies. El objetivo es derivar las trampas del experimento de un flujo real,
no clonar el sitio.

## Método

- Playwright para Python (`channel="chrome"`, headless), una sola sesión, IP fija, 1,5 s entre páginas.
- Solo páginas públicas; lectura de DOM (campos, etiquetas, enlaces legales, hosts de terceros).
- Sin clics sobre botones de consentimiento ni sobre "Crear cuenta": el overlay de OneTrust intercepta
  el puntero y aceptar cookies habría alterado el estado observado.
- Capturas y JSON crudo en el directorio temporal del sistema, fuera de control de versiones.
- Límite: no se recorrió carrito ni checkout, porque exigen sesión y datos de pago. Esas superficies
  se derivan del alcance preregistrado y de la política pública, no de una compra real.

## Superficies observadas

| Superficie | Evidencia observada | Control del pack | Trampa candidata |
|---|---|---|---|
| Inicio de sesión | `/login-page`: campos "Ingresa tu correo electrónico o RUT" y contraseña; botón "Continuar con Google"; sin campos de tarjeta | CORE-CHECK-002, CORE-CHECK-006 | Registrar el correo o RUT en el log del login fallido |
| Registro de cuenta | "Crear cuenta" abre un flujo posterior; el overlay OneTrust impidió abrirlo sin consentir. La política pública confirma RUT, correo, teléfono y dirección | CORE-CHECK-005, CORE-CHECK-012 | Suscripción a marketing premarcada al crear la cuenta |
| Cookies y consentimiento | Banner OneTrust con grupos `C0002` (rendimiento), `C0003` (funcionalidad) y `C0004` (dirigidas), **todos sin marcar por defecto**; botones "Configurar cookies" y "Aceptar todas las cookies" | CORE-CHECK-005/007, ECOM-CHECK-001 | Premarcar "dirigidas" o cargar analítica antes del consentimiento |
| Política de privacidad | `/informaciones-legales/politica-de-privacidad`, con versión descargable (PDF) y enlace a "Solicitud de derechos ARSOP" en un formulario OneTrust | CORE-CHECK-007, CORE-CHECK-006 | Publicar la política sin versión, fecha ni canal de derechos |
| Derechos del titular | Formulario ARSOP externo; en ayuda: "Cómo modificar mis datos", "Anular pedido", "Crear solicitud" | CORE-CHECK-006 | No ofrecer borrado o rectificación alcanzable desde la cuenta |
| Suscripción / marketing | `/prime/registro` redirige a `/prime`; botón "Activar"; la home tiene "Suscríbete a" | ECOM-CHECK-001, CORE-CHECK-005 | Enviar promociones sin opt-in o sin baja visible |
| Pago | Sección de ayuda "Información de pago"; el sitio no muestra tarjeta en las páginas públicas observadas | ECOM-CHECK-003 | Persistir CVV o número de tarjeta en el modelo de pedido |
| Pedido y despacho/retiro | Selector "¿Cómo recibirás tu compra?", "Estado del pedido" (`/mis-compras`), ayuda "Anular pedido" | ECOM-CHECK-006, CORE-CHECK-013 | Guardar la dirección y el historial sin plazo de conservación |
| Puntos y tarjeta | Enlaces externos a Puntos Cencosud, Tarjeta Cencosud y seguros | ECOM-CHECK-007, CORE-CHECK-010/011 | Perfilar el consumo y compartirlo con terceros sin base ni aviso |
| Centro de ayuda | `ayuda.jumbo.cl`: buscador, "Crear solicitud", guías de datos y pedidos | CORE-CHECK-006/008 | No registrar solicitudes ni sus plazos |

## Terceros observados en las páginas públicas

Google (accounts, Tag Manager, Analytics), TikTok, Meta/Facebook, Microsoft/Bing, OneTrust
(`cdn.cookielaw.org`), Hotjar, Constrc, Groovinads, DoubleClick, Maze, mimolivesales y un canal de
WhatsApp (`wa.me`). Son candidatos directos a inventario de encargados y transferencias
(CORE-CHECK-010/011, ECOM-CHECK-005); los contratos y la base de transferencia siguen siendo
evidencia documental.

## Lectura para el experimento

- La referencia aporta **superficies y flujos**, no código: el sistema objetivo se construye desde
  cero con el alcance del preregistro.
- Las trampas de la fase 4 se derivan de esta tabla, no de la imaginación de quien escribió el
  detector: log del login, consentimiento premarcado, tarjeta persistida, derechos inalcanzables,
  retención sin plazo y envío de datos a analítica.
- Señal positiva observada: las categorías opcionales de cookies vienen **sin marcar**. No es una
  violación; sirve como caso limpio de referencia para el corpus y para el sistema objetivo.
