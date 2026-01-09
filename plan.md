Decision GPT Algorithm and Design Specification
1. Decision Pipeline Spec (Phases and Stop Conditions)

The decision-making process is structured into clear phases, inspired by classic decision frameworks. Each phase has defined inputs, outputs, a stopping criterion, and known failure modes:

Phase 0: Intake (One-Line Decision & Metadata) – Input: The user provides a concise decision statement (e.g. “Deciding whether to move to a new city”). Contextual metadata (domain, urgency, stakes) is also captured. Output: A confirmed decision_statement and basic metadata (deadline, decision type). Stop Condition: The user agrees the statement reflects the decision to be made. Failure Modes: If the user problem is ill-defined or actually multiple decisions, the assistant may need to help narrow scope (failure if it proceeds with an unclear problem).

Phase 1: Clarify (Interactive Questioning) – Input: The decision statement and any initial info. Process: The system asks targeted questions to flesh out criteria, constraints, assumptions, and priorities. (This corresponds to “understanding the problem or objective”.) Output: A populated Decision Canvas (see Section 3) with fields like criteria (and their weights), hard/soft constraints, key assumptions (with confidence), and the user’s objectives. Stop Condition: The marginal value of asking another question is low (diminishing returns) or a preset question cap is reached. At this point, enough critical information has been gathered to proceed. Failure Modes: Asking too many questions (user fatigue), or missing a critical factor due to poor question selection. The system mitigates this by prioritizing high-value questions (see Section 2) and stopping when additional info yields minimal benefit.

Phase 2: Options (Generate & Refine Options) – Input: A clarified Decision Canvas from Phase 1. Process: The system generates a limited set of 2–3 actionable options plus a “do nothing / status quo” option. Options are trimmed via constraint-first filtering (discard any that violate hard constraints) and by focusing on a small number of diverse, high-quality choices (to avoid choice overload). The idea is to “thin-slice” the decision space and prevent analysis paralysis by not overloading the user with too many alternatives. Output: An options[] list in the canvas, each option with descriptive metadata (estimated pros/cons, scores on criteria, etc.). The system also computes an internal fit score for each option based on the user’s weighted criteria and other heuristics (see Section 5). Stop Condition: 2–3 viable options (plus the default “do nothing”) have been identified and evaluated against the criteria. Failure Modes: If no option meets hard constraints (failure to find feasible options), the assistant backtracks to Phase 1 to gather missing info or adjust constraints. If only one option is found (apart from doing nothing), the assistant may prompt for creative brainstorming or use option-generation heuristics to produce an alternative, since having at least two distinct options is critical for a real choice.

Phase 3: Commit (Decision & Action Plan) – Input: The evaluated options and Decision Canvas. Process: The system presents the options with summarized “Fit: High/Med/Low” ratings rather than raw scores or probabilities (to avoid overwhelming or “creepy” precision). The user chooses one option. Then the system helps solidify commitment: it formulates an action plan for the chosen option and probes for implementation details and contingency planning. This includes setting a “next action” and identifying if/then branches for key risks (“If X happens, then do Y”). The assistant triggers decision quality checks here, like a pre-mortem (“Imagine it’s months later and this choice failed – why?”) to prompt risk mitigation, and a reversibility check (highlight if the decision is easily reversible or a one-way door). Output: Updated canvas with chosen_option_id, a concrete next_action, listed risks with mitigations, and notes on reversibility/stakes. Stop Condition: The user has a clear commitment to an option and a plan (they explicitly say they’re ready to act, or the action steps are all defined). Failure Modes: The user might waver (e.g. second-guessing the decision). The assistant counters this by referencing the earlier criteria and encouraging a firm decision (as Mallory notes, delaying or second-guessing after thorough analysis only undermines future confidence). If the user still cannot commit, the system may offer a short “cooldown” or revert to Phase 2 to reconsider alternatives.

Phase 4: Outcome Logging & Calibration – Input: The chosen option and action plan, after some time has passed (this phase often occurs asynchronously post-decision). Process: The system prompts the user at defined intervals (e.g. 2 hours, 24 hours, 2 weeks later) to log the outcome of the decision: Did it succeed or not? How does the user feel (sentiment)? This includes capturing a binary success metric (or a scalar outcome if applicable) and the user’s self-reported satisfaction or regret. These logs are used to calibrate the decision model over time. The system computes a Brier score for the decision’s predicted success vs actual result (see Section 6) to update the model’s calibration. Output: Outcome fields in the canvas (actual result, time to outcome, user sentiment, etc.), and updated calibration parameters (stored globally for the user/model, not necessarily all in the canvas). Stop Condition: Outcome has been recorded and any learning (e.g. was our prediction accurate?) has been extracted. Failure Modes: The user might drop off and not report outcomes, reducing the feedback for learning – the product addresses this via reminders and making logging easy. Another risk is misinterpreting outcomes (for instance, a good decision can still have a bad outcome due to bad luck). To counter this, the system’s Decision Quality Heuristics separate the process from the outcome: even if an outcome was negative, the focus is on whether the decision process was sound. Over time, Phase 4 data helps improve Phase 2 (better probability estimates) and Phase 1 (highlighting which questions were predictive of success).

2. Question Selection Algorithm

Choosing which question to ask next is crucial – we want to maximize decision clarity and quality while minimizing user effort. The algorithm treats each potential question as an information-gathering action with a cost (time/effort) and a value (expected improvement in the decision). It uses a scoring system inspired by the Value of Information (VoI) concept: “how much answering a question allows a decision-maker to improve their decision”. Below are the components of this algorithm:

a. Question Value Scoring (VoI-based): We assign each candidate question a Question Value Score that estimates the impact of that question on the decision outcome. This score considers factors like: does the question reduce uncertainty about a key criterion or assumption? Would the answer eliminate or favor certain options? For example, asking “What is your budget range?” has high value if cost could rule out options. We use proxies for information gain: questions that split likely decision outcomes or rule in/out an alternative score high. In formal terms, the algorithm estimates the expected change in the best option’s score or the confidence in the decision, if that question were answered. A question that could change the recommended option has very high VoI. Questions whose answers likely wouldn’t affect anything (e.g. asking about a criterion that applies equally to all options) score low. We also incorporate uncertainty: if the model is currently “unsure” about some canvas fields (e.g. assumption confidence is low or criteria weights undefined), questions targeting those unknowns get a boost. In summary, the scoring function favors questions that shrink the decision uncertainty the most per unit effort. (This is analogous to focusing on “critical uncertainties” in decision analysis.)

b. Detecting Missing Critical Variables: The system maintains a checklist of critical decision elements (criteria, constraints, etc.). After each answer, it checks which essential fields remain blank or highly uncertain. If any critical slot is empty, questions that fill those take priority. For example, if no criteria have been identified yet, “What matters most to you in this decision?” becomes a mandatory early question. Conversely, if the user has already provided plenty of detail on criteria and options, the algorithm may decide no further clarification is needed and proceed to option generation. This addresses the stopping rule: the question phase ends early if the marginal value of more questions is below a threshold. We explicitly monitor diminishing returns: as soon as additional questions yield minimal new insight, we stop querying. For instance, if the last two questions barely changed the ranking of options or the predicted success probability, that suggests we have enough info (or the remaining uncertainty can only be resolved by actually making the decision). The system is effectively satisficing – once the decision canvas is “good enough” for a high-quality choice, it moves on without interrogating every detail. This prevents infinite questioning and respects user time.

c. Question Cap Strategy (Quick vs Deep Mode): To enforce efficiency, we implement mode-based caps: in Quick mode, the assistant asks at most ~5 questions; in Deep mode, it may ask ~12–15 (spread over multiple turns if needed). These caps are tunable but serve as safety limits to avoid exhausting the user. The algorithm chooses the highest-value questions first, so that even in Quick mode the most important bases are covered. If the cap is reached and some less critical details remain, the assistant will proceed with whatever information is gathered (possibly flagging any unknowns as assumptions). The user can always volunteer more info or switch to deep mode if unsatisfied. This approach recognizes diminishing returns – beyond a certain number of questions, each yields progressively less benefit. By capping, we force the algorithm to prioritize ruthlessly. (Internally, we treat it like a budgeted information acquisition problem: spend your “5 questions budget” for maximal gain.)

d. “Why I’m Asking” Tooltips: Every question the system asks comes with a brief explanation visible to the user (e.g. a tooltip or subtext). The algorithm generates these by referencing the question’s purpose and effect on the canvas. For example, if the question is “How would you define success for this decision?”, the tooltip might say: “Why I’m asking: Defining what a successful outcome looks like will clarify your top criteria. What this changes: It helps prioritize options that meet your true goal.” These explanations increase transparency and user trust. The content is templated: the system knows which canvas field or heuristic a question maps to, so it can fill in a template like “This question helps us update <field> which will influence <outcome>.” For instance, for a question aimed at uncovering constraints, the tooltip might read: “Knowing any deal-breakers ensures we only consider feasible options (this will filter out options that don’t meet your hard requirements).” The tooltips are concise (one sentence on the rationale, one on the impact) to avoid overwhelming the user. They effectively educate users on decision best-practices (like a coach explaining the reasoning behind each step) and reinforce that the system isn’t asking random or generic questions.

e. Avoiding Vague Questions – Specificity Rules: The algorithm actively avoids broad, ambiguous questions that yield unclear answers. It uses a library of rewrite rules and context to make questions concrete. For example, instead of asking “What are your values?” (too vague), it might ask “Is long-term career growth more important than immediate salary in this decision?” if it’s a career context, or “Which matters more for you now: financial security or pursuing a passion?”. It achieves this by leveraging the decision domain and any user profile info. If the user’s decision statement contains domain cues (say the category is “relationships”), the questions are phrased with relevant language (e.g. “What qualities in the relationship are you unwilling to compromise on?” rather than a generic “What are your criteria?”). We have rules to break down multi-faceted questions: if a question would contain multiple concepts, split them. For instance, “What are your financial and personal considerations?” becomes two separate questions (“What financial constraints or goals do you have?” and later “What personal or emotional considerations matter here?”). The system also avoids leading or loaded questions – it neutralizes wording to not bias the user’s answer. If the model generates a question like “Don’t you think option A is too risky?”, the algorithm would suppress that in favor of an open phrasing (“How do you feel about the risks involved in Option A?”). In short, every question is targeted, clear, and singular. Any detected vagueness triggers a rewrite using context or examples (“if asking about timeline, include units or specific period; if asking about priorities, list sample factors to consider”). By following these rules, the Q&A feels like a structured interview guided by best practices rather than a therapy session or aimless chat.

Pseudocode for the question selection loop might look like:

questions_asked = 0
while questions_asked < max_questions:
    candidates = generate_possible_questions(current_canvas)  # templated questions for empty/uncertain fields or heuristics
    for q in candidates:
        q.value = estimate_VoI(q, current_canvas)
    best_q = argmax(candidates, key=q.value)
    if best_q.value < threshold_min_gain:
        break  # stop if no question would add significant value
    ask(best_q, with_tooltip=True)
    record_answer(best_q.field, user_response)
    update_canvas(best_q.field, user_response)
    questions_asked += 1


