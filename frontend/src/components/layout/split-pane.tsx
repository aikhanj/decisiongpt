"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { GripVertical } from "lucide-react";
import { cn } from "@/lib/utils";

interface SplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultLeftWidth?: number; // percentage
  minLeftWidth?: number; // percentage
  maxLeftWidth?: number; // percentage
  className?: string;
}

export function SplitPane({
  left,
  right,
  defaultLeftWidth = 50,
  minLeftWidth = 30,
  maxLeftWidth = 70,
  className,
}: SplitPaneProps) {
  const [leftWidth, setLeftWidth] = useState(defaultLeftWidth);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging || !containerRef.current) return;

      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();
      const newLeftWidth =
        ((e.clientX - containerRect.left) / containerRect.width) * 100;

      if (newLeftWidth >= minLeftWidth && newLeftWidth <= maxLeftWidth) {
        setLeftWidth(newLeftWidth);
      }
    },
    [isDragging, minLeftWidth, maxLeftWidth]
  );

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex h-full w-full overflow-hidden",
        isDragging && "select-none cursor-col-resize",
        className
      )}
    >
      {/* Left Panel */}
      <motion.div
        className="h-full overflow-hidden"
        style={{ width: `${leftWidth}%` }}
        initial={false}
        animate={{ width: `${leftWidth}%` }}
        transition={{ duration: isDragging ? 0 : 0.1 }}
      >
        {left}
      </motion.div>

      {/* Divider */}
      <div
        className={cn(
          "relative flex-shrink-0 w-1 cursor-col-resize group",
          "bg-border hover:bg-primary/20 transition-colors",
          isDragging && "bg-primary/30"
        )}
        onMouseDown={handleMouseDown}
      >
        {/* Drag Handle */}
        <div
          className={cn(
            "absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2",
            "flex items-center justify-center",
            "w-4 h-8 rounded-full",
            "bg-muted border border-border",
            "opacity-0 group-hover:opacity-100 transition-opacity",
            isDragging && "opacity-100"
          )}
        >
          <GripVertical className="w-3 h-3 text-muted-foreground" />
        </div>
      </div>

      {/* Right Panel */}
      <motion.div
        className="h-full overflow-hidden flex-1"
        initial={false}
        animate={{ width: `${100 - leftWidth}%` }}
        transition={{ duration: isDragging ? 0 : 0.1 }}
      >
        {right}
      </motion.div>
    </div>
  );
}
