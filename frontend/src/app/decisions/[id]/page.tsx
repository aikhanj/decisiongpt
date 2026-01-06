"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Loader2,
  ChevronRight,
  MessageSquare,
  CheckCircle,
  GitBranch,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDecision } from "@/lib/api";
import type { Decision, DecisionNode } from "@/types";
import { toast } from "sonner";
import { formatDate, formatTime } from "@/lib/utils";

const phaseConfig = {
  clarify: {
    icon: MessageSquare,
    label: "Clarifying",
    color: "text-blue-500",
    bgColor: "bg-blue-50",
  },
  moves: {
    icon: GitBranch,
    label: "Choosing Move",
    color: "text-amber-500",
    bgColor: "bg-amber-50",
  },
  execute: {
    icon: CheckCircle,
    label: "Executing",
    color: "text-green-500",
    bgColor: "bg-green-50",
  },
};

export default function DecisionDetailPage() {
  const router = useRouter();
  const params = useParams();
  const decisionId = params.id as string;

  const [decision, setDecision] = useState<Decision | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDecision() {
      try {
        const data = await getDecision(decisionId);
        setDecision(data);
      } catch (error) {
        toast.error("Failed to load decision");
        router.push("/");
      } finally {
        setLoading(false);
      }
    }
    loadDecision();
  }, [decisionId, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!decision) {
    return null;
  }

  // Sort nodes by created_at
  const sortedNodes = [...decision.nodes].sort(
    (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
  );

  // Find the current active node (latest without a resolution)
  const activeNode = sortedNodes[sortedNodes.length - 1];

  // Determine where to continue
  const getContinueUrl = (node: DecisionNode) => {
    switch (node.phase) {
      case "clarify":
        return `/decisions/${decisionId}/clarify`;
      case "moves":
        return `/decisions/${decisionId}/moves`;
      case "execute":
        return `/decisions/${decisionId}/execute`;
      default:
        return `/decisions/${decisionId}`;
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <div className="flex items-center gap-2">
          <Badge
            variant={decision.status === "resolved" ? "success" : "warning"}
          >
            {decision.status}
          </Badge>
          {decision.situation_type && (
            <Badge variant="outline">
              {decision.situation_type.replace(/_/g, " ")}
            </Badge>
          )}
        </div>
        <h1 className="text-2xl font-bold">
          {decision.title || "Untitled Decision"}
        </h1>
        <p className="text-muted-foreground">{decision.situation_text}</p>
        <p className="text-sm text-muted-foreground">
          Started {formatDate(decision.created_at)} at{" "}
          {formatTime(decision.created_at)}
        </p>
      </motion.div>

      {/* Continue Button */}
      {decision.status === "active" && activeNode && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="border-primary">
            <CardContent className="flex items-center justify-between py-4">
              <div className="flex items-center gap-3">
                {(() => {
                  const config =
                    phaseConfig[activeNode.phase as keyof typeof phaseConfig];
                  const Icon = config?.icon || Clock;
                  return (
                    <>
                      <div
                        className={`p-2 rounded-full ${config?.bgColor || "bg-muted"}`}
                      >
                        <Icon className={`h-5 w-5 ${config?.color || ""}`} />
                      </div>
                      <div>
                        <p className="font-medium">
                          {config?.label || "In Progress"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          Continue where you left off
                        </p>
                      </div>
                    </>
                  );
                })()}
              </div>
              <Link href={getContinueUrl(activeNode)}>
                <Button>
                  Continue
                  <ChevronRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Timeline */}
      <div className="space-y-4">
        <h2 className="text-xl font-semibold">Timeline</h2>
        <div className="space-y-4">
          {sortedNodes.map((node, index) => {
            const config =
              phaseConfig[node.phase as keyof typeof phaseConfig];
            const Icon = config?.icon || Clock;
            const isLast = index === sortedNodes.length - 1;
            const hasParent = node.parent_node_id !== null;

            return (
              <motion.div
                key={node.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                {/* Connector line */}
                {index > 0 && (
                  <div className="absolute left-5 -top-4 w-0.5 h-4 bg-border" />
                )}

                <Card className={hasParent ? "ml-8" : ""}>
                  <CardHeader className="pb-2">
                    <div className="flex items-center gap-3">
                      <div
                        className={`p-2 rounded-full ${config?.bgColor || "bg-muted"}`}
                      >
                        <Icon className={`h-4 w-4 ${config?.color || ""}`} />
                      </div>
                      <div className="flex-1">
                        <CardTitle className="text-base">
                          {config?.label || node.phase}
                        </CardTitle>
                        <CardDescription>
                          {formatDate(node.created_at)} at{" "}
                          {formatTime(node.created_at)}
                        </CardDescription>
                      </div>
                      {hasParent && (
                        <Badge variant="outline" className="text-xs">
                          <GitBranch className="mr-1 h-3 w-3" />
                          Branch
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    {node.phase === "clarify" &&
                      node.questions_json?.questions && (
                        <p className="text-sm text-muted-foreground">
                          {node.questions_json.questions.length} questions
                          generated
                        </p>
                      )}
                    {node.phase === "moves" && node.moves_json?.moves && (
                      <p className="text-sm text-muted-foreground">
                        {node.moves_json.moves.length} options generated
                      </p>
                    )}
                    {node.phase === "execute" && node.chosen_move_id && (
                      <p className="text-sm text-muted-foreground">
                        Chose Move {node.chosen_move_id}
                      </p>
                    )}
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