This loop ensures we pick the highest-value question each time, and stops when additional questions don’t justify themselves (either hitting the cap or low expected gain).

3. Canonical Decision Canvas Schema

We represent the decision in a structured JSON schema that captures all relevant elements of the Decision Canvas. This schema ensures consistency and allows validation of input. Below is a high-level schema (in JSON Schema format) covering the required fields, along with types, some enums, and validation rules:

{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DecisionCanvas",
  "type": "object",
  "properties": {
    "decision_statement": {
      "type": "string",
      "minLength": 5,
      "description": "One-line description of the decision to be made."
    },
    "options": {
      "type": "array",
      "minItems": 1,
      "maxItems": 5,
      "items": {
        "type": "object",
        "required": ["id", "description"],
        "properties": {
          "id": { "type": "string", "description": "Unique option identifier" },
          "description": { "type": "string", "description": "Option text" },
          "pros": { "type": "array", "items": { "type": "string" } },
          "cons": { "type": "array", "items": { "type": "string" } },
          "score": { "type": "number", "minimum": 0, "maximum": 10, "description": "Internal 0-10 score based on criteria" },
          "fit_label": { "type": "string", "enum": ["Low", "Medium", "High"], "description": "Overall fit rating displayed to user" }
        }
      },
      "description": "List of decision options under consideration (including 'do nothing')."
    },
    "criteria": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "weight"],
        "properties": {
          "name": { "type": "string" },
          "weight": { "type": "number", "minimum": 0, "maximum": 1 }
        }
      },
      "description": "Evaluation criteria with relative weights (normalized to sum to 1)."
    },
    "constraints": {
      "type": "object",
      "properties": {
        "hard": {
          "type": "array", 
          "items": { "type": "string" },
          "description": "Non-negotiable requirements (options violating these are pruned)."
        },
        "soft": {
          "type": "array",
          "items": { "type": "string" },
          "description": "Desired but flexible preferences."
        }
      }
    },
    "assumptions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["statement", "confidence"],
        "properties": {
          "statement": { "type": "string" },
          "confidence": { "type": "string", "enum": ["Low", "Medium", "High"] }
        }
      },
      "description": "Key assumptions the decision hinges on, with confidence levels."
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["risk", "mitigation"],
        "properties": {
          "risk": { "type": "string", "description": "Identified potential problem if chosen option fails." },
          "mitigation": { "type": "string", "description": "Planned step to prevent or address this risk." }
        }
      },
      "description": "Risks of the chosen option and how to mitigate them (populated at commit)."
    },
    "timeline": {
      "type": "string",
      "format": "date-time",
      "description": "Deadline or time horizon for the decision or its outcome (if any)."
    },
    "reversibility": {
      "type": "string",
      "enum": ["Reversible", "Partially Reversible", "Irreversible"],
      "description": "How easily the decision can be undone (affects risk posture)."
    },
    "stakes": {
      "type": "string",
      "enum": ["Low", "Medium", "High"],
      "description": "The importance/impact of this decision (e.g. consequence magnitude)."
    },
    "next_action": {
      "type": "string",
      "description": "Immediate next step the user will take to implement the chosen option."
    },
    "chosen_option_id": {
      "type": "string",
      "description": "The ID of the option the user committed to (set in Phase 3)."
    },
    "outcome": {
      "type": "object",
      "properties": {
        "executed": { "type": "boolean", "description": "Whether the chosen action was executed." },
        "success": { "type": "boolean", "description": "Whether the outcome was successful (as defined by user upfront)." },
        "recorded_at": { "type": "string", "format": "date-time", "description": "Timestamp of outcome logging." },
        "sentiment": { 
          "type": "string",
          "enum": ["Very Satisfied", "Satisfied", "Neutral", "Regretful", "Very Regretful"],
          "description": "User's emotional state or regret level after outcome."
        },
        "predicted_success_prob": { "type": "number", "minimum": 0, "maximum": 1, "description": "Model's predicted probability of success for chosen option (p_raw or p_calibrated as stored)." },
        "brier_score": { "type": "number", "minimum": 0, "maximum": 1, "description": "Squared error between predicted success probability and actual outcome (0=perfect prediction, 1=worst)." }
      }
    }
  },
  "required": ["decision_statement", "options", "chosen_option_id"]
}


Notes on the schema: Many fields are optional until populated by the respective phase. For example, criteria[] might be empty if the user hasn’t defined any – but the algorithm ensures critical ones are filled by Phase 1. The options[] list is required (we need at least one option to decide on), and chosen_option_id becomes required by the end of Phase 3. Enums are used for categorical fields like reversibility (to standardize values like Reversible/Irreversible rather than free text). Weights in criteria are fractional (0 to 1) and can be validated to sum to ~1 (the system can normalize if needed). The outcome sub-object is filled in Phase 4; it contains both the actual result and the model’s prediction for that decision, allowing computation of the Brier score for calibration. The assumptions include a confidence enum – this forces the assistant to explicitly label assumptions as Low/Medium/High confidence, which can later be used for branching (revisiting low-confidence assumptions in “what-if” scenarios). We include timeline for deadlines or timing considerations, and stakes to capture the decision’s significance (which might influence how the algorithm behaves – e.g. a High-stakes irreversible decision triggers more thorough questioning and caution). The JSON schema above can be used to validate user inputs and ensure completeness of the canvas at various checkpoints.

4. Decision Quality Heuristics Library (Modular Checks)

Our system incorporates a library of proven decision-making techniques and “checks” derived from research in decision science, behavioral economics, and coaching practices. Each heuristic is implemented as a module that can be triggered at the appropriate time, asking the user a targeted question (or performing an action on the canvas) to improve decision quality. Below we detail each module, when to trigger it, what it asks, and how it updates the canvas:

Reversibility Check (One-way vs Two-way door): When to trigger: During Phase 1 (Clarify) for context and again in Phase 3 (Commit) for final perspective. If the user hasn’t explicitly considered how reversible the decision is, the module fires. Questions: “How easily could you undo this decision if needed?” or “Is this a one-way door (irreversible) or a two-way door (changeable) decision for you?”. Why: Jeff Bezos famously distinguishes irreversible “Type 1” decisions that require slow, careful deliberation, vs reversible “Type 2” decisions that can be made quickly and changed if wrong. A reversible choice shouldn’t be over-analyzed – the risk of waiting outweighs the risk of a quick trial. Updates: The user’s answer is recorded in the reversibility field (enum). If Reversible, the assistant might down-weight exhaustive analysis (perhaps suggesting a quick pilot of an option since it’s low regret). If Irreversible & High stakes, the assistant ensures all major criteria are considered and may prolong Phase 1 questioning (since the “cost to gather more information is worth it” for one-way decisions). It might also raise the bar for committing (ensuring the user double-checks their readiness or perhaps seeks additional expertise if needed). Essentially, this module calibrates the depth of decision process to decision type: “Make reversible decisions fast, and irreversible ones slow” becomes a programmatic rule.

Default Bias / Status Quo Check (“What if you do nothing?”): When to trigger: Early in Phase 2 (Options) and revisited in Phase 3. After generating options, the module ensures that “do nothing” (or delaying the decision) is explicitly considered as a baseline. Questions: “What happens if you decide to not choose any of these options – i.e. stick with the status quo?” and “Is doing nothing an acceptable or desirable outcome for you?”. Why: People have a cognitive tendency to stick with the default state or choose inaction (status quo bias). By explicitly surfacing the default scenario, we force the user to evaluate it objectively rather than by inertia. Often, articulating “doing nothing” as an option either reveals it’s worse than active options (spurring the user to overcome indecision) or in some cases, it might actually be the best choice (which is fine, but then it’s a conscious choice, not a bias). Research shows default bias encompasses preferring inaction and sticking with previous decisions. Updates: The canvas always includes a “do nothing” option in options[] by default. This module may add notes to that option’s pros/cons (e.g. pros: no immediate effort or change; cons: missed opportunities, or problem persists). It may also update constraints: if doing nothing violates a hard constraint (e.g. a deadline or external requirement), that’s recorded (so the user realizes inaction might not actually be viable). If the user expresses strong attachment to the status quo despite acknowledging major drawbacks, the assistant flags default_bias as a potential issue (this could be a hidden field or just an internal flag prompting the assistant to gently challenge the user’s reasoning). Overall, this module ensures “Default/Do nothing” is treated as a conscious option with its own outcomes, helping the user overcome any unconscious bias for or against it.

Pre-Mortem (Prospective Hindsight Risk Assessment): When to trigger: In Phase 3 (Commit), right after the user has chosen an option but before finalizing the plan. Questions: The assistant will say: “Let’s do a quick pre-mortem. Imagine it’s [some time frame in future] and this decision turned out to be a failure. List 2-3 reasons – what could have gone wrong?”. Follow-up: “What can we do now to prevent or mitigate these reasons?” Why: A pre-mortem encourages prospective hindsight, a technique where you assume the decision failed and work backward to identify possible causes. Gary Klein’s research found this increases the ability to spot risks by 30%, by making it safe to voice concerns that people might otherwise suppress. It counteracts optimism bias and groupthink. Updates: The reasons the user lists are added to the risks[] list in the canvas, each with a corresponding mitigation (the assistant helps turn the user’s ideas into concrete safeguards). For example, if the user says “If it failed, maybe because I didn’t have a backup plan for X,” the assistant records risk: “No backup plan if X happens” and mitigation: “Develop backup plan X (do Y if X occurs).” This not only enriches the action plan but also psychologically prepares the user – by addressing those failure points now, the user can proceed more confidently. This module effectively injects a final checkpoint to “imagine it failed and see if you still want to proceed”. If the user discovers an unacceptable risk with no mitigation, they might reconsider their option (the system would allow branching or option revision in that case). In practice, however, most pre-mortem outputs can be mitigated, improving the plan’s robustness without derailing the decision.

10/10/10 Future Frame: When to trigger: Typically in Phase 1 (Clarify), especially for emotionally-charged personal decisions where short-term emotions might cloud long-term thinking (common in relationship or career dilemmas). Also can be used in Phase 3 if the user still seems torn. Questions: “Consider the consequences of this decision in 10 minutes, 10 months, and 10 years – how do you think you will feel at each of those times?”. We might break it down into three prompts for each time frame, or ask the user to reflect holistically. Why: Suzy Welch’s “10-10-10” rule forces a decision-maker to weigh immediate, mid-term, and long-term implications, helping balance present bias vs future benefits. It often clarifies one’s values: an option that feels good now but terrible in 10 months might be the wrong choice, for example. Research (and Welch’s own experience) suggest this method helps surface what really matters to the person by comparing emotional reactions over time. Updates: The user’s reflections might update criteria or weights – for instance, if in 10-year view the user realizes they value “being true to myself” over “avoiding conflict,” the assistant might add a criterion like “authenticity” or increase the weight of long-term outcomes. It also can affect the options’ evaluation: if the user expresses that in 10 months they’d deeply regret not taking a certain opportunity, the model can tag that option as aligned with avoiding future regret (essentially it’s a positive indicator). This ties into regret minimization too (see next). The key outcome is documentation of the user’s time-based feelings: perhaps adding a note in each option’s pros/cons like “10mo: likely relief; 10yr: proud of having taken risk” versus another option “10mo: still wondering ‘what if’; 10yr: regretful if not tried.” These insights make it into the final consideration set or even the UI (perhaps as part of option details under a “future perspective” section). The process helps users step out of the immediacy of the decision and consider long-term consequences, often leading to more value-consistent choices.

