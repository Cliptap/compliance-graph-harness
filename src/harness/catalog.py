"""Multi-framework control catalog.

The catalog is the source of truth: every control declares the frameworks it
maps to (law, ISO 27001, CWE), the data categories it protects, and the
detection family that evaluates it. Adding a control is a data change; adding a
new source, sink or sanitizer is the only reason to touch the engine.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

POLICY_FAMILIES = frozenset(
    {"sink_exposure", "retention_deletion", "credential_exposure", "code_hygiene", "legacy"})


class CatalogError(ValueError):
    """Raised when a catalog is invalid or references an unknown component."""


@dataclass(frozen=True)
class FrameworkRef:
    framework: str
    ref: str
    title: str | None = None


@dataclass(frozen=True)
class Detection:
    policy: str
    sinks: tuple[str, ...] = ()
    context: dict = field(default_factory=dict)
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Control:
    id: str
    title: str
    severity: str
    frameworks: tuple[FrameworkRef, ...]
    data_categories: tuple[str, ...]
    detection: Detection
    remediation: str
    implemented: bool
    pack_control: str | None = None
    gap_reason: str | None = None

    def framework_labels(self) -> list[str]:
        return [f"{ref.framework} {ref.ref}" for ref in self.frameworks]


@dataclass(frozen=True)
class Catalog:
    pack_id: str
    version: int
    jurisdiction: str
    frameworks: dict[str, dict]
    data_categories: dict[str, dict]
    sinks: dict[str, dict]
    sanitizers: dict[str, tuple[str, ...]]
    tables: dict[str, tuple[str, ...]]
    controls: tuple[Control, ...]

    def synonyms(self, category: str) -> set[str]:
        return {synonym.lower() for synonym in self.data_categories[category].get("synonyms", ())}

    def category_for(self, token: str) -> str | None:
        lowered = token.lower().strip("\"'")
        for name in self.data_categories:
            if lowered in self.synonyms(name):
                return name
        return None

    def is_sanitizer(self, text: str) -> bool:
        """A sanitizer marker only counts when it is applied as a call.

        Substring matching treated a field named ``password_hash`` as sanitized because it
        contains the ``hash`` marker, which hid a real exposure. ``bcrypt.hashpw(...)`` still
        counts because the marker may be followed by a dotted attribute before the call.
        """
        lowered = text.lower()
        return any(
            re.search(rf"{re.escape(marker)}[a-z0-9_.]*\s*\(", lowered)
            for markers in self.sanitizers.values() for marker in markers
        )

    def control(self, control_id: str) -> Control:
        for control in self.controls:
            if control.id == control_id:
                return control
        raise CatalogError(f"unknown control {control_id}")


def _framework(raw: dict) -> FrameworkRef:
    if "framework" not in raw or "ref" not in raw:
        raise CatalogError(f"framework reference needs framework and ref: {raw}")
    return FrameworkRef(raw["framework"], raw["ref"], raw.get("title"))


def _detection(raw: dict) -> Detection:
    policy = raw.get("policy")
    if policy not in POLICY_FAMILIES:
        raise CatalogError(f"unknown detection policy {policy!r}; known: {sorted(POLICY_FAMILIES)}")
    return Detection(
        policy=policy,
        sinks=tuple(raw.get("sinks", ())),
        context=dict(raw.get("context", {})),
        params=dict(raw.get("params", {})),
    )


def _control(raw: dict) -> Control:
    for key in ("id", "title", "severity", "frameworks", "data_categories", "detection", "remediation"):
        if key not in raw:
            raise CatalogError(f"control missing {key}: {raw.get('id', raw)}")
    return Control(
        id=raw["id"],
        title=raw["title"],
        severity=raw["severity"],
        frameworks=tuple(_framework(item) for item in raw["frameworks"]),
        data_categories=tuple(raw["data_categories"]),
        detection=_detection(raw["detection"]),
        remediation=raw["remediation"],
        implemented=bool(raw.get("implemented", True)),
        pack_control=raw.get("pack_control"),
        gap_reason=raw.get("gap_reason"),
    )


def load_catalog(path: Path | str) -> Catalog:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    controls = tuple(_control(raw) for raw in data["controls"])
    catalog = Catalog(
        pack_id=data["pack_id"],
        version=int(data["version"]),
        jurisdiction=data.get("jurisdiction", ""),
        frameworks=dict(data["frameworks"]),
        data_categories=dict(data["data_categories"]),
        sinks=dict(data["sinks"]),
        sanitizers={name: tuple(values) for name, values in data["sanitizers"].items()},
        tables={name: tuple(values) for name, values in data.get("tables", {}).items()},
        controls=controls,
    )
    _validate(catalog)
    return catalog


def _validate(catalog: Catalog) -> None:
    seen: set[str] = set()
    for control in catalog.controls:
        if control.id in seen:
            raise CatalogError(f"duplicate control id {control.id}")
        seen.add(control.id)
        for ref in control.frameworks:
            if ref.framework not in catalog.frameworks:
                raise CatalogError(f"{control.id}: unknown framework {ref.framework}")
        for category in control.data_categories:
            if category not in catalog.data_categories:
                raise CatalogError(f"{control.id}: unknown data category {category}")
        for sink in control.detection.sinks:
            if sink not in catalog.sinks:
                raise CatalogError(f"{control.id}: unknown sink {sink}")
        if not control.implemented and not control.gap_reason:
            raise CatalogError(f"{control.id}: an unimplemented control needs gap_reason")
    for table, categories in catalog.tables.items():
        for category in categories:
            if category not in catalog.data_categories:
                raise CatalogError(f"table {table}: unknown data category {category}")
