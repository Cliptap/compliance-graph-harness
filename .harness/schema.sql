-- Esquema de Base de Datos Embebida para el Harness VibeCoding (Antigravity)
-- Soporta Arquitectura de Doble Grafo (Contexto de Código estilo Graphify + Data Lineage)
-- y Trazabilidad / Observabilidad de Subagentes.

PRAGMA foreign_keys = ON;

-- 1. NODOS DEL GRAFO (Unificado para Contexto y Data Lineage)
CREATE TABLE IF NOT EXISTS graph_nodes (
    id TEXT PRIMARY KEY,                       -- Ej: 'src_database_models_patient' o 'src/backend/api/patients.py'
    name TEXT NOT NULL,                         -- Nombre del símbolo: 'Patient' o 'create_patient'
    node_type TEXT NOT NULL,                   -- 'file', 'class', 'callable', 'endpoint', 'source', 'sink', 'sanitizer'
    file_path TEXT NOT NULL,                   -- Ruta relativa del archivo fuente
    line_start INTEGER,                        -- Línea inicial en código
    line_end INTEGER,                          -- Línea final en código
    data_classification TEXT DEFAULT 'PUBLIC', -- 'PUBLIC', 'IDENTIFIER_RUT', 'SENSITIVE_HEALTH', 'CONFIDENTIAL'
    community INTEGER DEFAULT 0,               -- Clúster de comunidad calculado por Graphify (Louvain/Leiden)
    norm_label TEXT,                           -- Etiqueta normalizada para deduplicación
    metadata_json TEXT DEFAULT '{}'            -- Metadatos adicionales (decoradores, callable, origin, etc.)
);

CREATE INDEX IF NOT EXISTS idx_nodes_community ON graph_nodes(community);

-- 2. ARISTAS DEL GRAFO (Relaciones de Contexto y Flujo de Datos)
CREATE TABLE IF NOT EXISTS graph_edges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,                   -- 'IMPORTS', 'DEFINES', 'CALLS', 'FLOWS_TO', 'SANITIZED_BY', 'WRITES_TO'
    metadata_json TEXT DEFAULT '{}',
    FOREIGN KEY (source_id) REFERENCES graph_nodes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES graph_nodes(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON graph_edges(target_id);
CREATE INDEX IF NOT EXISTS idx_edges_type ON graph_edges(edge_type);

-- 3. REGLAS TÉCNICAS DE CUMPLIMIENTO (Ley 21.719 de Protección de Datos Personales de Chile)
CREATE TABLE IF NOT EXISTS compliance_rules (
    rule_id TEXT PRIMARY KEY,                  -- Ej: 'CL-DATAPROT-001'
    law_article TEXT NOT NULL,                 -- 'Ley 21.719 Art. 14 quater / Arts. de Seguridad'
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    sensitive_category TEXT NOT NULL,          -- 'SENSITIVE_HEALTH', 'IDENTIFIER_RUT', etc.
    prohibited_sinks TEXT NOT NULL,            -- JSON array: ['logging', 'print', 'unencrypted_audit']
    required_mitigations TEXT NOT NULL,        -- JSON array: ['hash', 'encrypt', 'mask', 'redact']
    severity TEXT NOT NULL DEFAULT 'CRITICAL'  -- 'CRITICAL', 'HIGH', 'MEDIUM'
);

-- 4. HALLAZGOS Y VULNERABILIDADES DETECTADAS (Auditoría)
CREATE TABLE IF NOT EXISTS compliance_findings (
    id TEXT PRIMARY KEY,
    rule_id TEXT NOT NULL,
    source_node_id TEXT NOT NULL,
    sink_node_id TEXT NOT NULL,
    taint_path_json TEXT NOT NULL,             -- Ruta completa del flujo de datos no mitigado
    status TEXT DEFAULT 'OPEN',                -- 'OPEN', 'ISOLATED', 'PATCHED', 'FALSE_POSITIVE'
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    resolved_at DATETIME,
    patch_commit_or_diff TEXT,
    FOREIGN KEY (rule_id) REFERENCES compliance_rules(rule_id),
    FOREIGN KEY (source_node_id) REFERENCES graph_nodes(id),
    FOREIGN KEY (sink_node_id) REFERENCES graph_nodes(id)
);

-- 5. OBSERVABILIDAD Y REGISTRO DE RAZONAMIENTO DE SUBAGENTES
CREATE TABLE IF NOT EXISTS agent_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    agent_name TEXT NOT NULL,                  -- 'auditor_agent', 'developer_patcher_agent', etc.
    step_name TEXT NOT NULL,                   -- 'detect_vulnerabilities', 'subgraph_slice', 'generate_patch'
    input_payload TEXT,                        -- Prompt o datos de entrada del paso
    reasoning_trace TEXT NOT NULL,             -- Cadena de pensamiento o justificación de decisión
    output_result TEXT,                        -- Resultado del paso o código generado
    tokens_used INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_session ON agent_audit_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_agent_name ON agent_audit_logs(agent_name);

-- 6. AUDITORÍA PERICIAL DE CHECKLIST POR NODO Y ARCHIVO
CREATE TABLE IF NOT EXISTS file_checklist_audits (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_node_id TEXT NOT NULL,
    plugin_name TEXT NOT NULL,                 -- 'core_universal' o 'health_clinical'
    criterion_id TEXT NOT NULL,
    law_article TEXT NOT NULL,
    status TEXT NOT NULL,                      -- 'PASSED', 'VIOLATION', 'NOT_APPLICABLE'
    severity TEXT NOT NULL,
    details TEXT,
    evidence_snippet TEXT,
    remediation_advice TEXT,
    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_checklist_file ON file_checklist_audits(file_path);
CREATE INDEX IF NOT EXISTS idx_checklist_session ON file_checklist_audits(session_id);