Regret Minimization (Future Retrospective): When to trigger: Often for career or major life decisions (Phase 1 or 2), especially if the user mentions fear of regret or being torn by risk vs opportunity. Also if the user seems very risk-averse, this can be invoked. Questions: “Project yourself to age 80 and look back on this moment – which option do you believe you’ll regret not doing the most?” This can be phrased as Jeff Bezos did: “When I’m 80, will I regret not having tried [option]?”. Why: Bezos’s Regret-Minimization Framework is a powerful way to clarify choices by focusing on long-term regret avoidance. It shifts perspective from short-term fears (like failure) to long-term fulfillment. Bezos reasoned that even if his risky choice failed, the pain of failure would be transient, but the regret of not trying would haunt him. This heuristic counters the bias of over-valuing immediate loss vs long-term missed opportunities. Updates: The user’s answer directly influences option ranking. If they indicate “At 80, I’d regret not doing option B,” then option B likely gets a higher subjective value. The assistant can mark that option with a high score on criteria like long_term_alignment or personal fulfillment. Conversely, if an option doesn’t pass the regret test (the user says “I wouldn’t regret skipping it”), that option might be downgraded or even removed if it only appealed to short-term convenience. We also record the user’s stated greatest potential regret as a kind of decision driver – e.g., in the canvas or summary: “User’s future-self priority: avoid regret of not pursuing X.” This can be used in Phase 3 to bolster commitment (“Remember, you said your 80-year-old self would regret not doing this – that suggests it’s the right move for you”). Essentially, the Regret module injects the voice of the user’s future self into the decision. It aligns with values and can embolden the user to choose a courageous option if it’s truly meaningful (the system will also temper this with practical constraints, of course). This module encourages bold decisions when appropriate, echoing the insight that the pain of “what if I had done that” often outweighs the pain of failure.

Base-Rate Check (Outside View & Reference Class): When to trigger: In Phase 1 or 2, whenever the decision involves predictions (like “Will I succeed at X?” or “How likely is outcome Y?”). If the user is making assumptions that sound optimistic or if the decision is of a type with known statistics (startup success, weight loss, etc.), the module activates. Questions: “How often do people in situations like yours achieve the outcome you want? What do the base rates say?” and “What usually happens if someone [does option] under similar circumstances?” Why: People often ignore the base rate (the statistical frequency of an event) and rely on their specific scenario (inside view), leading to planning fallacy or wishful thinking. For instance, we tend to think our project will finish on time even if most similar projects don’t. Taking the outside view by examining the reference class outcome improves forecasting accuracy. Kahneman notes that using a base rate makes your estimates “much more accurate than if you only consider your own case”. Updates: The assistant might supply known base rates (if in its knowledge base) or simply prompt the user to recall them. For example, in a career decision about starting a business, it could remind “Typically, only ~50% of new businesses survive 5 years. How does that inform your decision?” If the base rate information is available, it may be added as an assumption with a low confidence if the user thinks they’re an exception (e.g., assumption: “I will beat the odds, despite only 1 in 10 succeed”, confidence: low). Or it updates risk: “Acknowledged risk: outcome may follow historical odds (e.g. fail 50% chance).” The purpose is not to deter the user arbitrarily but to ground their expectations. If the user still chooses an option with poor odds, at least it’s an informed risk. In calculations, if probabilities are being used (see Section 6), the base-rate can serve as a prior for our p_raw. For example, if the user estimates success chances unrealistically high, the system can adjust (calibrate) down toward the base rate unless strong evidence suggests otherwise. This module essentially adds an “outside view” lens to the decision canvas, often by adding a note in the assumptions like “Base rate: ~X% success historically” and potentially nudging the option score or probability to not wildly exceed that without reason. It checks optimism and anchors the decision in reality.

“Thin Slice” Option Limiter: When to trigger: During Phase 2 (Options), right after initial option generation. If more than 3–4 options are on the table (excluding the do-nothing), this module kicks in to enforce focus. Function: It will prune and prioritize options to a manageable few. Why: Research on decision-making and user experience indicates that too many choices can overwhelm and paralyze (the paradox of choice). We purposely limit to 2–3 options to force clearer comparisons and decisions. By thin slicing, we mean capturing the essence of the choice by selecting a representative small set of options. Malcolm Gladwell’s notion of “thin-slicing” suggests people can make better decisions with a small amount of key data than by drowning in information. Here, fewer options = more cognitive clarity. Implementation: If the user or brainstorming yields a long list of options (say 6 job offers, or 10 ways to invest money), the assistant will work with the user to narrow them. It might ask: “Which three of these are the most promising to you? Let’s focus on those.” Or it might automatically score them roughly on key criteria and drop the lowest. In fact, the Option Generation step itself usually generates only up to 3 high-scoring options by design (see Section 5) to avoid overload. Updates: The final options[] in the canvas is constrained to a max of 3 (the schema allowed up to 5 mostly to include “do nothing” and maybe an extra variant if needed, but the UI will typically show 2–3). If more were initially listed, those get filtered out or merged. The module might merge similar options (if two options are only minor variations, combine into one with notes). It also explicitly labels an option as “delay decision” if needed (some decisions include the meta-option to defer making the choice; this can be considered “do nothing for now”), to ensure that if the user isn’t ready, delaying is recognized as an option rather than an implicit default. The net effect: the user is presented with a concise slate – e.g. “Option A, Option B, or Do Nothing.” This is easier to compare and decide on. Any pruned options can be noted in the canvas’s history in case of branching later (so if the user asks “what about option X we dropped?”, the system can retrieve it in a branch scenario). By limiting options, we reduce decision fatigue and force the decision to hinge on the truly distinguishing factors rather than juggling minor nuances among many choices.

Constraint-First Filtering: When to trigger: Immediately when generating or inputting options (Phase 2) and also dynamically if the user adds a new hard constraint later. Function: Eliminate any option that fails to meet hard constraints and flag those that don’t meet soft constraints. Why: This is a straightforward dominance filter – an option that violates a must-have requirement is not viable and only clutters the decision space. It’s aligned with rational decision practices: apply knockout criteria first, then compare alternatives on other merits. Updates: The assistant checks each option against each item in constraints.hard. For example, if a hard constraint is “budget ≤ $1000” and an option “Purchase new device for $1500” exists, that option is removed (or at least marked as “Infeasible”). We may alert the user: “Option X was removed due to violating your hard constraint: budget.” This builds trust that the system respects their requirements. If a soft constraint (preference) is not met, the option isn’t removed but might get a penalty in scoring or a warning label. For instance, soft constraint “remote work preferred” and an option is “Job offer that requires relocation” – that option remains but is annotated (maybe a con: “Doesn’t satisfy your preference for remote work”). The canvas might reflect this by listing constraint mismatches in the option’s cons. This module ensures that by the time we present options to the user, all are realistic and honor their non-negotiables, streamlining the final choice. It effectively prunes the decision tree branches early, saving time. (In pseudocode: for each option, for each hard_constraint, if option violates -> drop option.) If dropping an option leaves none, that indicates an inconsistency in user inputs (e.g., constraints too restrictive); then the assistant would either relax a constraint (with user permission) or go back to Phase 1 to re-evaluate priorities.

Each of these modules can be thought of as pluggable checks that the main pipeline calls. For example, after clarifying inputs, the pipeline calls ReversibilityCheck() and BaseRateCheck(). After generating options, it calls ConstraintFilter() and ThinSliceLimiter(). Before final decision, it calls PremortemCheck(), DefaultBiasCheck(), etc. This modular design lets us maintain a Decision Quality Heuristics Library where new techniques can be added without altering core logic. We also ensure these checks are context-sensitive: e.g., the 10/10/10 or Regret modules might not run for a trivial low-stakes decision (the system might skip them if stakes are “Low”), whereas for a major life choice, they definitely will run.

By integrating research-backed techniques in this way, the system guides the user through a comprehensive analysis without the user needing to know these methods by name. It “bakes in” good decision habits: thinking of opportunity cost (default bias check), considering future outcomes (10/10/10, regret), using outside data (base-rate), limiting choices (thin-slice), planning for failure (premortem), etc. These ensure quality control on the decision process itself, not just the content.

5. Option Generation + Ranking (Without Being Creepy)

When it’s time to propose options (Phase 2), the system generates a small set of actionable choices and ranks them internally against the user’s criteria and other factors. The design goals are to avoid seeming “creepy” or overly prescriptive (we don’t want the user to feel the AI is making the decision), while still providing intelligent, personalized suggestions. Here’s how we do it:

Option Generation Method: By Phase 2, we have the decision statement, key criteria, and constraints. In many cases, the user may have already mentioned one or two options they’re considering. The assistant will include those and possibly generate an additional alternative the user hasn’t explicitly considered (to avoid false dichotomies). Option generation draws from a few strategies:

Transform the Problem: Use known solution templates (e.g., if the decision is “choose a job”, options are basically the different offers or staying put; if decision is “improve my relationship”, options might be “have an honest talk”, “seek counseling”, or “end it”). The system uses domain knowledge to suggest standard moves for common decisions.

Use Criteria to Differentiate: For example, if criteria are stability vs growth, the assistant might generate one option maximizing stability and another maximizing growth to illustrate the trade-off.

Incorporate Status Quo: Ensure one option is explicitly “do nothing / maintain current state / delay” as discussed. This is always included unless truly not applicable.

Limit to Max 3: As per the thin-slice heuristic, we intentionally do not output a laundry list. If the user provided many options, we apply constraint filtering and prioritization (see Section 4). If the user provided none, we generate at most two or three viable ones. This keeps things focused.

The generation may involve a call to an LLM or rules-based approach to come up with creative alternatives, but given our budget constraint (minimize LLM calls), the system will first try deterministic approaches (like checking a small library of common alternatives for the decision domain, or recombining user’s own ideas). Only if needed, a single LLM call might be used like “brainstorm an out-of-the-box alternative given this scenario,” and even then we would filter its outputs through constraints before presenting.

Internal Scoring Rubric (0–10 scale): Each option is evaluated on multiple criteria to produce an overall score. We assign weights to criteria (from the canvas) and also consider some universal factors. A possible rubric (scoring dimensions) includes:

Objective Criteria Fit: For each user-defined criterion (e.g. “salary”, “work-life balance”), we score the option from 0–10 on that. These get weighted by the user’s weights (if the user said salary is 0.7 weight and balance 0.3, the weighted sum contributes accordingly).

Self-Respect / Identity Fit: Does this option align with the user’s core values and sense of self? (This comes from any values mentioned or heuristics like regret/10-10-10 results. E.g., if user said authenticity is key, an option that compromises that scores low here.)

