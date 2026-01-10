// ============================================
// DECISION CANVAS TYPES
// ============================================

// Decision Types
export type DecisionType =
  | "career"
  | "financial"
  | "business"
  | "personal"
  | "relationship"
  | "health"
  | "education"
  | "other";

export type DecisionStatus = "active" | "resolved" | "archived";

export type NodePhase = "clarify" | "moves" | "execute";

export type RiskLevel = "low" | "medium" | "high";

export type AnswerType = "yes_no" | "text" | "number" | "single_select";

export type ConfidenceLevel = "low" | "medium" | "high";

// ============================================
// ADVISOR TYPES
// ============================================

export interface AdvisorInfo {
  id: string;
  name: string;
  avatar: string;
}

export interface Advisor {
  id: string;
  name: string;
  avatar: string;
  description: string;
  expertise_keywords: string[];
  personality_traits: string[];
  is_system: boolean;
}

// ============================================
// CHAT TYPES
// ============================================

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  advisor?: AdvisorInfo;
  // Optional fields for assistant messages with questions
  question_reason?: string; // Why this question matters (shown as tooltip)
  suggested_options?: string[]; // Quick reply options for the user to click
}

// ============================================
// CANVAS STATE TYPES
// ============================================

export interface Constraint {
  id: string;
  text: string;
  type: "hard" | "soft";
}

export interface Criterion {
  id: string;
  name: string;
  weight: number; // 1-10
  description?: string;
}

export interface Risk {
  id: string;
  description: string;
  severity: RiskLevel;
  mitigation?: string;
  option_id?: string;
}

export interface CanvasState {
  statement?: string;
  context_bullets: string[];
  constraints: Constraint[];
  criteria: Criterion[];
  risks: Risk[];
  next_action?: string;
}

// ============================================
// OPTION TYPES
// ============================================

export interface Option {
  id: string; // "A", "B", or "C"
  title: string;
  good_if: string;
  bad_if: string;
  pros: string[];
  cons: string[];
  risks: string[];
  steps: string[];
  confidence: ConfidenceLevel;
  confidence_reasoning?: string;
}

// ============================================
// COMMIT PLAN TYPES
// ============================================

export interface IfThenBranch {
  condition: string;
  action: string;
}

export interface CommitStep {
  number: number;
  title: string;
  description?: string;
  branches: IfThenBranch[];
  completed: boolean;
}

export interface CommitPlan {
  chosen_option_id: string;
  chosen_option_title: string;
  steps: CommitStep[];
}

// ============================================
// QUESTION TYPES
// ============================================

export interface Question {
  id: string;
  question: string;
  answer_type: AnswerType;
  choices?: string[];
  why_this_question: string;
  what_it_changes: string;
  priority: number;
}

export interface Answer {
  question_id: string;
  value: string | number | boolean;
}

// ============================================
// ADAPTIVE QUESTION TYPES
// ============================================

export type QuestioningMode = "quick" | "deep";

export interface CandidateQuestion extends Question {
  voi_score?: number;
  targets_canvas_field?: string;
  uncertainty_reduction_estimate?: number;
  critical_variable?: boolean;
  heuristic_trigger?: string | null;
}

export interface QuestionWithAnswer {
  question: CandidateQuestion;
  answer: Answer;
  answered_at?: string;
  canvas_impact?: string[];
}

export interface ConversationState {
  mode: QuestioningMode;
  question_cap: number;
  questions_asked: number;
  candidate_questions: CandidateQuestion[];
  asked_questions: QuestionWithAnswer[];
  current_question: CandidateQuestion | null;
  canvas_state: CanvasState;
  last_canvas_uncertainty: number;
  uncertainty_reduction_history: number[];
  ready_for_options: boolean;
  stop_reason?: string | null;
}

export interface AdaptiveQuestionResponse {
  next_question: CandidateQuestion | null;
  canvas_state: CanvasState;
  conversation_state: ConversationState;
}

export interface NextQuestionResponse {
  next_question?: CandidateQuestion | null;
  canvas_update: CanvasState;
  ready_for_options: boolean;
  questions_remaining?: number;
  progress?: number;
  stop_reason?: string | null;
  canvas_impact?: string[];
}

// ============================================
// OUTCOME TYPES
// ============================================

