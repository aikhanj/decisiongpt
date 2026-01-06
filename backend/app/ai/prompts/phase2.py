"""Phase 2 (Options) and Phase 3 (Commit) prompts for Decision Canvas."""


def get_phase2_prompt(
    summary: str,
    decision_type: str,
    questions_and_answers: str,
    canvas_state: dict,
    template_guardrails: str = "",
) -> str:
    """Generate the Phase 2 (Options) prompt for any decision domain."""

    constraints_str = ""
    if canvas_state.get("constraints"):
        constraints_str = "\n".join(
            [f"- [{c.get('type', 'soft').upper()}] {c.get('text', '')}"
             for c in canvas_state.get("constraints", [])]
        )

    criteria_str = ""
    if canvas_state.get("criteria"):
        criteria_str = "\n".join(
            [f"- {c.get('name', '')} (weight: {c.get('weight', 5)}/10)"
             for c in canvas_state.get("criteria", [])]
        )

    return f"""## Task: Generate 2-3 Decision Options

Based on the analyzed decision and user's answers, generate 2-3 distinct options.

## Decision Summary:
{summary}

## Decision Type: {decision_type}

## Decision Statement:
{canvas_state.get('statement', 'Not specified')}

## Constraints:
{constraints_str or 'None specified'}

## Decision Criteria:
{criteria_str or 'None specified'}

## Questions and Answers:
{questions_and_answers}

{template_guardrails}

## Requirements:
1. Generate exactly 2-3 options (labeled A, B, C)
2. Options must be DISTINCT - not minor variations
3. Each option represents a meaningfully different path
4. Include one "safe/conservative" option if appropriate

## Each Option Must Include:
- id: "A", "B", or "C"
- title: Clear, concise title (5 words max)
- good_if: When this option is the right choice
- bad_if: When this option is NOT the right choice
- pros: 3-5 bullet points
- cons: 2-4 bullet points
- risks: Risk tags (e.g., "financial_risk", "time_pressure", "irreversible")
- steps: 3-5 implementation steps
- confidence: "low", "medium", or "high"
- confidence_reasoning: Why this confidence level

## Option Quality Guidelines:
- Options should be actionable, not abstract
- Pros/cons should be specific, not generic
- Steps should be concrete and sequenced
- Risks should be honest and realistic

## Output JSON Schema:
{{
  "options": [
    {{
      "id": "A",
      "title": "string (5 words max)",
      "good_if": "string - when this option is best",
      "bad_if": "string - when to avoid this option",
      "pros": ["pro1", "pro2", "pro3"],
      "cons": ["con1", "con2"],
      "risks": ["risk_tag_1", "risk_tag_2"],
      "steps": ["step1", "step2", "step3"],
      "confidence": "low|medium|high",
      "confidence_reasoning": "string - why this confidence level"
    }}
  ],
  "canvas_state_update": {{
    "risks": [
      {{"id": "r1", "description": "string", "severity": "low|medium|high", "option_id": "A"}}
    ],
    "next_action": "Review options and choose one"
  }}
}}

Respond with valid JSON only."""


def get_execution_plan_prompt(
    option_title: str,
    option_details: dict,
    canvas_state: dict,
) -> str:
    """Generate the execution/commit plan prompt."""

    steps_str = "\n".join([f"- {step}" for step in option_details.get("steps", [])])

    return f"""## Task: Generate Commit Plan

Create a concrete execution plan for the chosen option.

## Chosen Option: {option_title}

## Option Steps:
{steps_str}

## Good If: {option_details.get('good_if', '')}
## Risks: {', '.join(option_details.get('risks', []))}

## Decision Context:
{canvas_state.get('statement', '')}

## Requirements:
1. Generate 3-6 specific, actionable steps
2. First step should be immediately actionable
3. Include if-then contingency branches
4. Steps should have clear completion criteria

## Step Requirements:
- Each step has a clear action
- Steps are sequenced logically
- Include contingencies for key decision points
- Final step confirms completion/resolution

## Output JSON Schema:
{{
  "commit_plan": {{
    "chosen_option_id": "{option_details.get('id', 'A')}",
    "chosen_option_title": "{option_title}",
    "steps": [
      {{
        "number": 1,
        "title": "string - action title",
        "description": "string - more detail if needed",
        "branches": [
          {{"condition": "success", "action": "Proceed to step 2"}},
          {{"condition": "failure", "action": "Revisit decision or try alternative"}}
        ],
        "completed": false
      }}
    ]
  }},
  "canvas_state_update": {{
    "next_action": "Execute step 1: [first step title]"
  }}
}}

Respond with valid JSON only."""


def get_chat_options_prompt(
    chat_history: list[dict],
    canvas_state: dict,
    options: list[dict],
) -> str:
    """Generate prompt for chat during options phase."""

    history_str = "\n".join(
        [f"{msg['role'].upper()}: {msg['content']}" for msg in chat_history[-10:]]
    )

    options_str = "\n".join([
        f"Option {opt['id']}: {opt['title']}"
        for opt in options
    ])

    return f"""## Task: Help User Evaluate Options

The user is reviewing their options and may have questions or want to discuss trade-offs.

## Current Options:
{options_str}

## Conversation History:
{history_str}

## Canvas State:
- Statement: {canvas_state.get('statement', '')}
- Criteria: {len(canvas_state.get('criteria', []))} defined

## Your Task:
1. Answer any questions about the options
2. Help compare options against their criteria
3. If they express a preference, encourage them to commit
4. Do NOT make the decision for them

## Response Requirements:
- Keep response under 150 words
- Be helpful but don't push
- If they choose, acknowledge and prepare for commit plan

## Output JSON Schema:
{{
  "response": "string - your conversational response",
  "user_chose_option": null or "A|B|C",
  "canvas_state_update": {{
    "next_action": "string"
  }}
}}

Respond with valid JSON only."""
