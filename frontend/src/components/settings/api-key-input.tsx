"use client";

import { useState, useEffect } from "react";
import { Eye, EyeOff, Key, ExternalLink, Check, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { getApiKey, setApiKey, clearApiKey, isValidApiKeyFormat, hasApiKey } from "@/lib/api";

interface ApiKeyInputProps {
  onKeySet?: () => void;
  trigger?: React.ReactNode;
}

export function ApiKeyInput({ onKeySet, trigger }: ApiKeyInputProps) {
  const [open, setOpen] = useState(false);
  const [key, setKey] = useState("");
  const [showKey, setShowKey] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);
  const [hasExistingKey, setHasExistingKey] = useState(false);

  useEffect(() => {
    // Check if there's an existing key on mount
    setHasExistingKey(hasApiKey());
    const existingKey = getApiKey();
    if (existingKey) {
      setKey(existingKey);
    }
  }, [open]);

  const handleSave = () => {
    setError(null);

    if (!key.trim()) {
      setError("Please enter your API key");
      return;
    }

    if (!isValidApiKeyFormat(key)) {
      setError("Invalid API key format. Keys should start with 'sk-'");
      return;
    }

    setApiKey(key);
    setSaved(true);
    setHasExistingKey(true);
    onKeySet?.();

    // Close after brief delay to show success
    setTimeout(() => {
      setOpen(false);
      setSaved(false);
    }, 1000);
  };

  const handleClear = () => {
    clearApiKey();
    setKey("");
    setHasExistingKey(false);
    setError(null);
  };

  const defaultTrigger = (
    <Button variant="outline" size="sm" className="gap-2">
      <Key className="h-4 w-4" />
      {hasExistingKey ? "API Key Set" : "Set API Key"}
    </Button>
  );

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        {trigger || defaultTrigger}
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Key className="h-5 w-5 text-amber-500" />
            OpenAI API Key
          </DialogTitle>
          <DialogDescription>
            Your API key is stored locally in your browser and sent directly to OpenAI.
            It is never stored on our servers.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <div className="relative">
              <Input
                type={showKey ? "text" : "password"}
                placeholder="sk-..."
                value={key}
                onChange={(e) => {
                  setKey(e.target.value);
                  setError(null);
                  setSaved(false);
                }}
                className={error ? "border-red-500 pr-10" : "pr-10"}
              />
              <button
                type="button"
                onClick={() => setShowKey(!showKey)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
              >
                {showKey ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>

            {error && (
              <p className="text-sm text-red-500 flex items-center gap-1">
                <AlertCircle className="h-3 w-3" />
                {error}
              </p>
            )}

            {saved && (
              <p className="text-sm text-green-500 flex items-center gap-1">
                <Check className="h-3 w-3" />
                API key saved successfully
              </p>
            )}
          </div>

          <a
            href="https://platform.openai.com/api-keys"
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-amber-500 hover:text-amber-600 flex items-center gap-1"
          >
            <ExternalLink className="h-3 w-3" />
            Get your API key from OpenAI
          </a>
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          {hasExistingKey && (
            <Button
              type="button"
              variant="ghost"
              onClick={handleClear}
              className="text-red-500 hover:text-red-600 hover:bg-red-50"
            >
              Clear Key
            </Button>
          )}
          <Button
            type="button"
            onClick={handleSave}
            disabled={saved}
            className="bg-amber-500 hover:bg-amber-600 text-white"
          >
            {saved ? (
              <>
                <Check className="h-4 w-4 mr-2" />
                Saved
              </>
            ) : (
              "Save Key"
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Prompt component for when API key is required
interface ApiKeyPromptProps {
  onKeySet: () => void;
}

export function ApiKeyPrompt({ onKeySet }: ApiKeyPromptProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 space-y-6 bg-muted/30 rounded-2xl border border-dashed">
      <div className="flex items-center justify-center w-16 h-16 rounded-full bg-amber-100">
        <Key className="h-8 w-8 text-amber-600" />
      </div>
      <div className="text-center space-y-2">
        <h3 className="text-lg font-semibold">OpenAI API Key Required</h3>
        <p className="text-muted-foreground text-sm max-w-md">
          To use Gentleman Coach, you need to provide your own OpenAI API key.
          Your key is stored locally and sent directly to OpenAI.
        </p>
      </div>
      <ApiKeyInput
        onKeySet={onKeySet}
        trigger={
          <Button className="bg-amber-500 hover:bg-amber-600 text-white gap-2">
            <Key className="h-4 w-4" />
            Enter Your API Key
          </Button>
        }
      />
      <a
        href="https://platform.openai.com/api-keys"
        target="_blank"
        rel="noopener noreferrer"
        className="text-sm text-muted-foreground hover:text-foreground flex items-center gap-1"
      >
        <ExternalLink className="h-3 w-3" />
        Don&apos;t have a key? Get one from OpenAI
      </a>
    </div>
  );
}
