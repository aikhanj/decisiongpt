"""Tests for Brier score calculation."""

import pytest
from decimal import Decimal

from app.services.calibration_service import CalibrationService


class TestBrierScore:
    """Tests for Brier score computation."""

    def test_perfect_prediction_success(self):
        """Test Brier score of 0 for perfect prediction of success."""
        # Predicted 1.0 (100% success), actual success
        brier = CalibrationService.compute_brier_score(1.0, True)
        assert brier == 0.0

    def test_perfect_prediction_failure(self):
        """Test Brier score of 0 for perfect prediction of failure."""
        # Predicted 0.0 (0% success), actual failure
        brier = CalibrationService.compute_brier_score(0.0, False)
        assert brier == 0.0

    def test_worst_prediction_high_confidence_wrong(self):
        """Test Brier score of 1 for maximally wrong prediction."""
        # Predicted 1.0 (100% success), actual failure
        brier = CalibrationService.compute_brier_score(1.0, False)
        assert brier == 1.0

        # Predicted 0.0 (0% success), actual success
        brier = CalibrationService.compute_brier_score(0.0, True)
        assert brier == 1.0

    def test_uncertain_prediction_success(self):
        """Test Brier score for 50% prediction with success."""
        # Predicted 0.5 (50% success), actual success
        brier = CalibrationService.compute_brier_score(0.5, True)
        assert brier == 0.25  # (0.5 - 1)^2 = 0.25

    def test_uncertain_prediction_failure(self):
        """Test Brier score for 50% prediction with failure."""
        # Predicted 0.5 (50% success), actual failure
        brier = CalibrationService.compute_brier_score(0.5, False)
        assert brier == 0.25  # (0.5 - 0)^2 = 0.25

    def test_moderate_confidence_correct(self):
        """Test Brier score for moderately confident correct prediction."""
        # Predicted 0.7 (70% success), actual success
        brier = CalibrationService.compute_brier_score(0.7, True)
        assert pytest.approx(brier, 0.001) == 0.09  # (0.7 - 1)^2 = 0.09

    def test_moderate_confidence_incorrect(self):
        """Test Brier score for moderately confident incorrect prediction."""
        # Predicted 0.7 (70% success), actual failure
        brier = CalibrationService.compute_brier_score(0.7, False)
        assert pytest.approx(brier, 0.001) == 0.49  # (0.7 - 0)^2 = 0.49

    def test_low_confidence_correct(self):
        """Test Brier score for low confidence correct prediction."""
        # Predicted 0.3 (30% success), actual failure
        brier = CalibrationService.compute_brier_score(0.3, False)
        assert pytest.approx(brier, 0.001) == 0.09  # (0.3 - 0)^2 = 0.09

    def test_brier_score_range(self):
        """Test that Brier score is always between 0 and 1."""
        test_cases = [
            (0.0, True),
            (0.0, False),
            (0.25, True),
            (0.25, False),
            (0.5, True),
            (0.5, False),
            (0.75, True),
            (0.75, False),
            (1.0, True),
            (1.0, False),
        ]

        for prob, outcome in test_cases:
            brier = CalibrationService.compute_brier_score(prob, outcome)
            assert 0.0 <= brier <= 1.0, f"Brier score {brier} out of range for ({prob}, {outcome})"

    def test_brier_score_symmetry(self):
        """Test Brier score symmetry properties."""
        # Same distance from actual outcome should give same Brier score
        # (0.7 success when actual success) vs (0.3 success when actual failure)
        brier1 = CalibrationService.compute_brier_score(0.7, True)  # 0.3 away from 1
        brier2 = CalibrationService.compute_brier_score(0.3, False)  # 0.3 away from 0

        assert pytest.approx(brier1, 0.001) == pytest.approx(brier2, 0.001)

    def test_lower_brier_is_better(self):
        """Test that lower Brier scores indicate better predictions."""
        # More confident correct prediction should beat less confident
        confident_correct = CalibrationService.compute_brier_score(0.9, True)
        uncertain_correct = CalibrationService.compute_brier_score(0.5, True)

        assert confident_correct < uncertain_correct

        # Uncertain incorrect should beat confident incorrect
        confident_incorrect = CalibrationService.compute_brier_score(0.9, False)
        uncertain_incorrect = CalibrationService.compute_brier_score(0.5, False)

        assert uncertain_incorrect < confident_incorrect

    def test_brier_score_formula(self):
        """Test Brier score matches the mathematical formula."""
        # Brier score = (forecast - outcome)^2
        # where outcome is 1 for success, 0 for failure

        test_cases = [
            (0.6, True, (0.6 - 1) ** 2),
            (0.6, False, (0.6 - 0) ** 2),
            (0.2, True, (0.2 - 1) ** 2),
            (0.2, False, (0.2 - 0) ** 2),
            (0.85, True, (0.85 - 1) ** 2),
            (0.85, False, (0.85 - 0) ** 2),
        ]

        for prob, outcome, expected in test_cases:
            brier = CalibrationService.compute_brier_score(prob, outcome)
            assert pytest.approx(brier, 0.0001) == expected
