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
        [f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-20:]]
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

    num_exchanges = len([m for m in chat_history if m.get('role') == 'user'])

    return f"""## Task: Be a Thoughtful Coach, Not a Question Machine

You are having a real conversation to understand someone's situation. You are NOT a survey bot.

## Original Situation:
{situation_text}

## Conversation So Far ({num_exchanges} exchanges):
{history_str}
{canvas_str}

## YOUR JOB - BE A REAL COACH:

### 1. SYNTHESIZE what you've learned
Before asking another question, think: What patterns do I see? What contradictions? What's the REAL issue underneath?

### 2. MAKE OBSERVATIONS
Share what you notice:
- "I notice you keep coming back to feeling like things are pointless..."
- "There's a pattern here - you want connection but also feel like everything is a waste of time"
- "You said you want to help others, but also don't want to waste time helping others. That's interesting - what's behind that?"

### 3. GO DEEPER, NOT WIDER
Don't keep asking shallow categorization questions. If someone says they want "deeper connections", don't ask "what KIND of deeper connections?" - that's useless. Instead:
- Explore WHY they feel disconnected
- Ask about specific past experiences
- Challenge assumptions gently

### 4. KNOW WHEN TO STOP QUESTIONING
After 5-6 exchanges, you should have enough. Time to:
- Summarize what you've learned
- Offer an observation or insight
- Propose a direction forward

## WHAT NOT TO DO:
- Don't start every response with "Understood." - it sounds robotic
- Don't ask "What kind of X: A, B, or C?" over and over - that's lazy
- Don't ignore contradictions - gently point them out
- Don't keep asking if you already have enough information
- Don't ask questions that lead nowhere ("what new skill?" when they said they have no time)

## GOOD RESPONSE EXAMPLES:
1. Making an observation: "You've mentioned feeling like things are pointless a few times now. It sounds like the issue isn't really about finding a hobby - it's about finding meaning. What would make something feel NOT like a waste of time to you?"

2. Connecting dots: "So let me make sure I'm tracking this: you want deeper connections, you feel relationships have been transactional, you have no close friends, and you enjoy things like chess that make you feel smart. It sounds like you value being seen for your mind. Does that resonate?"

3. Gentle challenge: "Earlier you said you wanted to help others, but just now you said you don't want to waste time helping others. I'm curious about that tension - what makes helping feel like a waste?"

4. Moving forward: "I think I understand the core issue now. You're craving genuine connection but have a pattern of seeing everything - including relationships - as transactional or pointless. Before we talk about solutions, does that framing feel right to you?"

## RESPONSE FORMAT:
{{
  "response": "Your actual response - make it SUBSTANTIVE. Observations, connections, or a meaningful question. NOT just 'Understood. What kind of X do you want?'",
  "question_reason": "Why you're saying/asking this (shown as tooltip)",
  "suggested_options": ["option1", "option2", "option3"] or null if not asking a multiple choice question,
  "canvas_state": {{
    "statement": "string or null",
    "context_bullets": ["key insights you've learned"],
    "constraints": [],
    "criteria": [],
    "next_action": "string"
  }},
  "ready_for_options": {str(num_exchanges >= 6).lower()}
}}

IMPORTANT: If ready_for_options is true, your response should be a SUMMARY of what you've learned and a proposed direction, not another question.

Respond with valid JSON only."""
