"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Clock } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import type { CanvasState, Option, CommitPlan, Question, NodePhase, DecisionNode, DecisionOutcome } from "@/types";

// Tab components - will be created separately
import { SummaryTab } from "./tabs/summary-tab";
import { OptionsTab } from "./tabs/options-tab";
import { CriteriaTab } from "./tabs/criteria-tab";
import { ConstraintsTab } from "./tabs/constraints-tab";
import { RisksTab } from "./tabs/risks-tab";
import { OutcomeTab } from "./tabs/outcome-tab";
import { HistoryTab } from "./tabs/history-tab";

interface CanvasContainerProps {
  canvasState: CanvasState | null;
  phase: NodePhase;
  options?: Option[];
  commitPlan?: CommitPlan | null;
  outcome?: DecisionOutcome | null;
  nodes?: DecisionNode[];
  currentNodeId?: string;
  questions?: Question[];
  onChooseOption?: (optionId: string) => void;
  onUpdateCanvas?: (updates: Partial<CanvasState>) => void;
  onLogOutcome?: (outcome: { progress_yesno: boolean; sentiment_2h?: number; sentiment_24h?: number; notes?: string }) => void;
  onNavigateNode?: (nodeId: string) => void;
  className?: string;
}

export function CanvasContainer({
  canvasState,
  phase,
  options = [],
  commitPlan,
  questions = [],
  onChooseOption,
  onUpdateCanvas,
  className,
}: CanvasContainerProps) {
  // Determine default tab based on phase
  const defaultTab =
    phase === "execute" && commitPlan
      ? "options"
      : phase === "moves"
      ? "options"
      : "summary";

  // Default canvas state when null
  const safeCanvasState: CanvasState = canvasState ?? {
    context_bullets: [],
    constraints: [],
    criteria: [],
    risks: [],
  };

  return (
    <div className={cn("flex flex-col h-full bg-muted/30", className)}>
      <Tabs defaultValue={defaultTab} className="flex flex-col h-full">
        {/* Tab Navigation */}
        <div className="border-b bg-background px-4">
          <TabsList className="h-12 bg-transparent gap-1">
            <TabsTrigger
              value="summary"
              className="data-[state=active]:bg-muted rounded-lg"
            >
              Summary
            </TabsTrigger>
            <TabsTrigger
              value="options"
              className="data-[state=active]:bg-muted rounded-lg"
              disabled={phase === "clarify" && options.length === 0}
            >
              Options
              {options.length > 0 && (
                <span className="ml-1.5 text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded">
                  {options.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger
              value="criteria"
              className="data-[state=active]:bg-muted rounded-lg"
            >
              Criteria
            </TabsTrigger>
            <TabsTrigger
              value="constraints"
              className="data-[state=active]:bg-muted rounded-lg"
            >
              Constraints
            </TabsTrigger>
            <TabsTrigger
              value="risks"
              className="data-[state=active]:bg-muted rounded-lg"
            >
              Risks
            </TabsTrigger>
            <TabsTrigger
              value="outcome"
              className="data-[state=active]:bg-muted rounded-lg"
            >
              Outcome
            </TabsTrigger>
            <TabsTrigger
              value="history"
              className="data-[state=active]:bg-muted rounded-lg"
            >
              History
            </TabsTrigger>
          </TabsList>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <TabsContent value="summary" className="h-full m-0 overflow-y-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <SummaryTab
                  canvasState={safeCanvasState}
                  phase={phase}
                  optionsCount={options.length}
                />
              </motion.div>
            </TabsContent>

            <TabsContent value="options" className="h-full m-0 overflow-y-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <OptionsTab
                  options={options}
                  commitPlan={commitPlan ?? undefined}
                  phase={phase}
                  onChooseOption={onChooseOption}
                />
              </motion.div>
            </TabsContent>

            <TabsContent value="criteria" className="h-full m-0 overflow-y-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <CriteriaTab
                  criteria={safeCanvasState.criteria}
                  onUpdate={(criteria) => onUpdateCanvas?.({ criteria })}
                />
              </motion.div>
            </TabsContent>

            <TabsContent
              value="constraints"
              className="h-full m-0 overflow-y-auto"
            >
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <ConstraintsTab
                  constraints={safeCanvasState.constraints}
                  onUpdate={(constraints) => onUpdateCanvas?.({ constraints })}
                />
              </motion.div>
            </TabsContent>

            <TabsContent value="risks" className="h-full m-0 overflow-y-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <RisksTab risks={safeCanvasState.risks} options={options} />
              </motion.div>
            </TabsContent>

            <TabsContent value="outcome" className="h-full m-0 overflow-y-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <OutcomeTab phase={phase} />
              </motion.div>
            </TabsContent>

            <TabsContent value="history" className="h-full m-0 overflow-y-auto">
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="p-6"
              >
                <HistoryTab />
              </motion.div>
            </TabsContent>
          </AnimatePresence>

          {/* Next Action Box */}
          {safeCanvasState.next_action && (
            <div className="absolute bottom-4 left-4 right-4">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-primary/5 border border-primary/20 rounded-xl p-4"
              >
                <div className="flex items-center gap-2 text-sm font-medium text-primary mb-1">
                  <Clock className="w-4 h-4" />
                  Next action in 10 min
                </div>
                <p className="text-sm text-muted-foreground">
                  {safeCanvasState.next_action}
                </p>
              </motion.div>
            </div>
          )}
        </div>
      </Tabs>
    </div>
  );
}
