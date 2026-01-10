"""Pattern detection service for the Psychologist's Algorithm.

This service handles:
- Extracting conversational threads from messages
- Detecting patterns and contradictions
- Scoring emotional intensity
- Updating thread exploration depth
"""

import re
import uuid
from typing import Optional

from pydantic import BaseModel, Field

from app.ai.gateway import AIGateway
from app.schemas.psychologist_state import (
    Thread,
    ThreadType,
    Observation,
    EmotionalIntensity,
    PsychologistConversationState,
)


class DetectedThread(BaseModel):
    """A newly detected thread from message analysis."""
    topic: str
    type: ThreadType
    emotional_intensity: EmotionalIntensity
    relevance_score: float = Field(ge=0.0, le=1.0)
    quote: str


class DetectedObservation(BaseModel):
    """A newly detected observation (pattern/contradiction)."""
    type: str  # pattern, contradiction, value, emotion
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    supporting_quotes: list[str]


class PatternAnalysisResult(BaseModel):
    """Result of analyzing a message for patterns."""
    new_threads: list[DetectedThread] = Field(default_factory=list)
    new_observations: list[DetectedObservation] = Field(default_factory=list)
    updated_thread_depths: dict[str, int] = Field(default_factory=dict)
    dominant_emotion: Optional[str] = None


