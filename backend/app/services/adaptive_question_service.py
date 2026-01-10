"""Adaptive Question Service - Orchestrates VoI-based conversational questioning."""

import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.decision_node import DecisionNode
from app.schemas.question import (
    ConversationState,
    QuestioningMode,
    CandidateQuestion,
    Answer,
    QuestionWithAnswer,
    NextQuestionResponse,
)
from app.schemas.canvas import CanvasState, Criterion, Constraint
from app.services.question_value_scorer import QuestionValueScorer
from app.services.question_generator import QuestionGenerator
from app.services.heuristics_engine import HeuristicsEngine


class AdaptiveQuestionService:
    """
    Manages adaptive, VoI-based conversational questioning.

    Responsibilities:
    - Initialize questioning session
    - Select next question adaptively
    - Process answers and update canvas
    - Detect stopping conditions
    - Track conversation state
    """

    # Stopping thresholds
    MIN_VOI_THRESHOLD = 20.0  # Questions below this VoI are skipped
    MIN_QUESTIONS = 3  # Minimum questions before stopping

    def __init__(self, db: AsyncSession):
        self.db = db
        self.scorer = QuestionValueScorer()
        self.generator = QuestionGenerator()
        self.heuristics = HeuristicsEngine()

    async def initialize_questioning(
        self,
        node: DecisionNode,
        situation_text: str,
        decision_type: str,
        mode: QuestioningMode = QuestioningMode.QUICK,
    ) -> ConversationState:
        """
        Initialize adaptive questioning session.

        Steps:
        1. Extract initial canvas from situation
        2. Generate initial question pool
        3. Calculate VoI scores
        4. Select first question
        5. Initialize conversation state

        Args:
            node: The decision node
            situation_text: User's situation description
            decision_type: Type of decision (career, financial, etc.)
            mode: Questioning mode (quick or deep)

        Returns:
            Initialized conversation state
        """
        # Create initial canvas (basic - will be populated by answers)
        initial_canvas = CanvasState(
            statement=None,  # Will be filled by questions
            context_bullets=[],
            constraints=[],
            criteria=[],
            risks=[],
        )

        # Generate initial question pool
        question_pool = self.generator.generate_initial_question_pool(
            situation_text, decision_type, initial_canvas
        )

        # Add heuristic questions
        heuristic_questions = self.heuristics.get_applicable_heuristics(
            initial_canvas, "clarify"
        )
        question_pool.extend(heuristic_questions)

        # Calculate VoI scores for all questions
        for question in question_pool:
            question.voi_score = self.scorer.score_question(
                question, initial_canvas, ConversationState(
                    mode=mode,
                    question_cap=5 if mode == QuestioningMode.QUICK else 15,
                    canvas_state=initial_canvas.model_dump(),
                )
            )

        # Sort by VoI score (descending)
        question_pool.sort(key=lambda q: q.voi_score, reverse=True)

        # Select first question (highest VoI)
        first_question = question_pool[0] if question_pool else None

        if not first_question:
            raise ValueError("No questions generated - this shouldn't happen")

        # Initialize conversation state
        conversation_state = ConversationState(
            mode=mode,
            question_cap=5 if mode == QuestioningMode.QUICK else 15,
            questions_asked=0,
            candidate_questions=question_pool,
            asked_questions=[],
            current_question=first_question,
            canvas_state=initial_canvas.model_dump(),
            last_canvas_uncertainty=1.0,
            uncertainty_reduction_history=[],
            ready_for_options=False,
            stop_reason=None,
        )

        return conversation_state

    async def get_next_question(
        self,
        node: DecisionNode,
        previous_answer: Answer,
    ) -> NextQuestionResponse:
        """
        Process answer and select next question adaptively.

        Steps:
        1. Load conversation state
        2. Process answer and update canvas
        3. Calculate uncertainty reduction
        4. Check stopping conditions
        5. Recalculate VoI scores
        6. Select next question or signal completion

        Args:
            node: The decision node
            previous_answer: Answer to the previous question

        Returns:
            Next question response (with next question or completion signal)
        """
        # Load conversation state from node
        if not node.conversation_state_json:
            raise ValueError("Conversation state not initialized")

        conv_state_dict = node.conversation_state_json
        conversation_state = ConversationState(**conv_state_dict)

        # Get the previous question
        previous_question = conversation_state.current_question
        if not previous_question:
            raise ValueError("No current question in conversation state")

        # Process answer and update canvas
        updated_canvas, canvas_impact = self._process_answer(
            conversation_state.canvas_state,
            previous_question,
            previous_answer,
        )

        # Calculate uncertainty reduction
        previous_uncertainty = conversation_state.last_canvas_uncertainty
        current_uncertainty = self.scorer.calculate_canvas_uncertainty(
            CanvasState(**updated_canvas)
        )
        uncertainty_reduction = previous_uncertainty - current_uncertainty

        # Update conversation state
        conversation_state.asked_questions.append(
            QuestionWithAnswer(
                question=previous_question,
                answer=previous_answer,
                canvas_impact=canvas_impact,
            )
        )
        conversation_state.questions_asked += 1
        conversation_state.canvas_state = updated_canvas
        conversation_state.last_canvas_uncertainty = current_uncertainty
        conversation_state.uncertainty_reduction_history.append(uncertainty_reduction)

        # Check stopping conditions
        should_stop, stop_reason = self._should_stop_questioning(
            conversation_state, CanvasState(**updated_canvas)
        )

        if should_stop:
            conversation_state.ready_for_options = True
            conversation_state.stop_reason = stop_reason

            return NextQuestionResponse(
                next_question=None,
                canvas_update=updated_canvas,
                ready_for_options=True,
                questions_remaining=0,
                progress=1.0,
                stop_reason=stop_reason,
            )

        # Recalculate VoI scores for remaining questions
        remaining_questions = [
            q
            for q in conversation_state.candidate_questions
            if q.id not in [qa.question.id for qa in conversation_state.asked_questions]
        ]

        for question in remaining_questions:
            question.voi_score = self.scorer.score_question(
                question, CanvasState(**updated_canvas), conversation_state
            )

        # Sort by VoI score
        remaining_questions.sort(key=lambda q: q.voi_score, reverse=True)

        # Select next question (highest VoI above threshold)
        next_question = None
        for q in remaining_questions:
            if q.voi_score >= self.MIN_VOI_THRESHOLD:
                next_question = q
                break

        if not next_question:
            # All remaining questions have low VoI - stop
            conversation_state.ready_for_options = True
            conversation_state.stop_reason = "all_remaining_questions_low_voi"

            return NextQuestionResponse(
                next_question=None,
                canvas_update=updated_canvas,
                ready_for_options=True,
                questions_remaining=0,
                progress=1.0,
                stop_reason="all_remaining_questions_low_voi",
            )

        # Update current question
        conversation_state.current_question = next_question

        # Calculate progress (based on canvas completeness, not just question count)
        progress = 1.0 - current_uncertainty

        return NextQuestionResponse(
            next_question=next_question,
            canvas_update=updated_canvas,
            ready_for_options=False,
            questions_remaining=conversation_state.question_cap
            - conversation_state.questions_asked,
            progress=progress,
            stop_reason=None,
        )

    def _process_answer(
        self,
        canvas_dict: dict,
        question: CandidateQuestion,
        answer: Answer,
    ) -> tuple[dict, list[str]]:
        """
        Process answer and update canvas.

        Args:
            canvas_dict: Current canvas as dict
            question: The question that was answered
            answer: The user's answer

        Returns:
            (updated_canvas_dict, canvas_impact_fields)
        """
        canvas = CanvasState(**canvas_dict)
        canvas_impact = []

        field = question.targets_canvas_field
        answer_value = str(answer.value)

        # Update canvas based on which field the question targets
        if field == "statement":
            canvas.statement = answer_value
            canvas_impact.append("statement")

        elif field == "criteria":
            # Extract criteria from answer
            criteria = self._extract_criteria_from_answer(answer_value, question)
            canvas.criteria.extend(criteria)
            if criteria:
                canvas_impact.append(f"criteria (+{len(criteria)})")

        elif field == "constraints":
            # Extract constraints from answer
            constraints = self._extract_constraints_from_answer(answer_value, question)
            canvas.constraints.extend(constraints)
            if constraints:
                canvas_impact.append(f"constraints (+{len(constraints)})")

        elif field == "context":
            # Add to context bullets
            if answer_value and len(answer_value) > 10:
                canvas.context_bullets.append(answer_value)
                canvas_impact.append("context")

        elif field in ["timeline", "reversibility", "stakes"]:
            # Add to context as metadata
            canvas.context_bullets.append(f"{field.capitalize()}: {answer_value}")
            canvas_impact.append(field)

        return canvas.model_dump(), canvas_impact

    def _extract_criteria_from_answer(
        self, answer_text: str, question: CandidateQuestion
    ) -> list[Criterion]:
        """
        Extract criteria from answer text.

        For MVP: Simple heuristic extraction.
        Future: Use AI to parse complex answers.
        """
        criteria = []

        # If it's a single-select question about priorities
        if question.answer_type == "single_select" and question.choices:
            # The choice itself is the criterion
            if answer_text in question.choices:
                criteria.append(
                    Criterion(
                        id=f"cr_{uuid.uuid4().hex[:8]}",
                        name=answer_text,
                        weight=8,  # High weight since it's a stated priority
                    )
                )
        else:
            # Parse text for criteria
            # Simple heuristic: split by commas, "and", etc.
            parts = answer_text.replace(" and ", ",").split(",")
            for part in parts:
                part = part.strip()
                if len(part) > 3 and len(part) < 100:
                    criteria.append(
                        Criterion(
                            id=f"cr_{uuid.uuid4().hex[:8]}",
                            name=part,
                            weight=5,  # Default weight
                        )
                    )

        return criteria

    def _extract_constraints_from_answer(
        self, answer_text: str, question: CandidateQuestion
    ) -> list[Constraint]:
        """
        Extract constraints from answer text.

        For MVP: Simple heuristic extraction.
        Future: Use AI to parse complex answers.
        """
        constraints = []

        # Detect if it's a hard or soft constraint
        constraint_type = "hard"
        if any(
            word in answer_text.lower()
            for word in ["prefer", "would like", "nice to have", "ideally"]
        ):
            constraint_type = "soft"

        # For yes/no questions about constraints
        if question.answer_type == "yes_no":
            if answer_text.lower() in ["yes", "true", "1"]:
                # Extract constraint from question context
                constraint_text = question.question
                constraints.append(
                    Constraint(
                        id=f"c_{uuid.uuid4().hex[:8]}",
                        text=constraint_text,
                        type=constraint_type,
                    )
                )
        else:
            # Parse text for constraints
            # Simple heuristic: each sentence is a constraint
            if answer_text and len(answer_text) > 10:
                constraints.append(
                    Constraint(
                        id=f"c_{uuid.uuid4().hex[:8]}",
                        text=answer_text,
                        type=constraint_type,
                    )
                )

        return constraints

    def _should_stop_questioning(
        self, conversation_state: ConversationState, canvas: CanvasState
    ) -> tuple[bool, str]:
        """
        Determine if questioning should stop.

        Checks:
        1. Question cap reached
        2. Diminishing returns detected
        3. Critical fields populated + min questions asked
        4. All remaining questions have low VoI

        Returns:
            (should_stop, reason)
        """
        # Check 1: Question cap reached
        if conversation_state.questions_asked >= conversation_state.question_cap:
            return (True, "question_cap_reached")

        # Check 2: Diminishing returns
        if self.scorer.detect_diminishing_returns(conversation_state):
            return (True, "diminishing_returns")

        # Check 3: Critical fields populated + minimum questions
        critical_populated = canvas.statement is not None and len(canvas.criteria) >= 1

        if critical_populated and conversation_state.questions_asked >= self.MIN_QUESTIONS:
            # Check if remaining questions have low average VoI
            remaining_questions = [
                q
                for q in conversation_state.candidate_questions
                if q.id
                not in [qa.question.id for qa in conversation_state.asked_questions]
            ]

            if not remaining_questions:
                return (True, "no_remaining_questions")

            avg_voi = sum(q.voi_score for q in remaining_questions) / len(
                remaining_questions
            )

            if avg_voi < 25.0:
                return (True, "sufficient_information")

        return (False, None)
