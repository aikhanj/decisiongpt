"use client";

import { useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";
import { ChatMessage } from "./chat-message";
import { ChatInput } from "./chat-input";
import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";

interface ChatPanelProps {
  messages: ChatMessageType[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
  disabled?: boolean;
  className?: string;
  children?: React.ReactNode; // For inline question cards etc.
}

export function ChatPanel({
  messages,
  onSendMessage,
  isLoading = false,
  disabled = false,
  className,
  children,
}: ChatPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const lastMessageCount = useRef(messages.length);

  // Auto-scroll on new messages
  useEffect(() => {
    if (messages.length > lastMessageCount.current) {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
    lastMessageCount.current = messages.length;
  }, [messages.length]);

  return (
    <div className={cn("flex flex-col h-full bg-background", className)}>
      {/* Messages Area */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-muted scrollbar-track-transparent"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-primary/10 to-accent/10 flex items-center justify-center mb-5 border border-primary/20">
              <Loader2 className="w-6 h-6 text-primary animate-spin" />
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-2">Analyzing your decision</h3>
            <p className="text-sm text-muted-foreground max-w-xs leading-relaxed">
              I&apos;m reviewing your situation and preparing questions to help clarify your thinking...
            </p>
          </div>
        ) : (
          <div className="py-4">
            <AnimatePresence mode="popLayout">
              {messages.map((message, index) => (
                <ChatMessage
                  key={message.id}
                  message={message}
                  isNew={index === messages.length - 1}
                />
              ))}
            </AnimatePresence>

            {/* Inline content (like question cards) */}
            {children && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="px-4 py-2"
              >
                {children}
              </motion.div>
            )}

            {/* Typing indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className="flex items-center gap-3 px-5 py-3"
              >
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-secondary to-secondary/80 border border-border/50 flex items-center justify-center shadow-sm">
                  <Loader2 className="w-4 h-4 animate-spin text-primary" />
                </div>
                <div className="flex gap-1.5 bg-card border border-border/60 rounded-2xl rounded-bl-lg px-4 py-3 shadow-sm">
                  <motion.span
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: 0 }}
                    className="w-2 h-2 rounded-full bg-primary/60"
                  />
                  <motion.span
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }}
                    className="w-2 h-2 rounded-full bg-primary/60"
                  />
                  <motion.span
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
                    className="w-2 h-2 rounded-full bg-primary/60"
                  />
                </div>
              </motion.div>
            )}
          </div>
        )}
      </div>

      {/* Input Area */}
      <ChatInput
        onSend={onSendMessage}
        isLoading={isLoading}
        disabled={disabled}
        placeholder="Tell me more about your decision..."
      />
    </div>
  );
}
