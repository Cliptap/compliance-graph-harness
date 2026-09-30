import pathlib
import pytest
import yaml

pytestmark = [pytest.mark.harness, pytest.mark.governance, pytest.mark.fast]

EXPECTED_SKILLS = [
    "01-prd",
    "02-architecture",
    "03-data-modeling",
    "04-api-design",
    "05-backend",
    "06-frontend",
    "07-auth",
    "08-testing",
    "09-cicd",
    "10-deployment",
    "11-observability",
    "12-documentation",
]

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent.parent


def test_all_12_skills_exist_in_agents_directory():
    """Verifica que las 12 etapas del pipeline de desarrollo existen físicamente en .agents/skills/."""
    skills_base = ROOT_DIR / ".agents" / "skills"
    assert skills_base.exists()
    
    for skill_name in EXPECTED_SKILLS:
        skill_dir = skills_base / skill_name
        assert skill_dir.is_dir(), f"Directorio de skill faltante: {skill_name}"
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.is_file(), f"SKILL.md no encontrado en: {skill_name}"


def test_skills_frontmatter_schema_and_yaml_validity():
    """Valida que todas las skills contienen frontmatter YAML sintácticamente válido y con campos obligatorios."""
    skills_base = ROOT_DIR / ".agents" / "skills"
    
    for skill_name in EXPECTED_SKILLS:
        skill_md = skills_base / skill_name / "SKILL.md"
        content = skill_md.read_text(encoding="utf-8")
        
        parts = content.split("---", 2)
        assert len(parts) >= 3, f"{skill_name}/SKILL.md no contiene delimitadores de frontmatter '---'"
        
        try:
            fm = yaml.safe_load(parts[1])
        except Exception as e:
            pytest.fail(f"Error parseando YAML en {skill_name}: {e}")
            
        assert isinstance(fm, dict), f"Frontmatter de {skill_name} no es un diccionario"
        assert "name" in fm and fm["name"], f"{skill_name} no tiene campo 'name'"
        assert "description" in fm and fm["description"], f"{skill_name} no tiene campo 'description'"
        assert "stage" in fm, f"{skill_name} no especifica campo 'stage'"
        assert "depends_on" in fm, f"{skill_name} no especifica dependencias"


def test_portable_skills_package_synchronized():
    """Verifica que el paquete portable harness/skills/ contiene las 12 especificaciones correspondientes."""
    portable_base = ROOT_DIR / "harness" / "skills"
    assert portable_base.exists()
    
    portable_files = list(portable_base.glob("*.md"))
    assert len(portable_files) >= 12, "harness/skills no contiene los 12 archivos de skill portables"
    
    for p_file in portable_files:
        content = p_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm = yaml.safe_load(parts[1])
            assert "name" in fm
            assert "description" in fm
