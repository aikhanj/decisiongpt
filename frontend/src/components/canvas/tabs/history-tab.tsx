"use client";

import { motion } from "framer-motion";
import { GitBranch, Clock, ChevronRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DecisionNode, NodePhase } from "@/types";

interface HistoryTabProps {
  nodes?: DecisionNode[];
  currentNodeId?: string;
  onSelectNode?: (nodeId: string) => void;
}

const phaseColors: Record<NodePhase, string> = {
  clarify: "bg-blue-500",
  moves: "bg-amber-500",
  execute: "bg-emerald-500",
};

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function HistoryTab({
  nodes = [],
  currentNodeId,
  onSelectNode,
}: HistoryTabProps) {
  if (nodes.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <GitBranch className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No history yet</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          Decision history will appear here as you progress through your
          decision. You can create branches to explore alternatives.
        </p>
      </div>
    );
  }

  // Build tree structure
  const nodeMap = new Map(nodes.map((n) => [n.id, n]));
  const rootNodes = nodes.filter((n) => !n.parent_node_id);

  const renderNode = (node: DecisionNode, depth: number = 0) => {
    const childNodes = nodes.filter((n) => n.parent_node_id === node.id);
    const isCurrent = node.id === currentNodeId;

    return (
      <motion.div
        key={node.id}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="relative"
      >
        {/* Connection line */}
        {depth > 0 && (
          <div
            className="absolute left-3 -top-3 w-px h-3 bg-border"
            style={{ marginLeft: depth * 24 - 24 }}
          />
        )}

        <Card
          className={cn(
            "cursor-pointer transition-all hover:shadow-md",
            isCurrent && "ring-2 ring-primary border-primary"
          )}
          style={{ marginLeft: depth * 24 }}
          onClick={() => onSelectNode?.(node.id)}
        >
          <CardContent className="pt-4 pb-4">
            <div className="flex items-start gap-3">
              {/* Phase indicator */}
              <div
                className={cn(
                  "w-3 h-3 rounded-full mt-1.5 shrink-0",
                  phaseColors[node.phase]
                )}
              />

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-sm capitalize">
                    {node.phase} phase
                  </span>
                  {isCurrent && (
                    <Badge variant="secondary" className="text-xs">
                      Current
                    </Badge>
                  )}
                  {node.parent_node_id && (
                    <Badge variant="outline" className="text-xs">
                      <GitBranch className="w-3 h-3 mr-1" />
                      Branch
                    </Badge>
                  )}
                </div>

                {/* Summary */}
                {node.canvas_state_json?.statement && (
                  <p className="text-sm text-muted-foreground truncate">
                    {node.canvas_state_json.statement}
                  </p>
                )}

                {/* Timestamp */}
                <div className="flex items-center gap-1 mt-2 text-xs text-muted-foreground">
                  <Clock className="w-3 h-3" />
                  {formatDate(node.created_at)}
                </div>
              </div>

              <ChevronRight className="w-4 h-4 text-muted-foreground shrink-0" />
            </div>
          </CardContent>
        </Card>

        {/* Child nodes */}
        {childNodes.length > 0 && (
          <div className="mt-2 space-y-2">
            {childNodes.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </motion.div>
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Decision History</h2>
        <p className="text-sm text-muted-foreground">
          Track your decision path and explore branches
        </p>
      </div>

      <div className="space-y-2">
        {rootNodes.map((node) => renderNode(node))}
      </div>
    </div>
  );
}
