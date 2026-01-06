"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { Send, Sparkles, ArrowLeft, Lightbulb, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { startDecision, hasApiKey } from "@/lib/api";
import { ApiKeyPrompt } from "@/components/settings/api-key-input";
import { toast } from "sonner";

const decisionExamples = [
  {
    label: "Career",
    example: "I've been offered a new job with a 30% raise, but it requires relocating. My current role has growth potential and I have good work-life balance...",
  },
  {
    label: "Financial",
    example: "I'm deciding whether to invest my savings in index funds, real estate, or pay off my student loans early...",
  },
  {
    label: "Life",
    example: "I'm considering going back to school for a master's degree while working full-time. The program would take 2 years...",
  },
  {
    label: "Business",
    example: "My startup needs to decide between seeking VC funding for rapid growth or bootstrapping to maintain control...",
  },
];

export default function NewDecisionPage() {
  const router = useRouter();
  const [situation, setSituation] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiKeySet, setApiKeySet] = useState<boolean | null>(null);

  useEffect(() => {
    setApiKeySet(hasApiKey());
  }, []);

  const handleSubmit = async () => {
    if (!hasApiKey()) {
      toast.error("Please set your OpenAI API key first");
      return;
    }

    if (situation.trim().length < 20) {
      toast.error("Please describe your decision in more detail (at least 20 characters)");
      return;
    }

    setLoading(true);
    try {
      const response = await startDecision({ situation_text: situation });
      toast.success("Decision created! Starting analysis...");
      router.push(`/d/${response.decision.id}`);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to create decision";
      toast.error(message);
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  // Header component used across all states
  const PageHeader = () => (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold text-lg">
          Decision Canvas
        </Link>
        <div className="flex items-center gap-2">
          <Link href="/d/new">
            <Button size="sm" variant="ghost">
              <Plus className="mr-2 h-4 w-4" />
              New Decision
            </Button>
          </Link>
        </div>
      </div>
    </header>
  );

  // Show loading state while checking for API key
  if (apiKeySet === null) {
    return (
      <div className="min-h-screen">
        <PageHeader />
        <main className="container mx-auto py-8 px-4">
          <div className="max-w-2xl mx-auto flex items-center justify-center py-16">
            <div className="animate-pulse text-muted-foreground">Loading...</div>
          </div>
        </main>
      </div>
    );
  }

  // Show API key prompt if not set
  if (!apiKeySet) {
    return (
      <div className="min-h-screen">
        <PageHeader />
        <main className="container mx-auto py-8 px-4">
          <div className="max-w-2xl mx-auto space-y-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center space-y-2"
            >
              <h1 className="text-3xl font-bold">Welcome to Decision Canvas</h1>
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
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <PageHeader />
      <main className="container mx-auto py-8 px-4">
        <div className="max-w-2xl mx-auto space-y-8">
          {/* Back link */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <Link href="/">
              <Button variant="ghost" size="sm" className="text-muted-foreground">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Dashboard
              </Button>
            </Link>
          </motion.div>

          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center space-y-2"
          >
            <h1 className="text-3xl font-bold">What are you deciding?</h1>
            <p className="text-muted-foreground">
              Describe your decision or dilemma. The more context you provide, the better
              the analysis will be.
            </p>
          </motion.div>

          {/* Main input card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  Your Decision
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <Textarea
                  placeholder="Example: I need to decide whether to accept a job offer at a new company. The salary is 25% higher but I'd have to relocate to a new city, leaving my support network behind. My current job is stable but has limited growth opportunities..."
                  value={situation}
                  onChange={(e) => setSituation(e.target.value)}
                  className="min-h-[180px] resize-none text-base"
                />

                {/* Character count */}
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">
                    {situation.length < 20 && situation.length > 0 && (
                      <span className="text-amber-500">
                        Need at least {20 - situation.length} more characters
                      </span>
                    )}
                  </span>
                  <span className="text-muted-foreground">
                    {situation.length} characters
                  </span>
                </div>

                {/* Example prompts */}
                <div className="space-y-2">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Lightbulb className="h-4 w-4" />
                    <span>Try an example:</span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {decisionExamples.map((ex) => (
                      <Badge
                        key={ex.label}
                        variant="outline"
                        className="cursor-pointer hover:bg-accent transition-colors"
                        onClick={() => setSituation(ex.example)}
                      >
                        {ex.label}
                      </Badge>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={handleSubmit}
                  disabled={loading || situation.trim().length < 20}
                  className="w-full h-12 text-base"
                  size="lg"
                >
                  {loading ? (
                    <span className="animate-pulse">Creating decision...</span>
                  ) : (
                    <>
                      <Send className="mr-2 h-5 w-5" />
                      Start Decision Analysis
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Privacy note */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="text-center text-sm text-muted-foreground"
          >
            <p>
              Your data is processed securely and used only to generate your personalized
              decision analysis.
            </p>
          </motion.div>
        </div>
      </main>
    </div>
  );
}
