"use client";

import { motion } from "framer-motion";
import { FileText, ListChecks, Filter, Target } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { CanvasState, NodePhase } from "@/types";

interface SummaryTabProps {
  canvasState: CanvasState;
  phase: NodePhase;
  optionsCount: number;
}

const phaseLabels: Record<NodePhase, { label: string; color: string }> = {
  clarify: { label: "Gathering Information", color: "bg-blue-500" },
  moves: { label: "Reviewing Options", color: "bg-amber-500" },
  execute: { label: "Ready to Execute", color: "bg-emerald-500" },
};

export function SummaryTab({
  canvasState,
  phase,
  optionsCount,
}: SummaryTabProps) {
  const hasContent =
    canvasState.statement ||
    canvasState.context_bullets.length > 0 ||
    canvasState.constraints.length > 0 ||
    canvasState.criteria.length > 0;

  if (!hasContent) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <FileText className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No decision yet</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          Start chatting to define your decision. The canvas will fill in as we
          gather information.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Phase Indicator */}
      <div className="flex items-center gap-3">
        <div
          className={cn(
            "w-3 h-3 rounded-full",
            phaseLabels[phase].color
          )}
        />
        <span className="text-sm font-medium">
          {phaseLabels[phase].label}
        </span>
      </div>

      {/* Decision Statement */}
      {canvasState.statement && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-2 border-primary/20 bg-primary/5">
            <CardContent className="pt-6">
              <p className="text-xl font-semibold leading-relaxed">
                {canvasState.statement}
              </p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Context */}
      {canvasState.context_bullets.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <ListChecks className="w-4 h-4" />
                Context
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {canvasState.context_bullets.map((bullet, i) => (
                  <motion.li
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05 }}
                    className="flex items-start gap-2 text-sm"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                    {bullet}
                  </motion.li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Stats Row */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="grid grid-cols-3 gap-4"
      >
        <Card className="bg-muted/50">
          <CardContent className="pt-4 pb-4 text-center">
            <div className="text-2xl font-bold text-primary">{optionsCount}</div>
            <div className="text-xs text-muted-foreground">Options</div>
          </CardContent>
        </Card>
        <Card className="bg-muted/50">
          <CardContent className="pt-4 pb-4 text-center">
            <div className="text-2xl font-bold text-primary">
              {canvasState.constraints.length}
            </div>
            <div className="text-xs text-muted-foreground">Constraints</div>
          </CardContent>
        </Card>
        <Card className="bg-muted/50">
          <CardContent className="pt-4 pb-4 text-center">
            <div className="text-2xl font-bold text-primary">
              {canvasState.criteria.length}
            </div>
            <div className="text-xs text-muted-foreground">Criteria</div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Quick View: Top Constraints */}
      {canvasState.constraints.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <Filter className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Key Constraints</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {canvasState.constraints.slice(0, 4).map((c) => (
              <Badge
                key={c.id}
                variant={c.type === "hard" ? "default" : "secondary"}
                className="text-xs"
              >
                {c.text}
              </Badge>
            ))}
            {canvasState.constraints.length > 4 && (
              <Badge variant="outline" className="text-xs">
                +{canvasState.constraints.length - 4} more
              </Badge>
            )}
          </div>
        </motion.div>
      )}

      {/* Quick View: Top Criteria */}
      {canvasState.criteria.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">Top Criteria</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {canvasState.criteria
              .sort((a, b) => b.weight - a.weight)
              .slice(0, 4)
              .map((c) => (
                <Badge
                  key={c.id}
                  variant="outline"
                  className="text-xs"
                >
                  {c.name}
                  <span className="ml-1 text-primary font-semibold">
                    {c.weight}
                  </span>
                </Badge>
              ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
