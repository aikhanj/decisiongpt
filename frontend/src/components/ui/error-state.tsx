"use client";

import { motion } from "framer-motion";
import { AlertCircle, RefreshCw, Home, Bug } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  showHomeButton?: boolean;
  showReportButton?: boolean;
  className?: string;
  variant?: "default" | "inline" | "minimal";
}

export function ErrorState({
  title = "Something went wrong",
  message = "We encountered an error. Please try again.",
  onRetry,
  showHomeButton = true,
  showReportButton = false,
  className,
  variant = "default",
}: ErrorStateProps) {
  if (variant === "minimal") {
    return (
      <div className={cn("flex items-center gap-2 text-destructive", className)}>
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">{message}</span>
        {onRetry && (
          <Button variant="ghost" size="sm" onClick={onRetry} className="h-6 px-2">
            <RefreshCw className="w-3 h-3 mr-1" />
            Retry
          </Button>
        )}
      </div>
    );
  }

  if (variant === "inline") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={cn(
          "flex items-center justify-between p-4 rounded-lg bg-destructive/10 border border-destructive/20",
          className
        )}
      >
        <div className="flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-destructive" />
          <div>
            <p className="font-medium text-destructive">{title}</p>
            <p className="text-sm text-muted-foreground">{message}</p>
          </div>
        </div>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Retry
          </Button>
        )}
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "flex flex-col items-center justify-center p-8 text-center",
        className
      )}
    >
      <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-6">
        <AlertCircle className="w-8 h-8 text-destructive" />
      </div>

      <h2 className="text-xl font-semibold text-foreground mb-2">{title}</h2>
      <p className="text-muted-foreground max-w-md mb-6">{message}</p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        {onRetry && (
          <Button onClick={onRetry}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Try Again
          </Button>
        )}
        {showHomeButton && (
          <Button variant="outline" asChild>
            <Link href="/">
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Link>
          </Button>
        )}
        {showReportButton && (
          <Button variant="ghost" size="sm">
            <Bug className="w-4 h-4 mr-2" />
            Report Issue
          </Button>
        )}
      </div>
    </motion.div>
  );
}

// Common error messages
export const ERROR_MESSAGES = {
  NETWORK: "Unable to connect. Please check your internet connection.",
  TIMEOUT: "The request took too long. Please try again.",
  SERVER: "Our servers are having issues. Please try again later.",
  NOT_FOUND: "The resource you're looking for doesn't exist.",
  UNAUTHORIZED: "Please set your API key to continue.",
  RATE_LIMIT: "Too many requests. Please wait a moment and try again.",
  UNKNOWN: "An unexpected error occurred. Please try again.",
} as const;

// Helper to get user-friendly error message
export function getErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    // Check for common error types
    if (error.message.includes("fetch") || error.message.includes("network")) {
      return ERROR_MESSAGES.NETWORK;
    }
    if (error.message.includes("timeout") || error.message.includes("TIMEOUT")) {
      return ERROR_MESSAGES.TIMEOUT;
    }
    if (error.message.includes("401") || error.message.includes("unauthorized")) {
      return ERROR_MESSAGES.UNAUTHORIZED;
    }
    if (error.message.includes("404") || error.message.includes("not found")) {
      return ERROR_MESSAGES.NOT_FOUND;
    }
    if (error.message.includes("429") || error.message.includes("rate")) {
      return ERROR_MESSAGES.RATE_LIMIT;
    }
    if (error.message.includes("500") || error.message.includes("server")) {
      return ERROR_MESSAGES.SERVER;
    }
    return error.message;
  }

  if (typeof error === "string") {
    return error;
  }

  return ERROR_MESSAGES.UNKNOWN;
}
