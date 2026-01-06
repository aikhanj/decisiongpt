"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  GitBranch,
  CheckCircle2,
  Download,
  ChevronLeft,
  Pencil,
  Check,
  X,
  Trash2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { NodePhase, DecisionStatus } from "@/types";
import Link from "next/link";

interface DecisionHeaderProps {
  title: string;
  status: DecisionStatus;
  phase: NodePhase;
  onTitleChange?: (title: string) => void;
  onBranchClick?: () => void;
  onOutcomeClick?: () => void;
  onExportClick?: () => void;
  onDeleteClick?: () => void;
  className?: string;
}

const phaseLabels: Record<NodePhase, string> = {
  clarify: "Clarifying",
  moves: "Options",
  execute: "Committed",
};

const phaseColors: Record<NodePhase, string> = {
  clarify: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  moves: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  execute: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
};

const statusColors: Record<DecisionStatus, string> = {
  active: "bg-blue-500",
  resolved: "bg-emerald-500",
  archived: "bg-muted",
};

export function DecisionHeader({
  title,
  status,
  phase,
  onTitleChange,
  onBranchClick,
  onOutcomeClick,
  onExportClick,
  onDeleteClick,
  className,
}: DecisionHeaderProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editedTitle, setEditedTitle] = useState(title);

  const handleSaveTitle = () => {
    if (editedTitle.trim() && onTitleChange) {
      onTitleChange(editedTitle.trim());
    }
    setIsEditing(false);
  };

  const handleCancelEdit = () => {
    setEditedTitle(title);
    setIsEditing(false);
  };

  return (
    <TooltipProvider>
      <motion.header
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "flex items-center justify-between gap-4 px-6 py-4",
          "border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60",
          className
        )}
      >
        {/* Left: Back + Title */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" asChild>
                <Link href="/">
                  <ChevronLeft className="h-5 w-5" />
                </Link>
              </Button>
            </TooltipTrigger>
            <TooltipContent>Back to decisions</TooltipContent>
          </Tooltip>

          {/* Status indicator */}
          <div
            className={cn("w-2 h-2 rounded-full", statusColors[status])}
            title={status}
          />

          {/* Title */}
          {isEditing ? (
            <div className="flex items-center gap-2 flex-1">
              <Input
                value={editedTitle}
                onChange={(e) => setEditedTitle(e.target.value)}
                className="h-8 text-lg font-semibold"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") handleSaveTitle();
                  if (e.key === "Escape") handleCancelEdit();
                }}
              />
              <Button size="icon" variant="ghost" onClick={handleSaveTitle}>
                <Check className="h-4 w-4 text-emerald-500" />
              </Button>
              <Button size="icon" variant="ghost" onClick={handleCancelEdit}>
                <X className="h-4 w-4 text-muted-foreground" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-2 min-w-0 flex-1">
              <h1 className="text-lg font-semibold truncate">{title}</h1>
              {onTitleChange && (
                <Button
                  size="icon"
                  variant="ghost"
                  className="h-6 w-6 opacity-0 group-hover:opacity-100 hover:opacity-100"
                  onClick={() => setIsEditing(true)}
                >
                  <Pencil className="h-3 w-3" />
                </Button>
              )}
            </div>
          )}

          {/* Phase badge */}
          <Badge
            variant="outline"
            className={cn("shrink-0", phaseColors[phase])}
          >
            {phaseLabels[phase]}
          </Badge>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-2">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="outline" size="sm" onClick={onBranchClick}>
                <GitBranch className="h-4 w-4 mr-2" />
                Branch
              </Button>
            </TooltipTrigger>
            <TooltipContent>Create alternative path</TooltipContent>
          </Tooltip>

          {phase === "execute" && (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline" size="sm" onClick={onOutcomeClick}>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Log Outcome
                </Button>
              </TooltipTrigger>
              <TooltipContent>Record decision result</TooltipContent>
            </Tooltip>
          )}

          <Tooltip>
            <TooltipTrigger asChild>
              <Button variant="ghost" size="icon" onClick={onExportClick}>
                <Download className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Export decision</TooltipContent>
          </Tooltip>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                onClick={onDeleteClick}
                className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Delete decision</TooltipContent>
          </Tooltip>
        </div>
      </motion.header>
    </TooltipProvider>
  );
}
