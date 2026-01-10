"""Chat service for Decision Canvas conversational flow."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.models.decision import Decision
from app.models.decision_node import DecisionNode, NodePhase
from app.ai.gateway import AIGateway
from app.ai.prompts.system import CHAT_SYSTEM_PROMPT
from app.ai.prompts.phase1 import get_phase1_prompt, get_chat_clarify_prompt
from app.ai.prompts.phase2 import get_phase2_prompt, get_execution_plan_prompt, get_chat_options_prompt
from app.ai.advisors.classifier import AdvisorClassifier, ClassificationResult
from app.ai.advisors.registry import get_advisor, Advisor
from app.ai.advisors.prompts.core_personality import build_enhanced_system_prompt
from app.services.psychologist_engine import PsychologistEngine, create_initial_state
from app.schemas.psychologist_state import PsychologistConversationState
from app.schemas.canvas import (
    ChatMessage,
    CanvasState,
    Option,
    CommitPlan,
    ChatResponse,
    AdvisorInfo,
)
from app.services.decision_service import DecisionService
from app.services.user_context_service import UserContextService
from app.services.observation_service import ObservationService


class ChatService:
    """Service for handling chat-based decision flow."""

    def __init__(self, db: AsyncSession, api_key: str):
        self.db = db
        self.api_key = api_key
        self.ai = AIGateway(api_key)
        self.decision_service = DecisionService(db)
        self.classifier = AdvisorClassifier(api_key)
        self.user_context_service = UserContextService(db)
        self.observation_service = ObservationService(db, api_key)
        self.psychologist_engine = PsychologistEngine(self.ai)

    async def start_decision(
        self,
        user_id: uuid.UUID,
        situation_text: str,
    ) -> tuple[Decision, DecisionNode, dict]:
        """Start a new decision with initial analysis.

        Returns:
            Tuple of (decision, node, phase1_response)
        """
        # Create decision
        decision = await self.decision_service.create_decision(
            user_id=user_id,
            situation_text=situation_text,
        )

        # Get initial analysis from AI
        phase1_response = await self._run_phase1(situation_text)

        # Create initial chat messages
        initial_messages = [
            {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "user",
                "content": situation_text,
                "timestamp": datetime.utcnow().isoformat(),
            },
            {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": self._format_phase1_response(phase1_response),
                "timestamp": datetime.utcnow().isoformat(),
            },
        ]

        # Create node with initial state
        node = await self.decision_service.create_node(
            decision_id=decision.id,
            phase=NodePhase.CLARIFY,
            state_json={
                "summary": phase1_response.get("summary"),
                "decision_type": phase1_response.get("decision_type"),
            },
            questions_json={"questions": phase1_response.get("questions", [])},
            chat_messages_json=initial_messages,
            canvas_state_json=phase1_response.get("canvas_state", {}),
        )

        # Update decision with title from summary
        decision.title = phase1_response.get("summary", situation_text[:50])
        decision.situation_type = phase1_response.get("decision_type", "other")
        await self.db.commit()

        return decision, node, phase1_response

    async def send_message(
        self,
        node: DecisionNode,
        user_message: str,
    ) -> ChatResponse:
        """Process a user message and return AI response with canvas updates."""
        # Get current state
        chat_messages = node.chat_messages_json or []
        canvas_state = node.canvas_state_json or {}
        questions = (node.questions_json or {}).get("questions", [])
        options = (node.moves_json or {}).get("options", [])
        user_id = node.decision.user_id

        # Build user context for personalization
        user_context = await self.user_context_service.build_user_context(
            user_id,
            decision_context=node.decision.situation_text,
        )

        # Classify the query to select the appropriate advisor
        classification = await self.classifier.classify(user_message)
        advisor = get_advisor(classification.advisor_id) or get_advisor("general")

        # Add user message
        user_msg = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat(),
        }
        chat_messages.append(user_msg)

        # Determine phase and get appropriate response using the selected advisor
        phase = node.phase
        response_data = {}

        if phase == NodePhase.CLARIFY:
            response_data = await self._handle_clarify_message(
                node,
                user_message,
                chat_messages,
                canvas_state,
                questions,
                advisor,
                user_context,
            )
        elif phase == NodePhase.MOVES:
            response_data = await self._handle_options_message(
                chat_messages,
                canvas_state,
                options,
                advisor,
                user_context,
            )
        else:
            # EXECUTE phase - general conversation
            response_data = await self._handle_general_message(
                chat_messages,
                canvas_state,
                advisor,
                user_context,
            )

        # Create assistant message with optional question metadata
        assistant_msg = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": "assistant",
            "content": response_data.get("response", "I understand. Let me help you with that."),
            "timestamp": datetime.utcnow().isoformat(),
        }
        # Add question metadata if present (for tooltip and quick reply options)
        if response_data.get("question_reason"):
            assistant_msg["question_reason"] = response_data["question_reason"]
        if response_data.get("suggested_options"):
            assistant_msg["suggested_options"] = response_data["suggested_options"]
        chat_messages.append(assistant_msg)

        # Update canvas state
        canvas_update = response_data.get("canvas_state_update", {}) or response_data.get("canvas_state", {})
        if canvas_update:
            canvas_state = self._merge_canvas_state(canvas_state, canvas_update)

        # Check for phase transitions
        new_phase = phase
        new_options = options
        commit_plan = None

        if response_data.get("ready_for_options"):
            # Transition to options phase
            new_phase = NodePhase.MOVES
            options_response = await self._generate_options(node, canvas_state)
            new_options = options_response.get("options", [])
            canvas_state = self._merge_canvas_state(
                canvas_state,
                options_response.get("canvas_state_update", {})
            )
            # Add options announcement message
            options_msg = {
                "id": f"msg_{uuid.uuid4().hex[:8]}",
                "role": "assistant",
                "content": self._format_options_message(new_options),
                "timestamp": datetime.utcnow().isoformat(),
            }
            chat_messages.append(options_msg)

        if response_data.get("user_chose_option"):
            # Transition to execute phase
            chosen_id = response_data["user_chose_option"]
            chosen_option = next(
                (o for o in options if o.get("id") == chosen_id),
                options[0] if options else None
            )
            if chosen_option:
                new_phase = NodePhase.EXECUTE
                commit_response = await self._generate_commit_plan(
                    chosen_option,
                    canvas_state,
                )
                commit_plan = commit_response.get("commit_plan")
                canvas_state = self._merge_canvas_state(
                    canvas_state,
                    commit_response.get("canvas_state_update", {})
                )
                # Add commit plan message
                commit_msg = {
                    "id": f"msg_{uuid.uuid4().hex[:8]}",
                    "role": "assistant",
                    "content": self._format_commit_message(commit_plan),
                    "timestamp": datetime.utcnow().isoformat(),
                }
                chat_messages.append(commit_msg)

        # Update node
        node.chat_messages_json = chat_messages
        node.canvas_state_json = canvas_state
        node.phase = new_phase
        if new_options != options:
            node.moves_json = {"options": new_options}
        if commit_plan:
            node.execution_plan_json = commit_plan
            node.chosen_move_id = commit_plan.get("chosen_option_id")

        # Flag JSON fields as modified so SQLAlchemy detects the changes
        flag_modified(node, "chat_messages_json")
        flag_modified(node, "canvas_state_json")
        await self.db.commit()

        # Build response with defensive parsing
        try:
            parsed_canvas = CanvasState(**canvas_state) if canvas_state else CanvasState()
        except Exception as e:
            print(f"[WARN] Failed to parse canvas_state: {e}, using empty")
            parsed_canvas = CanvasState()

        try:
            parsed_options = [Option(**o) for o in new_options] if new_options else None
        except Exception as e:
            print(f"[WARN] Failed to parse options: {e}, using None")
            parsed_options = None

        try:
            parsed_commit = CommitPlan(**commit_plan) if commit_plan else None
        except Exception as e:
            print(f"[WARN] Failed to parse commit_plan: {e}, using None")
            parsed_commit = None

        return ChatResponse(
            message=ChatMessage(
                id=assistant_msg["id"],
                role="assistant",
                content=assistant_msg["content"],
                timestamp=datetime.fromisoformat(assistant_msg["timestamp"]),
                question_reason=assistant_msg.get("question_reason"),
                suggested_options=assistant_msg.get("suggested_options"),
            ),
            canvas_state=parsed_canvas,
            phase=new_phase,
            questions=questions if new_phase == NodePhase.CLARIFY else None,
            options=parsed_options,
            commit_plan=parsed_commit,
            advisor=AdvisorInfo(
                id=advisor.id,
                name=advisor.name,
                avatar=advisor.avatar,
            ) if advisor else None,
        )

    async def choose_option(
        self,
        node: DecisionNode,
        option_id: str,
    ) -> ChatResponse:
        """User explicitly chooses an option."""
        options = (node.moves_json or {}).get("options", [])
        canvas_state = node.canvas_state_json or {}

        chosen_option = next(
            (o for o in options if o.get("id") == option_id),
            None
        )

        if not chosen_option:
            raise ValueError(f"Option {option_id} not found")

        # Generate commit plan
        commit_response = await self._generate_commit_plan(chosen_option, canvas_state)
        commit_plan = commit_response.get("commit_plan")
        canvas_state = self._merge_canvas_state(
            canvas_state,
            commit_response.get("canvas_state_update", {})
        )

        # Add system message about choice
        chat_messages = node.chat_messages_json or []
        choice_msg = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": "system",
            "content": f"User chose Option {option_id}: {chosen_option.get('title')}",
            "timestamp": datetime.utcnow().isoformat(),
        }
        chat_messages.append(choice_msg)

        commit_msg = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": "assistant",
            "content": self._format_commit_message(commit_plan),
            "timestamp": datetime.utcnow().isoformat(),
        }
        chat_messages.append(commit_msg)

        # Update node
        node.phase = NodePhase.EXECUTE
        node.chosen_move_id = option_id
        node.execution_plan_json = commit_plan
        node.chat_messages_json = chat_messages
        node.canvas_state_json = canvas_state

        # Flag JSON fields as modified so SQLAlchemy detects the changes
        flag_modified(node, "chat_messages_json")
        flag_modified(node, "canvas_state_json")
        await self.db.commit()

        # Build response with defensive parsing
        try:
            parsed_canvas = CanvasState(**canvas_state) if canvas_state else CanvasState()
        except Exception as e:
            print(f"[WARN] Failed to parse canvas_state: {e}, using empty")
            parsed_canvas = CanvasState()

        try:
            parsed_options = [Option(**o) for o in options] if options else None
        except Exception as e:
            print(f"[WARN] Failed to parse options: {e}, using None")
            parsed_options = None

        try:
            parsed_commit = CommitPlan(**commit_plan) if commit_plan else None
        except Exception as e:
            print(f"[WARN] Failed to parse commit_plan: {e}, using None")
            parsed_commit = None

        return ChatResponse(
            message=ChatMessage(
                id=commit_msg["id"],
                role="assistant",
                content=commit_msg["content"],
                timestamp=datetime.fromisoformat(commit_msg["timestamp"]),
            ),
            canvas_state=parsed_canvas,
            phase=NodePhase.EXECUTE,
            options=parsed_options,
            commit_plan=parsed_commit,
        )

    async def _run_phase1(self, situation_text: str) -> dict:
        """Run Phase 1 analysis."""
        from app.schemas.ai_responses import Phase1Response

        prompt = get_phase1_prompt(situation_text)
        response, _ = await self.ai.generate(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=Phase1Response,
            call_location="chat_service.run_phase1_analysis",
        )
        return response.model_dump()

    async def _handle_clarify_message(
        self,
        node: DecisionNode,
        user_message: str,
        chat_messages: list[dict],
        canvas_state: dict,
        questions: list[dict],
        advisor: Advisor,
        user_context: Optional[str] = None,
    ) -> dict:
        """Handle a message during clarify phase using the Psychologist Engine.

        The Psychologist Engine provides:
        - Phase-aware conversation flow (Opening → Exploration → Deepening → Insight → Closing)
        - Thread tracking (follow interesting topics deeper, not wider)
        - Forced synthesis (must reflect back every 3 exchanges)
        - Pattern/contradiction detection
        - Response validation (no shallow "What kind of X?" questions)
        """
        import logging
        logger = logging.getLogger(__name__)

        # Load or create psychologist conversation state
        psychologist_state = None
        if node.conversation_state_json:
            try:
                psychologist_state = PsychologistConversationState(
                    **node.conversation_state_json
                )
            except Exception as e:
                logger.warning(f"Failed to load psychologist state: {e}, creating new")
                psychologist_state = None

        if psychologist_state is None:
            psychologist_state = create_initial_state()

        # Use the psychologist engine to process the message
        try:
            result = await self.psychologist_engine.process_message(
                user_message=user_message,
                situation_text=node.decision.situation_text,
                chat_history=chat_messages,
                current_state=psychologist_state,
            )

            # Save updated state back to node (use mode='json' for JSON-compatible enum values)
            node.conversation_state_json = result.state.model_dump(mode='json')
            flag_modified(node, "conversation_state_json")

            # Log phase info for debugging
            logger.info(
                f"Psychologist: Phase={result.state.current_phase.value}, "
                f"Move={result.response_move.value}, "
                f"Threads={len(result.state.active_threads)}, "
                f"Observations={len(result.state.observations)}"
            )

            # Build canvas state update from synthesis points
            canvas_update = {}
            if result.synthesis_points:
                existing_context = canvas_state.get("context_bullets", [])
                new_context = [
                    p for p in result.synthesis_points
                    if p not in existing_context
                ]
                if new_context:
                    canvas_update["context_bullets"] = existing_context + new_context

            if result.core_issue:
                canvas_update["statement"] = result.core_issue

            return {
                "response": result.response,
                "question_reason": result.question_reason,
                "suggested_options": result.suggested_options,
                "canvas_state": canvas_update if canvas_update else None,
                "ready_for_options": result.ready_for_options,
            }

        except Exception as e:
            # Fallback to original prompt-based approach if engine fails
            logger.error(f"Psychologist engine failed: {e}, falling back to basic prompt")

            prompt = get_chat_clarify_prompt(
                node.decision.situation_text,
                chat_messages,
                canvas_state,
            )

            from pydantic import BaseModel, Field
            from typing import Optional as Opt

            class ClarifyChatResponse(BaseModel):
                response: str
                question_reason: Opt[str] = Field(
                    None, description="Why this question matters (shown as tooltip)"
                )
                suggested_options: Opt[list[str]] = Field(
                    None, description="Quick reply options for the user"
                )
                canvas_state: Opt[dict] = None
                ready_for_options: bool = False

            enhanced_prompt = build_enhanced_system_prompt(
                advisor.system_prompt,
                user_context=user_context,
                include_observation_prompt=True,
            )

            response, _ = await self.ai.generate(
                system_prompt=enhanced_prompt,
                user_prompt=prompt,
                response_model=ClarifyChatResponse,
                call_location="chat_service.clarify_phase",
            )
            return response.model_dump()

    async def _handle_options_message(
        self,
        chat_messages: list[dict],
        canvas_state: dict,
        options: list[dict],
        advisor: Advisor,
        user_context: Optional[str] = None,
    ) -> dict:
        """Handle a message during options phase using the selected advisor."""
        prompt = get_chat_options_prompt(chat_messages, canvas_state, options)

        from pydantic import BaseModel
        from typing import Optional as Opt

        class OptionsChatResponse(BaseModel):
            response: str
            user_chose_option: Opt[str] = None
            canvas_state_update: Opt[dict] = None

        # Build enhanced system prompt with user context and analytical personality
        enhanced_prompt = build_enhanced_system_prompt(
            advisor.system_prompt,
            user_context=user_context,
            include_observation_prompt=True,
        )

        response, _ = await self.ai.generate(
            system_prompt=enhanced_prompt,
            user_prompt=prompt,
            response_model=OptionsChatResponse,
            call_location="chat_service.options_phase",
        )
        return response.model_dump()

    async def _handle_general_message(
        self,
        chat_messages: list[dict],
        canvas_state: dict,
        advisor: Advisor,
        user_context: Optional[str] = None,
    ) -> dict:
        """Handle general conversation using the selected advisor."""
        from pydantic import BaseModel
        from typing import Optional as Opt

        class GeneralChatResponse(BaseModel):
            response: str
            canvas_state_update: Opt[dict] = None

        # Format the conversation history for context
        history = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in chat_messages[-10:]  # Last 10 messages for context
        ])

        prompt = f"""Based on the conversation history below, respond to the user's latest message.

