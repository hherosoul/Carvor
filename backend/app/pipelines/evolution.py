from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.database import EvolutionLog
from app.gateway.llm_gateway import gateway
from app.services.skill_service import (
    load_skill, save_skill, load_observing, append_observing,
    load_candidate, save_candidate,
)


async def observe_evolution(
    content: str,
    source: str,
    session: AsyncSession,
) -> dict:
    llm_result = await gateway.call_async("evolution_observe", {
        "content": content,
        "source": source,
    })

    observation = llm_result.get("observation", "")
    dimension = llm_result.get("dimension", "")

    skill_name = _dimension_to_skill(dimension)
    if skill_name:
        append_observing(skill_name, observation)

    log = EvolutionLog(
        content=observation,
        source=source,
        dimension=dimension,
        level=1,
        skill_name=skill_name or "",
    )
    session.add(log)
    await session.commit()

    return {"observation": observation, "dimension": dimension, "skill_name": skill_name}


async def check_pattern(skill_name: str, session: AsyncSession) -> dict:
    observing_content = load_observing(skill_name)
    if not observing_content.strip():
        return {"is_repeated": False}

    llm_result = await gateway.call_async("evolution_pattern", {
        "observing_content": observing_content,
    })

    is_repeated = llm_result.get("is_repeated", False)
    if is_repeated:
        pattern = llm_result.get("pattern", "")
        merged = llm_result.get("merged_observation", "")

        existing = load_candidate(skill_name)
        save_candidate(skill_name, existing + "\n" + merged if existing else merged)

        log = EvolutionLog(
            content=merged,
            source="pattern_detection",
            dimension=pattern,
            level=2,
            skill_name=skill_name,
        )
        session.add(log)
        await session.commit()

    return llm_result


async def confirm_evolution(
    evolution_log_id: int,
    session: AsyncSession,
) -> str:
    result = await session.execute(
        select(EvolutionLog).where(EvolutionLog.id == evolution_log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise ValueError(f"Evolution log {evolution_log_id} not found")

    current_skill = load_skill(log.skill_name)
    new_knowledge = log.content

    llm_result = await gateway.call_async("skill_compress", {
        "current_skill": current_skill,
        "new_knowledge": new_knowledge,
    })

    compressed = llm_result.get("compressed", "")
    save_skill(log.skill_name, compressed)

    log.level = 3
    session.add(log)
    await session.commit()

    return compressed


async def rollback_evolution(
    evolution_log_id: int,
    session: AsyncSession,
) -> None:
    result = await session.execute(
        select(EvolutionLog).where(EvolutionLog.id == evolution_log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        raise ValueError(f"Evolution log {evolution_log_id} not found")

    log.level = 2
    session.add(log)
    await session.commit()


def _dimension_to_skill(dimension: str) -> str | None:
    mapping = {
        "算法模型知识": "代码提示词生成",
        "提示词文档模板优化": "代码提示词生成",
        "论文质量评价": "文献跟踪",
        "个性化风格": "idea锤炼",
        "实验策略优化": "代码提示词生成",
        "文献偏好建模": "文献跟踪",
        "写作风格记忆": "论文润色",
    }
    return mapping.get(dimension)
