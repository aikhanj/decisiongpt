"""Advisor Registry - Central registry for all advisor personas."""

from dataclasses import dataclass, field
from typing import Optional

from app.ai.advisors.prompts.dating import DATING_ADVISOR_PROMPT
from app.ai.advisors.prompts.startup import STARTUP_ADVISOR_PROMPT
from app.ai.advisors.prompts.fitness import FITNESS_ADVISOR_PROMPT
from app.ai.advisors.prompts.nutrition import NUTRITION_ADVISOR_PROMPT
from app.ai.advisors.prompts.general import GENERAL_ADVISOR_PROMPT


@dataclass
class Advisor:
    """Represents an advisor persona."""
    id: str
    name: str
    avatar: str
    description: str
    expertise_keywords: list[str]
    system_prompt: str
    is_system: bool = True
    personality_traits: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "avatar": self.avatar,
            "description": self.description,
            "expertise_keywords": self.expertise_keywords,
            "personality_traits": self.personality_traits,
            "is_system": self.is_system,
        }


# Pre-built system advisors
SYSTEM_ADVISORS: dict[str, Advisor] = {
    "dating": Advisor(
        id="dating",
        name="The Gentleman",
        avatar="🎩",
        description="Charming advice on dating, relationships, and social confidence",
        expertise_keywords=[
            "dating", "relationship", "relationships", "love", "romance",
            "girlfriend", "boyfriend", "date", "first date", "tinder",
            "bumble", "hinge", "match", "attraction", "flirt", "flirting",
            "ask out", "asking out", "text", "texting", "message",
            "confidence", "social", "conversation", "charm", "charisma",
            "marriage", "partner", "spouse", "single", "meet people",
            "approach", "talk to", "how to get", "crush", "ex"
        ],
        system_prompt=DATING_ADVISOR_PROMPT,
        personality_traits=["charming", "sophisticated", "witty", "respectful"],
    ),
    "startup": Advisor(
        id="startup",
        name="The Founder",
        avatar="💡",
        description="Paul Graham-style wisdom on startups, business, and entrepreneurship",
        expertise_keywords=[
            "startup", "startups", "business", "entrepreneur", "entrepreneurship",
            "founder", "founding", "company", "venture", "vc", "investor",
            "funding", "fundraise", "fundraising", "pitch", "pitch deck",
            "product", "product-market fit", "pmf", "mvp", "launch",
            "scale", "scaling", "growth", "hire", "hiring", "team",
            "cofounder", "co-founder", "equity", "valuation", "revenue",
            "customers", "users", "b2b", "b2c", "saas", "pivot",
            "y combinator", "yc", "accelerator", "incubator",
            "business model", "monetize", "monetization", "market"
        ],
        system_prompt=STARTUP_ADVISOR_PROMPT,
        personality_traits=["direct", "contrarian", "first-principles", "honest"],
    ),
    "fitness": Advisor(
        id="fitness",
        name="The Coach",
        avatar="💪",
        description="Motivational guidance on gym, training, and building strength",
        expertise_keywords=[
            "gym", "workout", "exercise", "fitness", "training", "train",
            "muscle", "muscles", "strength", "lift", "lifting", "weights",
            "bodybuilding", "bodybuilder", "bulk", "bulking", "cut", "cutting",
            "bench", "squat", "deadlift", "press", "curl", "row",
            "cardio", "running", "run", "hiit", "crossfit",
            "abs", "chest", "back", "legs", "arms", "shoulders",
            "form", "reps", "sets", "routine", "program", "split",
            "gains", "swole", "shredded", "lean", "toned",
            "recovery", "rest", "overtraining", "injury", "sore",
            "home workout", "no equipment", "dumbbell", "barbell"
        ],
        system_prompt=FITNESS_ADVISOR_PROMPT,
        personality_traits=["motivational", "disciplined", "supportive", "direct"],
    ),
    "nutrition": Advisor(
        id="nutrition",
        name="The Nutritionist",
        avatar="🥗",
        description="Science-backed advice on diet, nutrition, and healthy eating",
        expertise_keywords=[
            "nutrition", "diet", "food", "eat", "eating", "meal", "meals",
            "protein", "carbs", "carbohydrates", "fat", "fats", "calories",
            "macro", "macros", "weight loss", "lose weight", "gain weight",
            "healthy", "health", "vitamin", "vitamins", "supplement", "supplements",
            "breakfast", "lunch", "dinner", "snack", "snacks",
            "meal prep", "meal plan", "cooking", "recipe", "recipes",
            "keto", "paleo", "vegan", "vegetarian", "intermittent fasting",
            "sugar", "sodium", "fiber", "gut", "digestion",
            "creatine", "whey", "pre workout", "post workout",
            "metabolism", "bmr", "tdee", "deficit", "surplus"
        ],
        system_prompt=NUTRITION_ADVISOR_PROMPT,
        personality_traits=["scientific", "patient", "myth-busting", "practical"],
    ),
    "general": Advisor(
        id="general",
        name="Assistant",
        avatar="🤖",
        description="General-purpose advisor for questions that don't fit other categories",
        expertise_keywords=[],  # Fallback, matches anything not matched by others
        system_prompt=GENERAL_ADVISOR_PROMPT,
        personality_traits=["helpful", "knowledgeable", "friendly"],
    ),
}


class AdvisorRegistry:
    """Registry for managing advisors (system + custom)."""

    def __init__(self):
        self._advisors: dict[str, Advisor] = SYSTEM_ADVISORS.copy()
        self._custom_advisors: dict[str, Advisor] = {}

    def get(self, advisor_id: str) -> Optional[Advisor]:
        """Get an advisor by ID."""
        return self._advisors.get(advisor_id) or self._custom_advisors.get(advisor_id)

    def get_all(self) -> list[Advisor]:
        """Get all advisors."""
        return list(self._advisors.values()) + list(self._custom_advisors.values())

    def get_system_advisors(self) -> list[Advisor]:
        """Get only system (pre-built) advisors."""
        return [a for a in self._advisors.values() if a.is_system]

    def add_custom_advisor(self, advisor: Advisor) -> None:
        """Add a custom advisor."""
        self._custom_advisors[advisor.id] = advisor

    def remove_custom_advisor(self, advisor_id: str) -> bool:
        """Remove a custom advisor. Returns True if removed, False if not found."""
        if advisor_id in self._custom_advisors:
            del self._custom_advisors[advisor_id]
            return True
        return False

    def get_classification_context(self) -> str:
        """Get context string for advisor classification."""
        lines = []
        for advisor in self.get_all():
            if advisor.id == "general":
                continue  # Don't include general in classification
            keywords = ", ".join(advisor.expertise_keywords[:10])
            lines.append(f"- {advisor.id}: {advisor.description} (keywords: {keywords})")
        return "\n".join(lines)


# Global registry instance
_registry = AdvisorRegistry()


def get_advisor(advisor_id: str) -> Optional[Advisor]:
    """Get an advisor by ID from the global registry."""
    return _registry.get(advisor_id)


def get_all_advisors() -> list[Advisor]:
    """Get all advisors from the global registry."""
    return _registry.get_all()


def get_registry() -> AdvisorRegistry:
    """Get the global registry instance."""
    return _registry
