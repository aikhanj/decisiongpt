"use client";

import { useMemo } from "react";
import { motion } from "framer-motion";
import { GitBranch, ChevronRight, Home } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { DecisionNode } from "@/types";

interface BranchIndicatorProps {
  nodes: DecisionNode[];
  currentNodeId: string;
  onNavigate: (nodeId: string) => void;
}

export function BranchIndicator({
  nodes,
  currentNodeId,
  onNavigate,
}: BranchIndicatorProps) {
  // Build path from root to current node
  const path = useMemo(() => {
    const nodeMap = new Map(nodes.map((n) => [n.id, n]));
    const pathNodes: DecisionNode[] = [];
    let current = nodeMap.get(currentNodeId);

    while (current) {
      pathNodes.unshift(current);
      current = current.parent_node_id
        ? nodeMap.get(current.parent_node_id)
        : undefined;
    }

    return pathNodes;
  }, [nodes, currentNodeId]);

  // Get sibling branches (other nodes with same parent)
  const getSiblings = (nodeId: string): DecisionNode[] => {
    const node = nodes.find((n) => n.id === nodeId);
    if (!node) return [];
    return nodes.filter(
      (n) => n.parent_node_id === node.parent_node_id && n.id !== nodeId
    );
  };

  // If only root node, show simple indicator
  if (path.length <= 1) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Home className="w-4 h-4" />
        <span>Root</span>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-1 text-sm"
    >
      {path.map((node, index) => {
        const isLast = index === path.length - 1;
        const siblings = getSiblings(node.id);
        const hasSiblings = siblings.length > 0;

        return (
          <div key={node.id} className="flex items-center">
            {index > 0 && (
              <ChevronRight className="w-3 h-3 mx-1 text-muted-foreground" />
            )}

            {hasSiblings ? (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className={cn(
                      "h-auto py-1 px-2",
                      isLast && "font-medium text-primary"
                    )}
                  >
                    {index === 0 ? (
                      <Home className="w-3 h-3 mr-1" />
                    ) : (
                      <GitBranch className="w-3 h-3 mr-1" />
                    )}
                    {index === 0 ? "Root" : `Branch ${index}`}
                    {siblings.length > 0 && (
                      <Badge
                        variant="secondary"
                        className="ml-1 text-xs py-0 px-1"
                      >
                        +{siblings.length}
                      </Badge>
                    )}
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  <DropdownMenuItem
                    onClick={() => onNavigate(node.id)}
                    className={cn(node.id === currentNodeId && "bg-accent")}
                  >
                    <div className="flex items-center gap-2">
                      {node.id === currentNodeId && (
                        <div className="w-2 h-2 rounded-full bg-primary" />
                      )}
                      <span>
                        {index === 0 ? "Root" : `Branch ${index}`}
                        {node.id === currentNodeId && " (current)"}
                      </span>
                    </div>
                  </DropdownMenuItem>
                  {siblings.map((sibling, sibIndex) => (
                    <DropdownMenuItem
                      key={sibling.id}
                      onClick={() => onNavigate(sibling.id)}
                      className={cn(
                        sibling.id === currentNodeId && "bg-accent"
                      )}
                    >
                      <div className="flex items-center gap-2">
                        {sibling.id === currentNodeId && (
                          <div className="w-2 h-2 rounded-full bg-primary" />
                        )}
                        <span>
                          Alternative {sibIndex + 1}
                          {sibling.id === currentNodeId && " (current)"}
                        </span>
                      </div>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigate(node.id)}
                className={cn(
                  "h-auto py-1 px-2",
                  isLast && "font-medium text-primary",
                  !isLast && "text-muted-foreground"
                )}
              >
                {index === 0 ? (
                  <Home className="w-3 h-3 mr-1" />
                ) : (
                  <GitBranch className="w-3 h-3 mr-1" />
                )}
                {index === 0 ? "Root" : `Branch ${index}`}
              </Button>
            )}
          </div>
        );
      })}
    </motion.div>
  );
}

// Compact version for tight spaces
interface CompactBranchIndicatorProps {
  depth: number;
  onOpenHistory: () => void;
}

export function CompactBranchIndicator({
  depth,
  onOpenHistory,
}: CompactBranchIndicatorProps) {
  if (depth === 0) return null;

  return (
    <Button
      variant="outline"
      size="sm"
      onClick={onOpenHistory}
      className="h-7 text-xs"
    >
      <GitBranch className="w-3 h-3 mr-1" />
      Branch depth: {depth}
    </Button>
  );
}
