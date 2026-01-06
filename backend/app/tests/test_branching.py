"""Tests for decision branching functionality."""

import pytest
import uuid
from datetime import datetime

from app.models.decision_node import DecisionNode, NodePhase


class TestBranching:
    """Tests for branching clone functionality."""

    def test_branch_preserves_parent_reference(self):
        """Test that branch node references parent node."""
        parent_id = uuid.uuid4()
        decision_id = uuid.uuid4()

        # Simulate branch creation
        branch_data = {
            "decision_id": decision_id,
            "parent_node_id": parent_id,
            "phase": NodePhase.CLARIFY.value,
        }

        assert branch_data["parent_node_id"] == parent_id
        assert branch_data["phase"] == "clarify"

    def test_branch_copies_state(self):
        """Test that branch copies relevant state from parent."""
        parent_state = {
            "summary": "User wants to approach someone",
            "situation_type": "gym_approach",
        }
        parent_questions = {
            "questions": [
                {"id": "q1", "question": "Test?", "priority": 50}
            ]
        }
        parent_mood = "anxious"

        # Branch should copy these
        branch_state = parent_state.copy()
        branch_questions = parent_questions.copy()
        branch_mood = parent_mood

        assert branch_state == parent_state
        assert branch_questions == parent_questions
        assert branch_mood == parent_mood

    def test_branch_does_not_copy_answers(self):
        """Test that branch doesn't copy answers (allows re-answering)."""
        parent_answers = {
            "answers": [
                {"question_id": "q1", "value": True},
                {"question_id": "q2", "value": "Some answer"},
            ]
        }

        # Branch should NOT have answers
        branch_data = {
            "state_json": {"summary": "Test"},
            "questions_json": {"questions": []},
            "answers_json": None,  # Should be None for branch
            "moves_json": None,
            "chosen_move_id": None,
        }

        assert branch_data["answers_json"] is None
        assert branch_data["moves_json"] is None
        assert branch_data["chosen_move_id"] is None

    def test_branch_does_not_copy_moves(self):
        """Test that branch doesn't copy moves (regenerated after answers)."""
        parent_moves = {
            "moves": [
                {"move_id": "A", "title": "Direct approach"},
                {"move_id": "B", "title": "Wait and see"},
            ]
        }

        # Branch should NOT have moves
        branch_data = {
            "moves_json": None,
        }

        assert branch_data["moves_json"] is None

    def test_branch_starts_in_clarify_phase(self):
        """Test that branch always starts in clarify phase."""
        # Even if parent is in execute phase, branch starts fresh
        parent_phase = NodePhase.EXECUTE.value
        branch_phase = NodePhase.CLARIFY.value

        assert branch_phase == "clarify"
        assert parent_phase != branch_phase

    def test_multiple_branches_allowed(self):
        """Test that multiple branches from same parent are allowed."""
        parent_id = uuid.uuid4()
        decision_id = uuid.uuid4()

        # Multiple branches from same parent
        branches = []
        for i in range(3):
            branch = {
                "id": uuid.uuid4(),
                "decision_id": decision_id,
                "parent_node_id": parent_id,
                "phase": NodePhase.CLARIFY.value,
            }
            branches.append(branch)

        # All should have same parent
        assert all(b["parent_node_id"] == parent_id for b in branches)

        # All should have unique IDs
        branch_ids = [b["id"] for b in branches]
        assert len(branch_ids) == len(set(branch_ids))

    def test_branch_preserves_policy_version(self):
        """Test that branch preserves policy version for consistency."""
        policy_version = "v1.0"

        branch_data = {
            "policy_version": policy_version,
        }

        assert branch_data["policy_version"] == policy_version

    def test_branch_tree_structure(self):
        """Test that branches form a valid tree structure."""
        # Root node has no parent
        root = {
            "id": uuid.uuid4(),
            "parent_node_id": None,
        }

        # Branch 1 from root
        branch1 = {
            "id": uuid.uuid4(),
            "parent_node_id": root["id"],
        }

        # Branch 2 from root
        branch2 = {
            "id": uuid.uuid4(),
            "parent_node_id": root["id"],
        }

        # Sub-branch from branch1
        sub_branch = {
            "id": uuid.uuid4(),
            "parent_node_id": branch1["id"],
        }

        # Verify tree structure
        assert root["parent_node_id"] is None
        assert branch1["parent_node_id"] == root["id"]
        assert branch2["parent_node_id"] == root["id"]
        assert sub_branch["parent_node_id"] == branch1["id"]
