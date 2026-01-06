"use client";

import { motion } from "framer-motion";
import { User } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType, AdvisorInfo } from "@/types";

interface ChatMessageProps {
  message: ChatMessageType;
  isNew?: boolean;
  advisor?: AdvisorInfo;
}

function formatTimestamp(timestamp: string): string {
  const date = new Date(timestamp);
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
      initial={isNew ? { opacity: 0, y: 8 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "flex gap-3 px-5 py-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center shadow-sm",
          isUser
            ? "bg-gradient-to-br from-primary to-primary/80 text-primary-foreground"
            : "bg-gradient-to-br from-secondary to-secondary/80 text-foreground border border-border/50"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4" />
        ) : (
          <span className="text-lg">{messageAdvisor?.avatar || "🤖"}</span>
        )}
      </div>

      {/* Content */}
      <div
        className={cn(
          "flex flex-col gap-1.5 max-w-[75%]",
          isUser ? "items-end" : "items-start"
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
            "px-4 py-3 rounded-2xl shadow-sm",
            isUser
              ? "bg-gradient-to-br from-primary to-primary/90 text-primary-foreground rounded-br-lg"
              : "bg-card border border-border/60 rounded-bl-lg"
          )}
        >
          <p className="text-[14px] leading-relaxed whitespace-pre-wrap">{message.content}</p>
        </div>
        <span className="text-[11px] text-muted-foreground/70 px-1 font-medium">
          {formatTimestamp(message.timestamp)}
        </span>
      </div>
    </motion.div>
  );
}
