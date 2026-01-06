from abc import ABC, abstractmethod
from typing import Optional


class BaseTemplate(ABC):
    """Base class for situation templates."""

    name: str = "generic"
    description: str = "Generic relationship decision"

    # Questions that must be asked for this template
    important_questions: list[str] = []

    # Weight overrides for gentleman score calculation
    # Default weights: all equal at 1.0
    scoring_weights: dict[str, float] = {
        "self_respect": 1.0,
        "respect_for_her": 1.0,
        "clarity": 1.0,
        "leadership": 1.0,
        "warmth": 1.0,
        "progress": 1.0,
        "risk_management": 1.0,
    }

    # Additional guardrail patterns specific to this template
    guardrail_additions: list[str] = []

    # Script style guidance
    script_style_direct: str = "Confident and clear"
    script_style_softer: str = "Warm and approachable"

    def get_template_context(self) -> str:
        """Get template-specific context for prompts."""
        context = f"""
## Template: {self.name}
{self.description}

## Important Questions for This Scenario:
{chr(10).join(f"- {q}" for q in self.important_questions)}

## Scoring Emphasis:
{self._format_scoring_emphasis()}

## Additional Guardrails:
{chr(10).join(f"- {g}" for g in self.guardrail_additions) if self.guardrail_additions else "None"}

## Script Style:
- Direct: {self.script_style_direct}
- Softer: {self.script_style_softer}
"""
        return context

    def _format_scoring_emphasis(self) -> str:
        """Format scoring weights as emphasis text."""
        emphasis = []
        for criterion, weight in self.scoring_weights.items():
            if weight > 1.0:
                emphasis.append(f"- Emphasize {criterion.replace('_', ' ')} (weight: {weight})")
            elif weight < 1.0:
                emphasis.append(f"- De-emphasize {criterion.replace('_', ' ')} (weight: {weight})")
        return "\n".join(emphasis) if emphasis else "Standard weighting"

    def calculate_gentleman_score(self, criteria_scores: dict[str, int]) -> int:
        """Calculate weighted gentleman score from criteria scores."""
        total_weight = sum(self.scoring_weights.values())
        weighted_sum = sum(
            criteria_scores.get(criterion, 5) * weight
            for criterion, weight in self.scoring_weights.items()
        )
        # Scale from 0-10 per criterion to 0-100 overall
        return int((weighted_sum / total_weight) * 10)


class GenericTemplate(BaseTemplate):
    """Generic template for unclassified situations."""

    name = "generic_relationship_next_step"
    description = "General romantic relationship decision"

    important_questions = [
        "What is your relationship stage?",
        "How long have you known each other?",
        "What outcome do you want?",
        "Has she shown interest?",
        "What's the context (work, social, dating app)?",
        "Are there any constraints (distance, timing)?",
        "Have you had meaningful conversation?",
        "What's the last interaction?",
    ]


# Template registry
_templates: dict[str, BaseTemplate] = {}


def register_template(template: BaseTemplate) -> None:
    """Register a template in the registry."""
    _templates[template.name] = template


def get_template(situation_type: str) -> BaseTemplate:
    """Get a template by situation type."""
    return _templates.get(situation_type, GenericTemplate())


# Register generic template
register_template(GenericTemplate())
