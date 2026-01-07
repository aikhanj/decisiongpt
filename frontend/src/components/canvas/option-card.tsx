"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Check,
  ChevronDown,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  TrendingDown,
  Minus,
} from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { Option, ConfidenceLevel } from "@/types";

interface OptionCardProps {
  option: Option;
  isSelected?: boolean;
  onSelect?: () => void;
  disabled?: boolean;
}

const confidenceColors: Record<ConfidenceLevel, string> = {
  low: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  medium: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  high: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
};

const confidenceBarColors: Record<ConfidenceLevel, string> = {
  low: "bg-rose-500",
  medium: "bg-amber-500",
  high: "bg-emerald-500",
};

const confidenceWidths: Record<ConfidenceLevel, string> = {
  low: "w-1/3",
  medium: "w-2/3",
  high: "w-full",
};

const confidenceIcons: Record<ConfidenceLevel, typeof TrendingUp> = {
  low: TrendingDown,
  medium: Minus,
  high: TrendingUp,
};

const riskColors: Record<string, string> = {
  financial_risk: "bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-400",
  time_pressure: "bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-400",
  irreversible: "bg-purple-100 text-purple-700 dark:bg-purple-950/50 dark:text-purple-400",
  uncertainty: "bg-blue-100 text-blue-700 dark:bg-blue-950/50 dark:text-blue-400",
  default: "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400",
};

export function OptionCard({
  option,
  isSelected = false,
  onSelect,
  disabled = false,
}: OptionCardProps) {
  const [expanded, setExpanded] = useState(false);
  const ConfidenceIcon = confidenceIcons[option.confidence];

  return (
    <TooltipProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ scale: disabled ? 1 : 1.01 }}
        transition={{ duration: 0.2 }}
      >
        <Card
          className={cn(
            "relative overflow-hidden transition-all duration-200",
            isSelected && "ring-2 ring-primary border-primary bg-primary/5",
            !disabled && "hover:shadow-lg hover:border-primary/50 cursor-pointer",
            option.confidence === "high" && !isSelected && "border-emerald-200 dark:border-emerald-800/50"
          )}
        >
          {/* Confidence bar at top */}
          <div className="h-1 bg-muted">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: "100%" }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={cn("h-full", confidenceWidths[option.confidence], confidenceBarColors[option.confidence])}
            />
          </div>

          {/* Selected indicator */}
          {isSelected && (
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              className="absolute top-3 right-3"
            >
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary text-primary-foreground">
                <Check className="w-5 h-5" />
              </div>
            </motion.div>
          )}

          {/* High confidence sparkle */}
          {option.confidence === "high" && !isSelected && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="absolute top-3 right-3"
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/50 text-emerald-600">
                    <Sparkles className="w-4 h-4" />
                  </div>
                </TooltipTrigger>
                <TooltipContent>Recommended option</TooltipContent>
              </Tooltip>
            </motion.div>
          )}

          <CardHeader className="pb-3">
            <div className="flex items-start justify-between gap-4 pr-10">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-bold text-primary bg-primary/10 px-2 py-0.5 rounded">
                    Option {option.id}
                  </span>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Badge
                        variant="outline"
                        className={cn("text-xs gap-1", confidenceColors[option.confidence])}
                      >
                        <ConfidenceIcon className="w-3 h-3" />
                        {option.confidence.charAt(0).toUpperCase() +
                          option.confidence.slice(1)}
                      </Badge>
                    </TooltipTrigger>
                    <TooltipContent>
                      {option.confidence === "high" && "Strong supporting evidence"}
                      {option.confidence === "medium" && "Moderate certainty"}
                      {option.confidence === "low" && "Consider gathering more information"}
                    </TooltipContent>
                  </Tooltip>
                </div>
                <h3 className="text-lg font-semibold leading-tight">{option.title}</h3>
              </div>
            </div>
          </CardHeader>

        <CardContent className="space-y-4">
          {/* Good if / Bad if */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/30">
              <div className="flex items-center gap-1 text-emerald-600 text-xs font-medium mb-1">
                <ThumbsUp className="w-3 h-3" />
                Good if
              </div>
              <p className="text-sm">{option.good_if}</p>
            </div>
            <div className="p-3 rounded-lg bg-amber-50 dark:bg-amber-950/30">
              <div className="flex items-center gap-1 text-amber-600 text-xs font-medium mb-1">
                <ThumbsDown className="w-3 h-3" />
                Bad if
              </div>
              <p className="text-sm">{option.bad_if}</p>
            </div>
          </div>

          {/* Pros & Cons */}
          <Accordion type="single" collapsible>
            <AccordionItem value="details" className="border-none">
              <AccordionTrigger className="py-2 text-sm hover:no-underline">
                <span className="flex items-center gap-2">
                  {expanded ? (
                    <ChevronUp className="w-4 h-4" />
                  ) : (
                    <ChevronDown className="w-4 h-4" />
                  )}
                  View pros & cons
                </span>
              </AccordionTrigger>
              <AccordionContent>
                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div>
                    <h4 className="text-xs font-medium text-emerald-600 mb-2">
                      Pros
                    </h4>
                    <ul className="space-y-1">
                      {option.pros.map((pro, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span className="text-emerald-500 mt-0.5">+</span>
                          {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-rose-600 mb-2">
                      Cons
                    </h4>
                    <ul className="space-y-1">
                      {option.cons.map((con, i) => (
                        <li
                          key={i}
                          className="flex items-start gap-2 text-sm"
                        >
                          <span className="text-rose-500 mt-0.5">-</span>
                          {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </AccordionContent>
            </AccordionItem>
          </Accordion>

          {/* Risk chips */}
          {option.risks.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {option.risks.map((risk) => (
                <Badge
                  key={risk}
                  variant="secondary"
                  className={cn(
                    "text-xs",
                    riskColors[risk] || riskColors.default
                  )}
                >
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  {risk.replace(/_/g, " ")}
                </Badge>
              ))}
            </div>
          )}

          {/* Steps preview */}
          <div>
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              Implementation steps
            </h4>
            <ol className="space-y-1">
              {option.steps.slice(0, 3).map((step, i) => (
                <li key={i} className="flex items-start gap-2 text-sm">
                  <span className="flex-shrink-0 w-5 h-5 rounded-full bg-muted text-xs flex items-center justify-center">
                    {i + 1}
                  </span>
                  {step}
                </li>
              ))}
              {option.steps.length > 3 && (
                <li className="text-xs text-muted-foreground pl-7">
                  +{option.steps.length - 3} more steps
                </li>
              )}
            </ol>
          </div>

          {/* Confidence reasoning */}
          {option.confidence_reasoning && (
            <Accordion type="single" collapsible>
              <AccordionItem value="confidence" className="border-none">
                <AccordionTrigger className="py-2 text-xs text-muted-foreground hover:no-underline">
                  Why {option.confidence} confidence?
                </AccordionTrigger>
                <AccordionContent>
                  <p className="text-sm text-muted-foreground">
                    {option.confidence_reasoning}
                  </p>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          )}

          {/* Select button */}
          {onSelect && !isSelected && (
            <Button
              onClick={onSelect}
              disabled={disabled}
              className="w-full group"
              variant={isSelected ? "secondary" : "default"}
              size="lg"
            >
              {isSelected ? (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Selected
                </>
              ) : (
                <>
                  Choose this option
                  <motion.span
                    className="ml-2"
                    initial={{ x: 0 }}
                    whileHover={{ x: 3 }}
                  >
                    →
                  </motion.span>
                </>
              )}
            </Button>
          )}
        </CardContent>
      </Card>
      </motion.div>
    </TooltipProvider>
  );
}
