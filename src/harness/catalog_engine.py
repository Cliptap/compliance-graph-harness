"""Pack-driven detection engine.

The engine walks the controls in the catalog, instantiates the declared policy
family and returns findings. Controls marked `implemented: false` are reported
as declared gaps instead of silently disappearing.
"""
from __future__ import annotations

from src.harness.catalog import Catalog, CatalogError, Control
from src.harness.contracts import Finding, TaskSpec
from src.harness.policy_engine import PolicyEngine
from src.harness.policy_families import (
    CodeHygieneFamily,
    CredentialExposureFamily,
    PolicyFamily,
    RetentionDeletionFamily,
    SinkExposureFamily,
)

FAMILIES: dict[str, type[PolicyFamily]] = {
    "sink_exposure": SinkExposureFamily,
    "retention_deletion": RetentionDeletionFamily,
    "credential_exposure": CredentialExposureFamily,
    "code_hygiene": CodeHygieneFamily,
}


class CatalogEngine:
    def __init__(self, catalog: Catalog, include_legacy: bool = True):
        self.catalog = catalog
        self.include_legacy = include_legacy

    def evaluate(self, task: TaskSpec, files: dict[str, str]) -> list[Finding]:
        findings: list[Finding] = []
        legacy_findings: list[Finding] | None = None
        for control in self.catalog.controls:
            if not control.implemented:
                continue
            if control.detection.policy == "legacy":
                if not self.include_legacy:
                    continue
                if legacy_findings is None:
                    legacy_findings = PolicyEngine().evaluate_changes(task, files)
                findings.extend(self._legacy_findings(control, legacy_findings))
                continue
            family = FAMILIES.get(control.detection.policy)
            if family is None:
                raise CatalogError(
                    f"{control.id}: no family registered for {control.detection.policy!r}")
            findings.extend(family(self.catalog).evaluate(control, task, files))
        return findings

    @staticmethod
    def _legacy_findings(control: Control, findings: list[Finding]) -> list[Finding]:
        legacy_id = control.detection.params.get("legacy_policy")
        out = []
        for finding in findings:
            if legacy_id and finding.policy_id != legacy_id:
                continue
            out.append(Finding(
                policy_id=control.id,
                severity=control.severity,
                status=finding.status,
                file=finding.file,
                line=finding.line,
                message=finding.message,
                evidence=finding.evidence,
                remediation_advice=control.remediation or finding.remediation_advice,
            ))
        return out

    def gaps(self) -> list[str]:
        return [control.id for control in self.catalog.controls if not control.implemented]

    def frameworks_for(self, finding: Finding) -> list[str]:
        try:
            return self.catalog.control(finding.policy_id).framework_labels()
        except CatalogError:
            return []
