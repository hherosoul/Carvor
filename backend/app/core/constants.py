import json
from pathlib import Path

_PROMPTS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "prompts.json"

_DEFAULT_SYSTEM_CONSTRAINT = """你是一个科研助手。你必须遵守以下约束：
1. 严格忠于原始内容，不得歪曲、夸大或缩小
2. 不确定的信息不要编造，宁可不写也不要瞎写
3. 如实标注你的不确定之处（如"此关联性较弱，仅供参考"）
4. 优先保证准确性，其次才是完整性"""

_DEFAULT_SCENARIO_CONSTRAINTS = {
    "paper_polish": "如果原文表述可能有歧义，优先保留原文而非猜测意图。不得添加原文未提及的新观点、新论据或新引用。严格保持原文语义，不得改变任何论点、结论或数据含义。",
    "paper_search": "返回的论文必须真实存在，必须是最新的，不得编造论文标题、作者或摘要。每篇论文必须包含published_date字段，格式为YYYY-MM-DD。",
    "on_demand_search": "返回的论文必须真实存在，不得编造论文标题、作者或摘要。每篇论文必须包含published_date字段，格式为YYYY-MM-DD。只返回在cutoff_date之后发表的论文，cutoff_date之前的论文一律不要返回。如果没有发布日期的论文，不要返回。根据用户的任务描述精准筛选相关论文，错过好过泛滥。在构造搜索query时，务必加入日期限定词，确保搜索引擎优先返回最新论文。",
    "paper_metadata": "BibTeX 条目中，无法确认的字段留空，不得编造或猜测。",
    "bibtex_generate": "BibTeX 条目中，无法确认的字段留空，不得编造或猜测。",
    "deep_reading_chat": "回答必须基于论文原文内容，不得编造论文中未提及的信息。如不确定，明确说明。",
    "deep_reading_summary": "总结中的每个论点必须在原文或对话中有对应依据，不得推断或补充。",
    "weekly_report": "对每篇论文的描述必须忠于原文，不得夸大或缩小其贡献。",
    "idea_analysis": "对比已有工作时，必须准确描述其内容，不得为突显新颖性而歪曲他人工作。",
    "idea_chat": "讨论必须围绕给定的idea展开，建议必须具体可操作，不得给出空泛的指导。引用已有工作时必须准确描述。",
    "method_discuss": "讨论必须围绕给定的研究方法展开，建议必须具体可操作，不得给出空泛的指导。",
    "method_generate": "生成的研究方法必须具体可执行，不得给出空泛的框架性描述。",
    "experiment_analysis": "分析结论必须基于提供的日志数据，数据不足时明确说明'数据不足以判断'，而非猜测。",
    "review_discuss": "讨论必须基于论文原文，不得编造论文中未提及的内容。",
    "review_generate": "对每篇论文的描述必须忠于原文，不得夸大或缩小其贡献。",
    "prompt_doc_generate": "生成的提示词必须具体、可执行，包含明确的输入输出格式和约束条件。",
    "tag_recommend": "推荐的标签必须与论文内容直接相关，不得编造不相关的标签。",
}

_DEFAULT_SKILL_MAP = {
    "paper_search": "文献跟踪",
    "paper_metadata": "文献跟踪",
    "weekly_report": "文献跟踪",
    "on_demand_search": "文献跟踪",
    "deep_reading_chat": "文献跟踪",
    "deep_reading_summary": "文献跟踪",
    "idea_analysis": "idea锤炼",
    "idea_chat": "idea锤炼",
    "bibtex_generate": "文献跟踪",
    "tag_recommend": "文献跟踪",
    "review_discuss": "文献跟踪",
    "review_generate": "文献跟踪",
    "prompt_doc_generate": "代码提示词生成",
    "experiment_analysis": "代码提示词生成",
    "paper_polish": "论文润色",
    "method_discuss": "idea锤炼",
    "method_generate": "idea锤炼",
}


def _load_prompts():
    if _PROMPTS_PATH.exists():
        with open(_PROMPTS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_prompts = _load_prompts()

SYSTEM_CONSTRAINT = _prompts.get("system_constraint", _DEFAULT_SYSTEM_CONSTRAINT)
SCENARIO_CONSTRAINTS = {**_DEFAULT_SCENARIO_CONSTRAINTS, **_prompts.get("scenario_constraints", {})}
SCENARIO_TASKS = _prompts.get("scenario_tasks", {})
SKILL_MAP = {**_DEFAULT_SKILL_MAP, **_prompts.get("skill_map", {})}
