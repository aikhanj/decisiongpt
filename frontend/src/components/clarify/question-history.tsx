"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Edit2, CheckCircle2, X } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { CandidateQuestion, Answer } from "./question-message";

interface QuestionWithAnswer {
  question: CandidateQuestion;
  answer: Answer;
  answered_at?: string;
  canvas_impact?: string[];
}

interface QuestionHistoryProps {
  history: QuestionWithAnswer[];
  onEditAnswer: (questionId: string, newAnswer: Answer) => void;
}

export function QuestionHistory({
  history,
  onEditAnswer,
}: QuestionHistoryProps) {
  const [editingQuestionId, setEditingQuestionId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState<string | number | boolean>("");

  const startEditing = (qa: QuestionWithAnswer) => {
    setEditingQuestionId(qa.question.id);
    setEditValue(qa.answer.value);
  };

  const cancelEditing = () => {
    setEditingQuestionId(null);
    setEditValue("");
  };

  const saveEdit = (questionId: string) => {
    // Skip if empty string (but allow 0 and false as valid values)
    if (editValue === "") return;

    onEditAnswer(questionId, {
      question_id: questionId,
      value: editValue,
    });

    setEditingQuestionId(null);
    setEditValue("");
  };

  if (history.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <h3 className="text-sm font-semibold text-muted-foreground px-2">
        Previous Answers ({history.length})
      </h3>
      <div className="space-y-2">
        <AnimatePresence>
          {history.map((qa, index) => (
            <motion.div
              key={qa.question.id}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2, delay: index * 0.03 }}
            >
              <Card className="bg-muted/30 hover:bg-muted/50 transition-colors">
                <CardContent className="p-4">
                  <div className="space-y-3">
                    {/* Question and answer */}
                    <div className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-1 shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium mb-1 leading-relaxed">
                          {qa.question.question}
                        </p>

                        {editingQuestionId === qa.question.id ? (
                          /* Edit mode */
                          <div className="space-y-2 mt-2">
                            {qa.question.answer_type === "yes_no" && (
                              <div className="flex gap-2">
                                <Button
                                  type="button"
                                  variant={editValue === true ? "default" : "outline"}
                                  size="sm"
                                  onClick={() => setEditValue(true)}
                                >
                                  Yes
                                </Button>
                                <Button
                                  type="button"
                                  variant={editValue === false ? "default" : "outline"}
                                  size="sm"
                                  onClick={() => setEditValue(false)}
                                >
                                  No
                                </Button>
                              </div>
                            )}
                            {qa.question.answer_type === "single_select" &&
                              qa.question.choices && (
                                <div className="space-y-1">
                                  {qa.question.choices.map((choice) => (
                                    <Button
                                      key={choice}
                                      type="button"
                                      variant={
                                        editValue === choice ? "default" : "outline"
                                      }
                                      size="sm"
                                      onClick={() => setEditValue(choice)}
                                      className="w-full justify-start"
                                    >
                                      {choice}
                                    </Button>
                                  ))}
                                </div>
                              )}
                            {qa.question.answer_type === "text" && (
                              <Textarea
                                value={editValue as string}
                                onChange={(e) => setEditValue(e.target.value)}
                                rows={2}
                                className="text-sm"
                              />
                            )}
                            {qa.question.answer_type === "number" && (
                              <Input
                                type="number"
                                value={editValue as number}
                                onChange={(e) =>
                                  setEditValue(parseFloat(e.target.value) || 0)
                                }
                                className="text-sm"
                              />
                            )}

                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                onClick={() => saveEdit(qa.question.id)}
                              >
                                Save
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={cancelEditing}
                              >
                                <X className="w-3 h-3 mr-1" />
                                Cancel
                              </Button>
                            </div>
                          </div>
                        ) : (
                          /* Display mode */
                          <div className="flex items-center justify-between gap-2">
                            <p className="text-sm text-muted-foreground">
                              <span className="font-medium text-foreground">
                                {String(qa.answer.value)}
                              </span>
                            </p>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => startEditing(qa)}
                              className="shrink-0"
                            >
                              <Edit2 className="w-3 h-3" />
                            </Button>
                          </div>
                        )}

                        {/* Canvas impact */}
                        {qa.canvas_impact && qa.canvas_impact.length > 0 && (
                          <div className="mt-2 flex flex-wrap gap-1">
                            {qa.canvas_impact.map((impact, idx) => (
                              <Badge
                                key={idx}
                                variant="secondary"
                                className="text-xs"
                              >
                                {impact}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
}
