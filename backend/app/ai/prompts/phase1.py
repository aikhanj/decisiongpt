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
3. Generate 3-5 specific clarifying questions (ONLY the most critical ones - don't over-question)
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
1. FIRST: Actually respond to what the user said or asked
   - If they asked a question (like "give me examples", "what do you mean", "like what?"), ANSWER IT
   - If they shared information, acknowledge it specifically
   - Do NOT ignore their message and just ask another question
2. THEN (optionally): Ask the next clarifying question if appropriate
3. Update the canvas state with any new information learned
4. Determine if we have enough information to generate options

## Critical: Respond to the user's actual message
- If user asks "give me some examples" → provide examples related to your previous question
- If user asks "what do you mean?" → clarify your previous question
- If user asks for help → help them, don't just ask another question
- The user is talking TO you, not filling out a form

## Handling "I don't know" or unclear answers:
- If the user says "I don't know", "not sure", "idk", or similar - ACCEPT IT and MOVE ON
- Do NOT rephrase the same question or push for an answer
- Do NOT say things like "that's okay, but..." and then ask the same thing differently
- Simply acknowledge briefly and ask a COMPLETELY DIFFERENT question
- Mark unclear answers as "unknown" in your mental model and work around them

## Response Requirements:
- Keep your response concise but complete (under 150 words)
- If answering a user question, give a real answer with specifics
- Ask at most ONE follow-up question - and only if needed
- Update canvas_state with any new information
- Set ready_for_options to true after 3-4 exchanges OR when you have enough to work with
- It's better to give options with some uncertainty than to interrogate the user

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
