-- ==========================================
-- REPORTERÍA Y VISTAS ANALÍTICAS - PACIENTES
-- ==========================================

-- 1. Vista de Estadísticas Generales (KPIs)
-- Agrupa el total de pacientes y la proporción FONASA vs ISAPRE.
CREATE OR REPLACE VIEW vw_patient_kpis AS
SELECT 
    COUNT(patient_id) AS total_pacientes,
    SUM(CASE WHEN prevision = 'fonasa' THEN 1 ELSE 0 END) AS total_fonasa,
    SUM(CASE WHEN prevision = 'isapre' THEN 1 ELSE 0 END) AS total_isapre
FROM patients;

-- 2. Vista de Pacientes Recientes (Filtros temporales base)
-- Ejemplo de CTE para reportar ingresos filtrados usando funciones de ventana y fechas
CREATE OR REPLACE VIEW vw_recent_patients_summary AS
WITH patient_timeline AS (
    SELECT 
        rut,
        nombres,
        apellidos,
        prevision,
        created_at,
        CASE 
            WHEN created_at >= CURRENT_DATE THEN 'today'
            WHEN created_at >= date_trunc('week', CURRENT_DATE) THEN 'this_week'
            WHEN created_at >= date_trunc('month', CURRENT_DATE) THEN 'this_month'
            ELSE 'older'
        END as time_group
    FROM patients
)
SELECT * FROM patient_timeline
ORDER BY created_at DESC;
