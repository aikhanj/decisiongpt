"use client";

import { useEffect, useCallback } from "react";

type KeyCombo = {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
};

type ShortcutHandler = () => void;

interface Shortcut {
  combo: KeyCombo;
  handler: ShortcutHandler;
  description: string;
}

interface UseKeyboardShortcutsOptions {
  shortcuts: Shortcut[];
  enabled?: boolean;
}

/**
 * Hook for managing keyboard shortcuts
 *
 * Usage:
 * ```tsx
 * useKeyboardShortcuts({
 *   shortcuts: [
 *     {
 *       combo: { key: "Enter", ctrl: true },
 *       handler: () => handleSend(),
 *       description: "Send message"
 *     },
 *     {
 *       combo: { key: "Escape" },
 *       handler: () => handleClose(),
 *       description: "Close modal"
 *     }
 *   ]
 * });
 * ```
 */
export function useKeyboardShortcuts({
  shortcuts,
  enabled = true,
}: UseKeyboardShortcutsOptions) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) return;

      // Don't trigger shortcuts when typing in inputs
      const target = event.target as HTMLElement;
      const isTyping =
        target.tagName === "INPUT" ||
        target.tagName === "TEXTAREA" ||
        target.isContentEditable;

      for (const shortcut of shortcuts) {
        const { combo, handler } = shortcut;

        // Check if all required modifiers match
        const ctrlMatch = combo.ctrl ? event.ctrlKey : !event.ctrlKey;
        const metaMatch = combo.meta ? event.metaKey : !event.metaKey;
        const shiftMatch = combo.shift ? event.shiftKey : !event.shiftKey;
        const altMatch = combo.alt ? event.altKey : !event.altKey;

        // For Enter and Escape, allow even when typing
        const allowWhileTyping =
          combo.key === "Escape" ||
          (combo.key === "Enter" && (combo.ctrl || combo.meta));

        if (isTyping && !allowWhileTyping) continue;

        if (
          event.key === combo.key &&
          (ctrlMatch || metaMatch) && // Treat ctrl and meta as interchangeable
          shiftMatch &&
          altMatch
        ) {
          event.preventDefault();
          handler();
          return;
        }
      }
    },
    [shortcuts, enabled]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);
}

// Common shortcuts for the application
export const SHORTCUTS = {
  SEND_MESSAGE: { key: "Enter", ctrl: true } as KeyCombo,
  CLOSE_MODAL: { key: "Escape" } as KeyCombo,
  NEW_DECISION: { key: "n", ctrl: true } as KeyCombo,
  TOGGLE_PANEL: { key: "\\", ctrl: true } as KeyCombo,
  FOCUS_CHAT: { key: "j", ctrl: true } as KeyCombo,
  FOCUS_CANVAS: { key: "k", ctrl: true } as KeyCombo,
} as const;

// Helper to get shortcut display text
export function getShortcutDisplay(combo: KeyCombo): string {
  const parts: string[] = [];
  const isMac = typeof navigator !== "undefined" && /Mac/i.test(navigator.platform);

  if (combo.ctrl || combo.meta) {
    parts.push(isMac ? "⌘" : "Ctrl");
  }
  if (combo.shift) {
    parts.push(isMac ? "⇧" : "Shift");
  }
  if (combo.alt) {
    parts.push(isMac ? "⌥" : "Alt");
  }

  // Format key
  let keyDisplay = combo.key;
  if (combo.key === "Enter") keyDisplay = "↵";
  if (combo.key === "Escape") keyDisplay = "Esc";
  if (combo.key === "\\") keyDisplay = "\\";

  parts.push(keyDisplay);

  return parts.join(isMac ? "" : "+");
}