## Conversation History:
{history}

## Instructions:
- Respond in your character's voice and style
- Be helpful and engaging
- Keep your response focused and concise
- If asked about something outside your expertise, acknowledge it but still try to be helpful

Respond with JSON: {{"response": "your response here"}}"""

        # Build enhanced system prompt with user context and analytical personality
        enhanced_prompt = build_enhanced_system_prompt(
            advisor.system_prompt,
            user_context=user_context,
            include_observation_prompt=True,
        )

        response, _ = await self.ai.generate(
            system_prompt=enhanced_prompt,
            user_prompt=prompt,
            response_model=GeneralChatResponse,
            call_location="chat_service.general_chat",
        )
        return response.model_dump()

    async def _generate_options(
        self,
        node: DecisionNode,
        canvas_state: dict,
    ) -> dict:
        """Generate options for the decision."""
        from app.schemas.ai_responses import Phase2Response

        # Format Q&A
        questions = (node.questions_json or {}).get("questions", [])
        answers = node.answers_json or {}
        qa_str = "\n".join([
            f"Q: {q.get('question', '')}\nA: {answers.get(q.get('id', ''), 'Not answered')}"
            for q in questions
        ])

        prompt = get_phase2_prompt(
            summary=node.state_json.get("summary", "") if node.state_json else "",
            decision_type=node.state_json.get("decision_type", "other") if node.state_json else "other",
            questions_and_answers=qa_str,
            canvas_state=canvas_state,
        )

        response, _ = await self.ai.generate(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=Phase2Response,
            call_location="chat_service.generate_phase2",
        )
        return response.model_dump()

    async def _generate_commit_plan(
        self,
        chosen_option: dict,
        canvas_state: dict,
    ) -> dict:
        """Generate commit plan for chosen option."""
        from pydantic import BaseModel
        from typing import Optional

        class CommitPlanResponse(BaseModel):
            commit_plan: dict
            canvas_state_update: Optional[dict] = None

        prompt = get_execution_plan_prompt(
            option_title=chosen_option.get("title", ""),
            option_details=chosen_option,
            canvas_state=canvas_state,
        )

        response, _ = await self.ai.generate(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_prompt=prompt,
            response_model=CommitPlanResponse,
            call_location="chat_service.generate_commit_plan",
        )
        return response.model_dump()

    def _merge_canvas_state(self, current: dict, update: dict) -> dict:
        """Merge canvas state updates."""
        if not update:
            return current

        result = current.copy()

        # Update simple fields
        for field in ["statement", "next_action"]:
            if update.get(field):
                result[field] = update[field]

        # Merge lists
        for field in ["context_bullets", "constraints", "criteria", "risks"]:
            if update.get(field):
                existing = result.get(field, [])
                new_items = update[field]
                # Add new items that aren't duplicates
                existing_ids = {item.get("id") for item in existing if isinstance(item, dict)}
                for item in new_items:
                    if isinstance(item, dict):
                        if item.get("id") not in existing_ids:
                            existing.append(item)
                    elif isinstance(item, str) and item not in existing:
                        existing.append(item)
                result[field] = existing

        return result

    def _format_phase1_response(self, response: dict) -> str:
        """Format Phase 1 response for chat display."""
        summary = response.get("summary", "")
        questions = response.get("questions", [])[:3]  # Show first 3

        questions_text = "\n".join([
            f"- {q.get('question', '')}"
            for q in questions
        ])

        return f"""I understand. {summary}

To help you make this decision, I have some questions:

{questions_text}

You can answer these in the panel on the right, or just tell me more about your situation."""

    def _format_options_message(self, options: list[dict]) -> str:
        """Format options announcement for chat."""
        options_text = "\n\n".join([
            f"**Option {o.get('id')}**: {o.get('title')}\n{o.get('good_if', '')}"
            for o in options
        ])

        return f"""Based on our conversation, here are your options:

{options_text}

Review the options in the panel on the right. Which one resonates with you?"""

    def _format_commit_message(self, commit_plan: dict) -> str:
        """Format commit plan announcement for chat."""
        title = commit_plan.get("chosen_option_title", "")
        steps = commit_plan.get("steps", [])[:3]

        steps_text = "\n".join([
            f"{s.get('number')}. {s.get('title')}"
            for s in steps
        ])

        return f"""Great choice! Here's your action plan for **{title}**:

{steps_text}

The full plan with contingencies is in the panel on the right. Your first step is ready to execute!"""
