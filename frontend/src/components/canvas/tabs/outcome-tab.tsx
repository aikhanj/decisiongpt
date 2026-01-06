"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { CheckCircle2, XCircle, Meh, Smile, Frown, PartyPopper } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import type { NodePhase, DecisionOutcome } from "@/types";

interface OutcomeTabProps {
  phase: NodePhase;
  outcome?: DecisionOutcome;
  onLogOutcome?: (outcome: {
    progress_yesno: boolean;
    sentiment_2h?: number;
    sentiment_24h?: number;
    notes?: string;
  }) => void;
}

const sentimentEmojis = [
  { value: -2, icon: Frown, label: "Very negative", color: "text-rose-500" },
  { value: -1, icon: Frown, label: "Negative", color: "text-orange-500" },
  { value: 0, icon: Meh, label: "Neutral", color: "text-gray-500" },
  { value: 1, icon: Smile, label: "Positive", color: "text-emerald-500" },
  { value: 2, icon: PartyPopper, label: "Very positive", color: "text-emerald-600" },
];

export function OutcomeTab({ phase, outcome, onLogOutcome }: OutcomeTabProps) {
  const [success, setSuccess] = useState<boolean | null>(null);
  const [sentiment2h, setSentiment2h] = useState(0);
  const [sentiment24h, setSentiment24h] = useState(0);
  const [notes, setNotes] = useState("");

  const handleSubmit = () => {
    if (success === null || !onLogOutcome) return;

    onLogOutcome({
      progress_yesno: success,
      sentiment_2h: sentiment2h,
      sentiment_24h: sentiment24h,
      notes: notes || undefined,
    });
  };

  // Not ready to log outcome
  if (phase !== "execute") {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <CheckCircle2 className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">Not ready yet</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          You&apos;ll be able to log the outcome once you&apos;ve chosen an
          option and started executing your plan.
        </p>
      </div>
    );
  }

  // Already logged
  if (outcome) {
    const getSentimentIcon = (value: number | null) => {
      if (value === null) return Meh;
      return sentimentEmojis.find((s) => s.value === value)?.icon || Meh;
    };

    const getSentimentColor = (value: number | null) => {
      if (value === null) return "text-gray-500";
      return sentimentEmojis.find((s) => s.value === value)?.color || "text-gray-500";
    };

    const Sentiment2hIcon = getSentimentIcon(outcome.sentiment_2h);
    const Sentiment24hIcon = getSentimentIcon(outcome.sentiment_24h);

    return (
      <div className="space-y-6">
        <div className="text-center">
          <div
            className={cn(
              "w-20 h-20 rounded-full mx-auto flex items-center justify-center mb-4",
              outcome.progress_yesno
                ? "bg-emerald-100 text-emerald-600"
                : "bg-rose-100 text-rose-600"
            )}
          >
            {outcome.progress_yesno ? (
              <CheckCircle2 className="w-10 h-10" />
            ) : (
              <XCircle className="w-10 h-10" />
            )}
          </div>
          <h2 className="text-xl font-semibold mb-1">
            {outcome.progress_yesno ? "Decision Successful" : "Didn't Work Out"}
          </h2>
          <p className="text-sm text-muted-foreground">
            Outcome logged on{" "}
            {new Date(outcome.created_at).toLocaleDateString()}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-4 pb-4 text-center">
              <Sentiment2hIcon
                className={cn("w-8 h-8 mx-auto mb-2", getSentimentColor(outcome.sentiment_2h))}
              />
              <div className="text-sm font-medium">After 2 hours</div>
              <div className="text-xs text-muted-foreground">
                {sentimentEmojis.find((s) => s.value === outcome.sentiment_2h)
                  ?.label || "Not recorded"}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4 text-center">
              <Sentiment24hIcon
                className={cn("w-8 h-8 mx-auto mb-2", getSentimentColor(outcome.sentiment_24h))}
              />
              <div className="text-sm font-medium">After 24 hours</div>
              <div className="text-xs text-muted-foreground">
                {sentimentEmojis.find((s) => s.value === outcome.sentiment_24h)
                  ?.label || "Not recorded"}
              </div>
            </CardContent>
          </Card>
        </div>

        {outcome.brier_score !== null && (
          <Card>
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Prediction Accuracy</span>
                <span className="text-lg font-bold text-primary">
                  {((1 - outcome.brier_score) * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Brier score: {outcome.brier_score.toFixed(3)} (lower is better)
              </p>
            </CardContent>
          </Card>
        )}

        {outcome.notes && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Notes</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm">{outcome.notes}</p>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  // Log outcome form
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Log Outcome</h2>
        <p className="text-sm text-muted-foreground">
          Record how your decision turned out to help improve future
          recommendations.
        </p>
      </div>

      {/* Success/Failure */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Did it work out?</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Button
              variant={success === true ? "default" : "outline"}
              className={cn(
                "flex-1",
                success === true && "bg-emerald-500 hover:bg-emerald-600"
              )}
              onClick={() => setSuccess(true)}
            >
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Yes
            </Button>
            <Button
              variant={success === false ? "default" : "outline"}
              className={cn(
                "flex-1",
                success === false && "bg-rose-500 hover:bg-rose-600"
              )}
              onClick={() => setSuccess(false)}
            >
              <XCircle className="w-4 h-4 mr-2" />
              No
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Sentiment 2h */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">
            How did you feel after 2 hours?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between mb-2">
            {sentimentEmojis.map(({ value, icon: Icon, color }) => (
              <button
                key={value}
                onClick={() => setSentiment2h(value)}
                className={cn(
                  "p-2 rounded-lg transition-all",
                  sentiment2h === value
                    ? "bg-muted scale-110"
                    : "hover:bg-muted/50"
                )}
              >
                <Icon
                  className={cn(
                    "w-6 h-6",
                    sentiment2h === value ? color : "text-muted-foreground"
                  )}
                />
              </button>
            ))}
          </div>
          <div className="text-center text-sm text-muted-foreground">
            {sentimentEmojis.find((s) => s.value === sentiment2h)?.label}
          </div>
        </CardContent>
      </Card>

      {/* Sentiment 24h */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">
            How did you feel after 24 hours?
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between mb-2">
            {sentimentEmojis.map(({ value, icon: Icon, color }) => (
              <button
                key={value}
                onClick={() => setSentiment24h(value)}
                className={cn(
                  "p-2 rounded-lg transition-all",
                  sentiment24h === value
                    ? "bg-muted scale-110"
                    : "hover:bg-muted/50"
                )}
              >
                <Icon
                  className={cn(
                    "w-6 h-6",
                    sentiment24h === value ? color : "text-muted-foreground"
                  )}
                />
              </button>
            ))}
          </div>
          <div className="text-center text-sm text-muted-foreground">
            {sentimentEmojis.find((s) => s.value === sentiment24h)?.label}
          </div>
        </CardContent>
      </Card>

      {/* Notes */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Notes (optional)</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Any reflections on this decision..."
            rows={3}
          />
        </CardContent>
      </Card>

      {/* Submit */}
      <Button
        onClick={handleSubmit}
        disabled={success === null || !onLogOutcome}
        className="w-full"
      >
        Log Outcome
      </Button>
    </div>
  );
}
