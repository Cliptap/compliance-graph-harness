-- Migracion: Tabla de Auditoria (Trazabilidad Alta Gobernanza)
-- Fecha: 2026-06-11
-- Descripcion: Agrega tabla audit_logs con indices para trazabilidad granular

CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR PRIMARY KEY,
    entity_type VARCHAR(50) NOT NULL,
    entity_id VARCHAR NOT NULL,
    field_name VARCHAR(100) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    operation VARCHAR(10) NOT NULL,
    changed_by VARCHAR(100) NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_changed_by ON audit_logs(changed_by);
CREATE INDEX IF NOT EXISTS idx_audit_changed_at ON audit_logs(changed_at DESC);
