"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  Plus,
  ChevronLeft,
  Sparkles,
  Trash2,
  Edit,
  User,
  Bot,
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
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getAdvisors, createAdvisor, deleteAdvisor } from "@/lib/api";
import type { Advisor } from "@/types";

const DEFAULT_PROMPT_TEMPLATE = `You are [ADVISOR_NAME], a helpful advisor specializing in [EXPERTISE_AREA].

## Your Character
- [PERSONALITY_TRAIT_1]
- [PERSONALITY_TRAIT_2]
- [PERSONALITY_TRAIT_3]

## Your Expertise
- [EXPERTISE_TOPIC_1]
- [EXPERTISE_TOPIC_2]
- [EXPERTISE_TOPIC_3]

## Your Approach
1. Listen carefully to understand the user's situation
2. Provide specific, actionable advice
3. Be encouraging but honest

## Response Style
- Keep responses conversational and helpful
- Use clear, simple language
- Give specific suggestions when possible
- Limit responses to 150-200 words

Always respond in valid JSON matching the requested schema exactly.
`;

export default function AdvisorsPage() {
  const [advisors, setAdvisors] = useState<Advisor[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    slug: "",
    name: "",
    avatar: "",
    description: "",
    expertise_keywords: "",
    personality_traits: "",
    system_prompt: DEFAULT_PROMPT_TEMPLATE,
  });

  useEffect(() => {
    loadAdvisors();
  }, []);

  async function loadAdvisors() {
    try {
      const data = await getAdvisors();
      setAdvisors(data);
    } catch (error) {
      console.error("Failed to load advisors:", error);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateAdvisor(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      await createAdvisor({
        slug: formData.slug.toLowerCase().replace(/\s+/g, "-"),
        name: formData.name,
        avatar: formData.avatar || "🤖",
        description: formData.description,
        expertise_keywords: formData.expertise_keywords
          .split(",")
          .map((k) => k.trim())
          .filter(Boolean),
        personality_traits: formData.personality_traits
          .split(",")
          .map((t) => t.trim())
          .filter(Boolean),
        system_prompt: formData.system_prompt,
      });

      // Reset form and close dialog
      setFormData({
        slug: "",
        name: "",
        avatar: "",
        description: "",
        expertise_keywords: "",
        personality_traits: "",
        system_prompt: DEFAULT_PROMPT_TEMPLATE,
      });
      setIsCreateOpen(false);

      // Reload advisors
      await loadAdvisors();
    } catch (error) {
      setError(error instanceof Error ? error.message : "Failed to create advisor");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDeleteAdvisor(advisorId: string) {
    if (!confirm("Are you sure you want to delete this advisor?")) return;

    try {
      await deleteAdvisor(advisorId);
      await loadAdvisors();
    } catch (error) {
      console.error("Failed to delete advisor:", error);
    }
  }

  const systemAdvisors = advisors.filter((a) => a.is_system);
  const customAdvisors = advisors.filter((a) => !a.is_system);

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="h-4 w-4" />
              Back
            </Link>
            <span className="font-semibold text-lg">Advisors</span>
          </div>
          <Dialog open={isCreateOpen} onOpenChange={setIsCreateOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-2 h-4 w-4" />
                Create Advisor
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Create Custom Advisor</DialogTitle>
                <DialogDescription>
                  Create your own AI advisor with a custom personality and expertise.
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleCreateAdvisor} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      placeholder="The Expert"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="slug">ID (slug)</Label>
                    <Input
                      id="slug"
                      placeholder="expert"
                      value={formData.slug}
                      onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                      required
                      pattern="^[a-z0-9-]+$"
                    />
                    <p className="text-xs text-muted-foreground">Lowercase letters, numbers, and hyphens only</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="avatar">Avatar (emoji)</Label>
                    <Input
                      id="avatar"
                      placeholder="🧙"
                      value={formData.avatar}
                      onChange={(e) => setFormData({ ...formData, avatar: e.target.value })}
                      required
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="personality_traits">Personality Traits</Label>
                    <Input
                      id="personality_traits"
                      placeholder="wise, patient, direct"
                      value={formData.personality_traits}
                      onChange={(e) => setFormData({ ...formData, personality_traits: e.target.value })}
                    />
                    <p className="text-xs text-muted-foreground">Comma-separated</p>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="description">Description</Label>
                  <Input
                    id="description"
                    placeholder="Expert advice on your specific topic"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    required
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="expertise_keywords">Expertise Keywords</Label>
                  <Input
                    id="expertise_keywords"
                    placeholder="topic1, topic2, keyword1, keyword2"
                    value={formData.expertise_keywords}
                    onChange={(e) => setFormData({ ...formData, expertise_keywords: e.target.value })}
                    required
                  />
                  <p className="text-xs text-muted-foreground">
                    Comma-separated keywords that will trigger this advisor
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="system_prompt">System Prompt</Label>
                  <Textarea
                    id="system_prompt"
                    placeholder="You are a helpful advisor..."
                    value={formData.system_prompt}
                    onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                    required
                    rows={12}
                    className="font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    Define your advisor's personality, expertise, and response style
                  </p>
                </div>

                {error && (
                  <p className="text-sm text-destructive">{error}</p>
                )}

                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setIsCreateOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" disabled={isSubmitting}>
                    {isSubmitting ? "Creating..." : "Create Advisor"}
                  </Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </header>

      <main className="container mx-auto py-8 px-4 space-y-8">
        {/* System Advisors */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Built-in Advisors</h2>
          </div>
          <p className="text-muted-foreground">
            These advisors are automatically selected based on your question.
          </p>

          {loading ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {[1, 2, 3, 4].map((i) => (
                <Card key={i} className="animate-pulse">
                  <CardHeader>
                    <div className="h-12 w-12 bg-muted rounded-full" />
                    <div className="h-5 bg-muted rounded w-3/4 mt-2" />
                    <div className="h-4 bg-muted rounded w-1/2" />
                  </CardHeader>
                </Card>
              ))}
            </div>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {systemAdvisors.map((advisor, index) => (
                <motion.div
                  key={advisor.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="h-full">
                    <CardHeader>
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center text-2xl">
                          {advisor.avatar}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-lg">{advisor.name}</CardTitle>
                            <Badge variant="secondary" className="text-xs">
                              <Bot className="mr-1 h-3 w-3" />
                              System
                            </Badge>
                          </div>
                          <CardDescription>{advisor.description}</CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-1.5">
                        {advisor.expertise_keywords.slice(0, 5).map((keyword) => (
                          <Badge key={keyword} variant="outline" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                        {advisor.expertise_keywords.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{advisor.expertise_keywords.length - 5} more
                          </Badge>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </div>

        {/* Custom Advisors */}
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            <h2 className="text-xl font-semibold">Your Custom Advisors</h2>
          </div>
          <p className="text-muted-foreground">
            Create your own advisors with custom personalities and expertise.
          </p>

          {customAdvisors.length === 0 ? (
            <Card className="border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mb-4">
                  <Plus className="w-8 h-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium mb-2">No custom advisors yet</h3>
                <p className="text-muted-foreground mb-6 text-center max-w-sm">
                  Create your first custom advisor with a unique personality and expertise.
                </p>
                <Button onClick={() => setIsCreateOpen(true)}>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Advisor
                </Button>
              </CardContent>
            </Card>
          ) : (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {customAdvisors.map((advisor, index) => (
                <motion.div
                  key={advisor.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <Card className="h-full">
                    <CardHeader>
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-full bg-secondary flex items-center justify-center text-2xl">
                          {advisor.avatar}
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <CardTitle className="text-lg">{advisor.name}</CardTitle>
                            <Badge variant="outline" className="text-xs">
                              <User className="mr-1 h-3 w-3" />
                              Custom
                            </Badge>
                          </div>
                          <CardDescription>{advisor.description}</CardDescription>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="flex flex-wrap gap-1.5">
                        {advisor.expertise_keywords.slice(0, 5).map((keyword) => (
                          <Badge key={keyword} variant="outline" className="text-xs">
                            {keyword}
                          </Badge>
                        ))}
                        {advisor.expertise_keywords.length > 5 && (
                          <Badge variant="outline" className="text-xs">
                            +{advisor.expertise_keywords.length - 5} more
                          </Badge>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm" className="flex-1">
                          <Edit className="mr-2 h-3 w-3" />
                          Edit
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-destructive hover:text-destructive"
                          onClick={() => handleDeleteAdvisor(advisor.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
