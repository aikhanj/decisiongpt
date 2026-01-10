"""Question Value Scorer - Calculates Value of Information (VoI) for questions."""

from app.schemas.question import CandidateQuestion, ConversationState
from app.schemas.canvas import CanvasState


class QuestionValueScorer:
    """
    Calculates Value of Information (VoI) for candidate questions.

    VoI Formula:
    VoI = (Critical_Weight × Critical_Score) +
          (Uncertainty_Weight × Uncertainty_Score) +
          (Impact_Weight × Impact_Score) -
          (Redundancy_Penalty)

    Weights: Critical=40%, Uncertainty=30%, Impact=20%, Redundancy=10%
    """

    # Scoring weights
    CRITICAL_WEIGHT = 0.4
    UNCERTAINTY_WEIGHT = 0.3
    IMPACT_WEIGHT = 0.2
    REDUNDANCY_WEIGHT = 0.1

    # Diminishing returns threshold
    DIMINISHING_RETURNS_THRESHOLD = 0.10  # 10% average reduction

    def score_question(
        self,
        question: CandidateQuestion,
        current_canvas: CanvasState,
        conversation_state: ConversationState,
    ) -> float:
        """
        Calculate VoI score (0-100) for a question.

        Args:
            question: The candidate question to score
            current_canvas: Current state of the decision canvas
            conversation_state: Current conversation state

        Returns:
            VoI score between 0 and 100
        """
        critical_score = self._calculate_critical_score(question, current_canvas)
        uncertainty_score = self._calculate_uncertainty_reduction(question, current_canvas)
        impact_score = self._calculate_impact_score(question, current_canvas)
        redundancy_penalty = self._calculate_redundancy(question, conversation_state)

        voi = (
            self.CRITICAL_WEIGHT * critical_score
            + self.UNCERTAINTY_WEIGHT * uncertainty_score
            + self.IMPACT_WEIGHT * impact_score
            - self.REDUNDANCY_WEIGHT * redundancy_penalty
        )

        # Clamp to 0-100 range
        return max(0.0, min(100.0, voi))

    def _calculate_critical_score(
        self, question: CandidateQuestion, canvas: CanvasState
    ) -> float:
        """
        Score based on whether question fills critical missing field.

        Critical fields (scored high):
        - Decision statement (if missing)
        - At least one criterion
        - At least one hard constraint
        - Stakes/reversibility

        Returns: 0-100
        """
        # If already marked as critical, give it high score
        if question.critical_variable:
            return 100.0

        field = question.targets_canvas_field

        # Check if field is critical and missing
        if field == "statement":
            return 100.0 if not canvas.statement else 20.0

        elif field == "criteria":
            return 100.0 if len(canvas.criteria) == 0 else 30.0

        elif field == "constraints":
            # Hard constraints are more critical
            has_hard = any(c.type == "hard" for c in canvas.constraints)
            if len(canvas.constraints) == 0:
                return 90.0
            elif not has_hard:
                return 50.0
            else:
                return 20.0

        elif field in ["reversibility", "timeline", "stakes"]:
            # These are important metadata fields
            return 70.0

        elif field == "context":
            # Context is helpful but not critical
            return 40.0

        else:
            # Other fields are less critical
            return 20.0

    def _calculate_uncertainty_reduction(
        self, question: CandidateQuestion, canvas: CanvasState
    ) -> float:
        """
        Estimate how much this question reduces decision uncertainty.

        Heuristic:
        - Questions about criteria/constraints: High impact (80)
        - Questions that could eliminate options: Very high (90)
        - Questions about already-clear topics: Low (20)

        Returns: 0-100
        """
        field = question.targets_canvas_field

        # Questions that define what matters are high value
        if field in ["criteria", "constraints"]:
            # If we have few criteria/constraints, more valuable
            if field == "criteria" and len(canvas.criteria) < 2:
                return 85.0
            elif field == "constraints" and len(canvas.constraints) < 1:
                return 90.0  # Constraints can eliminate options
            else:
                return 50.0  # Still useful but lower priority

        # Statement definition is critical for framing
        elif field == "statement":
            return 100.0 if not canvas.statement else 30.0

        # Metadata fields help with heuristics
        elif field in ["reversibility", "stakes", "timeline"]:
            return 70.0

        # Context is helpful but less impactful
        elif field == "context":
            return 40.0

        else:
            return 30.0

    def _calculate_impact_score(
        self, question: CandidateQuestion, canvas: CanvasState
    ) -> float:
        """
        Score based on expected impact on option generation/ranking.

        High impact:
        - Could rule out entire option categories (90)
        - Affects primary criterion weight (80)
        - Reveals hard constraint (85)

        Low impact:
        - Adds minor context (30)
        - Clarifies already-weighted criterion (40)

        Returns: 0-100
        """
        field = question.targets_canvas_field

        # Hard constraints can eliminate options
        if field == "constraints":
            # Check if this might be a hard constraint
            if "must" in question.question.lower() or "required" in question.question.lower():
                return 85.0
            else:
                return 60.0

        # Criteria affect option scoring
        elif field == "criteria":
            # First few criteria are most impactful
            num_criteria = len(canvas.criteria)
            if num_criteria == 0:
                return 90.0
            elif num_criteria < 3:
                return 70.0
            else:
                return 40.0

        # Statement frames everything
        elif field == "statement":
            return 95.0 if not canvas.statement else 20.0

        # Metadata impacts heuristics
        elif field in ["reversibility", "stakes"]:
            return 65.0

        else:
            return 35.0

    def _calculate_redundancy(
        self, question: CandidateQuestion, conversation_state: ConversationState
    ) -> float:
        """
        Calculate redundancy penalty (0-100).

        Higher penalty if:
        - Similar questions already asked
        - Same canvas field already thoroughly covered
        - Question targets already-populated field with many values

        Returns: 0-100 (higher = more redundant)
        """
        field = question.targets_canvas_field

        # Check how many questions already asked about this field
        questions_on_field = sum(
            1
            for qa in conversation_state.asked_questions
            if qa.question.targets_canvas_field == field
        )

        if questions_on_field == 0:
            return 0.0  # No redundancy
        elif questions_on_field == 1:
            return 20.0  # Some redundancy
        elif questions_on_field == 2:
            return 50.0  # High redundancy
        else:
            return 80.0  # Very high redundancy

    def detect_diminishing_returns(self, conversation_state: ConversationState) -> bool:
        """
        Detect if recent questions yielded little new information.

        Check:
        - Last 3 questions reduced uncertainty by < threshold
        - Canvas state stable (no significant changes)

        Returns: True if diminishing returns detected
        """
        history = conversation_state.uncertainty_reduction_history

        # Need at least 3 data points
        if len(history) < 3:
            return False

        # Get last 3 uncertainty reductions
        recent_reductions = history[-3:]

        # Calculate average reduction
        avg_reduction = sum(recent_reductions) / len(recent_reductions)

        # Check if below threshold
        return avg_reduction < self.DIMINISHING_RETURNS_THRESHOLD

    def calculate_canvas_uncertainty(self, canvas: CanvasState) -> float:
        """
        Calculate current canvas uncertainty (0-1).

        Lower uncertainty = more fields populated and complete.

        Returns: 0.0 (complete) to 1.0 (empty)
        """
        # Critical fields weights
        weights = {
            "statement": 0.25,
            "criteria": 0.30,
            "constraints": 0.20,
            "context": 0.15,
            "risks": 0.10,
        }

        uncertainty = 0.0

        # Statement
        if not canvas.statement:
            uncertainty += weights["statement"]

        # Criteria (need at least 2)
        if len(canvas.criteria) == 0:
            uncertainty += weights["criteria"]
        elif len(canvas.criteria) == 1:
            uncertainty += weights["criteria"] * 0.5

        # Constraints (need at least 1)
        if len(canvas.constraints) == 0:
            uncertainty += weights["constraints"]

        # Context (want some bullets)
        if len(canvas.context_bullets) == 0:
            uncertainty += weights["context"]
        elif len(canvas.context_bullets) < 2:
            uncertainty += weights["context"] * 0.5

        # Risks (optional but good to have)
        if len(canvas.risks) == 0:
            uncertainty += weights["risks"]

        return uncertainty