Ethical/Social Respect: Is the option respectful to others and ethically sound? (We include this to catch obviously bad or biased suggestions. For instance, an option “Lie to your friend” would score 0 on ethics, likely getting dropped. The assistant generally wouldn’t generate unethical options in the first place, but this is a safeguard.)

Clarity: How clear and concrete is this option? A nebulous option (“try to improve things somehow”) scores low, whereas a specific plan (“sign up for a course and switch careers to tech”) scores higher. We prefer options that are actionable and well-defined.

Progress & Growth: Does the option represent positive progress toward the user’s goals or growth? Or is it maintaining status quo? Depending on context, we may score doing nothing lower on this, and an ambitious option higher (unless user explicitly prioritizes stability over change).

Risk: We score higher for less risk if the user is risk-averse, or we incorporate risk as a negative factor overall. High risk lowers the score unless offset by high potential (which is often captured in criteria or long-term alignment).

Cost & Time: If an option requires significantly more cost or time than alternatives and the user has constraints, that option’s score is penalized. Conversely, a cost-effective, quick option might score higher.

Reversibility Fit: A highly reversible option might get a slight boost since it can be tried with less at stake (particularly if the decision was categorized as one where experimenting is okay). If irreversible and the user is wary, maybe a penalty unless it strongly meets other criteria.

Long-term Alignment: Does this option set the user up well for long-term success as they defined it (capturing things like career trajectory, relationship happiness years out, etc.)? This uses inputs from 10/10/10 or similar. E.g., an option that sacrifices long-term goals for short-term relief would score lower here.

Each of these can be normalized to a 0–10 scale and combined. For example, an internal scoring formula might be: Score = sum(criteria_i_score * weight_i) + bonus/malus for other factors. The output could be a raw score like 7.8 for Option A, 6.1 for Option B, 5.0 for “Do nothing”.

However, we do not show these raw scores to the user by default. Instead, we convert the top option’s score into a qualitative Fit rating for each: e.g., the highest option 7.8 becomes “High fit”, the one with 6.1 might be “Medium fit”, 5.0 might be “Low fit”. We define thresholds or relative scaling (perhaps >7 = High, 4–7 = Medium, <4 = Low, or simply relative to best option). This is what the UI displays, as the prompt specifies: only “Fit: Low/Med/High” by default; raw probabilities hidden under details. The idea is to communicate confidence or preference without over-precision. If the user wants more, they can click “Details” to see a breakdown: e.g. a table of criteria scores or even the numeric probabilities if they desire. This approach prevents the user from being overly anchored on a seemingly exact number (which might imply more certainty than exists).

Avoiding Creepy Suggestions: We ensure that any generated option is grounded in information the user provided or general common-sense, not some bizarrely specific insight that would make the user think “How did it know that?”. For instance, if the user didn’t mention their family, the assistant shouldn’t suddenly suggest “Ask your brother for help” out of the blue. We avoid using any personal data beyond the conversation. Options derived from patterns (like recommending a known strategy) will be explained in neutral terms. Also, we prefer to offer options as suggestions (“One possible option could be…”) rather than authoritative commands. This keeps the user in control. The assistant might even give each option in the form of choice persona like: “Option A: the safe bet – [description]. Option B: the bold move – [description].” framing them so the user can see the contrast and pick based on preference. This style feels less like the AI is making a judgement and more like it’s laying out a menu.

Method to Generate “Do Nothing/Delay”: As mentioned, we almost always include an explicit option reflecting inaction or deferring the decision. Its description could be tailored (“Stay in my current job for another year before deciding” or simply “Do nothing right now”). This is important for completeness and also leverages the default bias check (making the implicit explicit). The generation algorithm automatically adds this if the user didn’t, and evaluates it fairly. Sometimes “do nothing” might actually score reasonably (if no option clearly dominates it in benefit). If it scores low but the user seems inclined to it out of fear, the assistant can highlight that (e.g., Fit: Low for doing nothing because it doesn’t meet their stated goals or constraints).

Once options are generated and scored, the assistant presents them with brief supporting rationale (e.g., key pros/cons for each tied to user criteria). The user can then make an informed choice.

Pseudo-code snippet for option ranking might be:

for option in options:
    option.score = 0
    for criterion in criteria:
        option.score += criterion.weight * score_option_on(option, criterion.name)
    // add other factors
    option.score += bonus_for_clarity(option) 
                   + bonus_for_long_term(option) 
                   - penalty_for_risk(option) 
                   - penalty_for_cost(option)
    // etc, scaled appropriately
// Normalize scores 0-10:
max_score = max(opt.score for opt in options)
min_score = min(opt.score for opt in options)
for option in options:
    option.norm_score = 10 * (option.score - min_score) / (max_score - min_score)  // if range >0
    option.fit_label = ( "High" if option.norm_score >= 7 
                         else "Low" if option.norm_score <= 3 
                         else "Medium" )
sort options by option.score descending  // internal rank


The actual numeric formula can be refined, but the core is a weighted multi-criteria evaluation possibly akin to a decision matrix. This rigorous approach is balanced with the user’s qualitative input and the heuristics above to provide a recommendation that is both data-driven and aligned with the user’s values.

The result: 2–3 options plus the default, each with a High/Med/Low fit. The assistant might gently highlight the top-fit option (e.g., “Option A seems to align best with your priorities (High Fit), as it scores well on X and Y, whereas Option B is Medium Fit due to lower score on Z.”). But it stops short of outright saying “choose this one.” The final decision is left to the user, preserving agency.

This approach ensures the recommendations are transparent, personalized, but not overly deterministic – the user sees why an option is considered good or bad (through criteria and pros/cons), and the fit labels give guidance without implying certainty.

6. Probabilities & Calibration (Practical, Buildable)

Our system uses probabilities to express uncertainty in outcomes, specifically the probability that the chosen option will achieve the desired success outcome. We denote:

p_raw: the model’s initial estimate of success probability for an option (especially the chosen one).

p_calibrated: an adjusted probability after applying calibration based on past decisions.

What the Probability Represents: It’s essentially “Given all the information, how likely is it that this option will lead to a successful outcome (as defined by the user)?” Success outcome needs to be defined at intake (e.g., if the decision is which job to take, success might mean “I am satisfied in the new job 6 months in”). The probability is subjective, combining whatever data we have (user’s confidence, base rates, criteria fit, etc.) – it’s not a frequentist guarantee but a forecast that we want to make as well-calibrated as possible over time.

For example, if we say p_calibrated = 0.7 (70%) for the chosen option, we intend that in the long run, out of all decisions where we gave 70% chance, about 70% should succeed. Calibration means predicted probabilities match observed frequencies. If we consistently overshoot or undershoot, we correct it.

Producing p_raw: Initially, the model can derive a rough probability from the option’s score or using known data:

We might map the weighted score (from Section 5) to a probability. For instance, if an option scored 8/10, perhaps translate to 80% raw confidence. However, this might not be accurate since scores are relative and include qualitative factors.

Alternatively, we could train an internal simple model or use heuristics: start from a base rate probability of success (if available) and then adjust up or down based on how well this option meets criteria and mitigates risks.

The user’s own expressed confidence is valuable: if the user says “I’m 90% sure this will work,” p_raw might lean high (though the system will temper if user historically is overconfident via calibration).

If an LLM or prediction model is available, we might ask it for a probability estimate given the scenario (but to save calls, this could be done rarely or offline).

In practice, an easy way: assign p_raw corresponding to High/Med/Low fit tiers. E.g., High Fit -> p_raw ~0.7, Med -> ~0.5, Low -> ~0.3, adjusted by any concrete data. This is a starting estimate that we refine with calibration.

Calibration with Outcome Logs: Every time a decision’s outcome is logged in Phase 4, we get a data point: predicted p vs actual result (success=1 or fail=0). Over time, we gather a set of (p_raw, outcome) pairs. Because users might not make hundreds of decisions, data is sparse, so we use simple, robust calibration methods:

Binning: We can bucket decisions by predicted probability (e.g., 0–0.2, 0.2–0.4, 0.4–0.6, 0.6–0.8, 0.8–1.0). For each bin, compute the actual success frequency. For example, if we have 10 decisions with p_raw ~0.7 and 6 succeeded, actual frequency = 0.6. We then adjust future predictions in that bin towards 0.6 (the system might apply a linear interpolation or a lookup table). With few data points, we might use larger bins at first (like Low/Med/High bins).

Isotonic regression: As data grows (say dozens of points), we can apply isotonic regression which fits a non-decreasing mapping from raw probabilities to calibrated probabilities. This is a standard method that doesn’t assume a shape, just that higher p_raw should mean higher success chance. It will adjust the curve to better match observed outcomes. This method was mentioned as more powerful but requires more data, so it might come later.

Platt scaling: If we had a logistic model, we could do Platt scaling (fit a logistic function to map p_raw to actual outcomes). But in our context, simpler is fine.

Bayesian updating (low-data heuristic): For example, treat each decision as a Bernoulli trial. We could maintain a Beta distribution for calibration. Initially assume a prior (e.g., Beta(α=1, β=1) = uniform, meaning we have no bias). Each observed outcome updates a posterior on reliability. But because each decision has a different p_raw, it’s a bit complex to update a single beta. Instead, we might maintain calibration in bins as pseudo-counts: e.g., for the 0.7 bin, start with prior counts (3 successes, 7 failures as a mild prior making it ~30% success – meaning assume initial overconfidence until proven otherwise). Then as outcomes come in, add to these counts and compute empirical success rate.

The system can periodically recompute calibration parameters offline or on the fly after each new outcome. p_calibrated = f(p_raw) where f is the calibration mapping learned.

For example, suppose initially the assistant tends to be over-optimistic. After 20 decisions, it finds that when it said 80%, it was right only 60% of time. The calibration function f might then output ~0.6 when p_raw=0.8 going forward, until more data refines it. The UI to the user might not show these decimals except under details, but internally it improves honesty of predictions.

Brier Score Computation: We use Brier score as a measure of our calibration/accuracy. For each decision, Brier = (predicted_prob - outcome)^2. So if we predicted 0.8 and outcome was success (1), Brier = (0.8-1)^2 = 0.04. If outcome was failure (0), Brier = (0.8-0)^2 = 0.64. Brier ranges 0 (perfect prediction) to 1 (max error on a binary outcome). We will store each decision’s Brier in the outcome log (as shown in the schema under outcome.brier_score). Over time, we can track average Brier score – the goal is to reduce it, meaning our predictions are getting closer to reality. A well-calibrated system will have a low Brier and also proper calibration curve (like if we say 70% a lot, about 70% happen).

Practical Low-Data Calibration: Because each user might only log outcomes for, say, 10 decisions in months, we might aggregate calibration data across users or at least start with a global calibration (all decisions). If that’s not possible, we use domain knowledge to set an initial calibration. For instance, assume humans generally are overconfident in personal decisions – we might initially calibrate by pulling probabilities toward 0.5 a bit (a form of regularization). The system might initially output p_calibrated = (p_raw + 0.5)/2 as a naive shrinkage (meaning if it’s very sure, temper it, if it’s very unsure, also temper extreme low values up a bit). Then refine as we get personal data.

