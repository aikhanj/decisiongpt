"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ArrowRight, CheckCircle } from "lucide-react";
import { QuestionMessage, CandidateQuestion, Answer } from "./question-message";
import { CanvasSidebar } from "./canvas-sidebar";
import { QuestionHistory } from "./question-history";

interface ConversationalQuestionFlowProps {
  decisionId: string;
  nodeId: string;
  onComplete: () => void;
}

interface QuestionWithAnswer {
  question: CandidateQuestion;
  answer: Answer;
  canvas_impact?: string[];
}

interface ConversationState {
  mode: "quick" | "deep";
  question_cap: number;
  questions_asked: number;
  ready_for_options: boolean;
  stop_reason?: string;
}

interface CanvasState {
  statement?: string;
  context_bullets?: string[];
  constraints?: any[];
  criteria?: any[];
  risks?: any[];
}

export function ConversationalQuestionFlow({
  decisionId,
  nodeId,
  onComplete,
}: ConversationalQuestionFlowProps) {
  const [currentQuestion, setCurrentQuestion] = useState<CandidateQuestion | null>(null);
  const [canvas, setCanvas] = useState<CanvasState>({});
  const [questionHistory, setQuestionHistory] = useState<QuestionWithAnswer[]>([]);
  const [conversationState, setConversationState] = useState<ConversationState | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isInitializing, setIsInitializing] = useState(true);

  // Initialize questioning on mount
  useEffect(() => {
    startQuestioning();
  }, []);

  const startQuestioning = async () => {
    setIsInitializing(true);
    setError(null);

    try {
      const apiKey = localStorage.getItem("openai_api_key");
      if (!apiKey) {
        throw new Error("No API key found. Please set your OpenAI API key.");
      }

      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/adaptive-questions/decisions/${decisionId}/nodes/${nodeId}/start?mode=quick`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-OpenAI-Key": apiKey,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to start questioning");
      }

      const data = await response.json();

      setCurrentQuestion(data.next_question);
      setCanvas(data.canvas_state || {});
      setConversationState(data.conversation_state);
    } catch (err) {
      console.error("Error starting questioning:", err);
      setError(err instanceof Error ? err.message : "Failed to initialize");
    } finally {
      setIsInitializing(false);
    }
  };

  const handleAnswerSubmit = async (answer: Answer) => {
    if (!currentQuestion) return;

    setIsProcessing(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/adaptive-questions/decisions/${decisionId}/nodes/${nodeId}/answer`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(answer),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to process answer");
      }

      const data = await response.json();

      // Add to history
      setQuestionHistory((prev) => [
        ...prev,
        {
          question: currentQuestion,
          answer,
          canvas_impact: data.canvas_update?.canvas_impact || [],
        },
      ]);

      // Update canvas
      setCanvas(data.canvas_update || {});

      // Check if ready for options
      if (data.ready_for_options) {
        // Transition to options phase
        setTimeout(() => {
          onComplete();
        }, 500);
      } else {
        // Set next question
        setCurrentQuestion(data.next_question);

        // Update conversation state for progress
        if (conversationState) {
          setConversationState({
            ...conversationState,
            questions_asked: conversationState.questions_asked + 1,
          });
        }
      }
    } catch (err) {
      console.error("Error processing answer:", err);
      setError(err instanceof Error ? err.message : "Failed to process answer");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleEditAnswer = async (questionId: string, newAnswer: Answer) => {
    setIsProcessing(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(
        `${apiUrl}/api/adaptive-questions/decisions/${decisionId}/nodes/${nodeId}/modify-answer?question_id=${questionId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(newAnswer),
        }
      );

      if (!response.ok) {
        throw new Error("Failed to update answer");
      }

      const data = await response.json();

      // Update canvas
      setCanvas(data.canvas_state || {});

      // Update history
      setQuestionHistory((prev) =>
        prev.map((item) =>
          item.question.id === questionId
            ? { ...item, answer: newAnswer }
            : item
        )
      );
    } catch (err) {
      console.error("Error updating answer:", err);
      setError(err instanceof Error ? err.message : "Failed to update answer");
    } finally {
      setIsProcessing(false);
    }
  };

  if (isInitializing) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="text-sm text-muted-foreground">Preparing questions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const progress = conversationState
    ? (conversationState.questions_asked / conversationState.question_cap) * 100
    : 0;

  return (
    <div className="flex h-full">
      {/* Main content area */}
      <div className="flex-1 flex flex-col p-6 overflow-y-auto">
        {/* Progress bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium">
              Question {conversationState?.questions_asked || 0} of{" "}
              {conversationState?.question_cap || 5}
            </p>
            <p className="text-sm text-muted-foreground">
              {Math.round(progress)}% complete
            </p>
          </div>
          <Progress value={progress} className="h-2" />
        </div>

        {/* Question history (scrollable) */}
        {questionHistory.length > 0 && (
          <div className="mb-6 max-h-64 overflow-y-auto">
            <QuestionHistory
              history={questionHistory}
              onEditAnswer={handleEditAnswer}
            />
          </div>
        )}

        {/* Current question */}
        {currentQuestion ? (
          <QuestionMessage
            question={currentQuestion}
            onAnswerSubmit={handleAnswerSubmit}
            isProcessing={isProcessing}
          />
        ) : conversationState?.ready_for_options ? (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-800 rounded-lg p-6 text-center"
          >
            <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h3 className="text-lg font-semibold mb-2">All Set!</h3>
            <p className="text-muted-foreground mb-4">
              {conversationState.stop_reason === "question_cap_reached"
                ? "Reached question limit. Ready to generate options."
                : conversationState.stop_reason === "diminishing_returns"
                ? "Additional questions won't add much value. Ready to proceed."
                : "Gathered sufficient information to generate great options."}
            </p>
            <Button onClick={onComplete} size="lg">
              Generate Options
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </motion.div>
        ) : null}
      </div>

      {/* Canvas sidebar */}
      <div className="w-96 border-l overflow-hidden">
        <CanvasSidebar canvas={canvas} />
      </div>
    </div>
  );
}
