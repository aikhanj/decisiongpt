"""Tests for guardrail checking functionality."""

import pytest

from app.guardrails.checker import GuardrailChecker, check_move_guardrails, GuardrailViolation
from app.schemas.move import (
    Move,
    CriteriaScores,
    Scripts,
    Branches,
    BranchResponse,
)


def create_test_move(
    scripts_direct: str = "Hey, want to grab coffee?",
    scripts_softer: str = "I was wondering if you'd like to chat sometime",
    title: str = "Direct approach",
) -> Move:
    """Helper to create a test move with custom scripts."""
    return Move(
        move_id="A",
        title=title,
        when_to_use="When she seems open",
        tradeoff="Higher risk but clearer outcome",
        gentleman_score=80,
        risk_level="med",
        p_raw_progress=0.5,
        p_calibrated_progress=0.5,
        criteria_scores=CriteriaScores(
            self_respect=8,
            respect_for_her=8,
            clarity=8,
            leadership=7,
            warmth=7,
            progress=6,
            risk_management=7,
        ),
        scripts=Scripts(direct=scripts_direct, softer=scripts_softer),
        timing="After your workout",
        branches=Branches(
            warm=BranchResponse(next_move="Set a date", script="Great!"),
            neutral=BranchResponse(next_move="Leave door open", script="No worries!"),
            cold=BranchResponse(next_move="Exit gracefully", script="Have a great day!"),
        ),
    )


class TestGuardrailChecker:
    """Tests for guardrail checking."""

    def test_clean_move_passes(self):
        """Test that a clean move has no violations."""
        move = create_test_move()
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is True
        assert len([v for v in violations if v.severity == "error"]) == 0

    def test_rejects_persistence_pattern(self):
        """Test that persistence after rejection is caught."""
        move = create_test_move(
            scripts_direct="Keep texting until she responds",
        )
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False
        error_violations = [v for v in violations if v.severity == "error"]
        assert len(error_violations) > 0
        assert any("persistence" in v.description.lower() for v in error_violations)

    def test_rejects_jealousy_manipulation(self):
        """Test that jealousy tactics are caught."""
        move = create_test_move(
            scripts_direct="Make her jealous by posting with other women",
        )
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False
        error_violations = [v for v in violations if v.severity == "error"]
        assert any("jealous" in v.description.lower() for v in error_violations)

    def test_rejects_negging(self):
        """Test that negging/backhanded compliments are caught."""
        move = create_test_move(
            scripts_direct="You're pretty good-looking for someone your age. Neg her a little to build attraction.",
        )
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False

    def test_rejects_lying(self):
        """Test that deception is caught."""
        move = create_test_move(
            scripts_direct="Lie about having plans to seem busy",
        )
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False
        error_violations = [v for v in violations if v.severity == "error"]
        assert any("deception" in v.description.lower() for v in error_violations)

    def test_rejects_guilt_tripping(self):
        """Test that guilt manipulation is caught."""
        move = create_test_move(
            scripts_direct="Guilt her about not responding by mentioning you're hurt",
        )
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False

    def test_rejects_wall_of_text(self):
        """Test that overly long scripts are caught."""
        long_script = " ".join(["word"] * 100)  # 100 words
        move = create_test_move(scripts_direct=long_script)
        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False
        error_violations = [v for v in violations if v.severity == "error"]
        assert any("wall" in v.description.lower() or "words" in v.description.lower() for v in error_violations)

    def test_warns_on_triple_text(self):
        """Test that triple texting triggers a warning."""
        move = create_test_move(
            scripts_direct="Send a triple text to show you're interested",
        )
        is_valid, violations = check_move_guardrails(move)

        # Should be warning, not error
        warnings = [v for v in violations if v.severity == "warning"]
        assert any("triple" in v.description.lower() for v in warnings)

    def test_warns_on_late_night(self):
        """Test that late night messaging triggers a warning."""
        move = create_test_move(
            scripts_direct="Send a late night text to see if she's awake",
        )
        is_valid, violations = check_move_guardrails(move)

        # Should be warning, not error
        warnings = [v for v in violations if v.severity == "warning"]
        assert any("late night" in v.description.lower() for v in warnings)

    def test_checks_all_script_variants(self):
        """Test that both direct and softer scripts are checked."""
        # Bad direct script
        move = create_test_move(
            scripts_direct="Don't take no for an answer",
            scripts_softer="Clean softer script",
        )
        is_valid1, violations1 = check_move_guardrails(move)

        # Bad softer script
        move2 = create_test_move(
            scripts_direct="Clean direct script",
            scripts_softer="Keep texting until she responds",
        )
        is_valid2, violations2 = check_move_guardrails(move2)

        assert is_valid1 is False
        assert is_valid2 is False

    def test_checks_branch_scripts(self):
        """Test that branch scripts are also checked."""
        move = create_test_move()
        # Modify branch to have bad script
        move.branches.cold.script = "Don't take no for an answer"

        is_valid, violations = check_move_guardrails(move)

        assert is_valid is False
        cold_violations = [v for v in violations if "cold" in v.field]
        assert len(cold_violations) > 0

    def test_has_errors_helper(self):
        """Test has_errors helper method."""
        checker = GuardrailChecker()

        error_violation = GuardrailViolation(
            rule="test",
            severity="error",
            description="Test error",
            field="test",
        )
        warning_violation = GuardrailViolation(
            rule="test",
            severity="warning",
            description="Test warning",
            field="test",
        )

        assert checker.has_errors([error_violation]) is True
        assert checker.has_errors([warning_violation]) is False
        assert checker.has_errors([error_violation, warning_violation]) is True
        assert checker.has_errors([]) is False
