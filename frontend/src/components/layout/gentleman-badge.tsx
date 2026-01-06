"use client";

import { Shield } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function GentlemanBadge() {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge variant="gentleman" className="cursor-help">
            <Shield className="mr-1 h-3 w-3" />
            Gentleman Mode
          </Badge>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs">
          <p className="font-medium">Gentleman Mode Active</p>
          <p className="text-xs text-muted-foreground mt-1">
            All suggestions follow principles of respect, clarity, and confident
            leadership. No manipulation, pressure tactics, or disrespectful
            behavior.
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
