"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = "Type a message...",
  disabled = false,
  className,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
    }
  }, [message]);

  const handleSend = () => {
    if (message.trim() && !isLoading && !disabled) {
      onSend(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter") {
      if (e.shiftKey || e.ctrlKey || e.metaKey) {
        // Ctrl/Cmd/Shift + Enter = new line (let default behavior happen)
        return;
      }
      // Plain Enter = send
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className={cn(
        "flex items-end gap-3 p-4 border-t border-border/50 bg-gradient-to-t from-background to-background/80",
        className
      )}
    >
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={isLoading || disabled}
          rows={1}
          className={cn(
            "w-full resize-none rounded-xl border border-border/60 bg-card px-4 py-3",
            "text-sm placeholder:text-muted-foreground/60",
            "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50",
            "disabled:cursor-not-allowed disabled:opacity-50",
            "max-h-[120px] shadow-sm transition-all duration-200"
          )}
        />
        <span className="absolute right-3 bottom-2.5 text-[11px] text-muted-foreground/50 font-medium">
          {message.length > 0 && `${message.length}/5000`}
        </span>
      </div>

      <Button
        size="icon"
        onClick={handleSend}
        disabled={!message.trim() || isLoading || disabled}
        className="h-11 w-11 rounded-xl shrink-0 shadow-sm transition-all duration-200 hover:shadow-md"
      >
        {isLoading ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Send className="h-4 w-4" />
        )}
      </Button>
    </div>
  );
}
