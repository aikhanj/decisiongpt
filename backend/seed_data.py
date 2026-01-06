"""Seed data script for demo decisions."""

import asyncio
import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.config import get_settings
from app.models import (
    User,
    Decision,
    DecisionNode,
    DecisionEvent,
    DecisionOutcome,
)
from app.database import Base

settings = get_settings()

# Demo user ID
DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed_data():
    """Create seed data for demo purposes."""
    engine = create_async_engine(settings.database_url)

    async with engine.begin() as conn:
        # Create tables if they don't exist
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with AsyncSessionLocal() as db:
        # Check if demo user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == DEMO_USER_ID))
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                id=DEMO_USER_ID,
                email="demo@gentleman-coach.local",
                display_name="Demo User",
            )
            db.add(user)
            await db.commit()

        # Create Demo Decision 1: Gym Approach (Resolved)
        decision1_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        node1_id = uuid.UUID("11111111-1111-1111-1111-111111111112")

        result = await db.execute(select(Decision).where(Decision.id == decision1_id))
        if not result.scalar_one_or_none():
            decision1 = Decision(
                id=decision1_id,
                user_id=DEMO_USER_ID,
                title="Approaching Sarah at the gym",
                situation_text="There's a woman named Sarah I see at the gym 3-4 times a week. We've made eye contact a few times and she smiled once. She usually works out with headphones but takes them off between sets. I want to approach her but I'm not sure how to do it without being creepy.",
                situation_type="gym_approach",
                status="resolved",
                created_at=datetime.utcnow() - timedelta(days=7),
            )
            db.add(decision1)

            node1 = DecisionNode(
                id=node1_id,
                decision_id=decision1_id,
                phase="execute",
                state_json={"summary": "User wants to approach a woman at the gym who has shown some positive signals"},
                questions_json={
                    "questions": [
                        {"id": "q1", "question": "Is she wearing headphones right now?", "answer_type": "yes_no", "priority": 90},
                        {"id": "q2", "question": "Has she made eye contact today?", "answer_type": "yes_no", "priority": 85},
                        {"id": "q3", "question": "Are you mid-workout or finished?", "answer_type": "single_select", "choices": ["Mid-workout", "Just finished", "About to start"], "priority": 75},
                    ]
                },
                answers_json={
                    "answers": [
                        {"question_id": "q1", "value": False},
                        {"question_id": "q2", "value": True},
                        {"question_id": "q3", "value": "Just finished"},
                    ]
                },
                moves_json={
                    "moves": [
                        {
                            "move_id": "A",
                            "title": "Direct Introduction",
                            "when_to_use": "When she's between sets and seems relaxed",
                            "tradeoff": "Clear but puts you on the spot",
                            "gentleman_score": 85,
                            "risk_level": "med",
                            "p_raw_progress": 0.45,
                            "p_calibrated_progress": 0.45,
                            "scripts": {
                                "direct": "Hey, I see you here often. I'm [name]. Would you want to grab coffee sometime after a workout?",
                                "softer": "Hey, quick question - do you know if they're ever going to fix that cable machine?"
                            },
                            "timing": "Right after she finishes a set",
                            "branches": {
                                "warm": {"next_move": "Exchange numbers", "script": "Great! What's your number?"},
                                "neutral": {"next_move": "Leave door open", "script": "No worries, see you around!"},
                                "cold": {"next_move": "Exit gracefully", "script": "All good, have a great workout!"}
                            }
                        }
                    ],
                    "cooldown_recommended": False,
                },
                chosen_move_id="A",
                execution_plan_json={
                    "steps": [
                        "Wait until she takes off her headphones between sets",
                        "Approach from the front so she sees you coming",
                        "Make brief eye contact and smile",
                        "Deliver your line confidently",
                        "If positive, suggest exchanging numbers"
                    ],
                    "exact_message": "Hey, I see you here often. I'm Alex. Would you want to grab coffee sometime after a workout?",
                    "exit_line": "No worries at all. Have a great workout!",
                    "boundary_rule": "If she says no or seems uncomfortable, accept it immediately and leave."
                },
                mood_state="confident",
                policy_version="v1.0",
                created_at=datetime.utcnow() - timedelta(days=7),
            )
            db.add(node1)

            outcome1 = DecisionOutcome(
                node_id=node1_id,
                progress_yesno=True,
                sentiment_2h=1,
                sentiment_24h=2,
                brier_score=0.3025,  # (0.45 - 1)^2
                notes="She said yes! We're getting coffee on Saturday.",
            )
            db.add(outcome1)

            event1 = DecisionEvent(
                decision_id=decision1_id,
                node_id=node1_id,
                event_type="resolved",
                payload_json={"progress_yesno": True, "brier_score": 0.3025},
            )
            db.add(event1)

        # Create Demo Decision 2: Double Text (Active)
        decision2_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        node2_id = uuid.UUID("22222222-2222-2222-2222-222222222223")

        result = await db.execute(select(Decision).where(Decision.id == decision2_id))
        if not result.scalar_one_or_none():
            decision2 = Decision(
                id=decision2_id,
                user_id=DEMO_USER_ID,
                title="Should I double text Emma?",
                situation_text="I matched with Emma on Hinge 5 days ago. We had a great conversation and she was very responsive. I asked her out for drinks and she said 'that sounds fun, let me check my schedule!' That was 3 days ago and I haven't heard back. She still has me on her list and hasn't unmatched. I'm wondering if I should send a follow-up or wait.",
                situation_type="double_text",
                status="active",
                created_at=datetime.utcnow() - timedelta(hours=6),
            )
            db.add(decision2)

            node2 = DecisionNode(
                id=node2_id,
                decision_id=decision2_id,
                phase="moves",
                state_json={"summary": "User is wondering whether to send a follow-up message after 3 days of no response"},
                questions_json={
                    "questions": [
                        {"id": "q1", "question": "How long since your last message?", "answer_type": "text", "priority": 95},
                        {"id": "q2", "question": "What was your last message?", "answer_type": "text", "priority": 90},
                        {"id": "q3", "question": "Have you double-texted before in this conversation?", "answer_type": "yes_no", "priority": 85},
                        {"id": "q4", "question": "How was the conversation energy before this?", "answer_type": "single_select", "choices": ["Very engaged", "Moderately engaged", "She was slow to respond"], "priority": 80},
                    ]
                },
                answers_json={
                    "answers": [
                        {"question_id": "q1", "value": "3 days"},
                        {"question_id": "q2", "value": "Asked her out for drinks, she said let me check my schedule"},
                        {"question_id": "q3", "value": False},
                        {"question_id": "q4", "value": "Very engaged"},
                    ]
                },
                moves_json={
                    "moves": [
                        {
                            "move_id": "A",
                            "title": "Value-Add Follow-up",
                            "when_to_use": "When there was genuine interest and you have something new to share",
                            "tradeoff": "Shows initiative but risks seeming pushy",
                            "gentleman_score": 82,
                            "risk_level": "low",
                            "p_raw_progress": 0.55,
                            "p_calibrated_progress": 0.55,
                            "scripts": {
                                "direct": "Hey! Found this great spot with live jazz on Thursdays if you're free this week",
                                "softer": "No pressure on the drinks - just saw they're doing a comedy night at [place] this week"
                            },
                            "timing": "Send during normal hours (10am-8pm)",
                            "branches": {
                                "warm": {"next_move": "Confirm the date", "script": "Perfect! Thursday at 7 work?"},
                                "neutral": {"next_move": "Ball's in her court", "script": "Let me know if that works!"},
                                "cold": {"next_move": "Accept and move on", "script": "No worries, take care!"}
                            }
                        },
                        {
                            "move_id": "B",
                            "title": "Wait It Out",
                            "when_to_use": "When you want to give her space and see if she re-engages",
                            "tradeoff": "Preserves dignity but might lose momentum",
                            "gentleman_score": 88,
                            "risk_level": "low",
                            "p_raw_progress": 0.35,
                            "p_calibrated_progress": 0.35,
                            "scripts": {
                                "direct": "N/A - no message sent",
                                "softer": "N/A - no message sent"
                            },
                            "timing": "Wait at least another 3-4 days",
                            "branches": {
                                "warm": {"next_move": "Respond enthusiastically", "script": "Great to hear from you! How about [specific plan]?"},
                                "neutral": {"next_move": "Keep it light", "script": "Hey! How's it going?"},
                                "cold": {"next_move": "Move on gracefully", "script": "No follow-up needed"}
                            }
                        }
                    ],
                    "cooldown_recommended": False,
                },
                mood_state="anxious",
                policy_version="v1.0",
                created_at=datetime.utcnow() - timedelta(hours=6),
            )
            db.add(node2)

            event2 = DecisionEvent(
                decision_id=decision2_id,
                node_id=node2_id,
                event_type="phase2_completed",
                payload_json={"move_count": 2},
            )
            db.add(event2)

        await db.commit()
        print("Seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
