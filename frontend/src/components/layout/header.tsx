"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Crown, Key, Check } from "lucide-react";
import { GentlemanBadge } from "./gentleman-badge";
import { ApiKeyInput } from "@/components/settings/api-key-input";
import { hasApiKey } from "@/lib/api";
import { Button } from "@/components/ui/button";

export function Header() {
  const [keySet, setKeySet] = useState(false);

  useEffect(() => {
    setKeySet(hasApiKey());
  }, []);

  const handleKeySet = () => {
    setKeySet(true);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <Link href="/" className="flex items-center space-x-2">
          <Crown className="h-6 w-6 text-amber-500" />
          <span className="text-xl font-semibold">Gentleman Coach</span>
        </Link>
        <div className="flex items-center gap-4">
          <ApiKeyInput
            onKeySet={handleKeySet}
            trigger={
              <Button
                variant="outline"
                size="sm"
                className={`gap-2 ${keySet ? "border-green-500/50" : ""}`}
              >
                {keySet ? (
                  <>
                    <Check className="h-4 w-4 text-green-500" />
                    <span className="text-green-600">API Key Set</span>
                  </>
                ) : (
                  <>
                    <Key className="h-4 w-4" />
                    Set API Key
                  </>
                )}
              </Button>
            }
          />
          <GentlemanBadge />
        </div>
      </div>
    </header>
  );
}
