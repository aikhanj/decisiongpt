"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Plus, Clock, CheckCircle, Archive, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { getDecisions } from "@/lib/api";
import type { Decision } from "@/types";
import { formatDate } from "@/lib/utils";

const statusConfig = {
  active: { icon: Clock, label: "Active", variant: "warning" as const },
  resolved: { icon: CheckCircle, label: "Resolved", variant: "success" as const },
  archived: { icon: Archive, label: "Archived", variant: "secondary" as const },
};

export default function DashboardPage() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadDecisions() {
      try {
        const data = await getDecisions();
        setDecisions(data);
      } catch (error) {
        console.error("Failed to load decisions:", error);
      } finally {
        setLoading(false);
      }
    }
    loadDecisions();
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-4"
      >
        <h1 className="text-4xl font-bold tracking-tight">Gentleman Coach</h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
          Make confident, respectful decisions in your romantic life. Get clear
          options, not therapy.
        </p>
        <Link href="/new">
          <Button size="lg" className="mt-4">
            <Plus className="mr-2 h-5 w-5" />
            New Decision
          </Button>
        </Link>
      </motion.div>

      {/* Recent Decisions */}
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold">Recent Decisions</h2>

        {loading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3].map((i) => (
              <Card key={i} className="animate-pulse">
                <CardHeader>
                  <div className="h-5 bg-muted rounded w-3/4" />
                  <div className="h-4 bg-muted rounded w-1/2 mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="h-4 bg-muted rounded w-full" />
                </CardContent>
              </Card>
            ))}
          </div>
        ) : decisions.length === 0 ? (
          <Card className="border-dashed">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <p className="text-muted-foreground mb-4">
                No decisions yet. Start your first one.
              </p>
              <Link href="/new">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  New Decision
                </Button>
              </Link>
            </CardContent>
          </Card>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {decisions.map((decision, index) => {
              const status = statusConfig[decision.status as keyof typeof statusConfig];
              const StatusIcon = status.icon;

              return (
                <motion.div
                  key={decision.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Link href={`/decisions/${decision.id}`}>
                    <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                      <CardHeader>
                        <div className="flex items-start justify-between">
                          <CardTitle className="text-lg line-clamp-1">
                            {decision.title || "Untitled"}
                          </CardTitle>
                          <Badge variant={status.variant}>
                            <StatusIcon className="mr-1 h-3 w-3" />
                            {status.label}
                          </Badge>
                        </div>
                        <CardDescription>
                          {formatDate(decision.created_at)}
                          {decision.situation_type && (
                            <span className="ml-2">
                              · {decision.situation_type.replace(/_/g, " ")}
                            </span>
                          )}
                        </CardDescription>
                      </CardHeader>
                      <CardContent>
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {decision.situation_text}
                        </p>
                        <div className="flex items-center mt-4 text-sm text-primary">
                          View details
                          <ChevronRight className="ml-1 h-4 w-4" />
                        </div>
                      </CardContent>
                    </Card>
                  </Link>
                </motion.div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
