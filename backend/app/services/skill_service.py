from pathlib import Path
from app.core.config import SKILLS_DIR


def load_skill(skill_name: str) -> str:
    path = SKILLS_DIR / skill_name / "SKILL.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def save_skill(skill_name: str, content: str) -> None:
    path = SKILLS_DIR / skill_name / "SKILL.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_observing(skill_name: str) -> str:
    path = SKILLS_DIR / skill_name / "observing.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def append_observing(skill_name: str, content: str) -> None:
    path = SKILLS_DIR / skill_name / "observing.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(content + "\n")


def load_candidate(skill_name: str) -> str:
    path = SKILLS_DIR / skill_name / "candidate.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def save_candidate(skill_name: str, content: str) -> None:
    path = SKILLS_DIR / skill_name / "candidate.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def list_skills() -> list[dict]:
    result = []
    if not SKILLS_DIR.exists():
        return result
    for d in SKILLS_DIR.iterdir():
        if d.is_dir():
            skill_file = d / "SKILL.md"
            result.append({
                "name": d.name,
                "content": skill_file.read_text(encoding="utf-8") if skill_file.exists() else "",
            })
    return result
