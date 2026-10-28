import pathlib
import re
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent
SKILL_PATH = ROOT_DIR / ".agents" / "skills" / "05-backend" / "SKILL.md"
PORTABLE_SKILL_PATH = ROOT_DIR / "harness" / "skills" / "05_backend_implementation.md"


def _extract_frontmatter_and_body(text: str) -> tuple[dict, str]:
    """Extrae el frontmatter YAML y el cuerpo markdown de un documento."""
    parts = text.split("---", 2)
    assert len(parts) >= 3, "El documento no contiene delimitadores YAML '---'"
    fm = yaml.safe_load(parts[1])
    assert isinstance(fm, dict), "El frontmatter no es un diccionario válido"
    return fm, parts[2]


# ==============================================================================
# Linter Determinista de Contrato de Implementación de Backend
# ==============================================================================
def lint_backend_skill_contract(
    spec_or_code: str,
    allowed_paths: list[str] | None = None,
    out_of_scope_items: list[str] | None = None,
) -> list[str]:
    """Analizador determinista de cumplimiento de contrato para backend-implementation."""
    violations = []

    # 1. Delimitación Perimetral y TaskSpec (Invasión de Código Ajeno o Fuera de Scope)
    forbidden_path_prefixes = [
        "src/backend/",
        "src/database/",
        "src/cart/",
        "src/auth/",
        "src/users/",
        "src/payments/",
        "src/frontend/",
    ]
    if allowed_paths:
        for ap in allowed_paths:
            normalized_ap = ap.replace("\\", "/")
            for fp in forbidden_path_prefixes:
                if normalized_ap.startswith(fp) or normalized_ap == fp.rstrip("/"):
                    violations.append(
                        f"Invasión perimetral de TaskSpec: '{ap}' pertenece a una ruta prohibida (forbidden_path: '{fp}')"
                    )

    # Detección de edición o creación en rutas protegidas dentro del texto
    invasion_patterns = [
        r"\b(src/backend/[\w/\.\-]+)",
        r"\b(src/database/[\w/\.\-]+)",
    ]
    # Solo evaluar si no es una cita de forbidden_paths o referencia a código clínico
    for ip in invasion_patterns:
        matches = re.findall(ip, spec_or_code)
        # Si aparecen fuera de comentarios defensivos de forbidden_paths o advertencias
        for m in matches:
            if not any(
                ctx in spec_or_code[max(0, spec_or_code.find(m) - 60) : spec_or_code.find(m) + len(m) + 60]
                for ctx in ["forbidden_paths", "Preserva", "preservar", "clínico", "ajeno", "Invasión"]
            ):
                violations.append(f"Invasión perimetral detectada: modificación de ruta preexistente protegida '{m}'")

    # Separar texto activo para evaluar lógica y contratos (ignorar citas de PRD / OUT OF SCOPE defensivo)
    active_text = spec_or_code

    # 2. Anti-Amnesia: Violación de OUT OF SCOPE heredado
    default_exclusions = [
        "usuario",
        "user",
        "password",
        "credential",
        "credencial",
        "role",
        "jwt",
        "token",
        "auth",
        "login",
        "pago",
        "payment",
        "stripe",
        "tarjeta",
        "credit_card",
        "checkout",
        "recommendation",
        "recomendación",
    ]
    active_exclusions = out_of_scope_items if out_of_scope_items is not None else default_exclusions

    # Patrones explícitos de implementación tóxica
    toxic_code_patterns = [
        (r"\bclass\s+(User|Usuario|Auth|Role|Payment|Pago|Checkout|Cart|Carrito)\w*\(", "Definición de clase o modelo de dominio fuera de alcance"),
        (r"\b(JWT_SECRET|jwt_secret|create_access_token|decode_token)\b", "Uso de tokens o secretos JWT fuera de alcance"),
        (r"@router\.(post|get|put|delete)\(['\"]/(auth|login|users|payments|checkout)", "Endpoint o router para concepto fuera de alcance"),
        (r"\bdef\s+(login|authenticate|register_user|process_payment|checkout)\b", "Función o método para concepto fuera de alcance"),
    ]
    for pattern, reason in toxic_code_patterns:
        m = re.search(pattern, active_text, re.IGNORECASE)
        if m:
            violations.append(f"Violación de Anti-Amnesia: {reason} ('{m.group(0)}')")

    # 3. Coherencia con AD-003: Prohibición estricta de carrito en backend
    cart_backend_patterns = [
        r"\bclass\s+(Cart|CartItem|Carrito|ItemCarrito)\w*\(",
        r"\btable\s*=\s*['\"](carts|cart_items|carritos)['\"]",
        r"__tablename__\s*=\s*['\"](carts|cart_items|carritos)['\"]",
        r"@router\.(get|post|put|delete|patch)\(['\"]/(carts|cart_items|carritos)",
        r"\bdef\s+(add_to_cart|get_cart|create_cart|update_cart_item)\b",
    ]
    for cp in cart_backend_patterns:
        cm = re.search(cp, active_text, re.IGNORECASE)
        if cm:
            violations.append(f"Violación de AD-003: Persistencia, modelo o endpoint de carrito detectado en backend ('{cm.group(0)}')")

    # 4. No-Goldplating: API de solo lectura (únicamente endpoints GET autorizados)
    mutation_backend_patterns = [
        r"@router\.(post|put|patch|delete)\(['\"]/(api/v\d+/)?products",
        r"@router\.(post|put|patch|delete)\(['\"]/?['\"]",
        r"\bdef\s+(create_product|update_product|delete_product|patch_product)\b",
        r"\bdef\s+(crear_producto|actualizar_producto|eliminar_producto)\b",
    ]
    for mp in mutation_backend_patterns:
        mm = re.search(mp, active_text, re.IGNORECASE)
        if mm:
            violations.append(f"Violación de No-Goldplating: Operación de mutación detectada en backend de solo lectura ('{mm.group(0)}')")

    return violations


