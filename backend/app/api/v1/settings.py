import json
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import load_config, save_config, AppConfig
from app.core.database import get_session
from app.models.database import LLMProviderConfig
from app.services.skill_service import list_skills, load_skill, save_skill

logger = logging.getLogger("carvor.settings")
router = APIRouter(tags=["settings"])


class ProviderCreate(BaseModel):
    name: str
    base_url: str
    api_key: str
    model: str
    max_context_tokens: int = 131072
    extra_body: Optional[dict] = None


class ProviderUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None
    max_context_tokens: Optional[int] = None
    extra_body: Optional[dict] = None


@router.get("/api/providers")
async def list_providers(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(LLMProviderConfig).order_by(LLMProviderConfig.created_at))
    providers = result.scalars().all()
    return [{
        "id": p.id,
        "name": p.name,
        "base_url": p.base_url,
        "api_key": "***" if p.api_key else "",
        "model": p.model,
        "max_context_tokens": p.max_context_tokens,
        "extra_body": json.loads(p.extra_body) if p.extra_body else None,
        "is_active": p.is_active,
        "created_at": p.created_at,
    } for p in providers]


@router.post("/api/providers")
async def create_provider(data: ProviderCreate, session: AsyncSession = Depends(get_session)):
    provider = LLMProviderConfig(
        name=data.name,
        base_url=data.base_url,
        api_key=data.api_key,
        model=data.model,
        max_context_tokens=data.max_context_tokens,
        extra_body=json.dumps(data.extra_body, ensure_ascii=False) if data.extra_body else None,
        is_active=0,
    )
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return {"id": provider.id, "name": provider.name}


@router.put("/api/providers/{provider_id}")
async def update_provider(provider_id: int, data: ProviderUpdate, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(LLMProviderConfig).where(LLMProviderConfig.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Provider not found")
    if data.name is not None:
        provider.name = data.name
    if data.base_url is not None:
        provider.base_url = data.base_url
    if data.api_key is not None and data.api_key != "" and data.api_key != "***":
        provider.api_key = data.api_key
    if data.model is not None:
        provider.model = data.model
    if data.max_context_tokens is not None:
        provider.max_context_tokens = data.max_context_tokens
    if data.extra_body is not None:
        provider.extra_body = json.dumps(data.extra_body, ensure_ascii=False)
    session.add(provider)
    await session.commit()
    return {"ok": True}


@router.delete("/api/providers/{provider_id}")
async def delete_provider(provider_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(LLMProviderConfig).where(LLMProviderConfig.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Provider not found")
    if provider.is_active:
        raise HTTPException(400, "不能删除当前启用的配置")
    await session.delete(provider)
    await session.commit()
    return {"ok": True}


@router.post("/api/providers/{provider_id}/activate")
async def activate_provider(provider_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(LLMProviderConfig).where(LLMProviderConfig.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Provider not found")

    all_result = await session.execute(select(LLMProviderConfig))
    for p in all_result.scalars().all():
        p.is_active = 1 if p.id == provider_id else 0
        session.add(p)

    config = load_config()
    config.llm.base_url = provider.base_url
    config.llm.api_key = provider.api_key
    config.llm.model = provider.model
    config.llm.max_context_tokens = provider.max_context_tokens
    if provider.extra_body:
        config.llm.extra_body = json.loads(provider.extra_body)
    save_config(config)

    from app.gateway.llm_gateway import gateway
    gateway._config = config
    gateway._client = None

    await session.commit()
    return {"ok": True}


@router.post("/api/providers/{provider_id}/test")
async def test_provider(provider_id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(LLMProviderConfig).where(LLMProviderConfig.id == provider_id))
    provider = result.scalar_one_or_none()
    if not provider:
        raise HTTPException(404, "Provider not found")

    api_key = provider.api_key
    base_url = provider.base_url
    model = provider.model

    logger.info(f"Testing provider '{provider.name}': base_url={base_url}, model={model}")

    if not api_key:
        return {"ok": False, "error": "API Key 未配置"}

    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        kwargs: dict = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 5,
        }
        if provider.extra_body:
            kwargs["extra_body"] = json.loads(provider.extra_body)
        response = await client.chat.completions.create(**kwargs)
        logger.info(f"Provider '{provider.name}' test successful")
        return {"ok": True, "response": response.choices[0].message.content}
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        logger.error(f"Provider '{provider.name}' test failed: [{error_type}] {error_msg}")

        if "401" in error_msg or "incorrect_api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            friendly_msg = f"认证失败（401）：API Key 无效或不匹配。请检查 Key 是否正确，以及是否与 base_url（{base_url}）对应的平台一致。"
        elif "404" in error_msg or "model_not_found" in error_msg.lower():
            friendly_msg = f"模型不存在（404）：模型 '{model}' 在 {base_url} 上不存在，请检查模型名称。"
        elif "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            friendly_msg = f"连接失败：无法连接到 {base_url}，请检查网络和 base_url 是否正确。"
        else:
            friendly_msg = f"请求失败（{error_type}）：{error_msg}"

        return {"ok": False, "error": friendly_msg}


@router.get("/api/config/llm")
async def get_llm_config():
    config = load_config()
    return {
        "config_version": config.config_version,
        "llm": {
            "base_url": config.llm.base_url,
            "api_key": "***" if config.llm.api_key else "",
            "model": config.llm.model,
            "max_context_tokens": config.llm.max_context_tokens,
            "extra_body": config.llm.extra_body,
        },
        "features": config.features.model_dump(),
    }


class FeaturesConfigUpdate(BaseModel):
    web_search_tool_name: str | None = None
    daily_search_time: str | None = None
    compress_threshold: float | None = None


class ConfigUpdateRequest(BaseModel):
    features: FeaturesConfigUpdate | None = None


@router.put("/api/config/llm")
async def update_llm_config(data: ConfigUpdateRequest):
    config = load_config()
    if data.features:
        if data.features.web_search_tool_name is not None:
            config.features.web_search_tool_name = data.features.web_search_tool_name
        if data.features.daily_search_time is not None:
            config.features.daily_search_time = data.features.daily_search_time
        if data.features.compress_threshold is not None:
            config.features.compress_threshold = data.features.compress_threshold
    save_config(config)
    return {"ok": True}


@router.get("/api/skills")
async def list_all_skills():
    return list_skills()


@router.get("/api/skills/{name}")
async def get_skill(name: str):
    content = load_skill(name)
    return {"name": name, "content": content}


@router.put("/api/skills/{name}")
async def update_skill(name: str, content: str = ""):
    save_skill(name, content)
    return {"ok": True}
