from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class ScenarioDefinition:
    name: str
    mode: str
    requires_web_search: bool = False
    output_schema: dict = field(default_factory=dict)
    check_fn: Optional[Callable] = None


class ScenarioRegistry:
    _scenarios: dict[str, ScenarioDefinition] = {}

    @classmethod
    def register(cls, definition: ScenarioDefinition) -> None:
        cls._scenarios[definition.name] = definition

    @classmethod
    def get(cls, name: str) -> Optional[ScenarioDefinition]:
        return cls._scenarios.get(name)

    @classmethod
    def validate(cls, name: str) -> tuple[bool, str]:
        scenario = cls.get(name)
        if not scenario:
            return False, f"Unknown scenario: {name}"
        if scenario.check_fn and not scenario.check_fn():
            return False, f"Precondition check failed for scenario: {name}"
        return True, ""
