from app.gateway.registry import ScenarioRegistry, ScenarioDefinition
from app.core.config import load_config

config = load_config()


def _check_web_search():
    return bool(config.features.web_search_tool_name)


_SCENARIOS = [
    ("paper_search", "async", True, {"papers": [{"title": "string", "authors": "list", "institution": "string", "abstract": "string", "published_date": "string", "source_url": "string", "summary": "string", "keywords": "list"}]}, _check_web_search),
    ("paper_metadata", "async", False, {"title": "string", "authors": "list", "institution": "string", "abstract": "string", "keywords": "list"}, None),
    ("weekly_report", "async", False, {"report": "string"}, None),
    ("on_demand_search", "async", True, {"papers": [{"title": "string", "authors": "list", "summary": "string", "published_date": "string", "source_url": "string"}]}, _check_web_search),
    ("deep_reading_chat", "stream", False, {}, None),
    ("deep_reading_summary", "async", False, {"summary": "string"}, None),
    ("idea_analysis", "stream", True, {"novelty": "string", "hypotheses": "list", "feasibility": "string", "risks": "list"}, _check_web_search),
    ("idea_chat", "stream", False, {}, None),
    ("bibtex_generate", "async", True, {"bibtex": "string"}, _check_web_search),
    ("tag_recommend", "async", False, {"tags": ["string"]}, None),
    ("review_discuss", "stream", False, {}, None),
    ("review_generate", "stream", False, {}, None),
    ("prompt_doc_generate", "stream", False, {}, None),
    ("experiment_analysis", "async", False, {"report": "string"}, None),
    ("paper_polish", "stream", False, {"diffs": [{"orig": "string", "modified": "string", "reason": "string"}]}, None),
    ("method_discuss", "stream", False, {}, None),
    ("method_generate", "stream", False, {}, None),
    ("evolution_observe", "async", False, {"observation": "string", "dimension": "string"}, None),
    ("evolution_pattern", "async", False, {"is_repeated": "boolean", "pattern": "string", "merged_observation": "string"}, None),
    ("skill_compress", "async", False, {"compressed": "string"}, None),
    ("context_compress", "async", False, {"compressed_context": "string"}, None),
    ("optimize_query", "async", False, {"optimized_query": "string"}, None),
    ("note_optimize", "async", False, {"optimized_note": "string"}, None),
]

for name, mode, web_search, schema, check_fn in _SCENARIOS:
    ScenarioRegistry.register(ScenarioDefinition(
        name=name,
        mode=mode,
        requires_web_search=web_search,
        output_schema=schema if schema else {},
        check_fn=check_fn,
    ))
