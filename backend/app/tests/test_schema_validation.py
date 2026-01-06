"""Tests for Pydantic schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.question import Question
from app.schemas.move import Move, CriteriaScores, Scripts, Branches, BranchResponse
from app.schemas.ai_responses import Phase1Response, Phase2Response


class TestQuestionSchema:
    """Tests for Question schema validation."""

    def test_valid_yes_no_question(self):
        """Test valid yes/no question passes validation."""
        q = Question(
            id="q1",
            question="Is she wearing headphones?",
            answer_type="yes_no",
            why_this_question="Headphones indicate she doesn't want to be interrupted",
            what_it_changes="If yes, suggests waiting or not approaching",
            priority=80,
        )
        assert q.id == "q1"
        assert q.answer_type == "yes_no"

    def test_valid_single_select_question(self):
        """Test valid single_select question with choices."""
        q = Question(
            id="q2",
            question="What's your relationship stage?",
            answer_type="single_select",
            choices=["just met", "talked a few times", "been on dates"],
            why_this_question="Stage affects appropriate next steps",
            what_it_changes="Determines level of directness in recommendations",
            priority=90,
        )
        assert q.choices == ["just met", "talked a few times", "been on dates"]

    def test_invalid_priority_too_high(self):
        """Test that priority over 100 fails validation."""
        with pytest.raises(ValidationError):
            Question(
                id="q3",
                question="Test question",
                answer_type="text",
                why_this_question="Test",
                what_it_changes="Test",
                priority=150,  # Invalid: > 100
            )

    def test_invalid_priority_negative(self):
        """Test that negative priority fails validation."""
        with pytest.raises(ValidationError):
            Question(
                id="q3",
                question="Test question",
                answer_type="text",
                why_this_question="Test",
                what_it_changes="Test",
                priority=-10,  # Invalid: < 0
            )


class TestMoveSchema:
    """Tests for Move schema validation."""

    def test_valid_move(self):
        """Test valid move passes validation."""
        move = Move(
            move_id="A",
            title="Direct approach",
            when_to_use="When she's between sets and seems open",
            tradeoff="Higher risk but clearer outcome",
            gentleman_score=85,
            risk_level="med",
            p_raw_progress=0.6,
            p_calibrated_progress=0.55,
            criteria_scores=CriteriaScores(
                self_respect=8,
                respect_for_her=9,
                clarity=8,
                leadership=7,
                warmth=7,
                progress=6,
                risk_management=7,
            ),
            scripts=Scripts(
                direct="Hey, I see you here often. Want to grab coffee sometime?",
                softer="I've been meaning to ask - do you know if they have good protein shakes here?",
            ),
            timing="After your workout, when she's also wrapping up",
            branches=Branches(
                warm=BranchResponse(
                    next_move="Exchange numbers and set a date",
                    script="Great! How about Thursday evening?",
                ),
                neutral=BranchResponse(
                    next_move="Leave door open, don't push",
                    script="No worries, maybe another time. See you around!",
                ),
                cold=BranchResponse(
                    next_move="Exit gracefully",
                    script="All good, have a great workout!",
                ),
            ),
        )
        assert move.move_id == "A"
        assert move.gentleman_score == 85

    def test_invalid_move_id(self):
        """Test that invalid move_id fails validation."""
        with pytest.raises(ValidationError):
            Move(
                move_id="D",  # Invalid: must be A, B, or C
                title="Test",
                when_to_use="Test",
                tradeoff="Test",
                gentleman_score=50,
                risk_level="low",
                p_raw_progress=0.5,
                p_calibrated_progress=0.5,
                criteria_scores=CriteriaScores(
                    self_respect=5,
                    respect_for_her=5,
                    clarity=5,
                    leadership=5,
                    warmth=5,
                    progress=5,
                    risk_management=5,
                ),
                scripts=Scripts(direct="Test", softer="Test"),
                timing="Test",
                branches=Branches(
                    warm=BranchResponse(next_move="Test", script="Test"),
                    neutral=BranchResponse(next_move="Test", script="Test"),
                    cold=BranchResponse(next_move="Test", script="Test"),
                ),
            )

    def test_invalid_criteria_score_too_high(self):
        """Test that criteria score > 10 fails validation."""
        with pytest.raises(ValidationError):
            CriteriaScores(
                self_respect=15,  # Invalid: > 10
                respect_for_her=5,
                clarity=5,
                leadership=5,
                warmth=5,
                progress=5,
                risk_management=5,
            )


class TestPhase1Response:
    """Tests for Phase1Response schema."""

    def test_valid_phase1_response(self):
        """Test valid Phase1Response."""
        response = Phase1Response(
            summary="User wants to approach someone at the gym",
            situation_type="gym_approach",
            mood_detected="anxious",
            questions=[
                Question(
                    id="q1",
                    question="Is she wearing headphones?",
                    answer_type="yes_no",
                    why_this_question="Indicates openness to interaction",
                    what_it_changes="Affects approach timing",
                    priority=90,
                ),
                Question(
                    id="q2",
                    question="Has she looked your way?",
                    answer_type="yes_no",
                    why_this_question="Indicates potential interest",
                    what_it_changes="Affects confidence of approach",
                    priority=85,
                ),
                Question(
                    id="q3",
                    question="Are you mid-workout?",
                    answer_type="yes_no",
                    why_this_question="Timing matters",
                    what_it_changes="Best moment to approach",
                    priority=70,
                ),
                Question(
                    id="q4",
                    question="Do you have a natural opener?",
                    answer_type="text",
                    why_this_question="Natural openers work better",
                    what_it_changes="Script suggestions",
                    priority=75,
                ),
                Question(
                    id="q5",
                    question="Is the gym crowded?",
                    answer_type="yes_no",
                    why_this_question="Affects social dynamics",
                    what_it_changes="Timing and approach style",
                    priority=60,
                ),
            ],
        )
        assert response.situation_type == "gym_approach"
        assert len(response.questions) == 5

    def test_invalid_too_few_questions(self):
        """Test that fewer than 5 questions fails validation."""
        with pytest.raises(ValidationError):
            Phase1Response(
                summary="Test",
                situation_type="gym_approach",
                mood_detected="calm",
                questions=[
                    Question(
                        id="q1",
                        question="Test?",
                        answer_type="yes_no",
                        why_this_question="Test",
                        what_it_changes="Test",
                        priority=50,
                    ),
                ],  # Only 1 question, minimum is 5
            )
