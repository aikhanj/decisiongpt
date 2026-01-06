def get_phase2_prompt(
    summary: str,
    situation_type: str,
    mood_state: str,
    questions_and_answers: str,
    template_guardrails: str = "",
) -> str:
    """Generate the Phase 2 (Moves) prompt."""
    return f"""## Task: Generate 2-3 Move Options

Based on the analyzed situation and user's answers, generate 2-3 actionable moves.

## Situation Summary:
{summary}

## Situation Type: {situation_type}
## User Mood: {mood_state}

## Questions and Answers:
{questions_and_answers}

{template_guardrails}

## Requirements:
1. Generate exactly 2-3 moves (labeled A, B, C)
2. Each move must include:
   - Clear title (5 words max)
   - When to use (1-2 lines)
   - Tradeoff (1 line)
   - Gentleman score (0-100)
   - Risk level (low/med/high)
   - Probability of progress (0.0-1.0)
   - Criteria scores (each 0-10)
   - Two script variants (direct and softer)
   - Timing recommendation
   - Branch responses for warm/neutral/cold reactions

3. If mood is anxious/tired/horny/angry:
   - Include a "Wait and Reset" move as one option
   - Make scripts shorter and safer
   - Set cooldown_recommended to true with reason

## Gentleman Score Criteria (each 0-10):
- self_respect: Does this maintain the user's dignity?
- respect_for_her: Does this respect her autonomy and comfort?
- clarity: Is this clear and honest?
- leadership: Does this show confident initiative?
- warmth: Is this warm and approachable?
- progress: Does this move things forward?
- risk_management: Does this manage downside risk?

## Script Requirements:
- Direct variant: Confident, clear, gets to the point
- Softer variant: More cautious, gives more room
- Both must be under 50 words
- No manipulation, guilt, or pressure

## Hard Guardrails (Reject Any Move That):
- Suggests persistence after rejection
- Uses jealousy or manipulation
- Involves lying
- Pressures or guilts
- Sends wall of text (>200 words)
- Escalates physically without clear signals

## Output JSON Schema:
{{
  "moves": [
    {{
      "move_id": "A",
      "title": "string (5 words max)",
      "when_to_use": "string (1-2 lines)",
      "tradeoff": "string (1 line)",
      "gentleman_score": 0-100,
      "risk_level": "low|med|high",
      "p_raw_progress": 0.0-1.0,
      "p_calibrated_progress": 0.0-1.0,
      "criteria_scores": {{
        "self_respect": 0-10,
        "respect_for_her": 0-10,
        "clarity": 0-10,
        "leadership": 0-10,
        "warmth": 0-10,
        "progress": 0-10,
        "risk_management": 0-10
      }},
      "scripts": {{
        "direct": "string",
        "softer": "string"
      }},
      "timing": "string",
      "branches": {{
        "warm": {{"next_move": "string", "script": "string"}},
        "neutral": {{"next_move": "string", "script": "string"}},
        "cold": {{"next_move": "string", "script": "string"}}
      }}
    }}
  ],
  "cooldown_recommended": boolean,
  "cooldown_reason": "string or null"
}}

Respond with valid JSON only."""


def get_execution_plan_prompt(
    move_title: str,
    move_details: str,
    chosen_script: str,
) -> str:
    """Generate the execution plan prompt."""
    return f"""## Task: Generate Execution Plan

Create a concrete execution plan for the chosen move.

## Chosen Move: {move_title}
## Move Details: {move_details}
## Script to Use: {chosen_script}

## Requirements:
1. Generate 3-6 specific steps
2. Include the exact message/opener
3. Include an exit line if things go cold
4. Include one boundary rule

## Output JSON Schema:
{{
  "steps": ["step 1", "step 2", "step 3"],
  "exact_message": "string - the exact opener/message",
  "exit_line": "string - graceful exit if not receptive",
  "boundary_rule": "string - one rule to follow"
}}

Respond with valid JSON only."""
