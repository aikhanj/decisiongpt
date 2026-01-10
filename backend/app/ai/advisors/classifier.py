"""Query classifier to select the appropriate advisor."""

from typing import Optional
from pydantic import BaseModel

from app.ai.gateway import AIGateway
from app.ai.advisors.registry import get_registry, Advisor, get_advisor


class ClassificationResult(BaseModel):
    """Result of query classification."""
    advisor_id: str
    confidence: float
    reasoning: Optional[str] = None


CLASSIFICATION_PROMPT = """You are a query classifier. Your job is to determine which advisor should respond to a user's message.

## Available Advisors:
{advisors_context}
- general: For anything that doesn't clearly fit the above categories

## Classification Rules:
1. Match based on the topic and intent of the message
2. Look for keywords and context clues
3. If the query could fit multiple advisors, choose the MOST relevant one
4. If unsure or the query doesn't clearly fit any category, use "general"
5. Be generous with matching - if the topic is even somewhat related, match it

## Examples:
- "How do I ask a girl out?" → dating (relationship/social question)
- "Should I raise a seed round?" → startup (fundraising question)
- "What's a good chest workout?" → fitness (gym/exercise question)
- "How much protein do I need?" → nutrition (diet question)
- "What's the weather like?" → general (doesn't fit categories)
- "I'm nervous about my first date" → dating (dating context)
- "My startup is struggling to find PMF" → startup (startup terminology)
- "How do I build bigger arms?" → fitness (muscle building)
- "Is keto worth it?" → nutrition (diet question)

## User Message:
{user_message}

Return your classification as JSON with:
- advisor_id: The ID of the best matching advisor
- confidence: How confident you are (0.0 to 1.0)
- reasoning: Brief explanation of why you chose this advisor
"""


class AdvisorClassifier:
    """Classifies queries to select the appropriate advisor."""

    def __init__(self, api_key: str):
        self.ai = AIGateway(api_key)
        self.registry = get_registry()

    async def classify(self, user_message: str) -> ClassificationResult:
        """Classify a user message and return the best advisor."""
        # First, try keyword matching for fast classification
        keyword_match = self._keyword_match(user_message)
        if keyword_match and keyword_match.confidence >= 0.8:
            return keyword_match

        # Fall back to AI classification for ambiguous queries
        return await self._ai_classify(user_message)

    def _keyword_match(self, message: str) -> Optional[ClassificationResult]:
        """Quick keyword-based classification."""
        message_lower = message.lower()

        best_match = None
        best_score = 0

        for advisor in self.registry.get_all():
            if advisor.id == "general":
                continue

            # Count keyword matches
            matches = sum(
                1 for kw in advisor.expertise_keywords
                if kw.lower() in message_lower
            )

            if matches > best_score:
                best_score = matches
                best_match = advisor

        if best_match and best_score >= 2:
            # Strong keyword match
            return ClassificationResult(
                advisor_id=best_match.id,
                confidence=min(0.9, 0.5 + (best_score * 0.1)),
                reasoning=f"Keyword match: {best_score} keywords found"
            )
        elif best_match and best_score >= 1:
            # Weak keyword match - might want AI to verify
            return ClassificationResult(
                advisor_id=best_match.id,
                confidence=0.6,
                reasoning=f"Weak keyword match: {best_score} keyword(s) found"
            )

        return None

    async def _ai_classify(self, user_message: str) -> ClassificationResult:
        """Use AI for classification when keywords are ambiguous."""
        prompt = CLASSIFICATION_PROMPT.format(
            advisors_context=self.registry.get_classification_context(),
            user_message=user_message,
        )

        try:
            response, _ = await self.ai.generate(
                system_prompt="You are a precise query classifier. Return valid JSON only.",
                user_prompt=prompt,
                response_model=ClassificationResult,
                temperature=0.1,  # Low temperature for consistent classification
                call_location="classifier.ai_classify",
            )
            return response
        except Exception:
            # If AI classification fails, fall back to general
            return ClassificationResult(
                advisor_id="general",
                confidence=0.5,
                reasoning="Classification failed, defaulting to general"
            )


async def classify_query(api_key: str, user_message: str) -> ClassificationResult:
    """Convenience function to classify a query."""
    classifier = AdvisorClassifier(api_key)
    return await classifier.classify(user_message)


def get_advisor_for_query(api_key: str, classification: ClassificationResult) -> Advisor:
    """Get the advisor instance based on classification result."""
    advisor = get_advisor(classification.advisor_id)
    if not advisor:
        advisor = get_advisor("general")
    return advisor
