"use client";

import { motion } from "framer-motion";
import { MessageCircle, Lightbulb, Rocket, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { NodePhase } from "@/types";

interface PhaseStepperProps {
  currentPhase: NodePhase;
  className?: string;
}

const phases = [
  {
    id: "clarify",
    label: "Clarify",
    description: "Understanding your situation",
    icon: MessageCircle,
  },
  {
    id: "moves",
    label: "Options",
    description: "Exploring your choices",
    icon: Lightbulb,
  },
  {
    id: "execute",
    label: "Execute",
    description: "Your action plan",
    icon: Rocket,
  },
] as const;

const phaseOrder: Record<NodePhase, number> = {
  clarify: 0,
  moves: 1,
  execute: 2,
};

export function PhaseStepper({ currentPhase, className }: PhaseStepperProps) {
  const currentIndex = phaseOrder[currentPhase];

  return (
    <div className={cn("flex items-center gap-1", className)}>
      {phases.map((phase, index) => {
        const isCompleted = index < currentIndex;
        const isCurrent = index === currentIndex;
        const Icon = phase.icon;

        return (
          <div key={phase.id} className="flex items-center">
            {/* Step */}
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-2"
            >
              <div
                className={cn(
                  "relative flex items-center justify-center w-8 h-8 rounded-full transition-all duration-300",
                  isCompleted && "bg-emerald-500 text-white",
                  isCurrent && "bg-primary text-primary-foreground ring-2 ring-primary/30",
                  !isCompleted && !isCurrent && "bg-muted text-muted-foreground"
                )}
              >
                {isCompleted ? (
                  <Check className="w-4 h-4" />
                ) : (
                  <Icon className="w-4 h-4" />
                )}
                {isCurrent && (
                  <motion.div
                    className="absolute inset-0 rounded-full bg-primary/20"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  />
                )}
              </div>
              <div className="hidden sm:block">
                <p
                  className={cn(
                    "text-sm font-medium",
                    isCurrent && "text-primary",
                    isCompleted && "text-emerald-600",
                    !isCompleted && !isCurrent && "text-muted-foreground"
                  )}
                >
                  {phase.label}
                </p>
              </div>
            </motion.div>

            {/* Connector */}
            {index < phases.length - 1 && (
              <div className="mx-2 sm:mx-4">
                <div
                  className={cn(
                    "w-8 sm:w-12 h-0.5 rounded-full transition-colors duration-300",
                    index < currentIndex ? "bg-emerald-500" : "bg-muted"
                  )}
                />
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
