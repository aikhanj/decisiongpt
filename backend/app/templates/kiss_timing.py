from app.templates.base_template import BaseTemplate, register_template


class KissTimingTemplate(BaseTemplate):
    """Template for kiss timing situations."""

    name = "kiss_timing"
    description = "Timing physical intimacy requires reading signals accurately and ensuring mutual comfort."

    important_questions = [
        "How many dates have you been on?",
        "Have you had any physical contact (hand holding, arm touching)?",
        "Is there prolonged eye contact during pauses in conversation?",
        "Are you currently in a private or public setting?",
        "Has she leaned in or reduced physical distance?",
        "How is the conversation flowing?",
        "Has she touched you (arm, shoulder, etc.)?",
        "Are either of you under the influence of alcohol?",
        "What's the energy/vibe of the moment?",
        "Has she given verbal hints about attraction?",
    ]

    scoring_weights = {
        "self_respect": 1.0,
        "respect_for_her": 2.0,  # Most important - consent is paramount
        "clarity": 1.3,  # Clear signals matter
        "leadership": 1.0,
        "warmth": 1.2,
        "progress": 0.6,  # Don't rush this
        "risk_management": 1.5,  # Important to read signals right
    }

    guardrail_additions = [
        "Never attempt when either party is significantly intoxicated",
        "Must have clear positive signals first (eye contact, proximity, touch)",
        "Respect any hesitation immediately",
        "Don't persist if she turns away or creates distance",
        "Setting should feel comfortable and not trapped",
        "Verbal consent or clear non-verbal enthusiasm required",
    ]

    script_style_direct = "Brief pause, eye contact, lean in slowly. Give her time to meet you or pull back."
    script_style_softer = "Create the opportunity through proximity and eye contact, let her close the gap."


# Register this template
register_template(KissTimingTemplate())
