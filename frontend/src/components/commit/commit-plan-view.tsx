"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  Circle,
  ChevronDown,
  ChevronRight,
  ArrowRight,
  Sparkles,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CommitPlan, Option, CommitStep } from "@/types";

interface CommitPlanViewProps {
  commitPlan: CommitPlan;
  options: Option[];
}

interface StepCardProps {
  step: CommitStep;
  isFirst: boolean;
  onToggleComplete: () => void;
}

function StepCard({ step, isFirst, onToggleComplete }: StepCardProps) {
  const [expanded, setExpanded] = useState(isFirst);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: step.number * 0.1 }}
    >
      <Card
        className={cn(
          "transition-all",
          isFirst && !step.completed && "ring-2 ring-primary border-primary",
          step.completed && "opacity-75"
        )}
      >
        <CardContent className="pt-4 pb-4">
          <div className="flex items-start gap-3">
            {/* Checkbox */}
            <button
              onClick={onToggleComplete}
              className="mt-0.5 shrink-0"
            >
              {step.completed ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              ) : (
                <Circle className="w-5 h-5 text-muted-foreground" />
              )}
            </button>

            <div className="flex-1 min-w-0">
              {/* Step header */}
              <div className="flex items-center gap-2 mb-1">
                <Badge
                  variant={isFirst && !step.completed ? "default" : "secondary"}
                  className="text-xs"
                >
                  Step {step.number}
                </Badge>
                {isFirst && !step.completed && (
                  <Badge
                    variant="outline"
                    className="text-xs text-primary border-primary"
                  >
                    <Sparkles className="w-3 h-3 mr-1" />
                    Start here
                  </Badge>
                )}
              </div>

              {/* Step title */}
              <h4
                className={cn(
                  "font-medium",
                  step.completed && "line-through text-muted-foreground"
                )}
              >
                {step.title}
              </h4>

              {/* Description */}
              {step.description && (
                <p className="text-sm text-muted-foreground mt-1">
                  {step.description}
                </p>
              )}

              {/* If-then branches */}
              {step.branches.length > 0 && (
                <div className="mt-3">
                  <button
                    onClick={() => setExpanded(!expanded)}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
                  >
                    {expanded ? (
                      <ChevronDown className="w-3 h-3" />
                    ) : (
                      <ChevronRight className="w-3 h-3" />
                    )}
                    If-then contingencies
                  </button>

                  {expanded && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      exit={{ opacity: 0, height: 0 }}
                      className="mt-2 space-y-2"
                    >
                      {step.branches.map((branch, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-2 text-sm p-2 rounded-lg bg-muted/50"
                        >
                          <Badge
                            variant="outline"
                            className={cn(
                              "text-xs shrink-0",
                              branch.condition === "success"
                                ? "text-emerald-600 border-emerald-200"
                                : "text-amber-600 border-amber-200"
                            )}
                          >
                            {branch.condition}
                          </Badge>
                          <ArrowRight className="w-3 h-3 mt-0.5 shrink-0 text-muted-foreground" />
                          <span>{branch.action}</span>
                        </div>
                      ))}
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function CommitPlanView({ commitPlan, options }: CommitPlanViewProps) {
  const [steps, setSteps] = useState(commitPlan.steps);

  const chosenOption = options.find(
    (o) => o.id === commitPlan.chosen_option_id
  );

  const toggleStepComplete = (stepNumber: number) => {
    setSteps(
      steps.map((s) =>
        s.number === stepNumber ? { ...s, completed: !s.completed } : s
      )
    );
  };

  const completedCount = steps.filter((s) => s.completed).length;
  const progress = (completedCount / steps.length) * 100;

  // Find first incomplete step
  const firstIncompleteIndex = steps.findIndex((s) => !s.completed);

  return (
    <div className="space-y-6">
      {/* Chosen option summary */}
      {chosenOption && (
        <Card className="bg-primary/5 border-primary/20">
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="default">Chosen</Badge>
              <span className="text-sm font-medium">
                Option {chosenOption.id}
              </span>
            </div>
            <h3 className="font-semibold">{chosenOption.title}</h3>
            <p className="text-sm text-muted-foreground mt-1">
              {chosenOption.good_if}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Progress */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Progress</span>
          <span className="text-sm text-muted-foreground">
            {completedCount}/{steps.length} steps
          </span>
        </div>
        <div className="h-2 bg-muted rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        {steps.map((step, index) => (
          <StepCard
            key={step.number}
            step={step}
            isFirst={index === firstIncompleteIndex}
            onToggleComplete={() => toggleStepComplete(step.number)}
          />
        ))}
      </div>

      {/* All done */}
      {completedCount === steps.length && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center p-6 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl"
        >
          <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
          <h3 className="text-lg font-semibold mb-1">All steps complete!</h3>
          <p className="text-sm text-muted-foreground">
            Don&apos;t forget to log your outcome in the Outcome tab.
          </p>
        </motion.div>
      )}
    </div>
  );
}
