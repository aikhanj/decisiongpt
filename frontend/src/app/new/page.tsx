"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Send, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { createDecision, hasApiKey } from "@/lib/api";
import { ApiKeyPrompt } from "@/components/settings/api-key-input";
import { toast } from "sonner";

const situationExamples = [
  {
    type: "gym_approach",
    label: "Gym Approach",
    example: "There's a woman I see at the gym regularly...",
  },
  {
    type: "double_text",
    label: "Double Text",
    example: "She hasn't responded to my message from 2 days ago...",
  },
  {
    type: "kiss_timing",
    label: "Kiss Timing",
    example: "We're on our third date and I'm not sure when to...",
  },
  {
    type: "first_date_plan",
    label: "First Date",
    example: "She said yes and I need to plan our first date...",
  },
];

export default function NewDecisionPage() {
  const router = useRouter();
  const [situation, setSituation] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiKeySet, setApiKeySet] = useState<boolean | null>(null);

  useEffect(() => {
    // Check for API key on mount
    setApiKeySet(hasApiKey());
  }, []);

  const handleSubmit = async () => {
    if (!hasApiKey()) {
      toast.error("Please set your OpenAI API key first");
      return;
    }

    if (situation.trim().length < 10) {
      toast.error("Please describe your situation in more detail");
      return;
    }

    setLoading(true);
    try {
      const response = await createDecision({ situation_text: situation });
      toast.success("Analyzing your situation...");
      router.push(`/decisions/${response.decision.id}/clarify`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create decision";
      toast.error(message);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Show loading state while checking for API key
  if (apiKeySet === null) {
    return (
      <div className="max-w-2xl mx-auto flex items-center justify-center py-16">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }

  // Show API key prompt if not set
  if (!apiKeySet) {
    return (
      <div className="max-w-2xl mx-auto space-y-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-2"
        >
          <h1 className="text-3xl font-bold">Welcome to Gentleman Coach</h1>
          <p className="text-muted-foreground">
            Before we begin, you&apos;ll need to set up your OpenAI API key.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <ApiKeyPrompt onKeySet={() => setApiKeySet(true)} />
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-3xl font-bold">What&apos;s the situation?</h1>
        <p className="text-muted-foreground">
          Describe your romantic situation. Be specific - details help.
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-amber-500" />
              Your Situation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="Example: I've been texting this woman for a week. We matched on Hinge and had good conversations. She agreed to get coffee but we haven't set a date yet. Her responses have slowed down. I'm wondering if I should..."
              value={situation}
              onChange={(e) => setSituation(e.target.value)}
              className="min-h-[200px] resize-none"
            />

            <div className="flex flex-wrap gap-2">
              {situationExamples.map((ex) => (
                <Badge
                  key={ex.type}
                  variant="outline"
                  className="cursor-pointer hover:bg-accent"
                  onClick={() => setSituation(ex.example)}
                >
                  {ex.label}
                </Badge>
              ))}
            </div>

            <Button
              onClick={handleSubmit}
              disabled={loading || situation.trim().length < 10}
              className="w-full"
              size="lg"
            >
              {loading ? (
                "Analyzing..."
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Get Guidance
                </>
              )}
            </Button>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-center text-sm text-muted-foreground"
      >
        <p>
          Your responses are private and used only to generate personalized
          advice.
        </p>
      </motion.div>
    </div>
  );
}
