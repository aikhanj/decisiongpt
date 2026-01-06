"use client";

import { motion } from "framer-motion";
import { AlertTriangle, Shield } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Risk, Option, RiskLevel } from "@/types";

interface RisksTabProps {
  risks: Risk[];
  options: Option[];
}

const severityColors: Record<RiskLevel, string> = {
  low: "bg-emerald-100 text-emerald-700 border-emerald-200",
  medium: "bg-amber-100 text-amber-700 border-amber-200",
  high: "bg-rose-100 text-rose-700 border-rose-200",
};

const severityIcons: Record<RiskLevel, string> = {
  low: "bg-emerald-500",
  medium: "bg-amber-500",
  high: "bg-rose-500",
};

export function RisksTab({ risks = [], options = [] }: RisksTabProps) {
  // Also collect risks from options
  const optionRisks = options.flatMap((opt) =>
    opt.risks.map((r) => ({
      id: `${opt.id}_${r}`,
      description: r.replace(/_/g, " "),
      severity: "medium" as RiskLevel,
      option_id: opt.id,
      mitigation: undefined as string | undefined,
    }))
  );

  const allRisks = [...risks, ...optionRisks];

  if (allRisks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Shield className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No risks identified</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          Risks will be identified as we analyze your options. Continue the
          conversation to generate options.
        </p>
      </div>
    );
  }

  // Group risks by severity
  const highRisks = allRisks.filter((r) => r.severity === "high");
  const mediumRisks = allRisks.filter((r) => r.severity === "medium");
  const lowRisks = allRisks.filter((r) => r.severity === "low");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Risk Assessment</h2>
        <p className="text-sm text-muted-foreground">
          Potential risks identified across your options
        </p>
      </div>

      {/* Risk summary */}
      <div className="grid grid-cols-3 gap-4">
        <Card className="bg-rose-50 dark:bg-rose-950/20 border-rose-200">
          <CardContent className="pt-4 pb-4 text-center">
            <div className="text-2xl font-bold text-rose-600">
              {highRisks.length}
            </div>
            <div className="text-xs text-rose-600">High Risk</div>
          </CardContent>
        </Card>
        <Card className="bg-amber-50 dark:bg-amber-950/20 border-amber-200">
          <CardContent className="pt-4 pb-4 text-center">
            <div className="text-2xl font-bold text-amber-600">
              {mediumRisks.length}
            </div>
            <div className="text-xs text-amber-600">Medium Risk</div>
          </CardContent>
        </Card>
        <Card className="bg-emerald-50 dark:bg-emerald-950/20 border-emerald-200">
          <CardContent className="pt-4 pb-4 text-center">
            <div className="text-2xl font-bold text-emerald-600">
              {lowRisks.length}
            </div>
            <div className="text-xs text-emerald-600">Low Risk</div>
          </CardContent>
        </Card>
      </div>

      {/* Risk list */}
      <div className="space-y-3">
        {allRisks.map((risk, index) => (
          <motion.div
            key={risk.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-start gap-3">
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full mt-2 shrink-0",
                      severityIcons[risk.severity]
                    )}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium capitalize">
                        {risk.description}
                      </span>
                      <Badge
                        variant="outline"
                        className={cn("text-xs", severityColors[risk.severity])}
                      >
                        {risk.severity}
                      </Badge>
                      {risk.option_id && (
                        <Badge variant="secondary" className="text-xs">
                          Option {risk.option_id}
                        </Badge>
                      )}
                    </div>
                    {risk.mitigation && (
                      <p className="text-sm text-muted-foreground">
                        <span className="font-medium">Mitigation:</span>{" "}
                        {risk.mitigation}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
