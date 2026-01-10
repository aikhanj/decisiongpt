"""Psychologist Engine - Main orchestration for the coaching algorithm.

This service orchestrates the Psychologist's Algorithm:
1. Receives user messages
2. Updates conversation state (threads, observations, phase)
3. Generates phase-appropriate prompts
4. Validates responses
5. Returns structured responses with state updates
"""

import re
import logging
from typing import Optional
from pydantic import BaseModel, Field

from app.ai.gateway import AIGateway
from app.ai.prompts.psychologist_prompts import (
    build_psychologist_system_prompt,
    RESPONSE_FORMAT,
)
from app.schemas.psychologist_state import (
    ConversationPhase,
    PsychologistConversationState,
    Thread,
    Observation,
    ResponseMove,
    BANNED_QUESTION_PATTERNS as STATE_BANNED_PATTERNS,
)
from app.services.pattern_detector import (
    PatternDetector,
    create_thread_from_detected,
    create_observation_from_detected,
)

logger = logging.getLogger(__name__)


class PsychologistResponse(BaseModel):
    """Structured response from the psychologist engine."""
    response: str = Field(..., description="The actual response text")
    response_move: ResponseMove = Field(..., description="Type of move made")
    question_reason: Optional[str] = Field(None, description="Why this question/statement")
    suggested_options: Optional[list[str]] = Field(None, description="Quick reply options")

    # State updates
    state: PsychologistConversationState = Field(..., description="Updated conversation state")

    # For canvas updates
    synthesis_points: list[str] = Field(default_factory=list)
    core_issue: Optional[str] = Field(None)
    ready_for_options: bool = Field(default=False)


class AIResponseModel(BaseModel):
    """Expected structure from AI response."""
    response: str
    response_move: str
    threads_detected: list[dict] = Field(default_factory=list)
    observations_detected: list[dict] = Field(default_factory=list)
    synthesis_points: list[str] = Field(default_factory=list)
    core_issue: Optional[str] = None
    should_transition: bool = False
    transition_reason: Optional[str] = None
    question_reason: Optional[str] = None
    suggested_options: Optional[list[str]] = None


