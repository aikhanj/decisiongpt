"""Heuristics Engine - Decision quality heuristics from decision science research."""

from app.schemas.question import CandidateQuestion
from app.schemas.canvas import CanvasState


class HeuristicsEngine:
    """
    Manages decision quality heuristic modules.

    Based on research from:
    - Kahneman (base rate, outside view)
    - Suzy Welch (10/10/10 framework)
    - Jeff Bezos (reversibility, regret minimization)
    - Gary Klein (pre-mortem)
    """

    def get_applicable_heuristics(
        self, canvas: CanvasState, phase: str
    ) -> list[CandidateQuestion]:
        """
        Return heuristic questions that should be asked based on context.

        Args:
            canvas: Current canvas state
            phase: Decision phase (clarify, moves, execute)

        Returns:
            List of heuristic questions to inject
        """
        applicable = []

        # Only apply clarify-phase heuristics in clarify phase
        if phase != "clarify":
            return applicable

        # Reversibility Check - Always valuable, asked early
        if self._should_ask_reversibility(canvas):
            applicable.append(self._get_reversibility_question())

        # Regret Minimization - For major life decisions
        if self._is_major_life_decision(canvas):
            applicable.append(self._get_regret_minimization_question())

        # 10/10/10 Framework - For emotionally charged decisions
        if self._is_emotionally_charged(canvas):
            applicable.append(self._get_10_10_10_question())

        # Base Rate Check - When predictions/outcomes mentioned
        if self._involves_predictions(canvas):
            applicable.append(self._get_base_rate_question())

        return applicable

    # ========================================================================
    # Reversibility Check (Bezos: One-way vs Two-way Door)
    # ========================================================================

    def _should_ask_reversibility(self, canvas: CanvasState) -> bool:
        """Check if reversibility question should be asked."""
        # Always valuable to know - could be asked early
        # Check if we haven't gathered this info yet (would be in context or metadata)
        context_str = " ".join(canvas.context_bullets).lower()
        return "reversible" not in context_str and "undo" not in context_str

    def _get_reversibility_question(self) -> CandidateQuestion:
        """Get reversibility check question."""
        return CandidateQuestion(
            id="heuristic_reversibility",
            question="How easily could you undo or reverse this decision if needed?",
            answer_type="single_select",
            choices=[
                "Easily reversible (can change course with little cost)",
                "Partially reversible (some sunk costs, but changeable)",
                "Mostly irreversible (very difficult or costly to undo)",
            ],
            why_this_question="Irreversible decisions (one-way doors) require more careful analysis than reversible ones (two-way doors)",
            what_it_changes="Determines how much scrutiny we apply - irreversible decisions get deeper analysis and more risk assessment",
            priority=80,
            targets_canvas_field="reversibility",
            critical_variable=True,
            heuristic_trigger="reversibility_check",
        )

    # ========================================================================
    # Regret Minimization (Bezos Framework)
    # ========================================================================

    def _is_major_life_decision(self, canvas: CanvasState) -> bool:
        """Detect if this is a major life decision."""
        # Look for keywords suggesting high stakes life decisions
        statement = (canvas.statement or "").lower()
        context_str = " ".join(canvas.context_bullets).lower()
        combined = f"{statement} {context_str}"

        major_keywords = [
            "career",
            "job",
            "relationship",
            "marriage",
            "divorce",
            "move",
            "relocate",
            "college",
            "university",
            "business",
            "startup",
            "quit",
            "leave",
        ]

        return any(keyword in combined for keyword in major_keywords)

    def _get_regret_minimization_question(self) -> CandidateQuestion:
        """Get regret minimization question."""
        return CandidateQuestion(
            id="heuristic_regret",
            question="Imagine yourself at age 80 looking back on this moment. Which option would you most regret NOT trying?",
            answer_type="text",
            why_this_question="This helps identify what truly matters to your future self, beyond short-term fears or convenience",
            what_it_changes="May reveal your authentic preference and can boost priority for options aligned with long-term fulfillment",
            priority=75,
            targets_canvas_field="criteria",
            heuristic_trigger="regret_minimization",
        )

    # ========================================================================
    # 10/10/10 Framework (Suzy Welch)
    # ========================================================================

    def _is_emotionally_charged(self, canvas: CanvasState) -> bool:
        """Detect if decision is emotionally charged."""
        # Look for emotional language or relationship/personal contexts
        statement = (canvas.statement or "").lower()
        context_str = " ".join(canvas.context_bullets).lower()
        combined = f"{statement} {context_str}"

        emotional_keywords = [
            "feel",
            "worry",
            "afraid",
            "anxious",
            "excited",
            "scared",
            "relationship",
            "family",
            "friend",
            "partner",
            "conflict",
            "stress",
        ]

        return any(keyword in combined for keyword in emotional_keywords)

    def _get_10_10_10_question(self) -> CandidateQuestion:
        """Get 10/10/10 framework question."""
        return CandidateQuestion(
            id="heuristic_10_10_10",
            question="Think about the consequences of each option: How will you feel in 10 minutes, 10 months, and 10 years?",
            answer_type="text",
            why_this_question="This balances immediate emotions with long-term consequences, helping you avoid decisions you'll regret",
            what_it_changes="Helps weight short-term vs long-term factors appropriately in option evaluation",
            priority=70,
            targets_canvas_field="criteria",
            heuristic_trigger="10_10_10",
        )

    # ========================================================================
    # Base Rate Check (Kahneman: Outside View)
    # ========================================================================

    def _involves_predictions(self, canvas: CanvasState) -> bool:
        """Detect if decision involves predictions about outcomes."""
        statement = (canvas.statement or "").lower()
        context_str = " ".join(canvas.context_bullets).lower()
        combined = f"{statement} {context_str}"

        prediction_keywords = [
            "succeed",
            "fail",
            "work out",
            "likely",
            "probably",
            "expect",
            "forecast",
            "project",
            "estimate",
            "predict",
            "should be",
            "will be",
        ]

        return any(keyword in combined for keyword in prediction_keywords)

    def _get_base_rate_question(self) -> CandidateQuestion:
        """Get base rate check question."""
        return CandidateQuestion(
            id="heuristic_base_rate",
            question="For situations like yours, what typically happens? What do statistics or past examples suggest about the likely outcome?",
            answer_type="text",
            why_this_question="We tend to over-rely on our specific case and ignore general statistics. The 'outside view' improves accuracy.",
            what_it_changes="Grounds expectations in reality by incorporating historical success rates into option evaluation",
            priority=65,
            targets_canvas_field="context",
            heuristic_trigger="base_rate_check",
        )

    # ========================================================================
    # Phase 3 Heuristics (Not implemented in MVP - for future)
    # ========================================================================

    def _get_premortem_question(self) -> CandidateQuestion:
        """
        Get pre-mortem question (Phase 3 - Execute).

        Note: This is triggered in Phase 3 (Execute), not Phase 1 (Clarify).
        Included here for completeness but not used in current MVP.
        """
        return CandidateQuestion(
            id="heuristic_premortem",
            question="Imagine it's 6 months from now and this decision was a failure. What went wrong?",
            answer_type="text",
            why_this_question="Pre-mortems increase ability to spot risks by 30% by making it safe to voice concerns",
            what_it_changes="Identifies risks and mitigation strategies before committing to the decision",
            priority=85,
            targets_canvas_field="risks",
            heuristic_trigger="premortem",
        )

    def _get_default_bias_question(self) -> CandidateQuestion:
        """
        Get default bias check question (Phase 2 - Moves).

        Note: This is more of a "ensure do-nothing option is included" check
        than a question to ask the user. Included for completeness.
        """
        return CandidateQuestion(
            id="heuristic_default_bias",
            question="What happens if you decide to do nothing or maintain the status quo?",
            answer_type="text",
            why_this_question="We often stick with defaults by inertia. Explicitly evaluating 'do nothing' helps overcome status quo bias.",
            what_it_changes="Ensures the default/status quo is consciously evaluated as an option",
            priority=60,
            targets_canvas_field="context",
            heuristic_trigger="default_bias",
        )
