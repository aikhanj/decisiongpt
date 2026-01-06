"use client";

import { motion } from "framer-motion";
import { Shield, Clock, AlertTriangle, ChevronDown } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { Move } from "@/types";

interface MoveCardProps {
  move: Move;
  index: number;
  isSelected: boolean;
  onSelect: (moveId: string) => void;
}

const riskColors = {
  low: "success",
  med: "warning",
  high: "destructive",
} as const;

export function MoveCard({ move, index, isSelected, onSelect }: MoveCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card
        className={`cursor-pointer transition-all ${
          isSelected
            ? "ring-2 ring-primary shadow-lg"
            : "hover:shadow-md"
        }`}
        onClick={() => onSelect(move.move_id)}
      >
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-lg font-bold">
                  {move.move_id}
                </Badge>
                <CardTitle className="text-xl">{move.title}</CardTitle>
              </div>
              <CardDescription>{move.when_to_use}</CardDescription>
            </div>
            <div className="flex flex-col items-end gap-1">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-amber-500" />
                <span className="font-semibold">{move.gentleman_score}</span>
              </div>
              <Badge variant={riskColors[move.risk_level]}>
                {move.risk_level} risk
              </Badge>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* Progress probability */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">
                Probability of progress
              </span>
              <span className="font-medium">
                {Math.round(move.p_calibrated_progress * 100)}%
              </span>
            </div>
            <Progress value={move.p_calibrated_progress * 100} />
          </div>

          {/* Tradeoff */}
          <div className="flex items-start gap-2 p-3 bg-muted rounded-xl">
            <AlertTriangle className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
            <p className="text-sm">{move.tradeoff}</p>
          </div>

          {/* Scripts */}
          <Tabs defaultValue="direct" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="direct">Direct Script</TabsTrigger>
              <TabsTrigger value="softer">Softer Script</TabsTrigger>
            </TabsList>
            <TabsContent value="direct" className="mt-2">
              <div className="p-3 bg-secondary rounded-xl">
                <p className="text-sm italic">"{move.scripts.direct}"</p>
              </div>
            </TabsContent>
            <TabsContent value="softer" className="mt-2">
              <div className="p-3 bg-secondary rounded-xl">
                <p className="text-sm italic">"{move.scripts.softer}"</p>
              </div>
            </TabsContent>
          </Tabs>

          {/* Timing */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>{move.timing}</span>
          </div>

          {/* Branches accordion */}
          <Accordion type="single" collapsible>
            <AccordionItem value="branches" className="border-none">
              <AccordionTrigger className="text-sm hover:no-underline">
                What to do based on her response
              </AccordionTrigger>
              <AccordionContent>
                <div className="space-y-3">
                  <div className="p-3 bg-green-50 rounded-xl">
                    <p className="font-medium text-green-700 text-sm">
                      If warm response:
                    </p>
                    <p className="text-sm mt-1">{move.branches.warm.next_move}</p>
                    <p className="text-xs text-muted-foreground mt-1 italic">
                      "{move.branches.warm.script}"
                    </p>
                  </div>
                  <div className="p-3 bg-yellow-50 rounded-xl">
                    <p className="font-medium text-yellow-700 text-sm">
                      If neutral response:
                    </p>
                    <p className="text-sm mt-1">
                      {move.branches.neutral.next_move}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1 italic">
                      "{move.branches.neutral.script}"
                    </p>
                  </div>
                  <div className="p-3 bg-red-50 rounded-xl">
                    <p className="font-medium text-red-700 text-sm">
                      If cold response:
                    </p>
                    <p className="text-sm mt-1">{move.branches.cold.next_move}</p>
                    <p className="text-xs text-muted-foreground mt-1 italic">
                      "{move.branches.cold.script}"
                    </p>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {isSelected && (
            <Button className="w-full mt-2">
              Choose This Move
            </Button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
