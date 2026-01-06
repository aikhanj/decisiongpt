"use client";

import { motion } from "framer-motion";
import { Lightbulb } from "lucide-react";
import { OptionCard } from "../option-card";
import { CommitPlanView } from "@/components/commit/commit-plan-view";
import type { Option, CommitPlan, NodePhase } from "@/types";

interface OptionsTabProps {
  options: Option[];
  commitPlan?: CommitPlan;
  phase: NodePhase;
  onChooseOption?: (optionId: string) => void;
}

export function OptionsTab({
  options,
  commitPlan,
  phase,
  onChooseOption,
}: OptionsTabProps) {
  // If committed, show the commit plan
  if (phase === "execute" && commitPlan) {
    return (
      <div className="space-y-6">
        <CommitPlanView commitPlan={commitPlan} options={options} />
      </div>
    );
  }

  // No options yet
  if (options.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Lightbulb className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No options yet</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          Continue the conversation to gather enough information. Options will
          be generated once we understand your decision better.
        </p>
      </div>
    );
  }

  // Show options
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Your Options</h2>
          <p className="text-sm text-muted-foreground">
            Review and choose the best path forward
          </p>
        </div>
      </div>

      <div className="grid gap-6">
        {options.map((option, index) => (
          <motion.div
            key={option.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
          >
            <OptionCard
              option={option}
              isSelected={commitPlan?.chosen_option_id === option.id}
              onSelect={() => onChooseOption?.(option.id)}
              disabled={!!commitPlan}
            />
          </motion.div>
        ))}
      </div>

      {/* Help text */}
      <div className="text-center text-sm text-muted-foreground">
        <p>Choose an option to generate your action plan</p>
      </div>
    </div>
  );
}
