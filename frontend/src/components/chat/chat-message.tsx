"use client";

import { motion } from "framer-motion";
import { Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { ChatMessage as ChatMessageType, AdvisorInfo } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
  isNew?: boolean;
  advisor?: AdvisorInfo;
  onQuickReply?: (option: string) => void;
}

function formatTimestamp(timestamp: string): string {
  // Handle both ISO strings and already-local timestamps
  let date: Date;

  // If timestamp doesn't have timezone info, treat it as UTC
  if (timestamp.endsWith('Z') || timestamp.includes('+') || timestamp.includes('-')) {
    date = new Date(timestamp);
  } else {
    // Assume UTC if no timezone specified
    date = new Date(timestamp + 'Z');
  }

  // Check if date is valid
  if (isNaN(date.getTime())) {
    return "just now";
  }

  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);

  if (diffMins < 1) return "just now";
  if (diffMins < 60) return `${diffMins}m ago`;

  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;

  return date.toLocaleDateString();
}

export function ChatMessage({ message, isNew = false, advisor, onQuickReply }: ChatMessageProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  // Use advisor from props or from message
  const messageAdvisor = advisor || message.advisor;

  if (isSystem) {
    return (
      <motion.div
        initial={isNew ? { opacity: 0 } : false}
        animate={{ opacity: 1 }}
        className="flex justify-center py-3"
      >
        <span className="text-xs text-muted-foreground bg-secondary/80 px-4 py-1.5 rounded-full border border-border/50">
          {message.content}
        </span>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={isNew ? { opacity: 0, y: 20, scale: 0.95 } : false}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.3,
        ease: [0.25, 0.46, 0.45, 0.94],
        scale: { duration: 0.2 }
      }}
      className={cn(
        "flex gap-3 px-5 py-2",
        isUser ? "justify-end" : "justify-start"
      )}
    >
      {/* Content */}
      <div
        className={cn(
          "flex flex-col gap-1",
          isUser ? "items-end max-w-[70%]" : "items-start max-w-[80%]"
        )}
      >
        {/* Advisor name for assistant messages */}
        {!isUser && messageAdvisor && (
          <span className="text-xs font-medium text-muted-foreground px-1">
            {messageAdvisor.name}
          </span>
        )}
        <div
          className={cn(
            "px-4 py-3 rounded-2xl relative",
            isUser
              ? "bg-gradient-to-br from-primary to-primary/90 text-primary-foreground rounded-br-md shadow-md"
              : "bg-card border border-border/60 rounded-bl-md"
          )}
        >
          <p className="text-[14px] leading-relaxed whitespace-pre-wrap">{message.content}</p>

          {/* Question reason tooltip for assistant messages */}
          {!isUser && message.question_reason && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button className="absolute -right-2 -top-2 p-1 rounded-full bg-muted hover:bg-accent transition-colors">
                    <Info className="w-3.5 h-3.5 text-muted-foreground" />
                  </button>
                </TooltipTrigger>
                <TooltipContent side="top" className="max-w-xs">
                  <p className="text-sm">{message.question_reason}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>

        {/* Quick reply options for assistant messages */}
        {!isUser && message.suggested_options && message.suggested_options.length > 0 && onQuickReply && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-wrap gap-2 mt-2 px-1"
          >
            {message.suggested_options.map((option, idx) => (
              <Button
                key={idx}
                variant="outline"
                size="sm"
                className="text-xs h-8 px-3 rounded-full hover:bg-primary hover:text-primary-foreground transition-colors"
                onClick={() => onQuickReply(option)}
              >
                {option}
              </Button>
            ))}
          </motion.div>
        )}

        <span className="text-[11px] text-muted-foreground/60 px-1">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}
