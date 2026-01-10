"""Psychologist conversation state schemas.

This module defines the data structures for the Psychologist's Algorithm,
which transforms conversations from shallow "survey bot" questioning into
genuine decision coaching with phases, thread tracking, and forced synthesis.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ConversationPhase(str, Enum):
    """Phases within a coaching conversation.

    Each phase has different goals and response behaviors:
    - OPENING: Understand surface situation, identify threads
    - EXPLORATION: Follow ONE thread deep, not wider
    - DEEPENING: Surface patterns and contradictions
    - INSIGHT: Offer perspective and reframes
    - CLOSING: Confirm understanding, transition to options
    """
    OPENING = "opening"
    EXPLORATION = "exploration"
    DEEPENING = "deepening"
    INSIGHT = "insight"
    CLOSING = "closing"


class EmotionalIntensity(str, Enum):
    """Intensity level of emotional content in a thread."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"  # Existential themes, strong emotions


class ThreadType(str, Enum):
    """Types of conversational threads worth tracking."""
    MENTIONED = "mentioned"  # Topic mentioned but not explored
    EMOTIONAL = "emotional"  # Has emotional charge
    PATTERN = "pattern"  # Reveals a behavioral pattern
    CONTRADICTION = "contradiction"  # User contradicted themselves
    VALUE = "value"  # Reveals user's values


class ResponseMove(str, Enum):
    """Types of conversational moves the coach can make.

    The algorithm enforces variety - can't ask 2 questions in a row
    without reflection/synthesis between them.
    """
    REFLECTION = "reflection"  # Show you heard them
    OBSERVATION = "observation"  # Share pattern you noticed
    CHALLENGE = "challenge"  # Surface contradiction gently
    DEEPENING_QUESTION = "deepening_question"  # Follow thread deeper
    SYNTHESIS = "synthesis"  # Pull together learnings
    INSIGHT = "insight"  # Offer perspective/reframe
    TRANSITION = "transition"  # Move to next phase


class Thread(BaseModel):
    """A conversational thread worth exploring.

    Threads are topics mentioned that deserve deeper exploration.
    The algorithm scores threads to decide which to follow.
    """
    id: str = Field(..., description="Unique thread identifier (t1, t2, etc.)")
    topic: str = Field(..., description="Brief description of the thread")
    type: ThreadType = Field(default=ThreadType.MENTIONED)
    emotional_intensity: EmotionalIntensity = Field(default=EmotionalIntensity.MEDIUM)
    relevance_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="How relevant to the core decision (0-1)"
    )
    exploration_depth: int = Field(
        default=0,
        ge=0,
        description="0=mentioned, 1=asked once, 2=probed deeply"
    )
    first_mentioned_exchange: int = Field(
        default=0,
        description="Exchange number when first mentioned"
    )
    last_touched_exchange: int = Field(
        default=0,
        description="Exchange number when last explored"
    )
    related_quotes: list[str] = Field(
        default_factory=list,
        description="User quotes about this topic"
    )
    notes: Optional[str] = Field(
        default=None,
        description="AI's notes about what this thread reveals"
    )

    def compute_priority_score(self, current_exchange: int) -> float:
        """Compute thread priority score for selection.

        Score = (Emotional_Intensity × 0.35) +
                (Relevance × 0.30) +
                (Unexplored_Bonus × 0.20) +
                (Recency × 0.15)
        """
        # Emotional intensity score (0-100)
        intensity_scores = {
            EmotionalIntensity.LOW: 20,
            EmotionalIntensity.MEDIUM: 50,
            EmotionalIntensity.HIGH: 80,
            EmotionalIntensity.CRITICAL: 100,
        }
        intensity = intensity_scores[self.emotional_intensity]

        # Relevance (0-100)
        relevance = self.relevance_score * 100

        # Unexplored bonus (higher if not deeply explored)
        unexplored = max(0, 100 - (self.exploration_depth * 40))

        # Recency (slight boost for recently mentioned)
        exchanges_since = current_exchange - self.last_touched_exchange
        recency = max(0, 100 - (exchanges_since * 20))

        return (
            intensity * 0.35 +
            relevance * 0.30 +
            unexplored * 0.20 +
            recency * 0.15
        )


class Observation(BaseModel):
    """A pattern or insight noticed by the coach.

    Observations are detected patterns, contradictions, or insights
    that should be surfaced to the user at appropriate moments.
    """
    id: str = Field(..., description="Unique observation identifier")
    type: str = Field(
        ...,
        description="Type: pattern, contradiction, value, emotion, reframe"
    )
    text: str = Field(..., description="The observation text")
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Confidence level (0-1)"
    )
    supporting_quotes: list[str] = Field(
        default_factory=list,
        description="User quotes that support this observation"
    )
    surfaced: bool = Field(
        default=False,
        description="Whether we've shared this with the user"
    )
    surfaced_at_exchange: Optional[int] = Field(
        default=None,
        description="Exchange when surfaced"
    )
    user_confirmed: Optional[bool] = Field(
        default=None,
        description="Did user agree with the observation?"
    )


