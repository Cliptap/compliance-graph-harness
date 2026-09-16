-- ==========================================
-- Iteración 2: Esquema de Médicos y Citas
-- Gobernanza: Media
-- ==========================================

-- Extensión necesaria para índices de rangos (GIST) en validación temporal
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 1. Tabla de Médicos (doctors)
CREATE TABLE IF NOT EXISTS doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rut VARCHAR(12) UNIQUE NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    especialidad VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger para actualizar `updated_at` en doctors (asume que la función de actualización ya existe o debe crearse)
-- CREATE TRIGGER trg_doctors_updated_at BEFORE UPDATE ON doctors FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 2. Tabla de Citas (appointments) transaccional
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paciente_id UUID NOT NULL REFERENCES patients(id) ON DELETE RESTRICT,
    medico_id UUID NOT NULL REFERENCES doctors(id) ON DELETE RESTRICT,
    fecha_hora TIMESTAMP WITH TIME ZONE NOT NULL,
    duracion_minutos INTEGER NOT NULL DEFAULT 30 CHECK (duracion_minutos > 0),
    estado VARCHAR(20) NOT NULL DEFAULT 'Programada' 
        CHECK (estado IN ('Programada', 'Confirmada', 'Completada', 'Cancelada')),
    motivo_consulta TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Reglas de Negocio (Gobernanza Media): Prevención de Colisiones (Double-Booking)
-- Regla: Un médico no puede tener dos citas que se superpongan en el tiempo, 
-- a menos que alguna esté cancelada o completada.
ALTER TABLE appointments
ADD CONSTRAINT prevent_double_booking
EXCLUDE USING gist (
    medico_id WITH =,
    tsrange(
        fecha_hora, 
        fecha_hora + (duracion_minutos || ' minutes')::interval
    ) WITH &&
)
WHERE (estado IN ('Programada', 'Confirmada'));

-- Índices de rendimiento recomendados para las consultas de reportería y filtros
CREATE INDEX idx_appointments_medico_id_fecha ON appointments(medico_id, fecha_hora);
CREATE INDEX idx_appointments_paciente_id ON appointments(paciente_id);
