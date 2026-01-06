"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Info, Lightbulb, Settings, PlusCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";

export type BranchReason =
  | "new_info"
  | "changed_assumption"
  | "changed_constraint"
  | "add_option";

interface BranchReasonOption {
  value: BranchReason;
  label: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

const branchReasons: BranchReasonOption[] = [
  {
    value: "new_info",
    label: "New Information",
    description: "I learned something that changes my perspective",
    icon: Lightbulb,
  },
  {
    value: "changed_assumption",
    label: "Wrong Assumption",
    description: "One of my initial assumptions was incorrect",
    icon: Info,
  },
  {
    value: "changed_constraint",
    label: "Changed Constraints",
    description: "My requirements or limitations have changed",
    icon: Settings,
  },
  {
    value: "add_option",
    label: "Explore Alternative",
    description: "I want to explore a different option path",
    icon: PlusCircle,
  },
];

interface BranchModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreateBranch: (reason: BranchReason, details: string) => void;
  isLoading?: boolean;
}

export function BranchModal({
  open,
  onOpenChange,
  onCreateBranch,
  isLoading = false,
}: BranchModalProps) {
  const [reason, setReason] = useState<BranchReason | null>(null);
  const [details, setDetails] = useState("");

  const handleCreate = () => {
    if (reason) {
      onCreateBranch(reason, details);
    }
  };

  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      // Reset state when closing
      setReason(null);
      setDetails("");
    }
    onOpenChange(newOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitBranch className="w-5 h-5" />
            Create Branch
          </DialogTitle>
          <DialogDescription>
            Create a new branch to explore an alternative path without losing
            your current progress.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Reason selection */}
          <div className="space-y-2">
            <Label>What changed?</Label>
            <RadioGroup
              value={reason || ""}
              onValueChange={(v) => setReason(v as BranchReason)}
              className="space-y-2"
            >
              {branchReasons.map((opt) => {
                const Icon = opt.icon;
                return (
                  <motion.div
                    key={opt.value}
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                  >
                    <Label
                      htmlFor={opt.value}
                      className={cn(
                        "flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-all",
                        reason === opt.value
                          ? "border-primary bg-primary/5"
                          : "border-border hover:border-primary/50"
                      )}
                    >
                      <RadioGroupItem
                        value={opt.value}
                        id={opt.value}
                        className="mt-0.5"
                      />
                      <Icon
                        className={cn(
                          "w-4 h-4 mt-0.5 shrink-0",
                          reason === opt.value
                            ? "text-primary"
                            : "text-muted-foreground"
                        )}
                      />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-sm">{opt.label}</div>
                        <div className="text-xs text-muted-foreground">
                          {opt.description}
                        </div>
                      </div>
                    </Label>
                  </motion.div>
                );
              })}
            </RadioGroup>
          </div>

          {/* Details textarea */}
          <AnimatePresence>
            {reason && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2"
              >
                <Label htmlFor="details">Details (optional)</Label>
                <Textarea
                  id="details"
                  value={details}
                  onChange={(e) => setDetails(e.target.value)}
                  placeholder="Describe what changed or what you want to explore..."
                  rows={3}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => handleOpenChange(false)}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            onClick={handleCreate}
            disabled={!reason || isLoading}
          >
            {isLoading ? (
              <span className="animate-pulse">Creating...</span>
            ) : (
              <>
                <GitBranch className="w-4 h-4 mr-2" />
                Create Branch
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
