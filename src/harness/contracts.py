"""Contratos nucleares de datos para el arnés de gobernanza (Sprint 1).

Define las especificaciones formales de tareas (TaskSpec), hallazgos de auditoría (Finding)
y veredictos de validación (ValidationVerdict) utilizados por el Policy Engine y el Validation Engine.
"""

from __future__ import annotations

import uuid
from typing import Any, Literal
from pydantic import BaseModel, Field


class TaskSpec(BaseModel):
    """Contrato formal que especifica el alcance, restricciones y criterios de una tarea de desarrollo."""
    
    task_id: str = Field(..., description="Identificador único de la tarea (ej: 'T01', 'EXP-01')")
    goal: str = Field(..., description="Objetivo específico de la tarea en lenguaje natural")
    category: Literal["bug_fix", "feature", "refactor", "compliance", "adversarial"] = Field(
        default="feature", description="Categoría funcional de la tarea"
    )
    difficulty: Literal["low", "medium", "high"] = Field(
        default="medium", description="Nivel de complejidad esperado"
    )
    allowed_paths: list[str] = Field(
        default_factory=list,
        description="Rutas relativas de archivos que el agente tiene autorización para modificar",
    )
    forbidden_paths: list[str] = Field(
        default_factory=list,
        description="Rutas relativas de archivos expresamente prohibidos para edición",
    )
    allowed_symbol_mutations: list[str] = Field(
        default_factory=list,
        description="Nombres de funciones o clases que el agente puede agregar o modificar",
    )
    forbidden_patterns: list[str] = Field(
        default_factory=list,
        description="Patrones o tokens prohibidos en el diff (ej: 'logger.info', 'print')",
    )
    constraints: list[str] = Field(
        default_factory=list,
        description="Directivas de gobernanza específicas (ej: 'no external dependencies', 'soft-delete only')",
    )
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        description="Criterios de aceptación funcionales y normativos verificables",
    )
    test_targets: list[str] = Field(
        default_factory=list,
        description="Rutas de pruebas automatizadas que deben pasar para considerar la tarea exitosa",
    )


class Finding(BaseModel):
    """Esquema unificado de hallazgo emitido por cualquier evaluador de política del arnés."""
    
    id: str = Field(
        default_factory=lambda: f"FND-{uuid.uuid4().hex[:8].upper()}",
        description="Identificador único del hallazgo",
    )
    policy_id: str = Field(
        ...,
        description="Identificador de la política evaluada (ej: 'privacy.cwe_532', 'scope.unauthorized_file')",
    )
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"] = Field(
        default="HIGH", description="Nivel de severidad técnica del hallazgo"
    )
    status: Literal["VIOLATION", "WARNING", "PASSED"] = Field(
        default="VIOLATION", description="Estado de la regla sobre el artefacto inspeccionado"
    )
    file: str = Field(..., description="Ruta relativa del archivo evaluado")
    line: int | None = Field(default=None, description="Número de línea donde ocurre la infracción")
    message: str = Field(..., description="Explicación concisa y técnica de la infracción")
    evidence: str | None = Field(default=None, description="Fragmento de código o diff infractor")
    rule_version: str = Field(default="2.0.0", description="Versión de la regla normativa o técnica evaluada")
    remediation_advice: str | None = Field(
        default=None, description="Directiva técnica para que el agente o desarrollador mitigue el hallazgo"
    )


class ValidationVerdict(BaseModel):
    """Veredicto final emitido por el Validation Engine sobre la propuesta de cambio del agente."""
    
    task_id: str = Field(..., description="Identificador de la tarea evaluada")
    status: Literal["PASS", "FAIL"] = Field(..., description="Veredicto global del cambio")
    findings: list[Finding] = Field(default_factory=list, description="Lista de hallazgos activos")
    tests_passed: bool = Field(default=False, description="Indica si la suite de pruebas automatizadas pasó al 100%")
    test_summary: str | None = Field(default=None, description="Resumen de la ejecución de pytest")
    files_evaluated: list[str] = Field(default_factory=list, description="Archivos inspeccionados en la validación")
    unrequested_changes_detected: bool = Field(
        default=False, description="True si el agente intentó modificar archivos fuera de allowed_paths"
    )
    total_violations: int = Field(default=0, description="Cantidad de hallazgos con status VIOLATION")
    
    def model_post_init(self, __context: Any) -> None:
        violations = sum(1 for f in self.findings if f.status == "VIOLATION")
        object.__setattr__(self, "total_violations", violations)
        if violations > 0 or not self.tests_passed:
            object.__setattr__(self, "status", "FAIL")
        else:
            object.__setattr__(self, "status", "PASS")