export interface DecisionOutcome {
  id: string;
  node_id: string;
  progress_yesno: boolean | null;
  sentiment_2h: number | null; // -2 to +2
  sentiment_24h: number | null; // -2 to +2
  brier_score: number | null;
  notes: string | null;
  created_at: string;
}

// ============================================
// DECISION NODE TYPES
// ============================================

export interface DecisionNode {
  id: string;
  decision_id: string;
  parent_node_id: string | null;
  phase: NodePhase;
  created_at: string;

  // Chat & Canvas state
  chat_messages_json?: ChatMessage[];
  canvas_state_json?: CanvasState;

  // Questions & Answers
  questions_json?: { questions: Question[] };
  answers_json?: Record<string, string | number | boolean>;

  // Options & Choice
  moves_json?: { options: Option[] };
  chosen_move_id?: string;

  // Commit plan
  execution_plan_json?: CommitPlan;
}

// ============================================
// DECISION TYPES
// ============================================

export interface Decision {
  id: string;
  user_id: string;
  title: string | null;
  situation_text: string;
  situation_type: DecisionType | null;
  status: DecisionStatus;
  created_at: string;
  updated_at: string;
  nodes: DecisionNode[];
  current_node?: DecisionNode;
}

// ============================================
// BRANCHING TYPES
// ============================================

export type BranchReason =
  | "new_info"
  | "changed_assumption"
  | "changed_constraint"
  | "add_option";

export interface BranchRequest {
  reason: BranchReason;
  details: string;
}

// ============================================
// API REQUEST TYPES
// ============================================

export interface StartDecisionRequest {
  situation_text: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChooseOptionRequest {
  option_id: string;
}

export interface SubmitAnswersRequest {
  answers: Record<string, string | number | boolean>;
}

export interface ResolveOutcomeRequest {
  progress_yesno: boolean;
  sentiment_2h?: number;
  sentiment_24h?: number;
  notes?: string;
}

// ============================================
// API RESPONSE TYPES
// ============================================

export interface StartDecisionResponse {
  decision: Decision;
  node: DecisionNode;
  initial_message: ChatMessage;
  canvas_state: CanvasState;
  questions: Question[];
}

export interface ChatResponse {
  message: ChatMessage;
  canvas_state: CanvasState;
  phase: NodePhase;
  questions?: Question[];
  options?: Option[];
  commit_plan?: CommitPlan;
  advisor?: AdvisorInfo;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  canvas_state?: CanvasState;
  phase: NodePhase;
  options?: Option[];
  commit_plan?: CommitPlan;
}

// ============================================
// LEGACY TYPES (for backwards compatibility)
// ============================================

export type SituationType =
  | "gym_approach"
  | "double_text"
  | "kiss_timing"
  | "first_date_plan"
  | "generic_relationship_next_step";

export type MoodState =
  | "calm"
  | "anxious"
  | "angry"
  | "sad"
  | "horny"
  | "tired"
  | "confident"
  | "neutral";

export interface BranchResponse {
  next_move: string;
  script: string;
}

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

export interface ExecutionPlan {
  steps: string[];
  exact_message: string;
  exit_line: string;
  boundary_rule: string;
}

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

// ============================================
// OBSERVATION TYPES
// ============================================

export type ObservationType =
  | "pattern"
  | "value"
  | "strength"
  | "growth_area"
  | "insight";

export type ObservationFeedback = "helpful" | "not_relevant" | "incorrect";

export interface Observation {
  id: string;
  observation_text: string;
  observation_type: ObservationType;
  confidence: number;
  related_theme?: string;
  tags: string[];
  surfaced_count: number;
  user_feedback?: ObservationFeedback;
  created_at: string;
  decision_id?: string;
}

export interface ObservationsGrouped {
  patterns: Observation[];
  values: Observation[];
  strengths: Observation[];
  growth_areas: Observation[];
  insights: Observation[];
}

// ============================================
// USER PROFILE TYPES
// ============================================

export interface UserProfile {
  id: string;
  user_id: string;
  name?: string;
  age_range?: string;
  occupation?: string;
  industry?: string;
  specialty?: string;
  extended_profile: Record<string, unknown>;
  onboarding_completed: boolean;
  onboarding_step?: string;
  context_summary?: string;
}

export interface TopicSuggestion {
  topic: string;
  count: number;
  recent: boolean;
}
