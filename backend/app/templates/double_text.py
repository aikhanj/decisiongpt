from app.templates.base_template import BaseTemplate, register_template


class DoubleTextTemplate(BaseTemplate):
    """Template for double-text situations."""

    name = "double_text"
    description = "Deciding whether to send a follow-up message after no response requires balancing initiative with respect for her space."

    important_questions = [
        "How long has it been since your last message?",
        "What did your last message say?",
        "What is your relationship stage (just met, few dates, exclusive)?",
        "Have you double-texted before in this conversation?",
        "Was your last message a question or a statement?",
        "Has she been responsive in the past?",
        "Is there a time-sensitive reason to reach out (event, plans)?",
        "Did something change that warrants a new message (news, shared interest)?",
        "How did you meet?",
        "What was the tone of your last few exchanges?",
    ]

    scoring_weights = {
        "self_respect": 1.5,  # Very important - don't be needy
        "respect_for_her": 1.3,
        "clarity": 1.0,
        "leadership": 0.8,  # Less about leadership here
        "warmth": 1.0,
        "progress": 0.7,  # Don't force progress
        "risk_management": 1.2,
    }

    guardrail_additions = [
        "Maximum ONE follow-up message allowed",
        "Follow-up must add value, not just 'checking in'",
        "No guilt-tripping about not responding",
        "No asking if she got the message",
        "Minimum 24-48 hours before follow-up (situation dependent)",
        "If already double-texted once, wait for her response",
    ]

    script_style_direct = "Bring something new to the conversation. Reference shared interest or make specific plans."
    script_style_softer = "Light, low-pressure, gives her an easy way to re-engage without explaining silence."


# Register this template
register_template(DoubleTextTemplate())
