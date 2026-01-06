// Enums
export type SituationType =
  | "gym_approach"
  | "double_text"
  | "kiss_timing"
  | "first_date_plan"
  | "generic_relationship_next_step";

export type DecisionStatus = "active" | "resolved" | "archived";

export type NodePhase = "clarify" | "moves" | "execute";

export type MoodState =
  | "calm"
  | "anxious"
  | "angry"
  | "sad"
  | "horny"
  | "tired"
  | "confident"
  | "neutral";

export type RiskLevel = "low" | "med" | "high";

export type AnswerType = "yes_no" | "text" | "number" | "single_select";

// Question from Phase 1
export interface Question {
  id: string;
  question: string;
  answer_type: AnswerType;
  choices?: string[];
  why_this_question: string;
  what_it_changes: string;
  priority: number;
}

// Answer from user
export interface Answer {
  question_id: string;
  value: string | number | boolean;
}

// Branch response
export interface BranchResponse {
  next_move: string;
  script: string;
}

// Move from Phase 2
export interface Move {
  move_id: string;
  title: string;
  when_to_use: string;
  tradeoff: string;
  gentleman_score: number;
  risk_level: RiskLevel;
  p_raw_progress: number;
  p_calibrated_progress: number;
  criteria_scores: {
    self_respect: number;
    respect_for_her: number;
    clarity: number;
    leadership: number;
    warmth: number;
    progress: number;
    risk_management: number;
  };
  scripts: {
    direct: string;
    softer: string;
  };
  timing: string;
  branches: {
    warm: BranchResponse;
    neutral: BranchResponse;
    cold: BranchResponse;
  };
}

// Execution plan
export interface ExecutionPlan {
  steps: string[];
  exact_message: string;
  exit_line: string;
  boundary_rule: string;
}

// Decision node
export interface DecisionNode {
  id: string;
  decision_id: string;
  parent_node_id: string | null;
  phase: NodePhase;
  questions_json: { questions: Question[] } | null;
  answers_json: { answers: Answer[] } | null;
  moves_json: {
    moves: Move[];
    cooldown_recommended: boolean;
    cooldown_reason: string | null;
  } | null;
  chosen_move_id: string | null;
  execution_plan_json: ExecutionPlan | null;
  mood_state: MoodState | null;
  created_at: string;
}

// Decision
export interface Decision {
  id: string;
  user_id: string;
  title: string | null;
  situation_text: string;
  situation_type: SituationType | null;
  status: DecisionStatus;
  created_at: string;
  updated_at: string;
  nodes: DecisionNode[];
}

// Outcome
export interface DecisionOutcome {
  id: string;
  node_id: string;
  progress_yesno: boolean | null;
  sentiment_2h: number | null;
  sentiment_24h: number | null;
  brier_score: number | null;
  notes: string | null;
  created_at: string;
}

// API Request types
export interface CreateDecisionRequest {
  situation_text: string;
}

export interface AnswerQuestionsRequest {
  answers: Answer[];
}

export interface ChooseMoveRequest {
  move_id: string;
}

export interface ResolveOutcomeRequest {
  progress_yesno: boolean;
  sentiment_2h?: number;
  sentiment_24h?: number;
  notes?: string;
}

// API Response types
export interface Phase1Response {
  decision: Decision;
  node: DecisionNode;
  summary: string;
  situation_type: SituationType;
  mood_detected: MoodState;
  questions: Question[];
}

export interface Phase2Response {
  node: DecisionNode;
  moves: Move[];
  cooldown_recommended: boolean;
  cooldown_reason: string | null;
}

export interface ExecutionResponse {
  node: DecisionNode;
  execution_plan: ExecutionPlan;
}
