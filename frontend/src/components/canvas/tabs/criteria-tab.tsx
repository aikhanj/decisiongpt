"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, Target } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";
import type { Criterion } from "@/types";

interface CriteriaTabProps {
  criteria: Criterion[];
  onUpdate?: (criteria: Criterion[]) => void;
}

export function CriteriaTab({ criteria, onUpdate }: CriteriaTabProps) {
  const [newCriterion, setNewCriterion] = useState("");

  const handleAdd = () => {
    if (!newCriterion.trim() || !onUpdate) return;

    const newItem: Criterion = {
      id: `cr_${Date.now()}`,
      name: newCriterion.trim(),
      weight: 5,
    };

    onUpdate([...criteria, newItem]);
    setNewCriterion("");
  };

  const handleUpdateWeight = (id: string, weight: number) => {
    if (!onUpdate) return;
    onUpdate(
      criteria.map((c) => (c.id === id ? { ...c, weight } : c))
    );
  };

  const handleDelete = (id: string) => {
    if (!onUpdate) return;
    onUpdate(criteria.filter((c) => c.id !== id));
  };

  if (criteria.length === 0 && !onUpdate) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Target className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No criteria defined</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          Criteria will be extracted from your conversation as you discuss
          what&apos;s important to you.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Decision Criteria</h2>
        <p className="text-sm text-muted-foreground">
          What matters most in this decision? Adjust weights to prioritize.
        </p>
      </div>

      {/* Criteria list */}
      <div className="space-y-3">
        {criteria.map((criterion, index) => (
          <motion.div
            key={criterion.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
          >
            <Card>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium truncate">
                        {criterion.name}
                      </span>
                      <span className="text-sm font-semibold text-primary">
                        {criterion.weight}/10
                      </span>
                    </div>
                    <Slider
                      value={[criterion.weight]}
                      min={1}
                      max={10}
                      step={1}
                      onValueChange={([value]) =>
                        handleUpdateWeight(criterion.id, value)
                      }
                      disabled={!onUpdate}
                      className="w-full"
                    />
                    {criterion.description && (
                      <p className="text-xs text-muted-foreground mt-2">
                        {criterion.description}
                      </p>
                    )}
                  </div>
                  {onUpdate && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(criterion.id)}
                      className="shrink-0 text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Add new criterion */}
      {onUpdate && (
        <div className="flex gap-2">
          <Input
            value={newCriterion}
            onChange={(e) => setNewCriterion(e.target.value)}
            placeholder="Add a criterion..."
            onKeyDown={(e) => e.key === "Enter" && handleAdd()}
          />
          <Button onClick={handleAdd} disabled={!newCriterion.trim()}>
            <Plus className="w-4 h-4 mr-2" />
            Add
          </Button>
        </div>
      )}
    </div>
  );
}
