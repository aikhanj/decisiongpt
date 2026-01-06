"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion } from "framer-motion";
import { ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { CooldownBanner } from "@/components/layout/cooldown-banner";
import { QuestionCard } from "@/components/decision/question-card";
import { getDecision, answerQuestions } from "@/lib/api";
import type { Decision, Question, Answer } from "@/types";
import { toast } from "sonner";

export default function ClarifyPage() {
  const router = useRouter();
  const params = useParams();
  const decisionId = params.id as string;

  const [decision, setDecision] = useState<Decision | null>(null);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<Record<string, Answer>>({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [moodState, setMoodState] = useState<string | null>(null);

  useEffect(() => {
    async function loadDecision() {
      try {
        const data = await getDecision(decisionId);
        setDecision(data);

        // Get questions from the first node
        const node = data.nodes[0];
        if (node?.questions_json?.questions) {
          setQuestions(node.questions_json.questions);
          setMoodState(node.mood_state || null);
        }
      } catch (error) {
        toast.error("Failed to load decision");
        router.push("/");
      } finally {
        setLoading(false);
      }
    }
    loadDecision();
  }, [decisionId, router]);

  const handleAnswerChange = (answer: Answer) => {
    setAnswers((prev) => ({
      ...prev,
      [answer.question_id]: answer,
    }));
  };

  const answeredCount = Object.keys(answers).length;
  const progress = questions.length > 0 ? (answeredCount / questions.length) * 100 : 0;

  const handleSubmit = async () => {
    if (answeredCount < questions.length * 0.6) {
      toast.error("Please answer at least 60% of the questions");
      return;
    }

    setSubmitting(true);
    try {
      const nodeId = decision?.nodes[0]?.id;
      if (!nodeId) throw new Error("No node found");

      await answerQuestions(decisionId, nodeId, {
        answers: Object.values(answers),
      });

      toast.success("Generating your options...");
      router.push(`/decisions/${decisionId}/moves`);
    } catch (error) {
      toast.error("Failed to submit answers");
      console.error(error);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const needsCooldown = ["anxious", "tired", "horny", "angry"].includes(
    moodState || ""
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-2xl font-bold">Let's clarify</h1>
        <p className="text-muted-foreground">
          Answer these questions to help me understand your situation better.
        </p>
      </motion.div>

      {needsCooldown && (
        <CooldownBanner
          reason="Your current state suggests taking a moment before acting. I'll keep options calm and measured."
          moodState={moodState || undefined}
        />
      )}

      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="space-y-2"
      >
        <div className="flex items-center justify-between text-sm">
          <span className="text-muted-foreground">
            {answeredCount} of {questions.length} answered
          </span>
          <span className="font-medium">{Math.round(progress)}%</span>
        </div>
        <Progress value={progress} />
      </motion.div>

      <div className="space-y-4">
        {questions
          .sort((a, b) => b.priority - a.priority)
          .map((question, index) => (
            <QuestionCard
              key={question.id}
              question={question}
              index={index}
              value={answers[question.id]?.value}
              onChange={handleAnswerChange}
            />
          ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="sticky bottom-4 bg-background/95 backdrop-blur p-4 rounded-2xl border shadow-lg"
      >
        <Button
          onClick={handleSubmit}
          disabled={submitting || answeredCount < questions.length * 0.6}
          className="w-full"
          size="lg"
        >
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating options...
            </>
          ) : (
            <>
              See My Options
              <ArrowRight className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>
      </motion.div>
    </div>
  );
}
