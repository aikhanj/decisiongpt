"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  MessageCircle,
  Lightbulb,
  Rocket,
  GitBranch,
  X,
  ChevronRight,
  ChevronLeft,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

const STORAGE_KEY = "decision-canvas-onboarded";

interface WelcomeModalProps {
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

const steps = [
  {
    icon: MessageCircle,
    title: "Share Your Situation",
    description:
      "Start by describing the decision you're facing. Be as detailed as you want - the more context, the better the analysis.",
    color: "text-blue-500",
    bgColor: "bg-blue-500/10",
  },
  {
    icon: Lightbulb,
    title: "Explore Your Options",
    description:
      "AI analyzes your situation and presents 2-3 viable options, each with pros, cons, and confidence levels to help you decide.",
    color: "text-amber-500",
    bgColor: "bg-amber-500/10",
  },
  {
    icon: Rocket,
    title: "Execute Your Plan",
    description:
      "Choose an option and get a detailed action plan with specific steps and contingencies for different scenarios.",
    color: "text-emerald-500",
    bgColor: "bg-emerald-500/10",
  },
  {
    icon: GitBranch,
    title: "Branch & Learn",
    description:
      "Changed your mind? Create branches to explore alternative paths. Track outcomes to improve your future decisions.",
    color: "text-purple-500",
    bgColor: "bg-purple-500/10",
  },
];

export function WelcomeModal({ open, onOpenChange }: WelcomeModalProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  // Check if user has been onboarded
  useEffect(() => {
    if (typeof window !== "undefined") {
      const hasOnboarded = localStorage.getItem(STORAGE_KEY);
      if (!hasOnboarded && open === undefined) {
        setIsVisible(true);
      }
    }
  }, [open]);

  const handleClose = () => {
    setIsVisible(false);
    onOpenChange?.(false);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEY, "true");
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      handleClose();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const isOpen = open ?? isVisible;
  const currentStepData = steps[currentStep];
  const Icon = currentStepData.icon;

  return (
    <Dialog open={isOpen} onOpenChange={(value) => {
      if (!value) handleClose();
    }}>
      <DialogContent className="sm:max-w-lg p-0 overflow-hidden">
        <DialogHeader className="p-6 pb-0">
          <div className="flex items-center justify-between">
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Welcome to Decision Canvas
            </DialogTitle>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleClose}
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </DialogHeader>

        <div className="p-6">
          {/* Progress dots */}
          <div className="flex justify-center gap-2 mb-8">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentStep(index)}
                className={cn(
                  "w-2 h-2 rounded-full transition-all duration-300",
                  index === currentStep
                    ? "w-6 bg-primary"
                    : index < currentStep
                    ? "bg-primary/50"
                    : "bg-muted"
                )}
              />
            ))}
          </div>

          {/* Step content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentStep}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.2 }}
              className="text-center"
            >
              <div
                className={cn(
                  "w-20 h-20 rounded-2xl mx-auto mb-6 flex items-center justify-center",
                  currentStepData.bgColor
                )}
              >
                <Icon className={cn("w-10 h-10", currentStepData.color)} />
              </div>

              <h3 className="text-xl font-semibold mb-3">
                {currentStepData.title}
              </h3>
              <p className="text-muted-foreground leading-relaxed">
                {currentStepData.description}
              </p>
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between p-6 pt-0">
          <Button
            variant="ghost"
            onClick={handlePrev}
            disabled={currentStep === 0}
            className="gap-2"
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </Button>

          <Button onClick={handleNext} className="gap-2">
            {currentStep === steps.length - 1 ? (
              "Get Started"
            ) : (
              <>
                Next
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Hook to reset onboarding (for testing)
export function useResetOnboarding() {
  return () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEY);
    }
  };
}
