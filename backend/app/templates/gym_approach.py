from app.templates.base_template import BaseTemplate, register_template


class GymApproachTemplate(BaseTemplate):
    """Template for gym approach situations."""

    name = "gym_approach"
    description = "Approaching someone at the gym requires situational awareness and respect for the workout environment."

    important_questions = [
        "Is she wearing headphones?",
        "Has she made eye contact or looked your way?",
        "Is she mid-workout or resting between sets?",
        "Do you have a natural conversation opener (shared equipment, class, etc.)?",
        "Have you seen her at this gym before?",
        "Is the gym crowded or quiet?",
        "What time of day is it?",
        "Do you have mutual acquaintances at the gym?",
        "Has she ever initiated any interaction (smile, nod)?",
        "Are you a regular at this gym?",
    ]

    scoring_weights = {
        "self_respect": 1.0,
        "respect_for_her": 1.5,  # Extra important - gym is not a bar
        "clarity": 1.2,
        "leadership": 1.0,
        "warmth": 1.2,
        "progress": 0.8,  # Don't prioritize progress over respect
        "risk_management": 1.3,  # Important to manage social risk
    }

    guardrail_additions = [
        "Never interrupt mid-set or during focused exercise",
        "Never follow or hover around her workout area",
        "Never approach if headphones are in and she hasn't acknowledged you",
        "Never persist after a polite decline or disinterest",
        "Keep the initial interaction under 30 seconds",
        "Have a natural exit ready (going back to your workout)",
    ]

    script_style_direct = "Brief, friendly, with a natural reason to talk. Get to the point and offer an easy out."
    script_style_softer = "Casual observation or question, no pressure, leaves door open for future."


# Register this template
register_template(GymApproachTemplate())
