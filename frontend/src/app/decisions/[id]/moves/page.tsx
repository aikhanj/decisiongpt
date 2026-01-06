"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CooldownBanner } from "@/components/layout/cooldown-banner";
import { MoveCard } from "@/components/moves/move-card";
import { getDecision, chooseMove } from "@/lib/api";
import type { Decision, Move } from "@/types";
import { toast } from "sonner";

export default function MovesPage() {
  const router = useRouter();
  const params = useParams();
  const decisionId = params.id as string;

  const [decision, setDecision] = useState<Decision | null>(null);
  const [moves, setMoves] = useState<Move[]>([]);
  const [selectedMove, setSelectedMove] = useState<string | null>(null);
  const [cooldownRecommended, setCooldownRecommended] = useState(false);
  const [cooldownReason, setCooldownReason] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function loadDecision() {
      try {
        const data = await getDecision(decisionId);
        setDecision(data);

        // Get moves from the node in "moves" phase
        const node = data.nodes.find((n) => n.phase === "moves");
        if (node?.moves_json?.moves) {
          setMoves(node.moves_json.moves);
          setCooldownRecommended(node.moves_json.cooldown_recommended || false);
          setCooldownReason(node.moves_json.cooldown_reason || null);
        }
      } catch (error) {
        toast.error("Failed to load options");
        router.push("/");
      } finally {
        setLoading(false);
      }
    }
    loadDecision();
  }, [decisionId, router]);

  const handleSelectMove = (moveId: string) => {
    setSelectedMove(moveId);
  };

  const handleConfirm = async () => {
    if (!selectedMove) {
      toast.error("Please select a move first");
      return;
    }

    setSubmitting(true);
    try {
      const node = decision?.nodes.find((n) => n.phase === "moves");
      if (!node) throw new Error("No node found");

      await chooseMove(decisionId, node.id, { move_id: selectedMove });
      toast.success("Generating your execution plan...");
      router.push(`/decisions/${decisionId}/execute`);
    } catch (error) {
      toast.error("Failed to choose move");
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-2"
      >
        <h1 className="text-2xl font-bold">Your Options</h1>
        <p className="text-muted-foreground">
          Review each move carefully. Select the one that fits your situation
          best.
        </p>
      </motion.div>

      {cooldownRecommended && cooldownReason && (
        <CooldownBanner reason={cooldownReason} />
      )}

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
        {moves.map((move, index) => (
          <MoveCard
            key={move.move_id}
            move={move}
            index={index}
            isSelected={selectedMove === move.move_id}
            onSelect={handleSelectMove}
          />
        ))}
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="sticky bottom-4 bg-background/95 backdrop-blur p-4 rounded-2xl border shadow-lg"
      >
        <Button
          onClick={handleConfirm}
          disabled={!selectedMove || submitting}
          className="w-full"
          size="lg"
        >
          {submitting ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Generating plan...
            </>
          ) : selectedMove ? (
            `Confirm Move ${selectedMove}`
          ) : (
            "Select a move to continue"
          )}
        </Button>
      </motion.div>
    </div>
  );
}