class PatternDetector:
    """Service for detecting patterns, threads, and contradictions."""

    # Keywords that signal emotional intensity
    INTENSITY_MARKERS = {
        EmotionalIntensity.CRITICAL: [
            "terrified", "desperate", "hate", "love", "obsessed",
            "meaningless", "pointless", "hopeless", "devastating",
        ],
        EmotionalIntensity.HIGH: [
            "really", "very", "extremely", "always", "never",
            "frustrated", "angry", "anxious", "scared", "worried",
            "stuck", "trapped", "lost", "confused", "overwhelmed",
        ],
        EmotionalIntensity.MEDIUM: [
            "kind of", "somewhat", "a bit", "unsure", "maybe",
            "thinking about", "considering", "wonder",
        ],
    }

    # Patterns that might indicate contradiction
    CONTRADICTION_SIGNALS = [
        (r"want.*but", "wants X but Y"),
        (r"should.*but", "feels they should but"),
        (r"i know.*but", "knows X but does Y"),
        (r"on one hand.*other", "internal conflict"),
    ]

    # Value-indicating words
    VALUE_INDICATORS = [
        "important", "matters", "priority", "value", "care about",
        "need", "must", "have to", "want", "wish",
    ]

    def __init__(self, ai_gateway: Optional[AIGateway] = None):
        """Initialize the pattern detector.

        Args:
            ai_gateway: Optional AI gateway for advanced analysis.
                       If None, uses rule-based detection only.
        """
        self.ai = ai_gateway

    async def analyze_message(
        self,
        message: str,
        chat_history: list[dict],
        state: PsychologistConversationState,
    ) -> PatternAnalysisResult:
        """Analyze a user message for threads, patterns, and contradictions.

        This combines rule-based detection with optional AI analysis
        for more nuanced pattern detection.
        """
        result = PatternAnalysisResult()

        # Rule-based analysis (always runs)
        rule_result = self._rule_based_analysis(message, chat_history, state)
        result.new_threads.extend(rule_result.new_threads)
        result.new_observations.extend(rule_result.new_observations)
        result.dominant_emotion = rule_result.dominant_emotion

        # Update thread depths for mentioned threads
        result.updated_thread_depths = self._update_thread_depths(
            message, state.active_threads
        )

        # AI-based analysis (if gateway available and useful)
        if self.ai and len(chat_history) >= 2:
            try:
                ai_result = await self._ai_analysis(message, chat_history, state)
                # Merge AI results, avoiding duplicates
                for thread in ai_result.new_threads:
                    if not self._is_duplicate_thread(thread, result.new_threads):
                        result.new_threads.append(thread)
                for obs in ai_result.new_observations:
                    if not self._is_duplicate_observation(obs, result.new_observations):
                        result.new_observations.append(obs)
            except Exception:
                # AI analysis failed, continue with rule-based results
                pass

        return result

    def _rule_based_analysis(
        self,
        message: str,
        chat_history: list[dict],
        state: PsychologistConversationState,
    ) -> PatternAnalysisResult:
        """Perform rule-based pattern analysis."""
        result = PatternAnalysisResult()
        message_lower = message.lower()

        # Detect emotional intensity and emotion
        intensity, emotion = self._detect_emotion(message_lower)
        result.dominant_emotion = emotion

        # Look for emotional threads (repeated words, strong language)
        emotional_threads = self._detect_emotional_threads(
            message, message_lower, intensity
        )
        result.new_threads.extend(emotional_threads)

        # Look for contradictions with previous statements
        if chat_history:
            contradictions = self._detect_contradictions(
                message_lower, chat_history
            )
            result.new_observations.extend(contradictions)

        # Look for value statements
        value_threads = self._detect_value_statements(message, message_lower)
        result.new_threads.extend(value_threads)

        # Look for repeated themes across history
        if len(chat_history) >= 4:
            patterns = self._detect_repeated_themes(message_lower, chat_history)
            result.new_observations.extend(patterns)

        return result

    def _detect_emotion(self, message_lower: str) -> tuple[EmotionalIntensity, Optional[str]]:
        """Detect emotional intensity and dominant emotion from message."""
        # Check for critical intensity markers first
        for intensity, markers in self.INTENSITY_MARKERS.items():
            for marker in markers:
                if marker in message_lower:
                    # Map marker to emotion
                    emotion = self._marker_to_emotion(marker)
                    return intensity, emotion

        # Default to medium/neutral
        return EmotionalIntensity.MEDIUM, "neutral"

    def _marker_to_emotion(self, marker: str) -> str:
        """Map an intensity marker to an emotion label."""
        emotion_map = {
            "terrified": "anxious",
            "desperate": "anxious",
            "hate": "frustrated",
            "love": "excited",
            "meaningless": "sad",
            "pointless": "sad",
            "hopeless": "sad",
            "frustrated": "frustrated",
            "angry": "frustrated",
            "anxious": "anxious",
            "scared": "anxious",
            "worried": "anxious",
            "stuck": "frustrated",
            "trapped": "frustrated",
            "lost": "confused",
            "confused": "confused",
            "overwhelmed": "anxious",
        }
        return emotion_map.get(marker, "neutral")

    def _detect_emotional_threads(
        self,
        message: str,
        message_lower: str,
        intensity: EmotionalIntensity,
    ) -> list[DetectedThread]:
        """Detect threads with emotional charge."""
        threads = []

        # Check for explicit emotional statements
        emotional_patterns = [
            (r"i feel (like |that )?([\w\s]+)", "feeling"),
            (r"it feels (like |that )?([\w\s]+)", "feeling"),
            (r"i('m| am) ([\w\s]+)", "state"),
            (r"i('ve| have) been ([\w\s]+)", "pattern"),
        ]

        for pattern, thread_type in emotional_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                # Extract the relevant part
                if isinstance(match, tuple):
                    topic = match[-1].strip()[:50]  # Last group, limited length
                else:
                    topic = match.strip()[:50]

                if len(topic) > 3:  # Avoid tiny matches
                    threads.append(DetectedThread(
                        topic=f"feeling {topic}",
                        type=ThreadType.EMOTIONAL,
                        emotional_intensity=intensity,
                        relevance_score=0.7,
                        quote=self._extract_quote(message, topic),
                    ))

        return threads[:3]  # Limit to top 3

    def _detect_contradictions(
        self,
        message_lower: str,
        chat_history: list[dict],
    ) -> list[DetectedObservation]:
        """Detect contradictions between current message and history."""
        observations = []

        # Get previous user messages
        user_messages = [
            m["content"].lower()
            for m in chat_history
            if m.get("role") == "user"
        ]

        if not user_messages:
            return observations

        # Check for internal contradictions in current message
        for pattern, label in self.CONTRADICTION_SIGNALS:
            if re.search(pattern, message_lower):
                observations.append(DetectedObservation(
                    type="contradiction",
                    text=f"User shows internal conflict: {label}",
                    confidence=0.7,
                    supporting_quotes=[message_lower[:100]],
                ))

        # Check for contradictions with previous statements
        # Simple approach: look for negations of previously stated things
        negation_patterns = ["don't", "doesn't", "not", "never", "no longer"]
        affirmation_patterns = ["want", "need", "like", "enjoy", "love"]

        for neg in negation_patterns:
            for aff in affirmation_patterns:
                current_neg = f"{neg} {aff}" in message_lower
                if current_neg:
                    # Check if they previously affirmed this
                    for prev in user_messages:
                        if aff in prev and neg not in prev:
                            # Potential contradiction
                            observations.append(DetectedObservation(
                                type="contradiction",
                                text=f"Previously expressed '{aff}' positively, now negatively",
                                confidence=0.6,
                                supporting_quotes=[
                                    prev[:100],
                                    message_lower[:100],
                                ],
                            ))

        return observations[:2]  # Limit

    def _detect_value_statements(
        self,
        message: str,
        message_lower: str,
    ) -> list[DetectedThread]:
        """Detect statements that reveal user values."""
        threads = []

        for indicator in self.VALUE_INDICATORS:
            if indicator in message_lower:
                # Extract what they value
                pattern = rf"{indicator}s? (?:to |about |is )?([\w\s]+)"
                matches = re.findall(pattern, message_lower)
                for match in matches:
                    value = match.strip()[:40]
                    if len(value) > 3:
                        threads.append(DetectedThread(
                            topic=f"values {value}",
                            type=ThreadType.VALUE,
                            emotional_intensity=EmotionalIntensity.MEDIUM,
                            relevance_score=0.8,
                            quote=self._extract_quote(message, value),
                        ))

        return threads[:2]

    def _detect_repeated_themes(
        self,
        message_lower: str,
        chat_history: list[dict],
    ) -> list[DetectedObservation]:
        """Detect themes that repeat across conversation."""
        observations = []

        # Count word frequency across user messages
        user_text = " ".join(
            m["content"].lower()
            for m in chat_history
            if m.get("role") == "user"
        ) + " " + message_lower

        # Look for emotionally significant words that repeat
        significant_words = [
            "stuck", "pointless", "meaningless", "connection", "alone",
            "lost", "confused", "frustrated", "want", "need", "afraid",
            "scared", "worried", "happy", "excited", "hope",
        ]

        for word in significant_words:
            count = user_text.count(word)
            if count >= 3:
                observations.append(DetectedObservation(
                    type="pattern",
                    text=f"'{word}' mentioned {count} times - recurring theme",
                    confidence=min(0.5 + count * 0.1, 0.9),
                    supporting_quotes=[],
                ))

        return observations[:2]

    def _update_thread_depths(
        self,
        message: str,
        active_threads: list[Thread],
    ) -> dict[str, int]:
        """Update exploration depth for threads mentioned in message."""
        updates = {}
        message_lower = message.lower()

        for thread in active_threads:
            # Check if thread topic is mentioned in message
            topic_words = thread.topic.lower().split()
            if any(word in message_lower for word in topic_words if len(word) > 3):
                # Thread was touched, increase depth
                updates[thread.id] = min(thread.exploration_depth + 1, 3)

        return updates

    def _extract_quote(self, message: str, keyword: str) -> str:
        """Extract a relevant quote around a keyword."""
        message_lower = message.lower()
        idx = message_lower.find(keyword.lower())
        if idx == -1:
            return message[:100]

        start = max(0, idx - 20)
        end = min(len(message), idx + len(keyword) + 50)
        return message[start:end].strip()

    def _is_duplicate_thread(
        self,
        thread: DetectedThread,
        existing: list[DetectedThread],
    ) -> bool:
        """Check if a thread is a duplicate."""
        for e in existing:
            if thread.topic.lower() == e.topic.lower():
                return True
            # Check for significant overlap
            t_words = set(thread.topic.lower().split())
            e_words = set(e.topic.lower().split())
            if len(t_words & e_words) > len(t_words) * 0.5:
                return True
        return False

    def _is_duplicate_observation(
        self,
        obs: DetectedObservation,
        existing: list[DetectedObservation],
    ) -> bool:
        """Check if an observation is a duplicate."""
        for e in existing:
            if obs.type == e.type and obs.text.lower() == e.text.lower():
                return True
        return False

    async def _ai_analysis(
        self,
        message: str,
        chat_history: list[dict],
        state: PsychologistConversationState,
    ) -> PatternAnalysisResult:
        """Use AI for more nuanced pattern analysis."""
        # Build prompt
        history_summary = "\n".join(
            f"{m['role']}: {m['content'][:100]}"
            for m in chat_history[-6:]
        )

        known_threads = "\n".join(
            f"- {t.topic} ({t.type.value})"
            for t in state.active_threads
        ) or "None yet"

        known_observations = "\n".join(
            f"- [{o.type}] {o.text}"
            for o in state.observations
        ) or "None yet"

        prompt = f"""Analyze this user message for patterns:

User Message: {message}

Previous Messages:
{history_summary}

Known Threads: {known_threads}
Known Observations: {known_observations}

Return JSON:
{{
    "new_threads": [
        {{"topic": "...", "type": "emotional|pattern|contradiction|value|mentioned", "emotional_intensity": "low|medium|high|critical", "relevance_score": 0.0-1.0, "quote": "..."}}
    ],
    "new_observations": [
        {{"type": "pattern|contradiction|value|emotion", "text": "...", "confidence": 0.0-1.0, "supporting_quotes": ["..."]}}
    ],
    "dominant_emotion": "neutral|anxious|frustrated|excited|confused|sad|hopeful"
}}"""

        response, _ = await self.ai.generate(
            system_prompt="You are an expert at analyzing conversational patterns. Be concise.",
            user_prompt=prompt,
            response_model=PatternAnalysisResult,
        )

        return response


def create_thread_from_detected(
    detected: DetectedThread,
    exchange_num: int,
) -> Thread:
    """Create a Thread from a DetectedThread."""
    return Thread(
        id=f"t{uuid.uuid4().hex[:8]}",
        topic=detected.topic,
        type=detected.type,
        emotional_intensity=detected.emotional_intensity,
        relevance_score=detected.relevance_score,
        exploration_depth=0,
        first_mentioned_exchange=exchange_num,
        last_touched_exchange=exchange_num,
        related_quotes=[detected.quote] if detected.quote else [],
    )


def create_observation_from_detected(detected: DetectedObservation) -> Observation:
    """Create an Observation from a DetectedObservation."""
    return Observation(
        id=f"o{uuid.uuid4().hex[:8]}",
        type=detected.type,
        text=detected.text,
        confidence=detected.confidence,
        supporting_quotes=detected.supporting_quotes,
        surfaced=False,
    )
