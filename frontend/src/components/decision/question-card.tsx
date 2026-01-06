"use client";

import { motion } from "framer-motion";
import { HelpCircle, Lightbulb } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { Question, Answer } from "@/types";

interface QuestionCardProps {
  question: Question;
  index: number;
  value: string | number | boolean | undefined;
  onChange: (answer: Answer) => void;
}

export function QuestionCard({
  question,
  index,
  value,
  onChange,
}: QuestionCardProps) {
  const handleChange = (newValue: string | number | boolean) => {
    onChange({ question_id: question.id, value: newValue });
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-base font-medium">
              {question.question}
            </CardTitle>
            <div className="flex gap-1 shrink-0">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <HelpCircle className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left" className="max-w-xs">
                  <p className="font-medium">Why I'm asking</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {question.why_this_question}
                  </p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button variant="ghost" size="icon" className="h-8 w-8">
                    <Lightbulb className="h-4 w-4 text-muted-foreground" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="left" className="max-w-xs">
                  <p className="font-medium">What it changes</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {question.what_it_changes}
                  </p>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {question.answer_type === "yes_no" && (
            <div className="flex gap-2">
              <Button
                variant={value === true ? "default" : "outline"}
                onClick={() => handleChange(true)}
                className="flex-1"
              >
                Yes
              </Button>
              <Button
                variant={value === false ? "default" : "outline"}
                onClick={() => handleChange(false)}
                className="flex-1"
              >
                No
              </Button>
            </div>
          )}

          {question.answer_type === "single_select" && question.choices && (
            <div className="flex flex-wrap gap-2">
              {question.choices.map((choice) => (
                <Button
                  key={choice}
                  variant={value === choice ? "default" : "outline"}
                  onClick={() => handleChange(choice)}
                  size="sm"
                >
                  {choice}
                </Button>
              ))}
            </div>
          )}

          {question.answer_type === "number" && (
            <Input
              type="number"
              value={value as number || ""}
              onChange={(e) => handleChange(parseInt(e.target.value) || 0)}
              placeholder="Enter a number"
            />
          )}

          {question.answer_type === "text" && (
            <Textarea
              value={value as string || ""}
              onChange={(e) => handleChange(e.target.value)}
              placeholder="Type your answer..."
              className="min-h-[80px]"
            />
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