In the UI, when the user expands “Details”, we could show something like: “Predicted success chance: 70% (calibrated based on similar past decisions).” The word “calibrated” hints that it’s learned from experience, which may actually increase user trust if explained. We might even show a small calibration chart to interested users.

It’s important we don’t confuse the user with shifting probabilities. The user mostly sees Fit ratings unless they opt in. The calibration primarily serves to make our behind-the-scenes probability more accurate for measuring our performance and giving the user realistic expectations when they do choose to see the number.

Outcome Logging & Learning: Each outcome log entry provides one training point for calibration. With few data, our adjustments will be coarse. That’s fine; even knowing we were systematically 15% off is useful. For example, if after a while we see Brier score is high due to overconfidence, we adjust down all predictions a bit.

We also compute an individual Brier score for the user (average of their decisions’ Briers) and possibly a global one. Improvement in Brier over time is a key metric (see Evaluation Plan). A trending-down Brier means our predictions (and maybe decisions) are improving.

In summary, we define probabilities clearly, start with simple estimates, and update them with a calibration mechanism suitable for sparse data (binning or incremental updates). This ensures that over time, if the assistant often says “High Fit” but outcomes fail, it will learn to be more cautious (and vice versa). The calibrated probability is what we ultimately use to log and evaluate decision quality – ideally approaching a state where a “High (70%)” really means 70% success in practice. This keeps the system honest and continually learning from real-world results.

7. Branching Algorithm (Re-evaluating on New Information)

Decisions are rarely one-and-done; our product supports branching – creating a new decision path (DAG structure) when assumptions change or new information arrives. The goal of the branching algorithm is to reuse as much of the prior decision’s work as possible, only updating what’s affected by the changes, and to highlight the differences in outcomes.

When to Branch: A branch can be initiated by the user in cases like:

“What if I change this assumption?” (e.g., “Assume my budget is higher, which option would be best?”)

“If constraint X were lifted/added, how does the decision change?”

New information arrives post-decision (e.g., “I got an offer from another company, how does that compare?” – essentially a new option).

The user simply wants to explore a different scenario without overwriting the original (maintaining a history of scenarios).

Branch Creation: We implement branching by copying the original Decision Canvas to a new instance (inherit all fields), then applying the modifications. Each branch node in the DAG references its parent and what was changed.

Diff-Based Re-Evaluation: The algorithm identifies which parts of the decision need to be reprocessed by comparing the new branch’s canvas to the original’s:

Determine Changed Inputs: Compare the branch canvas to the parent’s canvas field by field. For example, if the user changed an assumption’s value or confidence, that is marked. Or if they added a new constraint or a new option, mark that.

Invalidate Affected Downstream Results: We have a dependency mapping:

Criteria weights influence option scores and ranking.

Constraints influence option feasibility.

New options require scoring/ranking.

Changed assumptions might influence risk analysis or certain criteria (if, say, an assumption was about an outcome probability).

New information might directly change an option’s projected outcome (for instance, if a branch assumes “market will decline”, the risk of an investment option changes).

Based on this, the algorithm flags modules from earlier phases that need re-running. For example:

If a constraint changed, re-run Constraint-First Filtering (Phase 2) to see which options survive. Also re-run Option Generation/Scoring if any were pruned or un-pruned.

If a criterion weight changed, no need to question user again (we have the new weight), but we should re-calc all option scores/ranks.

If an assumption about outcome changed (e.g., “chance of success if I do A” was updated), that directly affects the probabilities or perhaps the scoring of options. So we recalc probabilities p_raw for options if they depended on that assumption (like base-rate or risk factor).

If a new option was added in branch, we run the Option Generation & Scoring module for that option (and likely include it in the thin-slice limit if needed, possibly bumping out the worst option to keep count small).

If an option was removed (like user didn’t want to consider something), then just drop it and maybe if only one left, that simplifies the decision.

If reversibility or stakes changed (e.g., scenario is more risky), we might trigger heuristics modules again that are sensitive to those (like maybe re-run premortem if stakes went from low to high).

If timeline/deadline changed, it might not require re-questioning but could influence criteria (for instance, if the deadline is sooner, an option that takes a long time might score worse now).

Reuse Unchanged Parts: Any component not affected by changes is reused as-is. For instance, if no criteria or preferences changed, we don’t ask those questions again and we carry over the same criteria list and weights. This is crucial for user experience – branching should feel like modifying a previous decision, not starting over.

Diff Example: Suppose the original decision had options A, B with A recommended, and the user branches: “What if my budget were doubled?”. The algorithm sees “budget” (a constraint) changed. It re-runs Option Gen/Filtering: maybe now option C that was previously too expensive becomes viable. So it adds option C (which might have been pruned or not even considered last time). It then re-scores options A, B, C with the new budget (cost criterion weights might change or their scores on cost change). It likely finds a new ranking. But it doesn’t need to re-ask values or risk questions if those remain the same. The output could show: “In this scenario (budget doubled), Option C emerges as High Fit, whereas in the original scenario it was not available.”

Avoiding Redundant Q&A: The system must not bombard the user with the same questions on a branch. Since the canvas is copied, all Q&A from original remain filled. Only if a field is invalidated by a change do we ask again. For example, if the user changes a hard constraint, we don’t need to re-ask criteria or other unrelated items. If the user adds a new criterion in the branch (like now considering “prestige”), we may ask them to weight it relative to existing criteria – that’s a genuinely new question. But we won’t re-ask things like “what is your main goal?” because that presumably remains the same unless explicitly changed.

Branch Comparison Output: The interface can highlight differences: maybe the canvas shows side-by-side original vs branch outcomes (e.g., which option was best in each scenario). The DAG may allow multiple branches (like branching again from a branch). The algorithm tracks these relationships so that if something common to many branches changes, you could propagate that (but typically user initiates each branch individually).

Pseudo-code for branch re-evaluation:

function branch_decision(original_canvas, modifications):
    new_canvas = copy(original_canvas)
    apply(modifications to new_canvas)  // e.g., change assumption, add constraint, etc.
    changed_fields = diff(original_canvas, new_canvas)
    // Determine which modules to rerun:
    if changed_fields intersects {"criteria", "weights"}:
         recalc_option_scores(new_canvas)  // criteria weight change affects scoring
    if changed_fields intersects {"constraints"}:
         filter_options_by_constraints(new_canvas)
         // if options removed/added, mark scoring needed
         recalc_option_scores(new_canvas)
    if changed_fields intersects {"assumptions", "reversibility", "stakes"}:
         // Possibly update risk calculations or probabilities
         update_risk_and_probabilities(new_canvas)
    if changed_fields intersects {"options"}:
         // New option added, run scoring; Option removed, adjust selection if needed
         recalc_option_scores(new_canvas)
    // Trigger heuristics if needed based on new context:
    if new_canvas.stakes == "High" and original_canvas.stakes != "High":
         heuristics.run("premortem", new_canvas)
    // etc., for other heuristics if their trigger condition now satisfied
    evaluate_options_and_recommend(new_canvas)
    return new_canvas


The key is modular recomputation: we don’t throw away the whole analysis. Instead, we surgically update the affected parts. This is efficient and user-friendly.

Example Application: Imagine a user made a career decision choosing Job A over B given assumption “economy stable”. They logged outcome as pending. Now news comes that the economy is entering a recession. The user branches: changes assumption “economy = downturn”. The branch algorithm might mark that as affecting the risk of each job (maybe Job A was at a fragile startup – risk goes up, Job B is government – risk stable). The system would update the risks[] of options: Job A now has a new risk “startup may cut jobs in recession”. This might lower Job A’s score or probability of success. It then might actually switch the recommendation to Job B in the branch scenario. The user sees “If economy downturn, maybe Job B is safer (High Fit) whereas originally Job A was favored.” This helps them decide whether to alter their plan or prepare mitigations. All other factors (salary, location preferences, etc.) carry over unchanged.

Reusing Answers: We ensure the branch inherits all answers from the original as default. The user can tweak any if they want (maybe in branch they also adjust a weight). But by default, unchanged answers remain. This avoids repetition and also leverages the work done – making branching quick.

Multi-branch management: The DAG can become a tree of scenarios. The algorithm allows branching off any previous node. Each node stores differences from its parent for clarity. If a high-level change should apply to many branches (rare, but e.g., user realizes a criterion was wrongly weighted across scenarios), they might update the root and propagate new branches from there.

Pre-computation for Speed: If needed, we could anticipate some branches by asking in original run about uncertainties. But since the product is interactive, we primarily branch on demand.

In summary, the branching algorithm acts like a “what-if” engine: Only recalc what the “if” affects. This delivers results rapidly and shows the impact of changed assumptions without rehashing the entire decision dialogue.

8. Evaluation Plan (Measuring Algorithm Efficacy)

To ensure our decision-assist algorithm is actually helping users make better decisions, we define a set of metrics and tests. These allow us to iterate and prove the system’s value. Key evaluation criteria:

Reduced Regret (Sentiment Delta): We will measure users’ self-reported sentiment or regret before vs. after the decision. Concretely, at intake we might get a baseline mood/stress level and after outcome (2 hours or 24 hours later) we get a sentiment rating (as mentioned in the context). The metric could be the percentage of decisions where the user’s sentiment improved (or at least did not worsen significantly) after using the tool. We expect that a good decision process leads to less regret. For example, if a user was anxious and uncertain, and later reports they feel content or confident, that’s a success. We could use a simple Regret Likert scale (like outcome.sentiment in canvas: Very Satisfied down to Very Regretful). We aim for high satisfaction and low regret. If we see many “Regretful” outcomes, especially with decisions the model rated high, that’s a red flag. Trend: Over time, as calibration and algorithm improve, average regret should decrease relative to some baseline (perhaps compare to users not using the tool if possible, or to earlier versions of the algorithm).

Progress “Yes/No”: Many decisions are made with the goal of making progress in life or resolving a situation. We could periodically ask users a binary question: “Did using this tool help you make progress on your issue?” (Yes/No) or after outcome, “Do you feel this decision moved you forward?” The “progress_yesno” metric is the rate of Yes answers. Alternatively, measure the fraction of decisions that users actually implement (if they go through Phase 3 and execute the plan, that indicates progress vs being stuck in indecision). We want a high completion and execution rate: users not only decide but follow through. If many users drop out before deciding or decide but never act, that suggests the algorithm might be too convoluted or not convincing enough. Target: increase completion rate and self-reported progress over time.

Calibration Improvement (Brier Score Trend): We log the Brier score for each decision’s prediction (Section 6). By aggregating these, we can track if our probabilities are getting better calibrated. Specifically, we expect the average Brier score to trend down as the system learns. We also examine calibration plots: e.g., of all decisions we said ~70%, did ~70% succeed? Initially, there may be gaps, but with calibration adjustment, those gaps should narrow. This is more of an internal metric, but it’s crucial for trust – well-calibrated predictions mean we are neither overpromising nor underpromising outcomes. If we detect miscalibration (e.g., outcomes systematically lower than predicted), we adjust the model accordingly and expect subsequent Brier scores to reflect that (thus lowering). A target might be to get Brier score below some threshold (say <0.2) after N decisions.