class PsychologistConversationState(BaseModel):
    """Complete state for psychologist-style conversation.

    This state is stored in DecisionNode.conversation_state_json and
    tracks everything needed for the algorithm to function:
    - Current phase and exchange counts
    - Active threads being explored
    - Observations/patterns detected
    - Synthesis tracking
    - Response move history
    """

    # Phase management
    current_phase: ConversationPhase = Field(
        default=ConversationPhase.OPENING,
        description="Current conversation phase"
    )
    phase_exchange_count: int = Field(
        default=0,
        description="Number of exchanges in current phase"
    )
    total_exchange_count: int = Field(
        default=0,
        description="Total exchanges in conversation"
    )

    # Thread tracking
    active_threads: list[Thread] = Field(
        default_factory=list,
        description="Threads identified for potential exploration"
    )
    current_thread_id: Optional[str] = Field(
        default=None,
        description="ID of thread currently being explored"
    )
    completed_threads: list[str] = Field(
        default_factory=list,
        description="IDs of threads explored to satisfaction"
    )

    # Observations and patterns
    observations: list[Observation] = Field(
        default_factory=list,
        description="Patterns and insights detected"
    )

    # Synthesis tracking
    last_synthesis_exchange: int = Field(
        default=0,
        description="Exchange number of last synthesis"
    )
    synthesis_points: list[str] = Field(
        default_factory=list,
        description="Key learnings synthesized so far"
    )

    # Response tracking
    last_move: Optional[ResponseMove] = Field(
        default=None,
        description="The last response move used"
    )
    move_history: list[ResponseMove] = Field(
        default_factory=list,
        description="History of moves used"
    )

    # Emotional tracking
    dominant_emotion: Optional[str] = Field(
        default=None,
        description="The dominant emotion detected"
    )

    # Core issue tracking
    core_issue_identified: bool = Field(
        default=False,
        description="Whether the core issue has been identified"
    )
    core_issue_statement: Optional[str] = Field(
        default=None,
        description="Statement of the core issue"
    )

    # Readiness
    ready_for_options: bool = Field(
        default=False,
        description="Whether ready to transition to options generation"
    )
    transition_reason: Optional[str] = Field(
        default=None,
        description="Why we're transitioning to options"
    )

    def needs_synthesis(self) -> bool:
        """Check if synthesis is required before next question.

        Synthesis is required:
        - Every 3 exchanges
        - When there are unsurfaced high-confidence observations
        """
        exchanges_since_synthesis = (
            self.total_exchange_count - self.last_synthesis_exchange
        )
        return exchanges_since_synthesis >= 3

    def get_unsurfaced_observations(self) -> list[Observation]:
        """Get observations that haven't been shared with user yet."""
        return [
            obs for obs in self.observations
            if not obs.surfaced and obs.confidence >= 0.6
        ]

    def get_highest_priority_thread(self) -> Optional[Thread]:
        """Get the thread with highest priority score."""
        if not self.active_threads:
            return None

        threads_with_scores = [
            (thread, thread.compute_priority_score(self.total_exchange_count))
            for thread in self.active_threads
            if thread.id not in self.completed_threads
        ]

        if not threads_with_scores:
            return None

        return max(threads_with_scores, key=lambda x: x[1])[0]

    def should_transition_phase(self) -> tuple[bool, Optional[str]]:
        """Check if it's time to transition to the next phase.

        Returns (should_transition, reason)
        """
        phase_rules = {
            ConversationPhase.OPENING: {
                "min_exchanges": 1,
                "max_exchanges": 3,
                "conditions": [
                    ("threads_identified", len(self.active_threads) >= 2),
                ]
            },
            ConversationPhase.EXPLORATION: {
                "min_exchanges": 2,
                "max_exchanges": 5,
                "conditions": [
                    ("pattern_detected", len(self.observations) > 0),
                    ("thread_explored", any(
                        t.exploration_depth >= 2
                        for t in self.active_threads
                    )),
                ]
            },
            ConversationPhase.DEEPENING: {
                "min_exchanges": 2,
                "max_exchanges": 4,
                "conditions": [
                    ("core_issue_identified", self.core_issue_identified),
                    ("observation_surfaced", any(
                        o.surfaced for o in self.observations
                    )),
                ]
            },
            ConversationPhase.INSIGHT: {
                "min_exchanges": 1,
                "max_exchanges": 3,
                "conditions": [
                    ("insight_given", ResponseMove.INSIGHT in self.move_history[-3:] if len(self.move_history) >= 1 else False),
                ]
            },
            ConversationPhase.CLOSING: {
                "min_exchanges": 1,
                "max_exchanges": 2,
                "conditions": []
            }
        }

        rules = phase_rules.get(self.current_phase)
        if not rules:
            return False, None

        # Check max exchanges (force transition)
        if self.phase_exchange_count >= rules["max_exchanges"]:
            return True, f"Reached max exchanges for {self.current_phase.value}"

        # Check min exchanges
        if self.phase_exchange_count < rules["min_exchanges"]:
            return False, None

        # Check conditions
        for condition_name, condition_met in rules["conditions"]:
            if condition_met:
                return True, condition_name

        return False, None

    def get_next_phase(self) -> Optional[ConversationPhase]:
        """Get the next phase in the conversation flow."""
        phase_order = [
            ConversationPhase.OPENING,
            ConversationPhase.EXPLORATION,
            ConversationPhase.DEEPENING,
            ConversationPhase.INSIGHT,
            ConversationPhase.CLOSING,
        ]

        try:
            current_idx = phase_order.index(self.current_phase)
            if current_idx < len(phase_order) - 1:
                return phase_order[current_idx + 1]
        except ValueError:
            pass

        return None

    def advance_phase(self, reason: str) -> None:
        """Advance to the next conversation phase."""
        next_phase = self.get_next_phase()
        if next_phase:
            self.current_phase = next_phase
            self.phase_exchange_count = 0
            self.transition_reason = reason

            # Mark ready for options when entering CLOSING
            if next_phase == ConversationPhase.CLOSING:
                self.ready_for_options = True


