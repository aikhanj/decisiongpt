"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GripVertical, MessageCircle, LayoutGrid, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface SplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultLeftWidth?: number; // percentage
  minLeftWidth?: number; // percentage
  maxLeftWidth?: number; // percentage
  className?: string;
}

type MobileView = "left" | "right";

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
  const [mobileView, setMobileView] = useState<MobileView>("left");
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

  // Touch handlers for mobile divider dragging
  const handleTouchStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleTouchMove = useCallback(
    (e: TouchEvent) => {
      if (!isDragging || !containerRef.current) return;

      const container = containerRef.current;
      const containerRect = container.getBoundingClientRect();
      const touch = e.touches[0];
      const newLeftWidth =
        ((touch.clientX - containerRect.left) / containerRect.width) * 100;

      if (newLeftWidth >= minLeftWidth && newLeftWidth <= maxLeftWidth) {
        setLeftWidth(newLeftWidth);
      }
    },
    [isDragging, minLeftWidth, maxLeftWidth]
  );

  const handleTouchEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      window.addEventListener("mousemove", handleMouseMove);
      window.addEventListener("mouseup", handleMouseUp);
      window.addEventListener("touchmove", handleTouchMove);
      window.addEventListener("touchend", handleTouchEnd);
    }

    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
      window.removeEventListener("touchmove", handleTouchMove);
      window.removeEventListener("touchend", handleTouchEnd);
    };
  }, [isDragging, handleMouseMove, handleMouseUp, handleTouchMove, handleTouchEnd]);

  // Keyboard shortcut to toggle mobile view
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + [ or ] to switch panels on mobile
      if ((e.metaKey || e.ctrlKey) && (e.key === "[" || e.key === "]")) {
        e.preventDefault();
        setMobileView((prev) => (prev === "left" ? "right" : "left"));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <>
      {/* Desktop View */}
      <div
        ref={containerRef}
        className={cn(
          "hidden md:flex h-full w-full overflow-hidden",
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
          onTouchStart={handleTouchStart}
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

      {/* Mobile View - Swipeable panels */}
      <div className="md:hidden h-full w-full flex flex-col overflow-hidden">
        {/* Mobile Toggle Bar */}
        <div className="flex items-center justify-center gap-1 py-2 px-4 bg-muted/50 border-b">
          <Button
            variant={mobileView === "left" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMobileView("left")}
            className="flex-1 max-w-32"
          >
            <MessageCircle className="w-4 h-4 mr-2" />
            Chat
          </Button>
          <Button
            variant={mobileView === "right" ? "default" : "ghost"}
            size="sm"
            onClick={() => setMobileView("right")}
            className="flex-1 max-w-32"
          >
            <LayoutGrid className="w-4 h-4 mr-2" />
            Canvas
          </Button>
        </div>

        {/* Mobile Panel Content */}
        <div className="flex-1 overflow-hidden relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={mobileView}
              initial={{ opacity: 0, x: mobileView === "left" ? -20 : 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: mobileView === "left" ? 20 : -20 }}
              transition={{ duration: 0.2 }}
              className="h-full w-full"
            >
              {mobileView === "left" ? left : right}
            </motion.div>
          </AnimatePresence>

          {/* Floating switch button */}
          <Button
            variant="secondary"
            size="icon"
            onClick={() => setMobileView((prev) => (prev === "left" ? "right" : "left"))}
            className="absolute bottom-4 right-4 h-12 w-12 rounded-full shadow-lg z-10"
          >
            {mobileView === "left" ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </Button>
        </div>
      </div>
    </>
  );
}