User Completion Rate: We measure what percentage of decision sessions reach each phase. For example: X% complete Phase 1 (provided enough info to proceed), Y% generate options (Phase 2), Z% commit (Phase 3), and W% log outcomes (Phase 4). A healthy funnel would have minimal drop-off until at least Phase 3. If we notice heavy drop-off during Phase 1 clarify (meaning users quit while answering questions), that signals the Q&A might be too burdensome or not obviously useful to them. If drop-off is at Phase 2 (option generation), maybe the options didn’t resonate or the user didn’t trust the suggestions. If at Phase 3 commit they bail, maybe they still aren’t confident – possibly a sign to improve our heuristics or check if the system is pushing a choice the user isn’t comfortable with. We’ll use these stats to refine the UX. The goal is to maximize the percentage of users who get to a decision and log an outcome. Completion rate improvement is a success indicator (as more users find it worthwhile to finish the process).

A/B Tests for Question Ordering & Modes: We will run experiments on variations of the clarify phase and depth modes:

For example, A/B test two question selection strategies: one might prioritize criteria first vs another prioritizes constraints first. Measure which leads to faster decisions or higher user satisfaction.

Test Quick mode (5 questions max) vs Deep mode (15 questions) with similar users. Perhaps some users prefer brevity, others detail – but we can compare outcomes: do deep-mode users have less regret or better calibration? If deep mode yields marginal gains in decision quality but significantly more drop-off, perhaps the optimal number of questions is somewhere in between. These tests guide us in tuning the default behavior (maybe an adaptive mode that tries to ask the minimal necessary questions).

We can also test different tooltip styles (explanatory vs minimal) to see what leads to better user comprehension or less frustration.

Another test: ordering of heuristics prompts. For instance, some decisions we might inject 10/10/10 early vs later and see which approach leads to better clarity or user feedback. We will collect user ratings after sessions (“How helpful was this process?” on a scale) to correlate with approach.

Simulation with Synthetic Cases: Before deploying changes widely, we use a library of synthetic decision scenarios to simulate the algorithm’s behavior offline. For example, create 20 fake user profiles with preset preferences and “ground truth” best options. These could be common dilemmas (taken from literature or real stories) where we have an idea of what a good decision outcome would be. Run our pipeline on each (feeding in the synthetic answers the “user” would give) and see what the model recommends. We can then see if those recommendations align with known good solutions. We also simulate extreme cases to test failure modes: e.g., a case with conflicting constraints, or one with nearly equal options (to see if model wavers appropriately), or cases with erroneous inputs. This offline evaluation helps catch logical bugs and refine question selection in a controlled setting where we know what should happen. It’s like unit testing the algorithm on a variety of decisions (career, health, money, etc.). We can score the algorithm on these cases by whether it identifies the key factors and makes a reasonable suggestion.

User Feedback and Qualitative Review: In addition to metrics, we’ll gather qualitative feedback. Perhaps prompt users: “What did you like or dislike about the process?” or “Was there any question that felt irrelevant?”. This can highlight issues not evident in numbers (e.g., maybe users felt the tone was too interrogative, or they really loved the premortem exercise).

Continuous Learning and Tuning: The evaluation plan isn’t one-time. We will continuously monitor these metrics. For instance, each quarter, compute the average regret score and see if it’s improving. Monitor if calibration is staying good or drifting (if we introduce a new heuristic, did it affect our probability estimates?). Also track time taken per decision and user effort (maybe count of questions answered) – a shorter time for same outcome quality is improvement in efficiency.

Success Criteria: Ultimately, a “good” algorithm is one that users willingly use and credit with helping them decide better. So an excellent sign is repeat usage and referrals (user completes one decision and starts another, or tells friends). We might measure how many decisions per user on average are made – if that grows, it implies trust in the system.

To summarize:

We use regret/satisfaction surveys to ensure decisions feel good in hindsight.

We use progress/completion stats to ensure the process is effective and not overly cumbersome.

We use calibration/Brier to ensure our predictive aspects are scientifically sound and improving.

We use A/B experiments to fine-tune the process based on actual user responses.

We simulate and unit test scenarios to preemptively catch flaws.

Through these metrics, we’ll iterate. For example, if we find deep mode doesn’t significantly reduce regret but causes more dropouts, we might default to quick mode. If calibration is off, we adjust our probability model. If users frequently skip outcome logging, maybe incentivize it or shorten that process.

Our target is that after using Decision GPT:

90% of users report the process helped them clarify or feel more confident.

A majority have no significant regrets in follow-up.

Decisions outcomes (in terms of user’s own success criteria) are positive at a higher rate than their prior track record (if we can measure that).

The system’s decision advice gets more accurate (calibrated) the more it’s used (learning from data).

We will consider the algorithm “good” when it consistently produces decisions that users are happy with and when objective measures like calibration and outcome fulfillment are strong, all while maintaining a high completion rate (a sign that the process is acceptable in effort).

9. Concrete Examples (End-to-End Walkthroughs)

Let’s illustrate the entire flow with three scenarios in different domains: a relationship decision, a career decision, and a money decision. We will show the questions asked (with tooltips explaining them), how the canvas gets filled, the options and recommendation, and what gets logged.

Example 1: Relationship Decision – “Should I Break Up or Stay?”

Scenario: Alex is unsure whether to break up with their partner of 3 years or try to work things out. It’s a personal/emotional decision with high stakes for happiness.

Phase 0 – Intake:

Decision Statement: “Deciding whether to break up with my partner or stay together and work on the relationship.”

Metadata: Domain: relationships; Alex indicates stakes are High (it’s a big life decision), reversibility = Partially Reversible (they could get back together potentially, but not guaranteed), no hard deadline (timeline = “n/a”, though sooner is better for both of them). The model notes this is high stakes and somewhat irreversible emotionally.

Phase 1 – Clarify (Q&A): The assistant asks a few key questions:

Q1: “What is your main objective in this decision – is it to maximize your long-term happiness, minimize pain, fulfill obligations, or something else?”

Tooltip: “Why I’m asking: Defining your core goal helps identify decision criteria (e.g. personal happiness, partner’s well-being, family expectations). What this changes: It will focus the options on what achieves your true objective.”*
Alex answers: “My main goal is to be happy and true to myself, but without causing unnecessary hurt.”

Canvas update: Adds a criterion “Personal Happiness” (Alex’s happiness) and “Avoid Harm” (minimize hurt to partner). The assistant notes these two criteria, perhaps weighting happiness higher if Alex implies it. It also captures the nuance: Alex values authenticity (“true to myself”) – maybe add that as part of Personal Happiness definition.

Q2: “What are the biggest issues in your relationship currently (the things making you consider breaking up)?”

Tooltip: “Why I’m asking: Identifying specific pain points or deal-breakers helps clarify your constraints or criteria. What this changes: It documents what must change for staying together to be viable, or what you can/can’t accept.”*
Alex: “We have constant fights about future plans (I want kids, they don’t), and there’s a lack of trust due to some past incidents.”

Canvas update: Adds hard constraint: “Must align on major life goals (family/kids).” This is a likely deal-breaker Alex identified. Also adds an assumption: “Partner will not change mind about kids” (confidence: High, based on past talks). The trust issue is noted as a serious con of staying. Possibly a soft constraint like “relationship must have trust” is implicitly already a given, but we capture “rebuilding trust” as a challenge if staying.

Q3: “How do you envision your life in 1 year and 5 years if you stay versus if you break up? (Think 10/10/10: 10 months vs 10 years.)”

Tooltip: “Why I’m asking: Projecting into the future (e.g. 10 months, 10 years) helps assess long-term consequences of each path. What this changes: It may reveal which option aligns with your long-term values and which you might regret later.”*
Alex reflects: “If I stay, in 1 year we might still be stuck or maybe we’ve broken up acrimoniously later. In 5 years, I fear resentment if I compromise on kids. If I break up, in 10 months I’ll be sad and adjusting, but in 5 years I might be in a happier relationship or content being single.”

Canvas update: The assistant notes Alex’s long-term alignment clearly favors breaking up (to find someone with similar life goals). It adds a risk for staying: “Resentment in future over compromised life goals,” and a risk for breaking up: “Short-term loneliness and grief.” These will be used in evaluation. This also influences criteria weighting: perhaps “long-term alignment of values” becomes a criterion (or part of Personal Happiness). Also through this discussion, Alex indicates a likely future regret: “I’d regret not having a chance at kids/family” if they stay and partner never agrees. The Regret Minimization heuristic kicks in quietly – the assistant marks that breaking up avoids that life regret.

Q4: “What support system or resources do you have if you decide to break up? (For example, friends, therapy, etc.)”

Tooltip: “Why I’m asking: Considering your support can gauge how feasible the break-up option is and how to mitigate its difficulties. What this changes: It updates the action plan for the break-up scenario and assesses risk (e.g. risk of emotional difficulty can be mitigated with support).”*
Alex: “I have close friends and a sister I can stay with for a while. I’d likely start therapy too.”

Canvas update: This lowers the risk of the break-up option (“Has support network to cope”). It also indicates an action step if that option is chosen: “Lean on sister/friends, possibly find a therapist.” The assistant will include that in the action plan for break-up.

Q5 (Vague example turned specific): The model initially wanted to ask “How do you feel about your partner?” but that’s broad. Instead it asks: “On a scale of 1-10, how much love and fulfillment do you currently feel in the relationship?” (Specific, quantifiable)

Tooltip: “Why I’m asking: Gauging your current relationship satisfaction helps weigh the status quo. What this changes: It informs the comparison: if it’s very low, the ‘stay’ option has a high hurdle to clear (or it might be not worth staying without major changes).”*
Alex: “Honestly, right now maybe a 4/10. I love them, but I’m very unhappy with our dynamic.”

Canvas update: Records assumption: “Current relationship satisfaction = 4/10 (low).” This will be factored in evaluating staying – essentially the status quo is poor. It sets a baseline that improvement is needed if staying is to be viable.

After these questions, the Decision Canvas summary is:

Criteria: Personal Happiness (weight 0.7), Avoid Harm/Minimize Emotional Damage (weight 0.3). (The assistant infers Alex prioritizes own happiness but does care about not hurting partner too much.)

Hard Constraint: Alignment on future goals (kids). Partner doesn’t want kids – this is effectively failing a hard constraint in the “stay” scenario.

Assumptions: Partner unlikely to change on kids (High confidence). Relationship satisfaction is currently 4/10. Break-up would cause short-term pain but likely recover in few years (Mid confidence).

Risks (if stay): Continuing fights, future resentment, lost opportunity for family.

Risks (if break): Loneliness, need to find someone new, possible regret if issue could have been fixed.

Timeline: No fixed deadline, but sooner decision avoids dragging pain.

Reversibility: Breaking up is semi-reversible (they could theoretically get back, but unlikely if things got worse).

Stakes: High (life happiness and time).

Phase 2 – Options: The assistant distills the options:

