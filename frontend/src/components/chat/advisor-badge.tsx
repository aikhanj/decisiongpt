"use client";

import { cn } from "@/lib/utils";
import type { AdvisorInfo } from "@/types";

interface AdvisorBadgeProps {
  advisor: AdvisorInfo;
  size?: "sm" | "md";
  showName?: boolean;
}

export function AdvisorBadge({ advisor, size = "sm", showName = true }: AdvisorBadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full bg-secondary/50 border border-border/50",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm"
      )}
    >
      <span className={size === "sm" ? "text-sm" : "text-base"}>{advisor.avatar}</span>
      {showName && (
        <span className="font-medium text-muted-foreground">{advisor.name}</span>
      )}
    </div>
  );
}
