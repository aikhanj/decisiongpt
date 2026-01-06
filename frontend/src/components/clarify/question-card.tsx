"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  CheckCircle2,
  Circle,
  HelpCircle,
  Lightbulb,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

export type QuestionType = "yes_no" | "select" | "slider" | "text" | "number";

export interface QuestionOption {
  value: string;
  label: string;
}

export interface Question {
  id: string;
  text: string;
  type: QuestionType;
  options?: QuestionOption[];
  min?: number;
  max?: number;
  minLabel?: string;
  maxLabel?: string;
  required?: boolean;
  why?: string;
  impact?: string;
}

interface QuestionCardProps {
  question: Question;
  value?: string | number | boolean;
  onChange: (value: string | number | boolean) => void;
  index?: number;
}

export function QuestionCard({
  question,
  value,
  onChange,
  index = 0,
}: QuestionCardProps) {
  const isAnswered = value !== undefined && value !== "";

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card
        className={cn(
          "transition-all",
          isAnswered && "border-emerald-200 bg-emerald-50/50 dark:bg-emerald-950/20"
        )}
      >
        <CardContent className="pt-4 pb-4">
          <div className="flex items-start gap-3">
            {/* Checkbox indicator */}
            <div className="mt-0.5 shrink-0">
              {isAnswered ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-500" />
              ) : (
                <Circle className="w-5 h-5 text-muted-foreground" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              {/* Question text with tooltips */}
              <div className="flex items-start gap-2 mb-3">
                <p className="font-medium text-sm flex-1">{question.text}</p>
                <TooltipProvider>
                  <div className="flex gap-1 shrink-0">
                    {question.why && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                          >
                            <HelpCircle className="w-4 h-4 text-muted-foreground" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="max-w-xs">
                          <p className="text-xs">
                            <strong>Why this question?</strong> {question.why}
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                    {question.impact && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="h-6 w-6"
                          >
                            <Lightbulb className="w-4 h-4 text-amber-500" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent side="top" className="max-w-xs">
                          <p className="text-xs">
                            <strong>What it changes:</strong> {question.impact}
                          </p>
                        </TooltipContent>
                      </Tooltip>
                    )}
                  </div>
                </TooltipProvider>
              </div>

              {/* Input based on type */}
              <div className="space-y-2">
                {question.type === "yes_no" && (
                  <YesNoInput
                    value={value as boolean | undefined}
                    onChange={onChange}
                  />
                )}
                {question.type === "select" && question.options && (
                  <SelectInput
                    options={question.options}
                    value={value as string | undefined}
                    onChange={onChange}
                  />
                )}
                {question.type === "slider" && (
                  <SliderInput
                    min={question.min || 0}
                    max={question.max || 10}
                    minLabel={question.minLabel}
                    maxLabel={question.maxLabel}
                    value={value as number | undefined}
                    onChange={onChange}
                  />
                )}
                {question.type === "text" && (
                  <TextInput
                    value={value as string | undefined}
                    onChange={onChange}
                  />
                )}
                {question.type === "number" && (
                  <NumberInput
                    min={question.min}
                    max={question.max}
                    value={value as number | undefined}
                    onChange={onChange}
                  />
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
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
    <div className="flex gap-2">
      <Button
        variant={value === true ? "default" : "outline"}
        size="sm"
        onClick={() => onChange(true)}
        className={cn(
          "flex-1",
          value === true && "bg-emerald-500 hover:bg-emerald-600"
        )}
      >
        Yes
      </Button>
      <Button
        variant={value === false ? "default" : "outline"}
        size="sm"
        onClick={() => onChange(false)}
        className={cn(
          "flex-1",
          value === false && "bg-rose-500 hover:bg-rose-600"
        )}
      >
        No
      </Button>
    </div>
  );
}

// Radio-style select
function SelectInput({
  options,
  value,
  onChange,
}: {
  options: QuestionOption[];
  value?: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((opt) => (
        <Button
          key={opt.value}
          variant={value === opt.value ? "default" : "outline"}
          size="sm"
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </Button>
      ))}
    </div>
  );
}

// Slider with labels
function SliderInput({
  min,
  max,
  minLabel,
  maxLabel,
  value,
  onChange,
}: {
  min: number;
  max: number;
  minLabel?: string;
  maxLabel?: string;
  value?: number;
  onChange: (v: number) => void;
}) {
  const currentValue = value ?? Math.floor((min + max) / 2);

  return (
    <div className="space-y-2">
      <Slider
        value={[currentValue]}
        onValueChange={([v]) => onChange(v)}
        min={min}
        max={max}
        step={1}
        className="w-full"
      />
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{minLabel || min}</span>
        <span className="font-medium text-foreground">{currentValue}</span>
        <span>{maxLabel || max}</span>
      </div>
    </div>
  );
}

// Text input
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
      placeholder="Your answer..."
      rows={2}
      className="resize-none"
    />
  );
}

// Number input
function NumberInput({
  min,
  max,
  value,
  onChange,
}: {
  min?: number;
  max?: number;
  value?: number;
  onChange: (v: number) => void;
}) {
  return (
    <Input
      type="number"
      value={value ?? ""}
      onChange={(e) => onChange(parseFloat(e.target.value))}
      min={min}
      max={max}
      className="w-32"
    />
  );
}