Option 1: Stay and Actively Work on Relationship – with specifics: e.g. Couples therapy, serious discussions about future, attempt to rebuild trust over next 6 months. This is essentially the “try to fix it” option. It acknowledges constraint: (Would require a compromise or miracle on the kids issue – which is unlikely, but it’s the only way staying meets Alex’s core need.)

Option 2: Amicable Break-Up – End the relationship respectfully, possibly remain friendly, and pursue life aligned with your goals. This includes sub-steps like moving out, using support system, etc.

Option 3: Do Nothing (Delay Decision) – basically Stay by default for now without actively working on it. (We include this as the status quo baseline: Alex could just postpone the choice.)

The assistant immediately filters for constraints: The kids issue is a deal-breaker that Option 1 currently fails unless resolved. The assistant notes this: Option 1 violates the hard constraint “alignment on kids”. Rather than removing Option 1 (since Alex might still consider it hoping partner changes), the assistant flags it: “Option 1 requires your partner to change stance on kids, which we assumed is unlikely.” So it’s feasible only if that assumption is wrong.

Now it scores options:

Personal Happiness: Option 1 (stay) scored low because current satisfaction is 4/10 and likely won’t reach near 10 given the conflict; Option 2 (break-up) scored higher long-term happiness potential (Alex imagines being happier in future); Option 3 (delay) scored lowest (prolongs the 4/10 situation with no improvement).

Avoid Harm: Option 1 seems to avoid immediate hurt (no break-up now), but might lead to more hurt later (fights, deeper heartbreak if break-up happens later). Option 2 causes immediate hurt to partner (break-up pain) but might be kinder long-term than dragging it out. Option 3 avoids short-term conflict (no break-up conversation now) but is unfair to both in long run.
The assistant balances these: likely Option 2 is actually the most respectful in a way (if done amicably, it’s honest and doesn’t waste partner’s time).

Given all, the internal scores might be: Option 2 (Break-up) – High fit, Option 1 (Work on it) – Low fit (due to major unsolved issue), Option 3 (Do nothing) – Low fit (even worse, since it’s staying in dysfunction without trying to improve).

The UI might show:

Option 1: Try to Rebuild the Relationship – Fit: Low. (Pros: you honor your commitment, no immediate heartbreak. Cons: fundamental conflict on kids, ongoing unhappiness likely.)

Option 2: Amicable Separation – Fit: High. (Pros: freedom to find a compatible partner, long-term alignment with your life goals. Cons: short-term heartbreak for both, social and emotional upheaval.)

Option 3: Delay Decision – Fit: Low. (Pros: avoid action now. Cons: prolongs the inevitable, could lead to worse fallout later; essentially status quo of 4/10 happiness persists.)

The assistant might say: “Based on what you’ve shared, Option 2 (separation) aligns best with your long-term happiness and values (High Fit), despite the immediate pain. Option 1 has significant risks (Low Fit) – it would require resolving the kids issue which you’ve identified as unlikely. Doing nothing is also Low Fit as it doesn’t solve any problems and could deepen future hurt.”

Alex chooses Option 2: Break-Up (they essentially expected this but needed confirmation and clarity).

Phase 3 – Commit (Action Plan & Branches): The assistant now helps Alex plan the break-up:

It asks: “Do you want to try to end on good terms and what steps will you take?” (Alex: “Yes, I’ll have an honest talk this weekend, and suggest maybe we take some space rather than a dramatic fight.”)

Next: “What will you do immediately after to cope and stay healthy?” (Alex: “Call my sister to prepare to stay at her place for a few days. Schedule a therapy appointment for next week.”) The assistant adds these as next_action: “This weekend, have the break-up conversation calmly. Then stay with sister for support, start therapy, reconnect with friends.”

If-Then Branches: The assistant triggers a premortem: “Imagine a month after breaking up, you’re really struggling or regretful – what could cause that?” Alex says: “Maybe I’d feel regret if I thought we didn’t try everything (like counseling) or if being alone is harder than expected.” So the assistant notes two risks: (1) “Regret not trying counseling” – Mitigation: “Offer to go to one couples therapy session as closure attempt before fully ending, so you feel you tried.” (2) “Overwhelming loneliness” – Mitigation: “Line up regular hangouts with friends, maybe join a meetup to meet new people, keep busy.” These become part of the plan.

The canvas now has risks updated for Option 2 with mitigations. Also an if-branch suggestion: If after 3 months Alex feels it was a mistake and partner is open, consider reconnecting (since reversibility is partial – sometimes break-ups can reverse). However, the assistant cautions about that unicorn scenario (not explicitly unless Alex asks).

Reversibility Check: The assistant notes break-up is not easily reversible (Type 1-ish decision emotionally), so it ensures Alex is confident (which they are, given all signs). It might say “Given this is a hard-to-undo decision, you’ve been methodical which is good. You have a plan to manage the consequences.”

The final commitment: Alex confirms they will carry out the plan.

Phase 4 – Outcome Logging: Suppose a month later, the system pings Alex. Alex reports: “Outcome: I broke up as planned. I’m sad but I feel relieved. I’d rate my satisfaction 8/10 because I know it was the right choice, even though it hurts.” The assistant logs success = yes (from perspective of achieving goal of staying true to self and not prolonging an unworkable situation – Alex considers that success). They log sentiment: Satisfied (not Very Satisfied yet, but trending positive). If we had predicted maybe 90% that this would lead to long-term betterment, the Brier score for now is small (though true success of such decisions might be judged much later). The model updates calibration if needed. It also might schedule another check-in in 6 months (when the “long-term” outcome is clearer, e.g., did Alex find more happiness).

Metrics: Alex’s regret is low (they’re actually relieved). They definitely made progress (got out of limbo). Completion: they used all phases. From a product perspective, this is a success case.

Example 2: Career Decision – “Safe Job vs Startup Offer”

Scenario: Brianna has a stable job but an exciting startup offer came along. She’s torn between staying (security) or joining the startup (growth). She must decide within 2 weeks.

Phase 0 – Intake:

Decision: “Decide whether to leave my current job for a startup opportunity.”

Metadata: Domain: career; stakes: High (career trajectory), timeline: Decision needed in 2 weeks (offer exploding), reversibility: Reversible in some sense (could possibly return to industry, though not to same job; but career moves aren’t irrevocable like life/death). Budget not relevant, constraints not immediately given.

Phase 1 – Clarify:

Q1: “What matters more to you right now – stability or growth?”

Tooltip: “Why: This identifies your primary criterion (safety vs opportunity). Changes: It sets the weight for risk vs reward in options.”*
Brianna: “I value growth and learning, but I’m also concerned about financial stability. I’d say growth is slightly more important at this stage (60/40).”

Canvas: criteria: Growth/Career Advancement (0.6), Financial Stability (0.4).

Q2: “What is your risk tolerance if the startup might fail? (e.g., are you okay with possibly having to find another job?)”

Tooltip: “Why: Gauging risk tolerance influences how we evaluate the startup’s risk. Changes: A low tolerance would favor the safe option, high tolerance means we won’t penalize the risky option as much.”*
Brianna: “Medium – I have savings to cushion, but I’d be stressed if I had no job for long. I’m willing to risk it for a really good payoff, but not for something dubious.”

Canvas: assumption: RiskTolerance = Medium. This will adjust scoring: not extremely risk-averse, but not cavalier.

Q3: “How do the startup’s prospects look? Do you believe it has a high chance of success or is it very uncertain?” (Base-rate check)

Tooltip: “Why: Estimating the startup’s success chance sets an expectation (base rate: e.g., many startups fail). Changes: It will directly affect the probability of the ‘join startup’ option succeeding and helps calibrate optimism.”*
Brianna: “It’s somewhat uncertain. It’s in a crowded market. I’d guess maybe 50/50 it succeeds or gets acquired. Not a sure thing.”

Canvas: assumption: Startup success ~50% (p=0.5) – moderate. The assistant might note base rate: many startups ~10% succeed big, but maybe this one has decent backing to be 50%. This will feed into outcome probabilities.

Q4: “Fast forward to age 80. Which would you regret more: not taking this chance, or leaving your secure job and it going wrong?” (Regret Minimization)

Tooltip: “Why: Clarifies which regret is worse. Changes: Guides which option aligns with avoiding major life regret.”*
Brianna: “I think I’d regret not trying the startup more. I can find another stable job later, but this specific opportunity won’t come again.”

Canvas: note: She’d regret missing the opportunity (points strongly towards taking the risk). We mark RegretBias = favor taking chance. This likely tilts weight toward the startup option.

Q5: “Do you have any constraints (financial obligations, family needs) that require a certain income or stability?”

Tooltip: “Why: Identifying any hard constraints (e.g., must pay mortgage, insurance needs). Changes: If yes, the safe option might be necessary or the risky option must accommodate those.”*
Brianna: “I have a mortgage, but I have 6 months of emergency savings. No dependents. So short-term I’m okay, but I can’t go unemployed for years.”

Canvas: Hard constraint: “Cannot have $0 income beyond 6 months.” The startup job does pay (presumably), so not $0, but if it failed quickly, she’d need a new job within 6 months – we treat that as a risk rather than a constraint on the options themselves (both options provide income initially). So maybe no hard constraint eliminating an option; rather, it emphasizes risk of startup failing quickly.

Now the canvas:

Criteria: Growth (0.6), Stability (0.4).

Risk tolerance: Medium.

She leans toward regretting not trying more.

Constraint: avoid extended unemployment >6mo.

Assumption: Startup success ~50%. Also assume current job is stable (almost 100% stable).

We might also log salary difference: perhaps startup pay is slightly lower but has equity, current is higher base. She likely mentioned those details to assistant outside questions. Let’s assume: current salary is higher short-term, startup could be huge payoff long-term.

Phase 2 – Options:

Option A: Stay in Current Job. (Keep the stable salary, continue career as is, maybe slower growth but secure.)

Option B: Join Startup. (New role, possible big growth, but company could fail.)

(Option C: “Look for a middle-ground (e.g., ask current job for new challenges or a raise)” could be considered, but the user framed it as two-way choice. If the assistant is smart, it might propose an intermediate option: Negotiate with current job for more growth opportunities. Let’s say it does for comprehensiveness.)

Option C: Negotiate or Delay. (E.g., talk to current boss about a sabbatical or part-time involvement with startup, or delay decision if possible.) Realistically, delaying might not be feasible if the offer expires. So maybe not.

Assume main two:
The assistant scores them:

Growth: Startup (A) likely offers more learning and upside – score high on Growth. Current job (B) moderate or low on new growth (she’s presumably feeling plateaued).

Stability: Current job scores high (stable, good income). Startup low (risky).
Given weights 0.6/0.4, it’s a balance.

Default bias: The default is stay. The assistant will ensure do-nothing = stay is considered consciously, not just out of fear.

It will incorporate her regret bias: She said she’d regret not trying, which nudges in favor of the startup.