# ==============================================================================
# TEST 1: Estructura del SKILL.md y Secciones Contractuales Obligatorias
# ==============================================================================
def test_skill_structure_and_contract_sections():
    """Valida que 05-backend/SKILL.md y su versión portable contienen las secciones y metadatos contractuales v2.0."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        assert path.exists(), f"Archivo de skill no existe: {path}"
        content = path.read_text(encoding="utf-8")
        fm, body = _extract_frontmatter_and_body(content)

        # Validación de Frontmatter normativo
        assert fm.get("name") == "backend-implementation"
        assert fm.get("version") == "2.0.0"
        assert fm.get("stage") == 4
        assert "prd-generation" in fm.get("depends_on", [])
        assert "architecture-design" in fm.get("depends_on", [])
        assert "data-modeling" in fm.get("depends_on", [])
        assert "api-design" in fm.get("depends_on", [])
        assert "description" in fm and len(fm["description"]) > 20

        # Secciones estructurales obligatorias (Contrato v2.0)
        required_headers = [
            "Overview",
            "Cuándo Usar",
            "Precondiciones",
            "Entradas",
            "Taxonomía Formal",
            "Regla de Oro Anti-Amnesia",
            "Workflow de Implementación",
            "Señales de Alerta",
            "Contrato de Salida Formal",
            "Verificación del Artefacto",
            "Criterio de Término",
        ]
        for header in required_headers:
            assert header.lower() in body.lower(), f"Sección faltante en {path.name}: {header}"

        # Verificación del estándar metodológico genérico y sección de contexto de referencia
        assert "bounded context" in body.lower() or "contexto acotado" in body.lower(), (
            f"Falta estándar de delimitación de bounded context en {path.name}"
        )
        assert "upstream" in body.lower(), f"Falta referencia a trazabilidad upstream en {path.name}"
        assert "Reference Context: Demo Implementation" in body, (
            f"Falta sección de contexto de referencia de demo en {path.name}"
        )


# ==============================================================================
# TEST 2: Validación del Esquema de TaskSpec y Delimitación Perimetral
# ==============================================================================
def test_backend_skill_contract_schema_and_taskspec_rules():
    """Valida que la skill define formalmente TaskSpec con allowed_paths, forbidden_paths y prevención de orphan changes."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        assert "TaskSpec(" in content
        assert "allowed_paths" in content
        assert "forbidden_paths" in content
        assert "orphan_change" in content or "orphan changes" in content.lower()

        # Estándar metodológico genérico
        assert "<bounded_context>" in content or "contexto acotado" in content.lower()

        # Coexistencia de la sección de contexto de referencia de la demo
        assert "Reference Context: Demo Implementation" in content
        assert "src/catalog/**" in content
        assert "src/shared/**" in content
        assert "src/backend/**" in content  # Prohibición de tocar código clínico
        assert "src/database/**" in content  # Prohibición de tocar esquemas clínicos


# ==============================================================================
# TEST 3: Topología del Código y Aislamiento de Base de Datos en Pruebas
# ==============================================================================
def test_backend_skill_codebase_layout_compliance():
    """Valida que la skill prescribe la topología canónica (src/catalog/, src/shared/) y SQLite en memoria para tests."""
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        content = path.read_text(encoding="utf-8")
        # Topología modular en src/
        assert "src/catalog/models.py" in content
        assert "src/catalog/schemas.py" in content
        assert "src/catalog/repository.py" in content
        assert "src/catalog/service.py" in content
        assert "src/catalog/router.py" in content
        assert "src/catalog/seed.py" in content
        assert "src/shared/database.py" in content
        assert "src/shared/config.py" in content
        assert "src/main.py" in content

        # Aislamiento de base de datos en tests
        assert "sqlite:///:memory:" in content
        assert "test_catalog_backend.py" in content


# ==============================================================================
# TEST 4: Regla de Oro Anti-Amnesia y Detección de Violaciones de Scope
# ==============================================================================
def test_backend_skill_anti_amnesia_rules():
    """Verifica que el linter rechaza código backend que reintroduce conceptos OUT OF SCOPE."""
    toxic_backend_code = """
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class UserModel(BaseModel):
    id: int
    username: str
    password_hash: str

@router.post("/auth/login")
def login(username: str, password: str):
    token = create_access_token(username)
    return {"token": token}
"""
    violations = lint_backend_skill_contract(toxic_backend_code)
    assert len(violations) >= 2
    assert any("UserModel" in v or "Auth" in v for v in violations)
    assert any("login" in v or "token" in v for v in violations)

    # Verificar que las directivas anti-amnesia constan en ambas skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "Anti-Amnesia" in text
        assert "OUT OF SCOPE" in text
        assert "Amnesia de Scope" in text


# ==============================================================================
# TEST 5: Coherencia con AD-003 (Carrito en Cliente, Cero Persistencia en Servidor)
# ==============================================================================
def test_backend_skill_coherence_with_ad003_cart_in_client():
    """Verifica que el linter rechaza modelos, tablas o routers de carrito en backend."""
    toxic_cart_code = """
from sqlalchemy import Column, Integer, String
from src.shared.database import Base

class CartModel(Base):
    __tablename__ = "carts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)

def add_to_cart(cart_id: int, product_id: int):
    pass
"""
    violations = lint_backend_skill_contract(toxic_cart_code)
    assert len(violations) >= 1
    assert any("AD-003" in v or "carrito" in v.lower() for v in violations)

    # Verificar que el respeto a AD-003 consta en ambas skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "AD-003" in text
        assert "localStorage" in text or "Web Storage" in text


# ==============================================================================
# TEST 6: Detección y Rechazo de Goldplating (Endpoints de Mutación no Respaldados)
# ==============================================================================
def test_backend_skill_no_goldplating_read_only_backend():
    """Verifica que el linter rechaza endpoints o servicios de mutación (POST/PUT/PATCH/DELETE) para productos."""
    toxic_mutation_code = """
from fastapi import APIRouter
from src.catalog.schemas import ProductResponse

router = APIRouter(prefix="/products")

@router.post("/")
def create_product(product_data: dict):
    return {"message": "created"}

@router.delete("/{id}")
def delete_product(id: int):
    return {"message": "deleted"}
"""
    violations = lint_backend_skill_contract(toxic_mutation_code)
    assert len(violations) >= 1
    assert any("No-Goldplating" in v or "mutación" in v.lower() for v in violations)

    # Verificar que la invariante de solo lectura consta en ambas skills
    for path in [SKILL_PATH, PORTABLE_SKILL_PATH]:
        text = path.read_text(encoding="utf-8")
        assert "solo lectura" in text.lower() or "read-only" in text.lower()


# ==============================================================================
# TEST 7: Especificación Conforme Pasa el Linter Determinista
# ==============================================================================
def test_conforming_backend_spec_passes_linter():
    """Verifica que una especificación y código conforme al contrato pasa con 0 violaciones."""
    clean_backend_code = """
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.catalog import service, schemas
from src.shared.database import get_db

router = APIRouter(prefix="/products", tags=["catalog"])

@router.get("", response_model=schemas.ProductListResponse)
def list_products(q: str | None = None, db: Session = Depends(get_db)):
    items, total = service.get_products(db=db, search_term=q)
    return schemas.ProductListResponse(items=items, total=total)

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    product = service.get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product
"""
    allowed = ["src/catalog/router.py", "src/catalog/service.py", "src/shared/database.py"]
    violations = lint_backend_skill_contract(clean_backend_code, allowed_paths=allowed)
    assert len(violations) == 0, f"Violaciones inesperadas: {violations}"


# ==============================================================================
# TEST 8: Validación de Código Backend si ya está Implementado (Condicional/Skip)
# ==============================================================================
def test_backend_code_compliance_if_implemented():
    """Valida que si src/catalog/ existe en disco, cumpla rigurosamente con los contratos."""
    catalog_dir = ROOT_DIR / "src" / "catalog"
    if not catalog_dir.exists():
        pytest.skip("src/catalog/ aún no implementado (esperado en Etapa C)")

    # Archivos requeridos
    required_files = [
        "models.py",
        "schemas.py",
        "repository.py",
        "service.py",
        "router.py",
        "seed.py",
    ]
    for rf in required_files:
        target = catalog_dir / rf
        assert target.exists(), f"Archivo faltante en src/catalog/: {rf}"

    # Verificación de que no se reintroducen mutaciones ni carritos en los archivos implementados
    router_code = (catalog_dir / "router.py").read_text(encoding="utf-8")
    violations = lint_backend_skill_contract(router_code)
    assert len(violations) == 0, f"Violaciones en router.py: {violations}"


# ==============================================================================
# TEST 9: Verificación Mecánica de Perímetro Físico (Scope Policy Enforcement)
# ==============================================================================
def test_backend_physical_scope_enforcement():
    """Inspecciona los archivos físicos en src/ y verifica deterministamente el respeto al TaskSpec.

    Verifica que el 100% de los archivos creados o modificados pertenezcan a allowed_paths,
    utilizando el evaluador formal ScopePolicy del arnés, y asegura la ausencia de archivos
    o modificaciones huérfanas en rutas prohibidas o protegidas (src/backend/, src/database/,
    src/cart/, src/auth/, src/users/, src/payments/).
    """
    import subprocess
    from src.harness.contracts import TaskSpec
    from src.harness.policy_engine import ScopePolicy

    task_spec = TaskSpec(
        task_id="TS-BACKEND-001",
        goal="Implementar el backend ligero de catálogo de productos y búsqueda en SQLite/FastAPI",
        category="feature",
        allowed_paths=[
            "src/catalog/**",
            "src/shared/**",
            "src/main.py",
            "tests/catalog/**",
        ],
        forbidden_paths=[
            "src/backend/**",
            "src/database/**",
            "src/frontend/**",
            "src/cart/**",
            "src/auth/**",
            "src/users/**",
            "src/payments/**",
        ],
    )

    # 1. Inspección de archivos creados o modificados en git
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uall"],
        cwd=str(ROOT_DIR),
        capture_output=True,
        text=True,
        check=True,
    )

    changed_src_files: dict[str, str] = {}
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        status = line[:2].strip()
        filepath = line[3:].strip().replace("\\", "/")
        # Inspeccionar archivos de src/ pertenecientes a la tarea de backend (excluyendo frontend de TS-FRONTEND-001)
        if filepath.startswith("src/") and not filepath.startswith("src/frontend/"):
            changed_src_files[filepath] = status

    policy = ScopePolicy()

    # Si hay archivos modificados/creados en src/, evaluar formalmente con ScopePolicy
    if changed_src_files:
        findings = policy.evaluate(task_spec, changed_src_files)

        # Validar que no existan violaciones de ScopePolicy
        violations = [
            f"{f.policy_id} en {f.file}: {f.message} ({f.evidence})"
            for f in findings
            if f.status == "VIOLATION"
        ]
        assert len(violations) == 0, (
            f"Fallo de ScopePolicy Enforcement en backend. Se detectaron archivos huérfanos o fuera de perímetro:\n"
            + "\n".join(violations)
        )

        # Aserción explícita de pertenencia estricta a allowed_paths
        allowed_prefixes = ("src/catalog/", "src/shared/", "src/main.py")
        for fpath in changed_src_files.keys():
            assert any(fpath == p or fpath.startswith(p) for p in allowed_prefixes), (
                f"Archivo huérfano detectado fuera de allowed_paths: '{fpath}'. "
                f"Las rutas autorizadas son: {task_spec.allowed_paths}"
            )

    # 2. Verificación estricta de ausencia de directorios prohibidos en disco
    forbidden_directories = [
        ROOT_DIR / "src" / "cart",
        ROOT_DIR / "src" / "auth",
        ROOT_DIR / "src" / "users",
        ROOT_DIR / "src" / "payments",
        ROOT_DIR / "src" / "carritos",
    ]
    for fdir in forbidden_directories:
        assert not fdir.exists(), (
            f"Directorio prohibido fuera de alcance detectado en disco: '{fdir.relative_to(ROOT_DIR)}'. "
            f"Viola la delimitación perimetral de TaskSpec y la Regla Anti-Amnesia."
        )

    # 3. Verificación de que no existen modificaciones no autorizadas sobre código preexistente protegido
    protected_prefixes = ("src/backend/", "src/database/")
    for fpath in changed_src_files.keys():
        assert not any(fpath.startswith(p) for p in protected_prefixes), (
            f"Invasión perimetral de código preexistente: Se detectaron cambios en '{fpath}'. "
            f"Los módulos clínicos y bases de datos preexistentes son de solo lectura para este arnés."
        )

    # 4. Verificación de comportamiento reactivo del evaluador ante infracciones hipotéticas
    hypothetical_violations = policy.evaluate(
        task_spec,
        {"src/cart/cart_service.py": "??", "src/backend/leak.py": "M"},
    )
    assert len(hypothetical_violations) >= 2, "ScopePolicy debe reaccionar ante violaciones de perimeter"

