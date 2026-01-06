"use client";

import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType, AdvisorInfo } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
  isNew?: boolean;
  advisor?: AdvisorInfo;
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

export function ChatMessage({ message, isNew = false, advisor }: ChatMessageProps) {
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
            "px-4 py-3 rounded-2xl",
            isUser
              ? "bg-gradient-to-br from-primary to-primary/90 text-primary-foreground rounded-br-md shadow-md"
              : "bg-card border border-border/60 rounded-bl-md"
          )}
        >
          <p className="text-[14px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
        <span className="text-[11px] text-muted-foreground/60 px-1">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}
