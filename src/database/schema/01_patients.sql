-- Tabla de Pacientes
CREATE TABLE patients (
  patient_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  rut TEXT NOT NULL UNIQUE,
  nombres TEXT NOT NULL,
  apellidos TEXT NOT NULL,
  fecha_nacimiento DATE NOT NULL,
  sexo TEXT NOT NULL CHECK (sexo IN ('M', 'F', 'O')),
  correo TEXT,
  telefono TEXT,
  prevision TEXT NOT NULL CHECK (prevision IN ('fonasa', 'isapre')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Constricción para validar formato de RUT (básico)
ALTER TABLE patients
  ADD CONSTRAINT chk_patients_rut_format CHECK (rut ~ '^[0-9]+-[0-9kK]$');

-- Constricción para validar formato de correo
ALTER TABLE patients
  ADD CONSTRAINT chk_patients_email_format 
  CHECK (correo IS NULL OR correo ~ '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- Índices explícitos para búsquedas frecuentes
CREATE UNIQUE INDEX idx_patients_rut ON patients (rut);
CREATE INDEX idx_patients_apellidos ON patients (apellidos);
