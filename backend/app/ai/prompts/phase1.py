def get_phase1_prompt(situation_text: str, template_context: str = "") -> str:
    """Generate the Phase 1 (Clarify) prompt."""
    return f"""## Task: Analyze Situation and Generate Questions

Analyze the user's romantic situation and generate specific questions to understand it better.

## User's Situation:
{situation_text}

{template_context}

## Requirements:
1. Summarize the situation in 1-2 sentences
2. Detect the situation type:
   - gym_approach: Approaching someone at the gym
   - double_text: Whether to send another message after no response
   - kiss_timing: When/how to initiate physical intimacy
   - first_date_plan: Planning a first date
   - generic_relationship_next_step: Other relationship decisions
3. Detect the user's mood state from their language
4. Generate 5-15 specific questions (not vague) to understand the situation

## Question Requirements:
- Each question must have a unique ID (q1, q2, etc.)
- Questions must be specific and actionable, not therapeutic
- Include why_this_question (tooltip for user)
- Include what_it_changes (what the answer affects)
- Assign priority 0-100 (higher = more important)
- Use appropriate answer_type: yes_no, text, number, or single_select

## Example Good Questions:
- "How long ago did you send your last message?" (specific, measurable)
- "Has she initiated physical contact before?" (yes/no, actionable)
- "What's your relationship stage?" with choices: ["just met", "talked a few times", "been on dates", "exclusive"]

## Example Bad Questions (DO NOT USE):
- "How do you feel about her?" (therapy question)
- "Why do you think she hasn't responded?" (speculation)
- "What are your intentions?" (vague)

## Output JSON Schema:
{{
  "summary": "string - 1-2 sentence summary",
  "situation_type": "gym_approach|double_text|kiss_timing|first_date_plan|generic_relationship_next_step",
  "mood_detected": "calm|anxious|angry|sad|horny|tired|confident|neutral",
  "questions": [
    {{
      "id": "q1",
      "question": "string",
      "answer_type": "yes_no|text|number|single_select",
      "choices": ["option1", "option2"] // only for single_select
      "why_this_question": "string",
      "what_it_changes": "string",
      "priority": 0-100
    }}
  ]
}}

Respond with valid JSON only."""
