"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Brain,
  Heart,
  Sparkles,
  TrendingUp,
  Lightbulb,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Observation, ObservationsGrouped, ObservationType } from "@/types";

interface ObservationsTabProps {
  userId?: string;
}

const typeConfig: Record<
  ObservationType,
  { icon: React.ElementType; label: string; color: string; bgColor: string }
> = {
  pattern: {
    icon: Brain,
    label: "Patterns",
    color: "text-purple-600",
    bgColor: "bg-purple-50 dark:bg-purple-950/20",
  },
  value: {
    icon: Heart,
    label: "Values",
    color: "text-rose-600",
    bgColor: "bg-rose-50 dark:bg-rose-950/20",
  },
  strength: {
    icon: Sparkles,
    label: "Strengths",
    color: "text-emerald-600",
    bgColor: "bg-emerald-50 dark:bg-emerald-950/20",
  },
  growth_area: {
    icon: TrendingUp,
    label: "Growth Areas",
    color: "text-amber-600",
    bgColor: "bg-amber-50 dark:bg-amber-950/20",
  },
  insight: {
    icon: Lightbulb,
    label: "Insights",
    color: "text-blue-600",
    bgColor: "bg-blue-50 dark:bg-blue-950/20",
  },
};

function ObservationCard({
  observation,
  onFeedback,
}: {
  observation: Observation;
  onFeedback?: (id: string, feedback: "helpful" | "not_relevant") => void;
}) {
  const config = typeConfig[observation.observation_type];
  const Icon = config.icon;
  const confidencePercent = Math.round(observation.confidence * 100);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-4 rounded-lg border",
        config.bgColor,
        observation.user_feedback === "helpful" && "ring-2 ring-emerald-500/30"
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            "p-2 rounded-full bg-background/80",
            config.color
          )}
        >
          <Icon className="w-4 h-4" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm leading-relaxed">{observation.observation_text}</p>
          <div className="flex items-center gap-2 mt-2">
            <Badge variant="outline" className="text-xs">
              {confidencePercent}% confidence
            </Badge>
            {observation.related_theme && (
              <Badge variant="secondary" className="text-xs">
                {observation.related_theme}
              </Badge>
            )}
            {observation.surfaced_count > 0 && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Eye className="w-3 h-3" />
                {observation.surfaced_count}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Feedback buttons */}
      {onFeedback && !observation.user_feedback && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
          <span className="text-xs text-muted-foreground">Does this resonate?</span>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => onFeedback(observation.id, "helpful")}
          >
            <ThumbsUp className="w-3 h-3 mr-1" />
            Yes
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={() => onFeedback(observation.id, "not_relevant")}
          >
            <ThumbsDown className="w-3 h-3 mr-1" />
            Not quite
          </Button>
        </div>
      )}

      {observation.user_feedback && (
        <div className="flex items-center gap-2 mt-3 pt-3 border-t border-border/50">
          <span className="text-xs text-muted-foreground">
            {observation.user_feedback === "helpful"
              ? "Marked as helpful"
              : "Marked as not relevant"}
          </span>
        </div>
      )}
    </motion.div>
  );
}

function ObservationSection({
  type,
  observations,
  onFeedback,
}: {
  type: ObservationType;
  observations: Observation[];
  onFeedback?: (id: string, feedback: "helpful" | "not_relevant") => void;
}) {
  const config = typeConfig[type];
  const Icon = config.icon;

  if (observations.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-3"
    >
      <div className="flex items-center gap-2">
        <Icon className={cn("w-5 h-5", config.color)} />
        <h3 className="font-medium">{config.label}</h3>
        <Badge variant="secondary" className="text-xs">
          {observations.length}
        </Badge>
      </div>
      <div className="space-y-2">
        {observations.map((obs) => (
          <ObservationCard
            key={obs.id}
            observation={obs}
            onFeedback={onFeedback}
          />
        ))}
      </div>
    </motion.div>
  );
}

export function ObservationsTab({ userId }: ObservationsTabProps) {
  const [observations, setObservations] = useState<ObservationsGrouped | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchObservations = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/observations/me/grouped");
      if (!response.ok) {
        throw new Error("Failed to fetch observations");
      }
      const data = await response.json();
      setObservations(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchObservations();
  }, [userId]);

  const handleFeedback = async (id: string, feedback: "helpful" | "not_relevant") => {
    try {
      const response = await fetch(`/api/observations/${id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
      if (response.ok) {
        // Update local state
        if (observations) {
          const updateInArray = (arr: Observation[]) =>
            arr.map((o) => (o.id === id ? { ...o, user_feedback: feedback } : o));

          setObservations({
            patterns: updateInArray(observations.patterns),
            values: updateInArray(observations.values),
            strengths: updateInArray(observations.strengths),
            growth_areas: updateInArray(observations.growth_areas),
            insights: updateInArray(observations.insights),
          });
        }
      }
    } catch (err) {
      console.error("Failed to submit feedback:", err);
    }
  };

  const totalCount =
    (observations?.patterns.length || 0) +
    (observations?.values.length || 0) +
    (observations?.strengths.length || 0) +
    (observations?.growth_areas.length || 0) +
    (observations?.insights.length || 0);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <RefreshCw className="w-8 h-8 text-muted-foreground animate-spin" />
        <p className="text-sm text-muted-foreground mt-4">Loading observations...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-red-50 dark:bg-red-950/20 flex items-center justify-center mb-4">
          <Brain className="w-8 h-8 text-red-500" />
        </div>
        <h3 className="text-lg font-medium mb-2">Unable to load observations</h3>
        <p className="text-sm text-muted-foreground max-w-xs mb-4">{error}</p>
        <Button variant="outline" onClick={fetchObservations}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Try Again
        </Button>
      </div>
    );
  }

  if (totalCount === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Brain className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No observations yet</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          As you work through decisions, I&apos;ll notice patterns in how you think
          and what matters to you. Check back after a few conversations.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">My Observations</h2>
          <p className="text-sm text-muted-foreground">
            Patterns and insights I&apos;ve noticed about you
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchObservations}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Observation Sections */}
      <AnimatePresence mode="wait">
        <div className="space-y-8">
          <ObservationSection
            type="insight"
            observations={observations?.insights || []}
            onFeedback={handleFeedback}
          />
          <ObservationSection
            type="pattern"
            observations={observations?.patterns || []}
            onFeedback={handleFeedback}
          />
          <ObservationSection
            type="value"
            observations={observations?.values || []}
            onFeedback={handleFeedback}
          />
          <ObservationSection
            type="strength"
            observations={observations?.strengths || []}
            onFeedback={handleFeedback}
          />
          <ObservationSection
            type="growth_area"
            observations={observations?.growth_areas || []}
            onFeedback={handleFeedback}
          />
        </div>
      </AnimatePresence>

      {/* Info Card */}
      <Card className="bg-muted/30">
        <CardContent className="pt-4 pb-4">
          <p className="text-xs text-muted-foreground">
            These observations are based on our conversations. Your feedback helps
            me understand you better. Observations marked as &quot;not quite&quot; won&apos;t be
            used to inform future conversations.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
