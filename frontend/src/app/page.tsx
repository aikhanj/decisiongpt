"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
  Plus,
  Clock,
  CheckCircle,
  Archive,
  ChevronRight,
  Layers,
  Target,
  GitBranch,
  Settings,
  Trash2,
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
import { getDecisions, deleteDecision } from "@/lib/api";
import type { Decision } from "@/types";
import { formatDate } from "@/lib/utils";

const statusConfig = {
  active: { icon: Clock, label: "Active", variant: "warning" as const },
  resolved: { icon: CheckCircle, label: "Resolved", variant: "success" as const },
  archived: { icon: Archive, label: "Archived", variant: "secondary" as const },
};

const features = [
  {
    icon: Layers,
    title: "Structured Thinking",
    description: "Break down complex decisions into clear options with pros, cons, and risks",
  },
  {
    icon: Target,
    title: "AI-Powered Analysis",
    description: "Get intelligent options tailored to your specific situation and constraints",
  },
  {
    icon: GitBranch,
    title: "Decision Branching",
    description: "Explore alternative paths without losing your original analysis",
  },
];

export default function HomePage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDecisions() {
      try {
        const data = await getDecisions();
        setDecisions(data);
      } catch (error) {
        console.error("Failed to load decisions:", error);
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
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <Link href="/" className="font-semibold text-lg">
            Decision Canvas
          </Link>
          <div className="flex items-center gap-2">
            <Link href="/advisors">
              <Button variant="ghost" size="sm">
                <Settings className="mr-2 h-4 w-4" />
                Advisors
              </Button>
            </Link>
            <Link href="/d/new">
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                New Decision
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="container mx-auto py-8 px-4 space-y-12">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-6 py-8"
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

      {/* Features */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid gap-6 md:grid-cols-3"
      >
        {features.map((feature, index) => {
          const Icon = feature.icon;
          return (
            <Card key={feature.title} className="bg-muted/50">
              <CardContent className="pt-6">
                <div className="flex items-start gap-4">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </motion.div>

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
  );
}
