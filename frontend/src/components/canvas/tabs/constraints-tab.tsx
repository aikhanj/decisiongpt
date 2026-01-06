"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Plus, Trash2, Filter, Lock, Unlock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Constraint } from "@/types";

interface ConstraintsTabProps {
  constraints: Constraint[];
  onUpdate?: (constraints: Constraint[]) => void;
}

export function ConstraintsTab({ constraints, onUpdate }: ConstraintsTabProps) {
  const [newConstraint, setNewConstraint] = useState("");
  const [newType, setNewType] = useState<"hard" | "soft">("hard");

  const hardConstraints = constraints.filter((c) => c.type === "hard");
  const softConstraints = constraints.filter((c) => c.type === "soft");

  const handleAdd = () => {
    if (!newConstraint.trim() || !onUpdate) return;

    const newItem: Constraint = {
      id: `c_${Date.now()}`,
      text: newConstraint.trim(),
      type: newType,
    };

    onUpdate([...constraints, newItem]);
    setNewConstraint("");
  };

  const handleToggleType = (id: string) => {
    if (!onUpdate) return;
    onUpdate(
      constraints.map((c) =>
        c.id === id ? { ...c, type: c.type === "hard" ? "soft" : "hard" } : c
      )
    );
  };

  const handleDelete = (id: string) => {
    if (!onUpdate) return;
    onUpdate(constraints.filter((c) => c.id !== id));
  };

  if (constraints.length === 0 && !onUpdate) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
          <Filter className="w-8 h-8 text-muted-foreground" />
        </div>
        <h3 className="text-lg font-medium mb-2">No constraints defined</h3>
        <p className="text-sm text-muted-foreground max-w-xs">
          Constraints will be extracted from your conversation as you discuss
          your requirements.
        </p>
      </div>
    );
  }

  const ConstraintCard = ({ constraint }: { constraint: Constraint }) => (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-center gap-3 p-3 bg-background rounded-lg border"
    >
      <Button
        variant="ghost"
        size="icon"
        onClick={() => handleToggleType(constraint.id)}
        disabled={!onUpdate}
        className={cn(
          "shrink-0",
          constraint.type === "hard"
            ? "text-rose-500"
            : "text-muted-foreground"
        )}
      >
        {constraint.type === "hard" ? (
          <Lock className="w-4 h-4" />
        ) : (
          <Unlock className="w-4 h-4" />
        )}
      </Button>
      <span className="flex-1 text-sm">{constraint.text}</span>
      {onUpdate && (
        <Button
          variant="ghost"
          size="icon"
          onClick={() => handleDelete(constraint.id)}
          className="shrink-0 text-muted-foreground hover:text-destructive"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      )}
    </motion.div>
  );

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold mb-1">Constraints</h2>
        <p className="text-sm text-muted-foreground">
          Hard constraints are non-negotiable. Soft constraints are preferences.
        </p>
      </div>

      {/* Hard constraints */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Lock className="w-4 h-4 text-rose-500" />
            Hard Constraints
            <Badge variant="secondary" className="ml-auto">
              {hardConstraints.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {hardConstraints.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No hard constraints
            </p>
          ) : (
            hardConstraints.map((c) => (
              <ConstraintCard key={c.id} constraint={c} />
            ))
          )}
        </CardContent>
      </Card>

      {/* Soft constraints */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Unlock className="w-4 h-4 text-muted-foreground" />
            Soft Constraints (Preferences)
            <Badge variant="secondary" className="ml-auto">
              {softConstraints.length}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {softConstraints.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-4">
              No soft constraints
            </p>
          ) : (
            softConstraints.map((c) => (
              <ConstraintCard key={c.id} constraint={c} />
            ))
          )}
        </CardContent>
      </Card>

      {/* Add new constraint */}
      {onUpdate && (
        <div className="space-y-2">
          <div className="flex gap-2">
            <Button
              variant={newType === "hard" ? "default" : "outline"}
              size="sm"
              onClick={() => setNewType("hard")}
            >
              <Lock className="w-3 h-3 mr-1" />
              Hard
            </Button>
            <Button
              variant={newType === "soft" ? "default" : "outline"}
              size="sm"
              onClick={() => setNewType("soft")}
            >
              <Unlock className="w-3 h-3 mr-1" />
              Soft
            </Button>
          </div>
          <div className="flex gap-2">
            <Input
              value={newConstraint}
              onChange={(e) => setNewConstraint(e.target.value)}
              placeholder={`Add a ${newType} constraint...`}
              onKeyDown={(e) => e.key === "Enter" && handleAdd()}
            />
            <Button onClick={handleAdd} disabled={!newConstraint.trim()}>
              <Plus className="w-4 h-4 mr-2" />
              Add
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
