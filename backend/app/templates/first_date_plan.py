from app.templates.base_template import BaseTemplate, register_template


class FirstDatePlanTemplate(BaseTemplate):
    """Template for first date planning situations."""

    name = "first_date_plan"
    description = "Planning a first date that allows for conversation while showing thoughtfulness and initiative."

    important_questions = [
        "What are her interests or hobbies?",
        "What days/times work for both of you?",
        "What's your budget for the date?",
        "Do you have backup plans if first choice doesn't work?",
        "How far will she need to travel?",
        "Is there a shared interest you could build the date around?",
        "Coffee/drinks or full activity?",
        "Day date or evening?",
        "How long have you been talking?",
        "What's the vibe of your conversations so far?",
    ]

    scoring_weights = {
        "self_respect": 1.0,
        "respect_for_her": 1.2,
        "clarity": 1.3,  # Clear plans show leadership
        "leadership": 1.5,  # Taking initiative is key
        "warmth": 1.2,
        "progress": 1.0,
        "risk_management": 1.0,
    }

    guardrail_additions = [
        "First date should be in a public place",
        "Don't overpromise or go overboard on expense",
        "Have a clear end time in mind",
        "Don't plan something that traps her (long drive, isolated location)",
        "Keep first date to 1-2 hours max",
        "Choose a venue that allows for conversation",
    ]

    script_style_direct = "Specific plan with time, place, and activity. Confident ask with easy out for her."
    script_style_softer = "Suggest activity area, invite input on specifics. Shows initiative while being collaborative."


# Register this template
register_template(FirstDatePlanTemplate())
