import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.ai.prompts import SYSTEM_PROMPT, get_phase2_prompt, get_execution_plan_prompt
from app.config import get_settings
from app.guardrails import check_move_guardrails
from app.models import DecisionNode
from app.models.decision_node import NodePhase
from app.schemas.ai_responses import Phase2Response, ExecutionPlanResponse
from app.schemas.decision import Answer
from app.schemas.move import ExecutionPlan
from app.services.decision_service import DecisionService
from app.templates import get_template


class Phase2Service:
    """Service for Phase 2 (Moves) operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.decision_service = DecisionService(db)
        self.settings = get_settings()

    async def run_phase2(
        self, node: DecisionNode, answers: list[Answer], api_key: str
    ) -> tuple[DecisionNode, Phase2Response]:
        """
        Run Phase 2: Generate moves based on answers.

        Args:
            node: The decision node with Phase 1 data
            answers: User's answers to questions
            api_key: User's OpenAI API key

        Returns:
            Tuple of (updated node, Phase2Response with moves)
        """
        # Create AI gateway with user's API key
        ai = AIGateway(api_key)

        # Get context from node
        questions = node.questions_json.get("questions", [])
        summary = node.state_json.get("summary", "")
        mood_state = node.mood_state or "neutral"

        # Get template
        decision = await self.decision_service.get_decision(node.decision_id)
        situation_type = decision.situation_type or "generic_relationship_next_step"
        template = get_template(situation_type)

        # Format Q&A for prompt
        qa_text = self._format_qa(questions, answers)

        # Generate moves using AI
        prompt = get_phase2_prompt(
            summary=summary,
            situation_type=situation_type,
            mood_state=mood_state,
            questions_and_answers=qa_text,
            template_guardrails=template.get_template_context(),
        )

        response, metadata = await ai.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=Phase2Response,
            temperature=0.5,  # Slightly higher for creative scripts
        )

        # Validate moves against guardrails
        for move in response.moves:
            is_valid, violations = check_move_guardrails(
                move, template.guardrail_additions
            )
            if not is_valid:
                # Log violation but don't block - AI should have followed guidelines
                await self.decision_service.log_event(
                    decision_id=node.decision_id,
                    node_id=node.id,
                    event_type="guardrail_warning",
                    payload={
                        "move_id": move.move_id,
                        "violations": [
                            {"rule": v.rule, "description": v.description}
                            for v in violations
                        ],
                    },
                )

        # Update node
        updated_node = await self.decision_service.update_node(
            node,
            phase=NodePhase.MOVES.value,
            answers_json={"answers": [a.model_dump() for a in answers]},
            moves_json={
                "moves": [m.model_dump() for m in response.moves],
                "cooldown_recommended": response.cooldown_recommended,
                "cooldown_reason": response.cooldown_reason,
            },
            prompt_hash=metadata.get("prompt_hash"),
            model_version=metadata.get("model_version"),
        )

        # Log event
        await self.decision_service.log_event(
            decision_id=node.decision_id,
            node_id=node.id,
            event_type="phase2_completed",
            payload={
                "move_count": len(response.moves),
                "cooldown_recommended": response.cooldown_recommended,
            },
        )

        return updated_node, response

    async def generate_execution_plan(
        self, node: DecisionNode, move_id: str, api_key: str
    ) -> tuple[DecisionNode, ExecutionPlan]:
        """
        Generate execution plan for chosen move.

        Args:
            node: The decision node with moves
            move_id: The chosen move ID (A, B, or C)
            api_key: User's OpenAI API key

        Returns:
            Tuple of (updated node, ExecutionPlan)
        """
        # Create AI gateway with user's API key
        ai = AIGateway(api_key)

        # Find the chosen move
        moves = node.moves_json.get("moves", [])
        chosen_move = next((m for m in moves if m["move_id"] == move_id), None)
        if not chosen_move:
            raise ValueError(f"Move {move_id} not found")

        # Generate execution plan
        prompt = get_execution_plan_prompt(
            move_title=chosen_move["title"],
            move_details=chosen_move["when_to_use"],
            chosen_script=chosen_move["scripts"]["direct"],  # Default to direct
        )

        response, metadata = await ai.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=ExecutionPlanResponse,
            temperature=0.3,
        )

        execution_plan = ExecutionPlan(
            steps=response.steps,
            exact_message=response.exact_message,
            exit_line=response.exit_line,
            boundary_rule=response.boundary_rule,
        )

        # Update node
        updated_node = await self.decision_service.update_node(
            node,
            phase=NodePhase.EXECUTE.value,
            chosen_move_id=move_id,
            execution_plan_json=execution_plan.model_dump(),
        )

        # Log event
        await self.decision_service.log_event(
            decision_id=node.decision_id,
            node_id=node.id,
            event_type="move_chosen",
            payload={
                "move_id": move_id,
                "move_title": chosen_move["title"],
            },
        )

        return updated_node, execution_plan

    def _format_qa(self, questions: list[dict], answers: list[Answer]) -> str:
        """Format questions and answers for the prompt."""
        answer_map = {a.question_id: a.value for a in answers}
        lines = []
        for q in questions:
            qid = q["id"]
            question_text = q["question"]
            answer = answer_map.get(qid, "Not answered")
            lines.append(f"Q: {question_text}")
            lines.append(f"A: {answer}")
            lines.append("")
        return "\n".join(lines)
