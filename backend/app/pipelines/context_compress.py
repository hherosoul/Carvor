from app.core.constants import SKILL_MAP
from app.services.skill_service import load_skill
from app.gateway.llm_gateway import gateway
from app.core.config import load_config


async def compress_context(
    messages: list[dict],
    scenario: str,
    config=None,
) -> list[dict]:
    if config is None:
        config = load_config()

    system_messages = [m for m in messages if m["role"] == "system"]
    non_system = [m for m in messages if m["role"] != "system"]

    skill_name = SKILL_MAP.get(scenario)
    domain_rules = ""
    if skill_name:
        skill_content = load_skill(skill_name)
        if "领域规则" in skill_content:
            start = skill_content.index("领域规则")
            domain_rules = skill_content[start:start + 2000]

    compressible = "\n".join(m["content"] for m in non_system)

    llm_result = await gateway.call_async("context_compress", {
        "compressible_content": compressible,
        "domain_rules": domain_rules,
    })

    compressed = llm_result.get("compressed_context", compressible)

    return system_messages + [{"role": "user", "content": compressed}]
