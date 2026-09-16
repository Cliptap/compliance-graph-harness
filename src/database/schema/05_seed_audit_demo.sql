-- Seed data para demo de trazabilidad
-- Ejecutar: docker compose exec db psql -U vibecoding_user -d vibecoding_db -f /dev/stdin < seed.sql
-- O copiar al container y ejecutar

-- Limpiar
DELETE FROM audit_logs;
DELETE FROM appointments;
DELETE FROM practitioners;
DELETE FROM patients;

-- Medicos (telecom = telefono, email = vinculacion con usuario)
INSERT INTO practitioners (id, identifier, name, specialty, telecom, email, is_deleted) VALUES
('doc-1', '11111111-1', 'Dra. Maria Gonzalez', 'Medicina General', '+56911111111', 'medico@clinic.com', false),
('doc-2', '22222222-2', 'Dr. Pedro Silva', 'Pediatria', '+56922222222', 'medico2@clinic.com', false),
('doc-3', '33333333-3', 'Dra. Carmen Munoz', 'Cardiologia', '+56933333333', 'medico3@clinic.com', false);

-- Pacientes
INSERT INTO patients (id, identifier, name, is_deleted) VALUES
('pat-01', '15123456-7', 'Juan Perez', false),
('pat-02', '16234567-8', 'Ana Soto', false),
('pat-03', '17345678-9', 'Luis Rojas', false),
('pat-04', '18456789-0', 'Elena Diaz', false),
('pat-05', '19567890-1', 'Martin Castro', false);

-- Citas en diferentes horarios (hoy)
INSERT INTO appointments (id, status, start_time, end_time, patient_id, practitioner_id, is_deleted) VALUES
('apt-01', 'confirmada', NOW()::date + '09:00'::time, NOW()::date + '09:30'::time, 'pat-01', 'doc-1', false),
('apt-02', 'agendada', NOW()::date + '09:30'::time, NOW()::date + '10:00'::time, 'pat-02', 'doc-2', false),
('apt-03', 'agendada', NOW()::date + '10:00'::time, NOW()::date + '10:30'::time, 'pat-03', 'doc-1', false),
('apt-04', 'agendada', NOW()::date + '10:30'::time, NOW()::date + '11:00'::time, 'pat-04', 'doc-3', false),
('apt-05', 'cancelada', NOW()::date + '11:00'::time, NOW()::date + '11:30'::time, 'pat-05', 'doc-2', false),
('apt-06', 'agendada', NOW()::date + '14:00'::time, NOW()::date + '14:30'::time, 'pat-01', 'doc-3', false),
('apt-07', 'agendada', NOW()::date + '15:30'::time, NOW()::date + '16:00'::time, 'pat-03', 'doc-2', false);

-- Registros de auditoria simulados (con timestamps variados)
INSERT INTO audit_logs (id, entity_type, entity_id, field_name, old_value, new_value, operation, changed_by, changed_at) VALUES
-- 08:00 - admin crea medicos
(gen_random_uuid(), 'practitioners', 'doc-1', 'name', NULL, 'Dra. Maria Gonzalez', 'CREATE', 'admin@clinic.com', NOW()::date + '08:00'::time),
(gen_random_uuid(), 'practitioners', 'doc-1', 'identifier', NULL, '11111111-1', 'CREATE', 'admin@clinic.com', NOW()::date + '08:00'::time),
(gen_random_uuid(), 'practitioners', 'doc-1', 'specialty', NULL, 'Medicina General', 'CREATE', 'admin@clinic.com', NOW()::date + '08:00'::time),
(gen_random_uuid(), 'practitioners', 'doc-2', 'name', NULL, 'Dr. Pedro Silva', 'CREATE', 'admin@clinic.com', NOW()::date + '08:01'::time),
(gen_random_uuid(), 'practitioners', 'doc-2', 'identifier', NULL, '22222222-2', 'CREATE', 'admin@clinic.com', NOW()::date + '08:01'::time),
(gen_random_uuid(), 'practitioners', 'doc-2', 'specialty', NULL, 'Pediatria', 'CREATE', 'admin@clinic.com', NOW()::date + '08:01'::time),

