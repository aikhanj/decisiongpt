"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { HelpCircle, Lightbulb, Send } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

export interface CandidateQuestion {
  id: string;
  question: string;
  answer_type: "yes_no" | "text" | "number" | "single_select";
  choices?: string[];
  why_this_question: string;
  what_it_changes: string;
  priority: number;
  voi_score?: number;
  targets_canvas_field?: string;
  critical_variable?: boolean;
  heuristic_trigger?: string;
}

export interface Answer {
  question_id: string;
  value: string | number | boolean;
  confidence?: number;
}

interface QuestionMessageProps {
  question: CandidateQuestion;
  onAnswerSubmit: (answer: Answer) => void;
  isProcessing: boolean;
}

export function QuestionMessage({
  question,
  onAnswerSubmit,
  isProcessing,
}: QuestionMessageProps) {
  const [answerValue, setAnswerValue] = useState<string | number | boolean>("");

  const handleSubmit = () => {
    if (!answerValue && answerValue !== 0 && answerValue !== false) return;

    onAnswerSubmit({
      question_id: question.id,
      value: answerValue,
    });

    // Reset for next question
    setAnswerValue("");
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {/* Question text */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          {question.question}
        </h3>

        {/* Context cards - PROMINENT DISPLAY */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
          {/* Why this matters */}
          <Card className="bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800">
            <CardContent className="p-4">
              <div className="flex items-start gap-2">
                <HelpCircle className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-blue-900 dark:text-blue-100 mb-1">
                    Why this matters
                  </p>
                  <p className="text-sm text-blue-800 dark:text-blue-200 leading-relaxed">
                    {question.why_this_question}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* What it changes */}
          <Card className="bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-800">
            <CardContent className="p-4">
              <div className="flex items-start gap-2">
                <Lightbulb className="w-5 h-5 text-amber-600 dark:text-amber-400 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="text-xs font-semibold text-amber-900 dark:text-amber-100 mb-1">
                    What it changes
                  </p>
                  <p className="text-sm text-amber-800 dark:text-amber-200 leading-relaxed">
                    {question.what_it_changes}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Answer input */}
        <div className="space-y-3">
          {question.answer_type === "yes_no" && (
            <YesNoInput value={answerValue as boolean} onChange={setAnswerValue} />
          )}
          {question.answer_type === "single_select" && question.choices && (
            <SingleSelectInput
              choices={question.choices}
              value={answerValue as string}
              onChange={setAnswerValue}
            />
          )}
          {question.answer_type === "text" && (
            <TextInput value={answerValue as string} onChange={setAnswerValue} />
          )}
          {question.answer_type === "number" && (
            <NumberInput
              value={answerValue as number}
              onChange={setAnswerValue}
            />
          )}

          {/* Submit button */}
          <Button
            onClick={handleSubmit}
            disabled={isProcessing || answerValue === ""}
            className="w-full"
            size="lg"
          >
            {isProcessing ? (
              <>
                <span className="animate-pulse">Processing...</span>
              </>
            ) : (
              <>
                Submit Answer
                <Send className="w-4 h-4 ml-2" />
              </>
            )}
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

// Yes/No toggle buttons
function YesNoInput({
  value,
  onChange,
}: {
  value?: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex gap-3">
      <Button
        type="button"
        variant={value === true ? "default" : "outline"}
        size="lg"
        onClick={() => onChange(true)}
        className="flex-1"
      >
        Yes
      </Button>
      <Button
        type="button"
        variant={value === false ? "default" : "outline"}
        size="lg"
        onClick={() => onChange(false)}
        className="flex-1"
      >
        No
      </Button>
    </div>
  );
}

// Single select (radio-style buttons)
function SingleSelectInput({
  choices,
  value,
  onChange,
}: {
  choices: string[];
  value?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      {choices.map((choice) => (
        <Button
          key={choice}
          type="button"
          variant={value === choice ? "default" : "outline"}
          size="lg"
          onClick={() => onChange(choice)}
          className="w-full justify-start"
        >
          {choice}
        </Button>
      ))}
    </div>
  );
}

// Text input (textarea)
function TextInput({
  value,
  onChange,
}: {
  value?: string;
  onChange: (v: string) => void;
}) {
  return (
    <Textarea
      value={value || ""}
      onChange={(e) => onChange(e.target.value)}
      placeholder="Type your answer here..."
      rows={4}
      className="resize-none text-base"
    />
  );
}

// Number input
function NumberInput({
  value,
  onChange,
}: {
  value?: number;
  onChange: (v: number) => void;
}) {
  return (
    <Input
      type="number"
      value={value ?? ""}
      onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
      placeholder="Enter a number..."
      className="text-base"
    />
  );
}
