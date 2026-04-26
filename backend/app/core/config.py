import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
SKILLS_DIR = BASE_DIR / "skills"
CONFIG_DIR = BASE_DIR / "config"
DB_PATH = DATA_DIR / "carvor.db"
LLM_CONFIG_PATH = CONFIG_DIR / "llm_config.json"

CURRENT_CONFIG_VERSION = 2


class LLMConfig(BaseModel):
    base_url: str = "https://api.moonshot.cn/v1"
    api_key: str = ""
    model: str = "kimi-k2.6"
    max_context_tokens: int = 131072
    extra_body: Optional[dict] = {"thinking": {"type": "disabled"}}


class FeaturesConfig(BaseModel):
    web_search_tool_name: str = "$web_search"
    daily_search_time: str = "08:00"
    compress_threshold: float = 0.8


class AppConfig(BaseModel):
    config_version: int = CURRENT_CONFIG_VERSION
    llm: LLMConfig = LLMConfig()
    features: FeaturesConfig = FeaturesConfig()


def load_config() -> AppConfig:
    if LLM_CONFIG_PATH.exists():
        with open(LLM_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        version = raw.get("config_version", 0)
        if version < CURRENT_CONFIG_VERSION:
            raw = migrate_config(raw, version)
        return AppConfig(**raw)
    return AppConfig()


def save_config(config: AppConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LLM_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config.model_dump(), f, indent=2, ensure_ascii=False)


def migrate_config(raw: dict, from_version: int) -> dict:
    if from_version < 1:
        raw.setdefault("config_version", 1)
        raw.setdefault("llm", {})
        raw.setdefault("features", {})
    if from_version < 2:
        raw["config_version"] = 2
        llm = raw.setdefault("llm", {})
        llm.setdefault("base_url", "https://api.moonshot.cn/v1")
        llm.setdefault("model", "kimi-k2.6")
        llm.setdefault("extra_body", {"thinking": {"type": "disabled"}})
    raw["config_version"] = CURRENT_CONFIG_VERSION
    return raw