# Response requirements for each move type
MOVE_REQUIREMENTS = {
    ResponseMove.REFLECTION: {
        "purpose": "Show the user you heard them",
        "required_elements": [
            "Paraphrase their key point",
            "Name the emotion if present",
        ],
        "avoid": [
            "Starting with 'Understood'",
            "Immediately asking another question without acknowledgment",
        ],
    },
    ResponseMove.OBSERVATION: {
        "purpose": "Share a pattern or insight you've noticed",
        "required_elements": [
            "State what you've noticed",
            "Reference specific things they said",
            "Invite their reaction",
        ],
        "examples": [
            "I'm noticing a theme here - you've mentioned [X] three times now. What's behind that for you?",
            "Something stands out to me: you describe wanting [A] but also say [B]. That tension seems important.",
        ],
    },
    ResponseMove.CHALLENGE: {
        "purpose": "Gently surface a contradiction or assumption",
        "required_elements": [
            "Acknowledge their perspective",
            "Present the contradiction with curiosity",
            "Ask what they make of it",
        ],
        "caution": "Use sparingly - max 1 per conversation",
        "examples": [
            "Earlier you said [A], and just now you mentioned [B]. I'm curious about how those fit together for you.",
        ],
    },
    ResponseMove.DEEPENING_QUESTION: {
        "purpose": "Follow a thread deeper rather than going wider",
        "good_patterns": [
            "What would that look like for you specifically?",
            "Can you tell me about a time when...?",
            "What makes that feel important to you?",
            "What's the worst case you're worried about?",
            "If that worked out perfectly, what would be different?",
        ],
        "banned_patterns": [
            r"what (kind|type|category) of",
            r"would you prefer (A|B|C)",
            r"which of these",
            r"what new \w+ would you",
        ],
    },
    ResponseMove.SYNTHESIS: {
        "purpose": "Pull together learnings before asking more",
        "template": "So far I'm understanding that [key point 1], [key point 2], and underneath it all seems to be [core tension]. Does that capture it?",
        "required_every": 3,  # Must synthesize every 3 exchanges
    },
    ResponseMove.INSIGHT: {
        "purpose": "Offer a perspective or reframe",
        "required_elements": [
            "Offer the insight tentatively",
            "Connect to what they've shared",
            "Leave room for them to modify/reject",
        ],
        "examples": [
            "Here's what strikes me about all of this: [insight]. But you know yourself better than I do - does that land for you?",
            "I wonder if the real question isn't [surface question] but [deeper question]. What do you think?",
        ],
        "timing": "Only in INSIGHT or CLOSING phase",
    },
}


# Banned question patterns that will trigger regeneration
BANNED_QUESTION_PATTERNS = [
    r"what (kind|type|category) of",
    r"would you prefer (A|B|C)",
    r"which of these",
    r"what new \w+ would you",
    r"^Understood\.",
    r"^Got it\.",
]

# Preferred question patterns
PREFERRED_QUESTION_PATTERNS = [
    "what would that look like",
    "tell me about a time when",
    "what makes that feel",
    "what's behind",
    "can you walk me through",
    "what's the worst case you're worried about",
    "if that worked out perfectly, what would be different",
]