-- 08:30 - recepcionista registra pacientes
(gen_random_uuid(), 'patients', 'pat-01', 'name', NULL, 'Juan Perez', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '08:30'::time),
(gen_random_uuid(), 'patients', 'pat-01', 'identifier', NULL, '15123456-7', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '08:30'::time),
(gen_random_uuid(), 'patients', 'pat-02', 'name', NULL, 'Ana Soto', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '08:32'::time),
(gen_random_uuid(), 'patients', 'pat-02', 'identifier', NULL, '16234567-8', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '08:32'::time),
(gen_random_uuid(), 'patients', 'pat-03', 'name', NULL, 'Luis Rojas', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '08:35'::time),
(gen_random_uuid(), 'patients', 'pat-03', 'identifier', NULL, '17345678-9', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '08:35'::time),

-- 09:00 - recepcionista agenda citas de la manana
(gen_random_uuid(), 'appointments', 'apt-01', 'status', NULL, 'confirmada', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:00'::time),
(gen_random_uuid(), 'appointments', 'apt-01', 'start_time', NULL, NOW()::date::text || 'T09:00:00', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:00'::time),
(gen_random_uuid(), 'appointments', 'apt-01', 'patient_id', NULL, 'pat-01', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:00'::time),
(gen_random_uuid(), 'appointments', 'apt-01', 'practitioner_id', NULL, 'doc-1', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:00'::time),

-- 09:05 - recepcionista agenda cita para pat-02 con doc-2
(gen_random_uuid(), 'appointments', 'apt-02', 'status', NULL, 'agendada', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:05'::time),
(gen_random_uuid(), 'appointments', 'apt-02', 'patient_id', NULL, 'pat-02', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:05'::time),
(gen_random_uuid(), 'appointments', 'apt-02', 'practitioner_id', NULL, 'doc-2', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:05'::time),

-- 09:10 - recepcionista agenda mas citas
(gen_random_uuid(), 'appointments', 'apt-03', 'status', NULL, 'agendada', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:10'::time),
(gen_random_uuid(), 'appointments', 'apt-03', 'patient_id', NULL, 'pat-03', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:10'::time),
(gen_random_uuid(), 'appointments', 'apt-03', 'practitioner_id', NULL, 'doc-1', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '09:10'::time),

-- 09:15 - admin agenda para doc-3
(gen_random_uuid(), 'appointments', 'apt-04', 'status', NULL, 'agendada', 'CREATE', 'admin@clinic.com', NOW()::date + '09:15'::time),
(gen_random_uuid(), 'appointments', 'apt-04', 'patient_id', NULL, 'pat-04', 'CREATE', 'admin@clinic.com', NOW()::date + '09:15'::time),
(gen_random_uuid(), 'appointments', 'apt-04', 'practitioner_id', NULL, 'doc-3', 'CREATE', 'admin@clinic.com', NOW()::date + '09:15'::time),

-- 10:30 - recepcionista modifica nombre de paciente (UPDATE)
(gen_random_uuid(), 'patients', 'pat-02', 'name', 'Ana Soto', 'Ana Soto Actualizada', 'UPDATE', 'recepcionista@clinic.com', NOW()::date + '10:30'::time),

-- 11:00 - admin cancela cita
(gen_random_uuid(), 'appointments', 'apt-05', 'status', 'agendada', 'cancelada', 'UPDATE', 'admin@clinic.com', NOW()::date + '11:00'::time),

-- 14:00 - recepcionista agenda cita de la tarde
(gen_random_uuid(), 'appointments', 'apt-06', 'status', NULL, 'agendada', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '14:00'::time),
(gen_random_uuid(), 'appointments', 'apt-06', 'patient_id', NULL, 'pat-01', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '14:00'::time),
(gen_random_uuid(), 'appointments', 'apt-06', 'practitioner_id', NULL, 'doc-3', 'CREATE', 'recepcionista@clinic.com', NOW()::date + '14:00'::time),

-- 15:30 - admin agenda ultima cita
(gen_random_uuid(), 'appointments', 'apt-07', 'status', NULL, 'agendada', 'CREATE', 'admin@clinic.com', NOW()::date + '15:30'::time),
(gen_random_uuid(), 'appointments', 'apt-07', 'patient_id', NULL, 'pat-03', 'CREATE', 'admin@clinic.com', NOW()::date + '15:30'::time),
(gen_random_uuid(), 'appointments', 'apt-07', 'practitioner_id', NULL, 'doc-2', 'CREATE', 'admin@clinic.com', NOW()::date + '15:30'::time),

-- 16:30 - recepcionista elimina paciente (soft-delete)
(gen_random_uuid(), 'patients', 'pat-05', '*', '{"id":"pat-05","identifier":"19567890-1","name":"Martin Castro"}', NULL, 'DELETE', 'recepcionista@clinic.com', NOW()::date + '16:30'::time);
