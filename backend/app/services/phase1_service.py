import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.gateway import AIGateway
from app.ai.prompts import SYSTEM_PROMPT, get_phase1_prompt
from app.config import get_settings
from app.models import DecisionNode
from app.models.decision_node import NodePhase
from app.schemas.ai_responses import Phase1Response
from app.services.decision_service import DecisionService
from app.templates import get_template


class Phase1Service:
    """Service for Phase 1 (Clarify) operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.decision_service = DecisionService(db)
        self.settings = get_settings()

    async def run_phase1(
        self, user_id: uuid.UUID, situation_text: str, api_key: str
    ) -> tuple[DecisionNode, Phase1Response]:
        """
        Run Phase 1: Analyze situation and generate questions.

        Args:
            user_id: ID of the user
            situation_text: User's description of the situation
            api_key: User's OpenAI API key

        Returns:
            Tuple of (created node, Phase1Response with questions)
        """
        # Create AI gateway with user's API key
        ai = AIGateway(api_key)

        # Generate questions using AI
        prompt = get_phase1_prompt(situation_text)

        response, metadata = await ai.generate(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=Phase1Response,
            temperature=0.3,
        )

        # Get template for additional context
        template = get_template(response.situation_type)

        # Create decision
        decision = await self.decision_service.create_decision(
            user_id=user_id,
            situation_text=situation_text,
            situation_type=response.situation_type,
        )

        # Create node with Phase 1 results
        node = await self.decision_service.create_node(
            decision_id=decision.id,
            phase=NodePhase.CLARIFY,
            state_json={"summary": response.summary},
            questions_json={
                "questions": [q.model_dump() for q in response.questions]
            },
            mood_state=response.mood_detected,
            metadata_json={
                "template": template.name,
            },
            policy_version=self.settings.policy_version,
            prompt_hash=metadata.get("prompt_hash"),
            model_version=metadata.get("model_version"),
        )

        # Log event
        await self.decision_service.log_event(
            decision_id=decision.id,
            node_id=node.id,
            event_type="phase1_completed",
            payload={
                "question_count": len(response.questions),
                "situation_type": response.situation_type,
                "mood_detected": response.mood_detected,
            },
        )

        return node, response
