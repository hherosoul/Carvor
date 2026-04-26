import json
import asyncio
import logging
from typing import AsyncGenerator, Optional

import httpx
from openai import AsyncOpenAI

from app.core.config import load_config, AppConfig
from app.core.constants import SYSTEM_CONSTRAINT, SCENARIO_CONSTRAINTS, SCENARIO_TASKS, SKILL_MAP
from app.gateway.registry import ScenarioRegistry
from app.services.skill_service import load_skill

FORMULA_BASE = "https://api.moonshot.cn/v1/formulas/moonshot/web-search:latest"


class LLMGateway:
    def __init__(self, config: Optional[AppConfig] = None):
        self._config = config or load_config()
        self._client: Optional[AsyncOpenAI] = None
        self._token_callback = None
        self._logger = logging.getLogger("carvor.llm_gateway")

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                base_url=self._config.llm.base_url,
                api_key=self._config.llm.api_key,
            )
        return self._client

    def set_token_callback(self, callback):
        self._token_callback = callback

    def _build_system_prompt(self, scenario: str) -> str:
        parts = [SYSTEM_CONSTRAINT]
        scenario_constraint = SCENARIO_CONSTRAINTS.get(scenario)
        if scenario_constraint:
            parts.append(scenario_constraint)
        return "\n".join(parts)

    def _build_user_message(self, scenario: str, input_data: dict, output_schema: dict) -> str:
        parts = []
        scenario_task = SCENARIO_TASKS.get(scenario)
        if scenario_task:
            parts.append(f"任务要求：{scenario_task}")
        skill_name = SKILL_MAP.get(scenario)
        if skill_name:
            skill_content = load_skill(skill_name)
            if skill_content:
                parts.append(f"以下是你在{scenario}中应遵循的个性化知识和规则：\n{skill_content}")

        parts.append(f"业务输入数据：\n{json.dumps(input_data, ensure_ascii=False, indent=2)}")

        if output_schema:
            parts.append(f"请严格按照以下JSON Schema返回结果：\n{json.dumps(output_schema, ensure_ascii=False, indent=2)}")

        return "\n\n".join(parts)

    def _estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    def _build_web_search_tool(self) -> list[dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "web_search",
                    "description": "用于信息检索的网络搜索",
                    "parameters": {
                        "type": "object",
                        "required": ["query"],
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "要搜索的内容",
                            },
                            "classes": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "enum": ["all", "academic", "social", "library", "finance", "code", "ecommerce", "medical"],
                                },
                                "description": "要关注的搜索领域。如果未指定，则默认为 'all'。",
                            },
                        },
                    },
                },
            }
        ]

    async def _execute_fiber(self, tool_call_name: str, tool_call_arguments: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{FORMULA_BASE}/fibers",
                    headers={
                        "Authorization": f"Bearer {self._config.llm.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "name": tool_call_name,
                        "arguments": tool_call_arguments,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return data.get("context", {}).get("encrypted_output", "") or json.dumps(data, ensure_ascii=False)
        except Exception as e:
            self._logger.warning(f"Fiber execution failed for {tool_call_name}: {e}")
            return json.dumps({"error": str(e)})

    async def _handle_tool_calls(self, tool_calls: list) -> list[dict]:
        tool_messages = []
        for tool_call in tool_calls:
            tool_call_name = tool_call.function.name
            tool_call_arguments = tool_call.function.arguments
            fiber_result = await self._execute_fiber(tool_call_name, tool_call_arguments)
            tool_messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_call_name,
                "content": fiber_result,
            })
        return tool_messages

    async def _check_and_compress(self, messages: list[dict], scenario: str) -> list[dict]:
        total = sum(self._estimate_tokens(m.get("content", "") or "") for m in messages)
        threshold = int(self._config.llm.max_context_tokens * self._config.features.compress_threshold)
        if total < threshold:
            return messages
        from app.pipelines.context_compress import compress_context
        return await compress_context(messages, scenario, self._config)

    async def call_async(self, scenario: str, input_data: dict, context: Optional[list[dict]] = None, progress_callback=None) -> dict:
        definition = ScenarioRegistry.get(scenario)
        if not definition:
            raise ValueError(f"Unknown scenario: {scenario}")

        ok, msg = ScenarioRegistry.validate(scenario)
        if not ok:
            raise ValueError(msg)

        self._logger.info(f"[call_async] scenario={scenario}, web_search={definition.requires_web_search}")
        system_prompt = self._build_system_prompt(scenario)
        output_schema = definition.output_schema
        user_msg = self._build_user_message(scenario, input_data, output_schema)

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": user_msg})

        messages = await self._check_and_compress(messages, scenario)

        tools = None
        if definition.requires_web_search:
            tools = self._build_web_search_tool()

        last_error = None
        for attempt in range(3):
            try:
                kwargs: dict = {
                    "model": self._config.llm.model,
                    "messages": messages,
                    "max_tokens": 32768,
                }
                if tools:
                    kwargs["tools"] = tools
                if self._config.llm.extra_body:
                    kwargs["extra_body"] = self._config.llm.extra_body

                finish_reason = None
                tool_round = 0
                while finish_reason is None or finish_reason == "tool_calls":
                    tool_round += 1
                    if tool_round > 5:
                        self._logger.warning(f"Tool call loop exceeded 5 rounds for scenario '{scenario}', forcing final response")
                        break
                    response = await self.client.chat.completions.create(**kwargs)
                    choice = response.choices[0]
                    finish_reason = choice.finish_reason
                    self._logger.info(f"[call_async] scenario={scenario}, round={tool_round}, finish_reason={finish_reason}")

                    if finish_reason == "tool_calls" and choice.message.tool_calls:
                        msg_dict = {
                            "role": "assistant",
                            "content": choice.message.content or "",
                            "tool_calls": [
                                {
                                    "id": tc.id,
                                    "type": "function",
                                    "function": {
                                        "name": tc.function.name,
                                        "arguments": tc.function.arguments,
                                    },
                                }
                                for tc in choice.message.tool_calls
                            ],
                        }
                        messages.append(msg_dict)
                        if progress_callback:
                            try:
                                await progress_callback(f"searching", tool_round, f"正在搜索第 {tool_round} 轮...")
                            except Exception:
                                pass
                        tool_messages = await self._handle_tool_calls(choice.message.tool_calls)
                        messages.extend(tool_messages)
                        self._logger.info(f"[call_async] scenario={scenario}, tool_calls processed, continuing")
                        kwargs["messages"] = messages
                    else:
                        break

                if finish_reason == "tool_calls":
                    final_kwargs = {
                        "model": self._config.llm.model,
                        "messages": messages,
                        "max_tokens": 32768,
                    }
                    if self._config.llm.extra_body:
                        final_kwargs["extra_body"] = self._config.llm.extra_body
                    response = await self.client.chat.completions.create(**final_kwargs)
                    choice = response.choices[0]
                    self._logger.info(f"[call_async] scenario={scenario}, forced final response, finish_reason={choice.finish_reason}")

                content = choice.message.content or ""
                usage = response.usage

                if usage and self._token_callback:
                    await self._token_callback(scenario, self._config.llm.model, usage.prompt_tokens, usage.completion_tokens)

                self._logger.info(f"[call_async] scenario={scenario} completed, tokens={usage.prompt_tokens if usage else '?'}/{usage.completion_tokens if usage else '?'}")
                self._logger.info(f"[call_async] scenario={scenario}, response preview: {content[:300]}")

                if output_schema:
                    try:
                        json_str = content
                        if "```json" in json_str:
                            json_str = json_str.split("```json")[1].split("```")[0]
                        elif "```" in json_str:
                            json_str = json_str.split("```")[1].split("```")[0]
                        return json.loads(json_str.strip())
                    except (json.JSONDecodeError, IndexError):
                        return {"raw": content}
                return {"raw": content}

            except Exception as e:
                last_error = e
                if attempt < 2:
                    await asyncio.sleep(2 ** attempt)

        raise RuntimeError(f"LLM call failed after 3 retries for scenario '{scenario}': {last_error}")

    async def call_stream(self, scenario: str, input_data: dict, context: Optional[list[dict]] = None) -> AsyncGenerator[str, None]:
        definition = ScenarioRegistry.get(scenario)
        if not definition:
            raise ValueError(f"Unknown scenario: {scenario}")

        ok, msg = ScenarioRegistry.validate(scenario)
        if not ok:
            raise ValueError(msg)

        self._logger.info(f"[call_stream] scenario={scenario}, web_search={definition.requires_web_search}")

        system_prompt = self._build_system_prompt(scenario)
        user_msg = self._build_user_message(scenario, input_data, {})

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.extend(context)
        messages.append({"role": "user", "content": user_msg})

        messages = await self._check_and_compress(messages, scenario)

        tools = None
        if definition.requires_web_search:
            tools = self._build_web_search_tool()

        if definition.requires_web_search and tools:
            async for chunk in self._call_stream_with_tools(scenario, messages, tools, kwargs):
                yield chunk
            return

        kwargs: dict = {
            "model": self._config.llm.model,
            "messages": messages,
            "max_tokens": 32768,
            "stream": True,
        }
        if self._config.llm.extra_body:
            kwargs["extra_body"] = self._config.llm.extra_body

        try:
            stream = await self.client.chat.completions.create(**kwargs)
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            yield f"\n[Error: {str(e)}]"

    async def _call_stream_with_tools(self, scenario: str, messages: list[dict], tools: list[dict], base_kwargs: dict) -> AsyncGenerator[str, None]:
        kwargs: dict = {
            "model": self._config.llm.model,
            "messages": messages,
            "max_tokens": 32768,
            "tools": tools,
        }
        if self._config.llm.extra_body:
            kwargs["extra_body"] = self._config.llm.extra_body

        finish_reason = None
        tool_round = 0
        while finish_reason is None or finish_reason == "tool_calls":
            tool_round += 1
            if tool_round > 5:
                self._logger.warning(f"Tool call loop exceeded 5 rounds in stream for scenario '{scenario}', forcing final response")
                break
            response = await self.client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            finish_reason = choice.finish_reason

            if finish_reason == "tool_calls" and choice.message.tool_calls:
                msg_dict = {
                    "role": "assistant",
                    "content": choice.message.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            },
                        }
                        for tc in choice.message.tool_calls
                    ],
                }
                messages.append(msg_dict)
                tool_messages = await self._handle_tool_calls(choice.message.tool_calls)
                messages.extend(tool_messages)
                kwargs["messages"] = messages
            else:
                break

        if finish_reason == "tool_calls":
            final_kwargs = {
                "model": self._config.llm.model,
                "messages": messages,
                "max_tokens": 32768,
            }
            if self._config.llm.extra_body:
                final_kwargs["extra_body"] = self._config.llm.extra_body
            response = await self.client.chat.completions.create(**final_kwargs)
            choice = response.choices[0]

        content = choice.message.content or ""
        if content:
            yield content


gateway = LLMGateway()
