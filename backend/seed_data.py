"""Seed data script for demo decisions - Decision Canvas."""

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
                email="demo@decision-canvas.local",
                display_name="Demo User",
            )
            db.add(user)
            await db.commit()

        # =============================================
        # Demo Decision 1: Job Offer (Resolved)
        # =============================================
        decision1_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
        node1_id = uuid.UUID("11111111-1111-1111-1111-111111111112")

        result = await db.execute(select(Decision).where(Decision.id == decision1_id))
        if not result.scalar_one_or_none():
            decision1 = Decision(
                id=decision1_id,
                user_id=DEMO_USER_ID,
                title="Should I accept the startup job offer?",
                situation_text="I've received a job offer from a well-funded startup. The salary is 25% higher than my current role, but it requires relocating to a new city. My current company has good work-life balance and I've built strong relationships here.",
                situation_type="career",
                status="resolved",
                created_at=datetime.utcnow() - timedelta(days=14),
            )
            db.add(decision1)

            node1 = DecisionNode(
                id=node1_id,
                decision_id=decision1_id,
                phase="execute",
                chat_messages_json=[
                    {
                        "id": "msg1",
                        "role": "assistant",
                        "content": "I understand you're facing a significant career decision. Let me help you think through this systematically. A 25% salary increase is substantial, but relocating involves many factors. Let's explore your priorities.",
                        "timestamp": (datetime.utcnow() - timedelta(days=14)).isoformat()
                    },
                    {
                        "id": "msg2",
                        "role": "user",
                        "content": "I'm really torn. The startup seems exciting and the money is great, but I'm worried about leaving my current team and the stability.",
                        "timestamp": (datetime.utcnow() - timedelta(days=14, hours=-1)).isoformat()
                    },
                    {
                        "id": "msg3",
                        "role": "assistant",
                        "content": "Those are valid concerns. Stability vs. growth is a classic trade-off in career decisions. Let me ask: How important is career growth to you in the next 3-5 years? And do you have strong ties to your current location?",
                        "timestamp": (datetime.utcnow() - timedelta(days=14, hours=-1, minutes=-5)).isoformat()
                    },
                    {
                        "id": "msg4",
                        "role": "user",
                        "content": "Career growth is very important. I feel like I've plateaued here. I don't have family ties to this city, but I do have close friends.",
                        "timestamp": (datetime.utcnow() - timedelta(days=14, hours=-2)).isoformat()
                    },
                    {
                        "id": "msg5",
                        "role": "assistant",
                        "content": "Based on what you've shared, I've generated three options for you. Given your emphasis on career growth and the fact that you've plateaued, Option A (Accept the offer) seems like a strong choice, though each option has merit depending on your risk tolerance.",
                        "timestamp": (datetime.utcnow() - timedelta(days=14, hours=-2, minutes=-5)).isoformat()
                    }
                ],
                canvas_state_json={
                    "statement": "Should I accept a startup job offer that pays 25% more but requires relocation?",
                    "context_bullets": [
                        "Current role is stable with good work-life balance",
                        "Feel plateaued in current position",
                        "Startup is well-funded with growth potential",
                        "Would need to relocate to a new city",
                        "No family ties to current location, but have close friends"
                    ],
                    "constraints": [
                        {"id": "c1", "text": "Need at least current salary level", "type": "hard"},
                        {"id": "c2", "text": "Prefer not to relocate more than once in 3 years", "type": "soft"},
                        {"id": "c3", "text": "Want meaningful career growth opportunities", "type": "hard"}
                    ],
                    "criteria": [
                        {"id": "cr1", "name": "Career Growth", "weight": 9, "description": "Opportunities for advancement and skill development"},
                        {"id": "cr2", "name": "Compensation", "weight": 7, "description": "Total compensation including salary, equity, benefits"},
                        {"id": "cr3", "name": "Work-Life Balance", "weight": 6, "description": "Hours, flexibility, stress levels"},
                        {"id": "cr4", "name": "Location", "weight": 5, "description": "Quality of life in the city, proximity to friends/family"}
                    ],
                    "risks": [
                        {"id": "r1", "description": "Startup may fail or pivot significantly", "severity": "medium", "mitigation": "Research runway and product-market fit"},
                        {"id": "r2", "description": "Burnout from startup culture", "severity": "medium", "mitigation": "Set boundaries early, discuss expectations"},
                        {"id": "r3", "description": "Social isolation in new city", "severity": "low", "mitigation": "Budget time for building new connections"}
                    ],
                    "next_action": "Complete Step 1: Schedule call with hiring manager"
                },
                moves_json={
                    "options": [
                        {
                            "id": "A",
                            "title": "Accept the startup offer",
                            "good_if": "You prioritize career growth and are excited about the opportunity",
                            "bad_if": "You value stability and strong local relationships above growth",
                            "pros": ["25% salary increase", "New challenges and learning opportunities", "Potential equity upside", "Break from career plateau"],
                            "cons": ["Need to relocate", "Higher risk of company failure", "Leave established relationships", "Potentially longer hours"],
                            "risks": ["startup_failure", "burnout", "isolation"],
                            "steps": ["Negotiate terms and start date", "Plan relocation logistics", "Give notice at current job", "Build relationships at new company"],
                            "confidence": "high",
                            "confidence_reasoning": "Strong alignment with your stated career growth priority. Well-funded startup reduces failure risk."
                        },
                        {
                            "id": "B",
                            "title": "Decline and negotiate current role",
                            "good_if": "Your current company offers meaningful growth path when pushed",
                            "bad_if": "The company is genuinely limited in what they can offer",
                            "pros": ["Keep existing relationships", "No relocation stress", "Known environment", "Can use offer as leverage"],
                            "cons": ["May not get meaningful growth", "Missed opportunity", "Salary likely won't match offer"],
                            "risks": ["stagnation", "resentment"],
                            "steps": ["Request meeting with manager", "Present growth goals", "Negotiate promotion timeline", "Set review milestones"],
                            "confidence": "medium",
                            "confidence_reasoning": "Success depends on company's flexibility. Your plateau feeling suggests limited internal options."
                        },
                        {
                            "id": "C",
                            "title": "Negotiate remote work arrangement with startup",
                            "good_if": "The startup is open to remote and you can be effective remotely",
                            "bad_if": "The role requires in-person presence or company culture is office-first",
                            "pros": ["Best of both worlds", "Keep local relationships", "Get the growth opportunity"],
                            "cons": ["May reduce chances of getting role", "Could miss team bonding", "Harder to advance remotely"],
                            "risks": ["offer_withdrawal", "career_impact"],
                            "steps": ["Research company's remote policy", "Prepare value proposition for remote", "Negotiate hybrid arrangement", "Plan for occasional visits"],
                            "confidence": "low",
                            "confidence_reasoning": "Startup likely values in-person collaboration. Request may be seen as lack of commitment."
                        }
                    ]
                },
                chosen_move_id="A",
                execution_plan_json={
                    "chosen_option_id": "A",
                    "chosen_option_title": "Accept the startup offer",
                    "steps": [
                        {
                            "number": 1,
                            "title": "Schedule call with hiring manager to negotiate",
                            "description": "Discuss start date flexibility, equity package, and relocation assistance",
                            "branches": [
                                {"condition": "success", "action": "Proceed to step 2"},
                                {"condition": "failure", "action": "Reconsider Option B if terms are non-negotiable"}
                            ],
                            "completed": True
                        },
                        {
                            "number": 2,
                            "title": "Sign offer and set start date",
                            "description": "Allow 3-4 weeks for transition and relocation",
                            "branches": [
                                {"condition": "success", "action": "Proceed to step 3"},
                                {"condition": "failure", "action": "Negotiate timeline if dates don't work"}
                            ],
                            "completed": True
                        },
                        {
                            "number": 3,
                            "title": "Give notice at current company",
                            "description": "Standard 2-week notice, offer to help with transition",
                            "branches": [
                                {"condition": "success", "action": "Complete handoff documentation"},
                                {"condition": "failure", "action": "Remain professional regardless of reaction"}
                            ],
                            "completed": True
                        },
                        {
                            "number": 4,
                            "title": "Begin relocation logistics",
                            "description": "Find housing, set up moving, update address",
                            "branches": [
                                {"condition": "success", "action": "Settle in before start date"},
                                {"condition": "failure", "action": "Request delayed start if needed"}
                            ],
                            "completed": True
                        }
                    ]
                },
                policy_version="v1.0",
                created_at=datetime.utcnow() - timedelta(days=14),
            )
            db.add(node1)

            outcome1 = DecisionOutcome(
                node_id=node1_id,
                progress_yesno=True,
                sentiment_2h=1,
                sentiment_24h=2,
                brier_score=0.09,  # High confidence was justified
                notes="Started the new role last week. The team is great and I'm already learning a lot. No regrets about the move!",
            )
            db.add(outcome1)

            event1 = DecisionEvent(
                decision_id=decision1_id,
                node_id=node1_id,
                event_type="resolved",
                payload_json={"progress_yesno": True, "brier_score": 0.09},
            )
            db.add(event1)

        # =============================================
        # Demo Decision 2: Apartment Choice (Active)
        # =============================================
        decision2_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
        node2_id = uuid.UUID("22222222-2222-2222-2222-222222222223")

        result = await db.execute(select(Decision).where(Decision.id == decision2_id))
        if not result.scalar_one_or_none():
            decision2 = Decision(
                id=decision2_id,
                user_id=DEMO_USER_ID,
                title="Which apartment should I rent?",
                situation_text="I'm choosing between two apartments. Apartment A is in a trendy neighborhood, walking distance to work, but smaller and $300/month more expensive. Apartment B is larger, quieter, better value, but requires a 30-minute commute.",
                situation_type="personal",
                status="active",
                created_at=datetime.utcnow() - timedelta(hours=4),
            )
            db.add(decision2)

            node2 = DecisionNode(
                id=node2_id,
                decision_id=decision2_id,
                phase="moves",
                chat_messages_json=[
                    {
                        "id": "msg1",
                        "role": "assistant",
                        "content": "Finding the right apartment is a decision that affects your daily quality of life. Let me help you think through the trade-offs between these two options systematically.",
                        "timestamp": (datetime.utcnow() - timedelta(hours=4)).isoformat()
                    },
                    {
                        "id": "msg2",
                        "role": "user",
                        "content": "I can't decide! The trendy neighborhood sounds fun but I'm not sure if it's worth the extra money and smaller space.",
                        "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=50)).isoformat()
                    },
                    {
                        "id": "msg3",
                        "role": "assistant",
                        "content": "Let's break this down. What's your current commute situation, and how much do you value being able to walk to work vs. having more space at home?",
                        "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=45)).isoformat()
                    },
                    {
                        "id": "msg4",
                        "role": "user",
                        "content": "I currently drive 20 minutes. Walking to work would be amazing and I'd save on gas and parking. But I do work from home 2 days a week, so the extra space would be nice for a home office.",
                        "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=30)).isoformat()
                    },
                    {
                        "id": "msg5",
                        "role": "assistant",
                        "content": "That's helpful context. Based on your hybrid work arrangement, here are the options I see. Each has different trade-offs depending on whether you prioritize convenience or space.",
                        "timestamp": (datetime.utcnow() - timedelta(hours=3, minutes=25)).isoformat()
                    }
                ],
                canvas_state_json={
                    "statement": "Which apartment should I rent: walkable & trendy (A) or spacious & affordable (B)?",
                    "context_bullets": [
                        "Apartment A: Trendy neighborhood, walkable to work, smaller, +$300/month",
                        "Apartment B: Larger, quieter, 30-min commute, better value",
                        "Currently drive 20 minutes to work",
                        "Work from home 2 days per week",
                        "Would save on gas and parking with walkable apartment"
                    ],
                    "constraints": [
                        {"id": "c1", "text": "Must be within budget (including transportation costs)", "type": "hard"},
                        {"id": "c2", "text": "Need space for home office", "type": "soft"},
                        {"id": "c3", "text": "Safe neighborhood", "type": "hard"}
                    ],
                    "criteria": [
                        {"id": "cr1", "name": "Commute Quality", "weight": 8, "description": "Time spent commuting and mode of transport"},
                        {"id": "cr2", "name": "Living Space", "weight": 7, "description": "Square footage and layout functionality"},
                        {"id": "cr3", "name": "Total Cost", "weight": 8, "description": "Rent plus transportation, parking, etc."},
                        {"id": "cr4", "name": "Neighborhood Vibe", "weight": 6, "description": "Restaurants, culture, walkability"}
                    ],
                    "risks": [
                        {"id": "r1", "description": "Trendy neighborhood may have noise issues", "severity": "low", "option_id": "A"},
                        {"id": "r2", "description": "Commute fatigue may impact WFH productivity", "severity": "medium", "option_id": "B"},
                        {"id": "r3", "description": "Smaller space may feel cramped for WFH", "severity": "medium", "option_id": "A"}
                    ],
                    "next_action": "Review options and select one to proceed with"
                },
                moves_json={
                    "options": [
                        {
                            "id": "A",
                            "title": "Choose Apartment A (Trendy & Walkable)",
                            "good_if": "You value convenience and lifestyle over space",
                            "bad_if": "You need dedicated home office space or the budget is tight",
                            "pros": ["Walk to work (time and money savings)", "Trendy neighborhood amenities", "No parking costs", "Better work-life integration"],
                            "cons": ["$300/month more in rent", "Smaller space", "May be noisier", "Less room for home office"],
                            "risks": ["noise", "cramped_space"],
                            "steps": ["Submit application", "Review lease terms", "Plan space optimization", "Sign lease"],
                            "confidence": "medium",
                            "confidence_reasoning": "Good for lifestyle but WFH 2 days/week makes space a real consideration."
                        },
                        {
                            "id": "B",
                            "title": "Choose Apartment B (Spacious & Affordable)",
                            "good_if": "You value space for home office and saving money",
                            "bad_if": "Commuting significantly impacts your quality of life",
                            "pros": ["More space for home office", "$300/month savings", "Quieter environment", "Better value per square foot"],
                            "cons": ["30-minute commute 3 days/week", "Less walkable neighborhood", "Car dependency continues"],
                            "risks": ["commute_fatigue", "isolation"],
                            "steps": ["Submit application", "Review lease terms", "Plan home office setup", "Sign lease"],
                            "confidence": "medium",
                            "confidence_reasoning": "Better for WFH productivity but commute adds up to 3 hours/week."
                        }
                    ]
                },
                policy_version="v1.0",
                created_at=datetime.utcnow() - timedelta(hours=4),
            )
            db.add(node2)

            event2 = DecisionEvent(
                decision_id=decision2_id,
                node_id=node2_id,
                event_type="phase2_completed",
                payload_json={"option_count": 2},
            )
            db.add(event2)

        await db.commit()
        print("Decision Canvas seed data created successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
