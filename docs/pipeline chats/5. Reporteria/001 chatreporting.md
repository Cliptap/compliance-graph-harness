# Registro de Chat - Etapa 5: Reportería

**Usuario:**
> Total de pacientes y fonasa vs isapre que sea posible ordenar... integramos como opcion en el frontend. Utiliza la lógica que corresponda de `data_reporting.md`.

**Agente:**
> Para implementar la reporteria básica (KPIs del consultorio) y respetar la "Separación de Intereses" de `data_reporting.md`:
> 
> 1. En SQL: He creado vistas para análisis. Ej: `vw_patient_kpis` (`src/database/schema/02_analytics_views.sql`).
> 2. En el API: He expuesto el endpoint `/patients/stats/kpis` en el backend `api/patients.py` para devolver los totales y desgloses.
> 3. En el UI: Voy a agregar un panel de tarjetas estáticas encima de la tabla en `index.html` para mostrar la cuenta: "Total", "Mismo mes" y "Agrupación Previsional". Incluiré un select estático de "Orden" y "Filtro Temporal".

**Usuario:**
> Carga los datos por defecto cuando abra la página y veamos.

**Agente:**
> Listo. `app.js` ahora hace fetch a `/patients/stats/kpis` y actualiza automáticamente los divs `#total-pacientes`, `#pacientes-fonasa` y `#pacientes-isapre` pintándolos con colores para destacar la métrica principal.
> Se han añadido los selects de `Filtro Temporal: Histórico Completo` en la UI para aplicar *sorting*.

**Usuario:**
> Corramos el proyecto para revisar esta iteración completa.

**Agente:**
> Todo levantado.
> Servidor FastAPI encendido en `http://127.0.0.1:8000`.
> Servidor de UI operando en `http://127.0.0.1:8080`.
> Simple Browser abierto. Te invito a hacer pruebas llenando pacientes y revisar cómo los KPIs suben en tiempo real.