class PsychologistEngine:
    """Main orchestration engine for the Psychologist's Algorithm.

    This engine manages the entire conversation flow:
    - Phase management and transitions
    - Thread tracking and selection
    - Pattern/contradiction detection
    - Synthesis enforcement
    - Response validation
    """

    # Maximum regeneration attempts for invalid responses
    MAX_REGEN_ATTEMPTS = 2

    def __init__(self, ai_gateway: AIGateway):
        """Initialize the engine.

        Args:
            ai_gateway: AI gateway for generating responses
        """
        self.ai = ai_gateway
        self.pattern_detector = PatternDetector(ai_gateway)

    async def process_message(
        self,
        user_message: str,
        situation_text: str,
        chat_history: list[dict],
        current_state: Optional[PsychologistConversationState] = None,
    ) -> PsychologistResponse:
        """Process a user message and generate a coached response.

        This is the main entry point for the algorithm:
        1. Initialize or update state
        2. Detect patterns in the new message
        3. Check for phase transitions
        4. Generate response with constraints
        5. Validate response
        6. Update state and return

        Args:
            user_message: The user's message
            situation_text: Original decision situation
            chat_history: Full chat history
            current_state: Current conversation state (None for first message)

        Returns:
            PsychologistResponse with response and updated state
        """
        # Initialize state if needed
        state = current_state or PsychologistConversationState()

        # Increment exchange count
        state.total_exchange_count += 1
        state.phase_exchange_count += 1

        # Step 1: Detect patterns in the new message
        pattern_result = await self.pattern_detector.analyze_message(
            user_message, chat_history, state
        )

        # Update state with detected patterns
        self._update_state_with_patterns(state, pattern_result)

        # Step 2: Check for phase transitions
        should_transition, reason = state.should_transition_phase()
        if should_transition:
            logger.info(f"Transitioning phase: {reason}")
            state.advance_phase(reason)

        # Step 3: Build prompt and generate response
        system_prompt = build_psychologist_system_prompt(
            state, situation_text, chat_history
        )

        # Generate response with validation loop
        response = await self._generate_validated_response(
            system_prompt, user_message, state
        )

        # Step 4: Update state with response information
        self._update_state_from_response(state, response)

        # Build final response
        return PsychologistResponse(
            response=response.response,
            response_move=self._parse_move(response.response_move),
            question_reason=response.question_reason,
            suggested_options=response.suggested_options,
            state=state,
            synthesis_points=state.synthesis_points,
            core_issue=state.core_issue_statement,
            ready_for_options=state.ready_for_options,
        )

    def _update_state_with_patterns(
        self,
        state: PsychologistConversationState,
        pattern_result,
    ) -> None:
        """Update state with detected patterns from message analysis."""
        from app.services.pattern_detector import (
            create_thread_from_detected,
            create_observation_from_detected,
        )

        # Add new threads
        for detected in pattern_result.new_threads:
            # Check for duplicates
            existing_topics = [t.topic.lower() for t in state.active_threads]
            if detected.topic.lower() not in existing_topics:
                thread = create_thread_from_detected(
                    detected, state.total_exchange_count
                )
                state.active_threads.append(thread)

        # Update thread depths
        for thread_id, new_depth in pattern_result.updated_thread_depths.items():
            for thread in state.active_threads:
                if thread.id == thread_id:
                    thread.exploration_depth = new_depth
                    thread.last_touched_exchange = state.total_exchange_count

        # Add new observations
        for detected in pattern_result.new_observations:
            # Check for duplicates
            existing_texts = [o.text.lower() for o in state.observations]
            if detected.text.lower() not in existing_texts:
                obs = create_observation_from_detected(detected)
                state.observations.append(obs)

        # Update dominant emotion
        if pattern_result.dominant_emotion:
            state.dominant_emotion = pattern_result.dominant_emotion

    async def _generate_validated_response(
        self,
        system_prompt: str,
        user_message: str,
        state: PsychologistConversationState,
    ) -> AIResponseModel:
        """Generate a response and validate it, regenerating if needed."""
        for attempt in range(self.MAX_REGEN_ATTEMPTS + 1):
            # Generate response
            response, _ = await self.ai.generate(
                system_prompt=system_prompt,
                user_prompt=user_message,
                response_model=AIResponseModel,
            )

            # Validate response
            issues = self._validate_response(response, state)

            if not issues:
                return response

            if attempt < self.MAX_REGEN_ATTEMPTS:
                logger.warning(
                    f"Response validation failed (attempt {attempt + 1}): {issues}"
                )
                # Add correction to prompt
                correction = self._build_correction_prompt(issues)
                system_prompt = system_prompt + "\n\n" + correction
            else:
                # Final attempt failed, fix the response ourselves
                logger.warning(f"Max attempts reached, applying fixes: {issues}")
                response = self._apply_fixes(response, issues, state)
                return response

        return response

    def _validate_response(
        self,
        response: AIResponseModel,
        state: PsychologistConversationState,
    ) -> list[str]:
        """Validate a response against the algorithm rules.

        Returns list of issues (empty if valid).
        """
        issues = []
        text = response.response.lower()

        # Check for banned openers
        if text.startswith("understood"):
            issues.append("Starts with 'Understood' (robotic)")
        if text.startswith("got it"):
            issues.append("Starts with 'Got it' (robotic)")

        # Check for banned question patterns
        for pattern in STATE_BANNED_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(f"Contains banned pattern: {pattern}")

        # Check multiple questions
        question_count = text.count("?")
        if question_count > 1:
            issues.append(f"Contains {question_count} questions (max 1)")

        # Check synthesis requirement
        if state.needs_synthesis():
            synthesis_indicators = [
                "so far",
                "understanding that",
                "i'm hearing",
                "let me check",
                "what i'm getting",
                "to summarize",
            ]
            has_synthesis = any(ind in text for ind in synthesis_indicators)
            if not has_synthesis:
                issues.append(
                    f"Missing synthesis (required every 3 exchanges, "
                    f"last was {state.total_exchange_count - state.last_synthesis_exchange} ago)"
                )

        # Check move is appropriate for phase
        move = self._parse_move(response.response_move)
        if not self._is_move_allowed_in_phase(move, state.current_phase):
            issues.append(
                f"Move {move.value} not appropriate for phase {state.current_phase.value}"
            )

        # Check for consecutive questions without reflection
        if move == ResponseMove.DEEPENING_QUESTION:
            recent_moves = state.move_history[-2:] if len(state.move_history) >= 2 else []
            if len(recent_moves) >= 2 and all(
                m == ResponseMove.DEEPENING_QUESTION for m in recent_moves
            ):
                issues.append(
                    "Asked 2+ questions in a row without reflection/synthesis"
                )

        return issues

    def _build_correction_prompt(self, issues: list[str]) -> str:
        """Build a correction prompt based on validation issues."""
        corrections = []

        for issue in issues:
            if "Understood" in issue or "Got it" in issue:
                corrections.append(
                    "DO NOT start with 'Understood' or 'Got it' - be more natural"
                )
            elif "banned pattern" in issue:
                corrections.append(
                    "DO NOT ask 'What type/kind of X?' - ask deeper questions like "
                    "'What would that look like?' or 'Tell me about a time when...'"
                )
            elif "questions" in issue:
                corrections.append(
                    "Ask only ONE question per response. Choose the most important one."
                )
            elif "synthesis" in issue:
                corrections.append(
                    "You MUST include a synthesis statement. Start with something like "
                    "'So far I'm understanding that...' before asking anything new."
                )
            elif "Move" in issue:
                corrections.append(
                    "Use a different response move that's appropriate for the current phase."
                )

        return "## CORRECTIONS REQUIRED\n" + "\n".join(f"- {c}" for c in corrections)

    def _apply_fixes(
        self,
        response: AIResponseModel,
        issues: list[str],
        state: PsychologistConversationState,
    ) -> AIResponseModel:
        """Apply fixes to a response that failed validation."""
        text = response.response

        # Fix banned openers
        if text.lower().startswith("understood"):
            text = text[10:].strip()
            if text.startswith("."):
                text = text[1:].strip()
            if text.startswith(","):
                text = text[1:].strip()

        if text.lower().startswith("got it"):
            text = text[6:].strip()
            if text.startswith("."):
                text = text[1:].strip()

        # Fix multiple questions - keep only the last one
        if text.count("?") > 1:
            sentences = re.split(r"(?<=[.?!])\s+", text)
            questions = [s for s in sentences if "?" in s]
            non_questions = [s for s in sentences if "?" not in s]
            if questions and non_questions:
                text = " ".join(non_questions) + " " + questions[-1]

        # Note: We don't mechanically prepend synthesis here because it creates
        # awkward third-person references. Instead, we rely on the correction prompt
        # to force the AI to regenerate with proper synthesis. If we've exhausted
        # regeneration attempts, we accept the response as-is rather than creating
        # a worse output by mechanical prepending.

        response.response = text
        return response

    def _parse_move(self, move_str: str) -> ResponseMove:
        """Parse a move string into ResponseMove enum."""
        move_str = move_str.upper().replace("-", "_")
        try:
            return ResponseMove(move_str.lower())
        except ValueError:
            # Default to deepening question
            return ResponseMove.DEEPENING_QUESTION

    def _is_move_allowed_in_phase(
        self,
        move: ResponseMove,
        phase: ConversationPhase,
    ) -> bool:
        """Check if a move is allowed in the given phase."""
        allowed_moves = {
            ConversationPhase.OPENING: [
                ResponseMove.REFLECTION,
                ResponseMove.DEEPENING_QUESTION,
            ],
            ConversationPhase.EXPLORATION: [
                ResponseMove.REFLECTION,
                ResponseMove.DEEPENING_QUESTION,
                ResponseMove.OBSERVATION,
            ],
            ConversationPhase.DEEPENING: [
                ResponseMove.REFLECTION,
                ResponseMove.OBSERVATION,
                ResponseMove.CHALLENGE,
                ResponseMove.SYNTHESIS,
                ResponseMove.DEEPENING_QUESTION,
            ],
            ConversationPhase.INSIGHT: [
                ResponseMove.SYNTHESIS,
                ResponseMove.INSIGHT,
                ResponseMove.REFLECTION,
            ],
            ConversationPhase.CLOSING: [
                ResponseMove.SYNTHESIS,
                ResponseMove.TRANSITION,
                ResponseMove.INSIGHT,
            ],
        }

        return move in allowed_moves.get(phase, [])

    def _update_state_from_response(
        self,
        state: PsychologistConversationState,
        response: AIResponseModel,
    ) -> None:
        """Update state based on the generated response."""
        # Update move history
        move = self._parse_move(response.response_move)
        state.last_move = move
        state.move_history.append(move)

        # Update synthesis tracking
        if move == ResponseMove.SYNTHESIS:
            state.last_synthesis_exchange = state.total_exchange_count

        # Add synthesis points
        if response.synthesis_points:
            for point in response.synthesis_points:
                if point not in state.synthesis_points:
                    state.synthesis_points.append(point)

        # Update core issue
        if response.core_issue:
            state.core_issue_identified = True
            state.core_issue_statement = response.core_issue

        # Add threads from response
        for thread_data in response.threads_detected:
            existing_topics = [t.topic.lower() for t in state.active_threads]
            topic = thread_data.get("topic", "")
            if topic.lower() not in existing_topics:
                state.active_threads.append(Thread(
                    id=f"t{len(state.active_threads) + 1}",
                    topic=topic,
                    type=thread_data.get("type", "mentioned"),
                    emotional_intensity=thread_data.get("emotional_intensity", "medium"),
                    relevance_score=thread_data.get("relevance_score", 0.5),
                    exploration_depth=0,
                    first_mentioned_exchange=state.total_exchange_count,
                    last_touched_exchange=state.total_exchange_count,
                    related_quotes=[thread_data.get("supporting_quote", "")],
                ))

        # Add observations from response
        for obs_data in response.observations_detected:
            existing_texts = [o.text.lower() for o in state.observations]
            obs_text = obs_data.get("text", "")
            if obs_text.lower() not in existing_texts:
                state.observations.append(Observation(
                    id=f"o{len(state.observations) + 1}",
                    type=obs_data.get("type", "pattern"),
                    text=obs_text,
                    confidence=obs_data.get("confidence", 0.7),
                    supporting_quotes=obs_data.get("supporting_quotes", []),
                    surfaced=False,
                ))

        # Mark observation as surfaced if it was an observation move
        if move == ResponseMove.OBSERVATION:
            unsurfaced = state.get_unsurfaced_observations()
            if unsurfaced:
                unsurfaced[0].surfaced = True
                unsurfaced[0].surfaced_at_exchange = state.total_exchange_count

        # Check for phase transition from response
        if response.should_transition:
            state.advance_phase(response.transition_reason or "AI indicated transition")


def create_initial_state() -> PsychologistConversationState:
    """Create a fresh conversation state for a new decision."""
    return PsychologistConversationState(
        current_phase=ConversationPhase.OPENING,
        phase_exchange_count=0,
        total_exchange_count=0,
        active_threads=[],
        observations=[],
        synthesis_points=[],
        move_history=[],
    )
