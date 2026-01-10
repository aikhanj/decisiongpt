"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Plus,
  Clock,
  CheckCircle,
  Archive,
  ChevronRight,
  Layers,
  Settings,
  Trash2,
  Keyboard,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { getDecisions, deleteDecision } from "@/lib/api";
import { WelcomeModal } from "@/components/onboarding/welcome-modal";
import type { Decision } from "@/types";
import { formatDate } from "@/lib/utils";
import { useKeyboardShortcuts, SHORTCUTS, getShortcutDisplay } from "@/hooks/use-keyboard-shortcuts";

const statusConfig = {
  active: { icon: Clock, label: "Active", variant: "warning" as const },
  resolved: { icon: CheckCircle, label: "Resolved", variant: "success" as const },
  archived: { icon: Archive, label: "Archived", variant: "secondary" as const },
};

export default function HomePage() {
  const router = useRouter();
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showWelcome, setShowWelcome] = useState(false);

  // Keyboard shortcuts
  useKeyboardShortcuts({
    shortcuts: [
      {
        combo: SHORTCUTS.NEW_DECISION,
        handler: () => router.push("/d/new"),
        description: "Create new decision",
      },
    ],
  });

  useEffect(() => {
    async function loadDecisions() {
      try {
        setError(null);
        const data = await getDecisions();
        setDecisions(data);
      } catch (err) {
        console.error("Failed to load decisions:", err);
        setError(err instanceof Error ? err.message : "Failed to load decisions");
      } finally {
        setLoading(false);
      }
    }
    loadDecisions();
  }, []);

  const handleDeleteDecision = async (e: React.MouseEvent, decisionId: string) => {
    e.preventDefault();
    e.stopPropagation();

    const confirmed = window.confirm(
      "Are you sure you want to delete this decision? This action cannot be undone."
    );

    if (!confirmed) return;

    try {
      await deleteDecision(decisionId);
      setDecisions((prev) => prev.filter((d) => d.id !== decisionId));
      toast.success("Decision deleted");
    } catch (error) {
      console.error("Failed to delete decision:", error);
      toast.error("Failed to delete decision");
    }
  };

  const recentDecisions = decisions.slice(0, 6);

  return (
    <TooltipProvider>
      <div className="min-h-screen">
        {/* Welcome Modal for first-time users */}
        <WelcomeModal />

        {/* Header */}
        <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
          <div className="container mx-auto px-4 h-14 flex items-center justify-between">
            <Link href="/" className="font-semibold text-lg flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-primary" />
              Decision Canvas
            </Link>
            <div className="flex items-center gap-2">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="hidden sm:flex"
                    onClick={() => setShowWelcome(true)}
                    aria-label="View keyboard shortcuts"
                  >
                    <Keyboard className="h-4 w-4" />
                  </Button>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <p className="font-medium mb-1">Keyboard Shortcuts</p>
                  <p className="text-xs text-muted-foreground">
                    {getShortcutDisplay(SHORTCUTS.NEW_DECISION)} - New Decision
                  </p>
                </TooltipContent>
              </Tooltip>
              <Link href="/advisors">
                <Button variant="ghost" size="sm">
                  <Settings className="mr-2 h-4 w-4" />
                  Advisors
                </Button>
              </Link>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Link href="/d/new">
                    <Button size="sm">
                      <Plus className="mr-2 h-4 w-4" />
                      New Decision
                    </Button>
                  </Link>
                </TooltipTrigger>
                <TooltipContent side="bottom">
                  <span className="text-xs">{getShortcutDisplay(SHORTCUTS.NEW_DECISION)}</span>
                </TooltipContent>
              </Tooltip>
            </div>
          </div>
        </header>

      <main id="main-content" className="container mx-auto py-8 px-4 space-y-12">
      {/* Hero Section with gradient background */}
      <div className="relative py-16 sm:py-24">
        {/* Gradient backgrounds */}
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-accent/5 to-background -z-10" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,hsl(var(--primary)/0.08),transparent_50%)] -z-10" />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center space-y-6"
        >
          <div className="space-y-2">
            <h1 className="text-5xl font-bold tracking-tight">Decision Canvas</h1>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Make better decisions with AI-powered structured thinking.
              Clarify your situation, explore options, and commit with confidence.
            </p>
          </div>
          <Link href="/d/new">
            <Button size="lg" className="mt-4 h-12 px-8 text-lg">
              <Plus className="mr-2 h-5 w-5" />
              New Decision
            </Button>
          </Link>
        </motion.div>
      </div>

      {/* Recent Decisions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold">Recent Decisions</h2>
          {decisions.length > 6 && (
            <Button variant="ghost" size="sm">
              View all
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          )}
        </div>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader>
                  <div className="h-5 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2 mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : error ? (
          <Card className="border-destructive/50">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mb-4">
                <Archive className="w-8 h-8 text-destructive" />
              </div>
              <h3 className="text-lg font-medium mb-2">Failed to load decisions</h3>
              <p className="text-muted-foreground mb-4 text-center max-w-sm text-sm">
                {error}
              </p>
              <Button
                variant="outline"
                onClick={() => {
                  setLoading(true);
                  setError(null);
                  getDecisions()
                    .then(setDecisions)
                    .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"))
                    .finally(() => setLoading(false));
                }}
              >
                Try Again
              </Button>
            </CardContent>
          </Card>
        ) : recentDecisions.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-16">
              <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                <Layers className="w-8 h-8 text-muted-foreground" />
              </div>
              <h3 className="text-lg font-medium mb-2">No decisions yet</h3>
              <p className="text-muted-foreground mb-6 text-center max-w-sm">
                Start your first decision to experience AI-powered structured thinking.
              </p>
              <Link href="/d/new">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Decision
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {recentDecisions.map((decision, index) => {
              const status = statusConfig[decision.status as keyof typeof statusConfig] || statusConfig.active;
              const StatusIcon = status.icon;

              return (
                <motion.div
                  key={decision.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Link href={`/d/${decision.id}`}>
                    <Card className="hover:shadow-md transition-all hover:scale-[1.01] cursor-pointer h-full group">
                      <CardHeader>
                        <div className="flex items-start justify-between gap-2">
                          <CardTitle className="text-lg line-clamp-1">
                            {decision.title || "Untitled Decision"}
                          </CardTitle>
                          <div className="flex items-center gap-1 shrink-0">
                            <Badge variant={status.variant}>
                              <StatusIcon className="mr-1 h-3 w-3" />
                              {status.label}
                            </Badge>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                              onClick={(e) => handleDeleteDecision(e, decision.id)}
                              aria-label={`Delete decision: ${decision.title || 'Untitled'}`}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                        <CardDescription>
                          {formatDate(decision.created_at)}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {decision.situation_text || "No description"}
                        </p>
                        <div className="flex items-center mt-4 text-sm text-primary font-medium">
                          Continue
                          <ChevronRight className="ml-1 h-4 w-4" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
      </main>
      </div>
    </TooltipProvider>
  );
}
