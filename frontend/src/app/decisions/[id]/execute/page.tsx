"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Check,
  Copy,
  Loader2,
  CheckCircle2,
  XCircle,
  MessageSquare,
  Shield,
  DoorOpen,
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Textarea } from "@/components/ui/textarea";
import { getDecision, resolveOutcome } from "@/lib/api";
import type { Decision, ExecutionPlan } from "@/types";
import { toast } from "sonner";

export default function ExecutePage() {
  const router = useRouter();
  const params = useParams();
  const decisionId = params.id as string;

  const [decision, setDecision] = useState<Decision | null>(null);
  const [plan, setPlan] = useState<ExecutionPlan | null>(null);
  const [chosenMoveTitle, setChosenMoveTitle] = useState<string>("");
  const [completedSteps, setCompletedSteps] = useState<Set<number>>(new Set());
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [outcomeDialogOpen, setOutcomeDialogOpen] = useState(false);
  const [outcomeLoading, setOutcomeLoading] = useState(false);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    async function loadDecision() {
      try {
        const data = await getDecision(decisionId);
        setDecision(data);

        // Get execution plan from the node in "execute" phase
        const node = data.nodes.find((n) => n.phase === "execute");
        if (node?.execution_plan_json) {
          setPlan(node.execution_plan_json);

          // Get chosen move title
          if (node.moves_json?.moves && node.chosen_move_id) {
            const move = node.moves_json.moves.find(
              (m: any) => m.move_id === node.chosen_move_id
            );
            if (move) {
              setChosenMoveTitle(move.title);
            }
          }
        }
      } catch (error) {
        toast.error("Failed to load execution plan");
        router.push("/");
      } finally {
        setLoading(false);
      }
    }
    loadDecision();
  }, [decisionId, router]);

  const toggleStep = (index: number) => {
    setCompletedSteps((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const copyMessage = async () => {
    if (plan?.exact_message) {
      await navigator.clipboard.writeText(plan.exact_message);
      setCopied(true);
      toast.success("Message copied to clipboard");
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleOutcome = async (progress: boolean) => {
    setOutcomeLoading(true);
    try {
      const node = decision?.nodes.find((n) => n.phase === "execute");
      if (!node) throw new Error("No node found");

      await resolveOutcome(decisionId, node.id, {
        progress_yesno: progress,
        notes: notes || undefined,
      });

      toast.success("Outcome recorded. Great job tracking your progress!");
      setOutcomeDialogOpen(false);
      router.push("/");
    } catch (error) {
      toast.error("Failed to record outcome");
      console.error(error);
    } finally {
      setOutcomeLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!plan) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">No execution plan found.</p>
      </div>
    );
  }

  const allStepsComplete = completedSteps.size === plan.steps.length;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <Badge variant="gentleman" className="mb-2">
          Move: {chosenMoveTitle}
        </Badge>
        <h1 className="text-2xl font-bold">Your Execution Plan</h1>
        <p className="text-muted-foreground">
          Follow these steps. Check them off as you go.
        </p>
      </motion.div>

      {/* Steps Checklist */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Steps</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {plan.steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.05 }}
              className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                completedSteps.has(index)
                  ? "bg-green-50 text-green-800"
                  : "bg-muted hover:bg-muted/80"
              }`}
              onClick={() => toggleStep(index)}
            >
              <div
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 ${
                  completedSteps.has(index)
                    ? "bg-green-500 border-green-500 text-white"
                    : "border-muted-foreground"
                }`}
              >
                {completedSteps.has(index) && <Check className="h-4 w-4" />}
              </div>
              <span className={completedSteps.has(index) ? "line-through" : ""}>
                {step}
              </span>
            </motion.div>
          ))}
        </CardContent>
      </Card>

      {/* Exact Message */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <MessageSquare className="h-5 w-5" />
            Your Message
          </CardTitle>
          <CardDescription>Copy and send when you're ready</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <div className="p-4 bg-secondary rounded-xl">
              <p className="italic">"{plan.exact_message}"</p>
            </div>
            <Button
              variant="outline"
              size="sm"
              className="absolute top-2 right-2"
              onClick={copyMessage}
            >
              {copied ? (
                <Check className="h-4 w-4" />
              ) : (
                <Copy className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Exit Line */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <DoorOpen className="h-5 w-5" />
            Exit Line
          </CardTitle>
          <CardDescription>
            If things don't go well, use this to exit gracefully
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-red-50 rounded-xl">
            <p className="italic text-red-800">"{plan.exit_line}"</p>
          </div>
        </CardContent>
      </Card>

      {/* Boundary Rule */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Shield className="h-5 w-5 text-amber-500" />
            Boundary Rule
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="p-4 bg-amber-50 rounded-xl">
            <p className="font-medium text-amber-800">{plan.boundary_rule}</p>
          </div>
        </CardContent>
      </Card>

      {/* Log Outcome */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="sticky bottom-4 bg-background/95 backdrop-blur p-4 rounded-2xl border shadow-lg"
      >
        <Dialog open={outcomeDialogOpen} onOpenChange={setOutcomeDialogOpen}>
          <DialogTrigger asChild>
            <Button
              className="w-full"
              size="lg"
              disabled={!allStepsComplete}
            >
              {allStepsComplete
                ? "Log Outcome"
                : `Complete all steps (${completedSteps.size}/${plan.steps.length})`}
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>How did it go?</DialogTitle>
              <DialogDescription>
                This helps improve future recommendations.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <Textarea
                placeholder="Any notes about what happened? (optional)"
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
              />
            </div>
            <DialogFooter className="flex gap-2 sm:gap-0">
              <Button
                variant="outline"
                onClick={() => handleOutcome(false)}
                disabled={outcomeLoading}
                className="flex-1"
              >
                <XCircle className="mr-2 h-4 w-4" />
                Didn't progress
              </Button>
              <Button
                onClick={() => handleOutcome(true)}
                disabled={outcomeLoading}
                className="flex-1"
              >
                <CheckCircle2 className="mr-2 h-4 w-4" />
                Made progress
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </motion.div>
    </div>
  );
}