Probabilities: p_raw for “success if join startup” – perhaps interpret success as “career move leads to better outcome.” That’s subjective, but could tie to “startup doesn’t implode + she’s happy”. Given 50% success chance for startup itself, maybe the model sets p_raw ~0.6 that this choice leads to positive outcome (e.g., even if startup fails, she might find another job and still valued the experience, so maybe a bit above 0.5). For staying, probability of success (being happy in job) might be, say, 0.7 if she’s content but maybe regretful later (or vice versa, depending).

It will calibrate after many such cases, but right now it’s more comparative.

Likely the assistant finds these two options somewhat balanced but leaning startup because of her personal inclination:
It might come out as:

Option A (Stay): Fit: Medium. Pros: Secure salary, low stress about job loss, can continue mortgage easily. Cons: Limited growth, potential regret of missed opportunity.

Option B (Startup): Fit: Medium-High. Pros: Exciting growth, potential high reward, aligns with long-term ambition (entrepreneurial perhaps). Cons: Risk of failure (~50% chance), would need new job if fails (but you have savings to cushion 6 months).
Given her answers, the model might actually label Startup as “High Fit” unless the risk heavily drags it down. But with risk tolerance medium and regret avoidance high, I suspect Startup gets slight edge:
So maybe Option B: Fit = High, Option A: Fit = Med.

The assistant explicitly notes:
“Option B (Join startup) aligns with your growth goal and you indicated you’d regret missing the chance (so it scores well on personal fulfillment). It is riskier, but your moderate risk tolerance and savings mitigate that. Option A (Stay) offers stability which you do value, but it might not fulfill your desire for growth and could leave a ‘what if’ in the long run. Thus, I’d rate the startup as a somewhat better fit for you, assuming you’re prepared for the worst-case scenario. Fit: High vs Medium.”

Brianna, seeing this and reflecting, chooses Option B: Join the Startup.

Phase 3 – Commit Plan:

Next steps: “Resign professionally from current job (with 2 weeks notice), negotiate start date with startup, ensure finances in order (save up another month of expenses before leaving).”

The assistant asks premortem: “If 1 year from now this move is a disaster, what likely happened?” Brianna: “Startup ran out of money and I’m jobless, plus my old position is gone.” Mitigation: “Keep networking even while at startup, keep an eye on industry jobs, update resume proactively.” Also “I might feel I made a mistake if I hate the startup culture.” Mitigation: “Do due diligence now: talk to current employees to ensure culture fit, so you won’t be blindsided.”

These are added to canvas risks & mitigations.

“If the startup’s looking shaky at 6 months, what’s your exit plan?” – Possibly branch planning: If X metric not met by 6 months, start job hunting (a kill-switch as Bezos would say).

The plan includes: finish critical mortgage paperwork or emergency fund deposit before jumping.

Reversibility: Actually somewhat reversible – could probably find another corporate job if needed. The assistant notes: “This is a two-way door decision – if it doesn’t work out, you can likely go back to a similar role. Knowing that, it makes sense not to overthink beyond reasonable diligence. You’ve done the due diligence and set guardrails (like a timeline to re-evaluate) which is good.”

Phase 4 – Outcome:
Say 1 year later, outcome: The startup did okay but not great; however, Brianna learned tons and moved to an even better position after pivoting. She logs success: “Yes, it was the right move. Not a home run but it accelerated my career.” Sentiment: Very Satisfied (she’s proud she took the leap, no major regrets).
Predicted 0.6 vs actual success=1 yields some Brier error (0.16) – calibration might adjust if many like her succeed more than predicted.

Example highlights: The system applied base-rate thinking (50% success), regret framework (she’d regret not trying, which favored the adventurous option), and reversibility logic (it’s a Type 2 reversible decision, encouraging a faster move with safeguards rather than endless deliberation). It thus gave a slight bias toward taking the risk given her profile, which matches known entrepreneurship advice: many say the bigger regret is not trying.

Example 3: Money Decision – “Buy New Car Now or Keep Old Car”

Scenario: Carlos’s car is aging. He’s debating whether to buy a new car (and which type possibly) or keep the current one for another year. It’s a mid-stakes financial decision.

Phase 0 – Intake:

Decision: “Should I replace my 10-year-old car now or continue with it for a while?”

Metadata: Domain: money/consumer; stakes: Medium (a few thousand dollars, safety considerations), timeline: none strict but old car is deteriorating. Reversibility: Reversible (he could sell new car, but with depreciation; or fix old car if changes mind – relatively, financial decisions are semi-reversible with cost).

Phase 1 – Clarify:

Q1: “What’s your budget or financial limit for a new car?”

Tooltip: “Why: To set a hard constraint on option cost. Changes: Options beyond this budget won’t be considered.”*
Carlos: “I’d spend at most $25k. Preferably around $20k.”

Canvas: Hard constraint: Max $25k spend.

Q2: “What do you use your car for and how critical is reliability right now?”

Tooltip: “Why: Understand usage (commute, family?) and reliability needs. Changes: If reliability is crucial (e.g., long commute), that favors buying new now; if not, waiting might be fine.”*
Carlos: “I commute 30 miles a day. If the car breaks, it’s a big hassle. So reliability is fairly important. I also drive kids occasionally.”

Canvas: Criteria: Reliability (weight perhaps 0.7 for him if he’s leaning that way), Cost-Saving (0.3 if he cares about money). Actually, let’s ask that explicitly:

Q3: “Which is more important: saving money or having a reliable, safe car?”

Tooltip: “Why: This clarifies criteria trade-off between cost and reliability/safety. Changes: Sets weights – e.g., frugality vs peace-of-mind.”*
Carlos: “Safety/reliability is somewhat more important, but I also don’t want to waste money. Maybe 60% reliability, 40% saving money.”

Canvas: Criteria updated: Reliability/Safety (0.6), Financial (0.4).

Q4: “How bad are the old car’s issues? (E.g., high maintenance costs? Safety concerns?)”

Tooltip: “Why: Evaluating the current car’s condition helps estimate how long it can last and costs if you keep it. Changes: Informs the ‘keep car’ option viability and risk.”*
Carlos: “It’s generally okay, but has needed more repairs (spent $1200 last year). It’s not unsafe yet, but I worry it could break down unexpectedly.”

Canvas: assumption: OldCar reliability = moderate, maintenance ~$1200/year and rising. Possibly risk: “Old car breakdown could cause towing or missed work” – so risk of keeping is moderate inconvenience plus cost uncertainty.

Q5: “What kind of new car were you considering – basic model or something fancy?”

Tooltip: “Why: If considering expensive vs cheap new car, options differ. Changes: Could add an option for a cheaper used car etc.”*
Carlos: “I’d get a decent used car maybe 2-3 years old for around $20k. Not a luxury car.”

Canvas: So option can be precisely that. Also option of “keep old car” with continuing maintenance.

Now the assistant might identify thin slice of options:

Option 1: Buy a Reliable Used Car now (~$20k).

Option 2: Keep Old Car 1-2 more years, then replace. (Do nothing now, essentially.)
Maybe Option 3: “Buy a very cheap used car or lease as interim” (if it thinks of that as compromise), but likely not needed.

Applying heuristics:

Default bias: People often keep status quo by inertia. The assistant will make sure to justify the keep vs buy objectively.

Base rate: It might say typical car of that model lasts X years/ miles. If known, could mention (or user might).

Possibly 10/10/10: If not explicitly asked, the assistant could incorporate: 10 months from now with old car you might spend more on repairs, vs new car you have peace of mind.

Pre-mortem: Not needed unless in commit (like if buy new, finances maybe? But low stakes enough).

Regret: might ask “Will you regret not getting new car if the old one fails on a highway one day?” But scenario already covers reliability.

It scores:

Reliability: New car high (no breakdowns likely), Old car low (risk of breakdown).

Financial: New car big expense $20k, old car cheaper short-term (just maintenance). Possibly cost of old plus repairs vs depreciation of new – could do some math. But qualitatively, keeping is cheaper if no major failure.

Given weights 0.6/0.4, reliability has edge, so likely it leans new car now, unless old car is still quite fine.

But old car currently working. The algorithm might produce something like:

Option1 (Buy now): Fit: Medium-High. Pros: High reliability, safety for commute and family (no worry of breakdown)【39†L89-L96? not exactly 10/10/10 but peace of mind in future】, newer features possibly. Cons: $20k cost now, car depreciates; you lose the chance to extract remaining life of old car.

Option2 (Keep old): Fit: Medium. Pros: Save money in short term, use car’s remaining life fully. Cons: Risk of breakdown and high repair costs, potential inconvenience or safety issue; likely will need to spend that $20k in a couple of years anyway (just delayed).

Might mention the default bias: “Many people hold on too long to avoid spending, but end up paying in stress and repairs.”

The assistant might bring in a base-rate fact: e.g., the average cost of maintaining a 10-year-old car tends to rise each year, and chance of major failure in next year is X%. If it found a stat: “Cars >10 years old have a 1/3 chance of serious breakdown each year” (just hypothetical), that would support buy.

It also might run numbers: e.g., if you keep old car, expect maybe $1500/year maintenance and maybe lower resale value later; if you buy now, you spend $20k but less maintenance and get resale value on that eventually.

Carlos’s answers indicated reliability edges out savings, so likely the recommendation is to Buy now.
If he had said money is top priority and old car is not that bad, it would go the other way.

So final output:
“Option 1: Buy a newer car now – Fit: High. This gives you peace of mind and safety for your commute and family. You won’t worry about breakdowns, and you indicated reliability is slightly more important than the cost. The $20k expense is within your budget and you avoid unpredictable repair bills.
Option 2: Keep the old car – Fit: Medium. You save money in the immediate term, but risk inconvenience or a big repair. Since you can afford a new car and value reliability, this option may be false economy if a breakdown could cause big troubles. It’s essentially delaying an inevitable purchase, and you might end up paying in stress or even tow truck fees.
Given your priorities, getting a newer car (option 1) seems the better choice – it aligns with your reliability focus and you have budgeted for it.”

Carlos chooses Option 1: Buy now (perhaps confirming his leaning, if he was leaning that way).

Phase 3 – Commit:

Action plan: research specific models within budget, get car loan if needed, sell old car (that’s an action step to recoup maybe $3k).

If-then: “If new car’s monthly cost starts straining budget, cut other expenses or consider a fuel-efficient model to save gas $$” (just a thought).

The assistant might add: “Consider getting a certified pre-owned to minimize risk” if not already considered (that’s basically what he said 2-3yr used).

Premortem: “Imagine you bought a car and regret it – what happened?” Perhaps “I overspent or the car had hidden issues.” Mitigation: “Get a pre-purchase inspection or warranty.” That’s added.

Phase 4 – Outcome:
After purchase, outcome likely “successful – no breakdowns, happy with new car, finances okay.” If he says he’s satisfied, no regret, we log success. Brier down, etc.

These examples demonstrate how the algorithm operates across domains: it asks targeted questions with clear intent, populates the canvas, uses heuristics (we saw regret minimization in career, default bias and base-rate in money, 10/10/10 in relationship, etc.), and produces options with reasoning. The user remains in control, but benefits from a structured, thorough analysis – likely leading to more confident and quality decisions. Each step is documented and learnings are fed back to improve future decisions, both for the user (through experience) and the model (through calibration).