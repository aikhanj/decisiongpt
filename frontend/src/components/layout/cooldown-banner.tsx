"use client";

import { motion } from "framer-motion";
import { Clock, AlertTriangle } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface CooldownBannerProps {
  reason: string;
  moodState?: string;
}

export function CooldownBanner({ reason, moodState }: CooldownBannerProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-blue-200 bg-blue-50 p-4"
    >
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100">
          <Clock className="h-5 w-5 text-blue-600" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-blue-900">Cool-down Suggested</h3>
            {moodState && (
              <Badge variant="cooldown" className="text-xs">
                {moodState}
              </Badge>
            )}
          </div>
          <p className="mt-1 text-sm text-blue-700">{reason}</p>
          <div className="mt-3 flex items-center gap-2 text-xs text-blue-600">
            <AlertTriangle className="h-3 w-3" />
            <span>
              Consider waiting or using a safer, shorter script option.
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
