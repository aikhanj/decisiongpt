"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Target, Shield, List, AlertTriangle } from "lucide-react";

interface Criterion {
  id: string;
  name: string;
  weight: number;
  description?: string;
}

interface Constraint {
  id: string;
  text: string;
  type: "hard" | "soft";
}

interface Risk {
  id: string;
  description: string;
  severity: "low" | "medium" | "high";
  mitigation?: string;
  option_id?: string;
}

interface CanvasState {
  statement?: string;
  context_bullets?: string[];
  constraints?: Constraint[];
  criteria?: Criterion[];
  risks?: Risk[];
  next_action?: string;
}

interface CanvasSidebarProps {
  canvas: CanvasState;
}

export function CanvasSidebar({ canvas }: CanvasSidebarProps) {
  const hasContent =
    canvas.statement ||
    (canvas.criteria && canvas.criteria.length > 0) ||
    (canvas.constraints && canvas.constraints.length > 0) ||
    (canvas.context_bullets && canvas.context_bullets.length > 0);

  return (
    <div className="h-full overflow-y-auto p-6 space-y-6 bg-muted/20">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold mb-2 text-gray-900 dark:text-gray-100">
          Decision Canvas
        </h2>
        <p className="text-sm text-muted-foreground">
          Watch your decision take shape in real-time
        </p>
      </div>

      {!hasContent && (
        <Card className="border-dashed">
          <CardContent className="pt-6 text-center text-muted-foreground text-sm">
            Answer questions to build your decision canvas
          </CardContent>
        </Card>
      )}

      <AnimatePresence>
        {/* Decision Statement */}
        {canvas.statement && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Target className="w-4 h-4 text-primary" />
                  Decision
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm font-medium leading-relaxed">
                  {canvas.statement}
                </p>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Criteria */}
        {canvas.criteria && canvas.criteria.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Target className="w-4 h-4 text-blue-600" />
                  What Matters Most
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <AnimatePresence>
                    {canvas.criteria.map((criterion, index) => (
                      <motion.div
                        key={criterion.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                        className="flex items-center justify-between gap-2"
                      >
                        <span className="text-sm flex-1">{criterion.name}</span>
                        <Badge
                          variant="secondary"
                          className="tabular-nums font-mono"
                        >
                          {criterion.weight}/10
                        </Badge>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Constraints */}
        {canvas.constraints && canvas.constraints.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Shield className="w-4 h-4 text-amber-600" />
                  Constraints
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <AnimatePresence>
                    {canvas.constraints.map((constraint, index) => (
                      <motion.div
                        key={constraint.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                        className="flex items-start gap-2"
                      >
                        <Badge
                          variant={
                            constraint.type === "hard" ? "destructive" : "secondary"
                          }
                          className="mt-0.5 shrink-0"
                        >
                          {constraint.type}
                        </Badge>
                        <span className="text-xs leading-relaxed flex-1">
                          {constraint.text}
                        </span>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Context bullets */}
        {canvas.context_bullets && canvas.context_bullets.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <List className="w-4 h-4 text-gray-600" />
                  Context
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="text-xs space-y-2 list-disc list-inside">
                  <AnimatePresence>
                    {canvas.context_bullets.map((bullet, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                        className="leading-relaxed"
                      >
                        {bullet}
                      </motion.li>
                    ))}
                  </AnimatePresence>
                </ul>
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Risks (if any) */}
        {canvas.risks && canvas.risks.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
          >
            <Card className="border-amber-200 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-800">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  Identified Risks
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <AnimatePresence>
                    {canvas.risks.map((risk, index) => (
                      <motion.div
                        key={risk.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        transition={{ duration: 0.2, delay: index * 0.05 }}
                        className="space-y-1"
                      >
                        <div className="flex items-start gap-2">
                          <Badge
                            variant={
                              risk.severity === "high"
                                ? "destructive"
                                : risk.severity === "medium"
                                ? "default"
                                : "secondary"
                            }
                            className="mt-0.5 shrink-0 text-xs"
                          >
                            {risk.severity}
                          </Badge>
                          <span className="text-xs leading-relaxed flex-1">
                            {risk.description}
                          </span>
                        </div>
                        {risk.mitigation && (
                          <p className="text-xs text-muted-foreground pl-16">
                            → {risk.mitigation}
                          </p>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
