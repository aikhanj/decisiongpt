"use client";

import { useState, useMemo } from "react";
import { motion } from "framer-motion";
import { ArrowRight, CheckCircle2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { QuestionCard, Question } from "./question-card";

interface QuestionsListProps {
  questions: Question[];
  onSubmit: (answers: Record<string, string | number | boolean>) => void;
  isLoading?: boolean;
}

export function QuestionsList({
  questions,
  onSubmit,
  isLoading = false,
}: QuestionsListProps) {
  const [answers, setAnswers] = useState<Record<string, string | number | boolean>>({});

  const handleAnswerChange = (questionId: string, value: string | number | boolean) => {
    setAnswers((prev) => ({
      ...prev,
      [questionId]: value,
    }));
  };

  // Calculate progress
  const requiredQuestions = questions.filter((q) => q.required !== false);
  const answeredRequired = requiredQuestions.filter(
    (q) => answers[q.id] !== undefined && answers[q.id] !== ""
  );
  const progress = requiredQuestions.length > 0
    ? (answeredRequired.length / requiredQuestions.length) * 100
    : 100;

  const allRequiredAnswered = answeredRequired.length === requiredQuestions.length;

  const handleSubmit = () => {
    if (allRequiredAnswered) {
      onSubmit(answers);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <Card className="bg-primary/5 border-primary/20">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center justify-between">
            <span>Clarifying Questions</span>
            <span className="text-muted-foreground font-normal">
              {answeredRequired.length}/{requiredQuestions.length} answered
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Progress bar */}
          <div className="space-y-1">
            <Progress value={progress} className="h-2" />
            <p className="text-xs text-muted-foreground">
              {allRequiredAnswered
                ? "All questions answered! Ready to continue."
                : "Answer all required questions to generate options."}
            </p>
          </div>

          {/* Questions */}
          <div className="space-y-3">
            {questions.map((question, index) => (
              <QuestionCard
                key={question.id}
                question={question}
                value={answers[question.id]}
                onChange={(value) => handleAnswerChange(question.id, value)}
                index={index}
              />
            ))}
          </div>

          {/* Submit button */}
          <Button
            onClick={handleSubmit}
            disabled={!allRequiredAnswered || isLoading}
            className="w-full"
          >
            {isLoading ? (
              <>
                <span className="animate-pulse">Generating options...</span>
              </>
            ) : allRequiredAnswered ? (
              <>
                Continue to Options
                <ArrowRight className="w-4 h-4 ml-2" />
              </>
            ) : (
              <>
                Answer all questions to continue
                <CheckCircle2 className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </CardContent>
      </Card>
    </motion.div>
  );
}

// Compact inline questions for chat messages
interface InlineQuestionsProps {
  questions: Question[];
  answers: Record<string, string | number | boolean>;
  onAnswerChange: (questionId: string, value: string | number | boolean) => void;
}

export function InlineQuestions({
  questions,
  answers,
  onAnswerChange,
}: InlineQuestionsProps) {
  const answeredCount = questions.filter(
    (q) => answers[q.id] !== undefined && answers[q.id] !== ""
  ).length;

  return (
    <div className="space-y-3 mt-3">
      <div className="flex items-center gap-2 text-xs text-muted-foreground">
        <span>Questions</span>
        <span className="px-1.5 py-0.5 bg-muted rounded text-xs">
          {answeredCount}/{questions.length}
        </span>
      </div>
      {questions.map((question, index) => (
        <QuestionCard
          key={question.id}
          question={question}
          value={answers[question.id]}
          onChange={(value) => onAnswerChange(question.id, value)}
          index={index}
        />
      ))}
    </div>
  );
}
