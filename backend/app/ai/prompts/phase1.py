"""Phase 1 (Clarify) prompts for Decision Canvas."""


def get_phase1_prompt(situation_text: str, template_context: str = "") -> str:
    """Generate the Phase 1 (Clarify) prompt for any decision domain."""
    return f"""## Task: Analyze Decision and Generate Clarifying Questions

Analyze the user's decision situation and generate specific questions to understand it better.

## User's Situation:
{situation_text}

{template_context}

## Requirements:
1. Summarize the decision in 1-2 sentences
2. Detect the decision type:
   - career: Job offers, career changes, negotiations, promotions
   - financial: Investments, purchases, budgeting, debt decisions
   - business: Strategy, hiring, partnerships, product decisions
   - personal: Relocations, lifestyle changes, major life decisions
   - relationship: Dating, family, friendship decisions
   - health: Treatment options, lifestyle changes, provider choices
   - education: Programs, courses, certifications, schools
   - other: Any decision that doesn't fit above categories
3. Generate 5-12 specific clarifying questions
4. Extract initial canvas state (statement, context, constraints, criteria)

## Question Requirements:
- Each question must have a unique ID (q1, q2, etc.)
- Questions must be specific and actionable
- Include why_this_question (tooltip explaining relevance)
- Include what_it_changes (what the answer affects in the decision)
- Assign priority 0-100 (higher = more important to answer)
- Use appropriate answer_type: yes_no, text, number, or single_select

## Good Question Examples:
- "What is your deadline for making this decision?" (specific, measurable)
- "Is relocation an option for you?" (yes/no, actionable)
- "What is your current salary?" (number, relevant context)
- "Which matters more to you?" with choices: ["salary", "growth", "work-life balance", "team culture"]

## Bad Questions (DO NOT USE):
- "How do you feel about this?" (therapy question)
- "What do you think will happen?" (speculation)
- "Why is this important to you?" (too vague)

## Canvas State Extraction:
From the user's input, extract:
- statement: A clear 1-sentence decision statement (e.g., "Should I accept the job offer from TechCorp?")
- context_bullets: 3-5 key facts from their description
- constraints: Any hard requirements or soft preferences mentioned
- criteria: Any decision factors they've mentioned or implied

## Output JSON Schema:
{{
  "summary": "string - 1-2 sentence summary of the decision",
  "situation_type": "career|financial|business|personal|relationship|health|education|major_purchase|other",
  "mood_detected": "calm|anxious|stressed|excited|uncertain|confident|neutral",
  "questions": [
    {{
      "id": "q1",
      "question": "string",
      "answer_type": "yes_no|text|number|single_select",
      "choices": ["option1", "option2"],
      "why_this_question": "string",
      "what_it_changes": "string",
      "priority": 0-100
    }}
  ],
  "decision_statement": "string - clear decision statement",
  "context_bullets": ["bullet1", "bullet2"],
  "initial_constraints": [
    {{"id": "c1", "text": "string", "type": "hard|soft"}}
  ]
}}

Respond with valid JSON only."""


def get_chat_clarify_prompt(
    situation_text: str,
    chat_history: list[dict],
    current_canvas: dict,
) -> str:
    """Generate prompt for chat-based clarification."""
    history_str = "\n".join(
        [f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-10:]]
    )

    canvas_str = ""
    if current_canvas:
        canvas_str = f"""
## Current Canvas State:
- Statement: {current_canvas.get('statement', 'Not yet defined')}
- Context: {', '.join(current_canvas.get('context_bullets', []))}
- Constraints: {len(current_canvas.get('constraints', []))} identified
- Criteria: {len(current_canvas.get('criteria', []))} identified
"""

    return f"""## Task: Continue Clarifying the Decision

You are in a conversation helping the user clarify their decision.

## Original Situation:
{situation_text}

## Conversation History:
{history_str}
{canvas_str}

## Your Task:
1. Acknowledge what the user just shared
2. Ask the next most important clarifying question
3. Update the canvas state with any new information learned
4. Determine if we have enough information to generate options

## Response Requirements:
- Keep your response under 100 words
- Ask only ONE question at a time
- Update canvas_state with any new information
- Set ready_for_options to true if you have enough information

## Output JSON Schema:
{{
  "response": "string - your conversational response with one question",
  "canvas_state": {{
    "statement": "string or null if unchanged",
    "context_bullets": ["new bullets to add"],
    "constraints": [{{"id": "c1", "text": "string", "type": "hard|soft"}}],
    "criteria": [{{"id": "cr1", "name": "string", "weight": 5}}],
    "next_action": "string"
  }},
  "ready_for_options": false
}}

Respond with valid JSON only."""
