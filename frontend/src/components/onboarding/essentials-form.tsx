"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { User, Briefcase, Building2, GraduationCap, ArrowRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface EssentialsFormData {
  name: string;
  occupation: string;
  industry?: string;
  age_range?: string;
}

interface EssentialsFormProps {
  onComplete: (data: EssentialsFormData) => void;
  onSkip?: () => void;
  loading?: boolean;
}

const AGE_RANGES = [
  { value: "18-24", label: "18-24" },
  { value: "25-34", label: "25-34" },
  { value: "35-44", label: "35-44" },
  { value: "45-54", label: "45-54" },
  { value: "55-64", label: "55-64" },
  { value: "65+", label: "65+" },
];

const INDUSTRIES = [
  { value: "tech", label: "Technology" },
  { value: "finance", label: "Finance / Banking" },
  { value: "healthcare", label: "Healthcare" },
  { value: "education", label: "Education" },
  { value: "retail", label: "Retail / E-commerce" },
  { value: "manufacturing", label: "Manufacturing" },
  { value: "consulting", label: "Consulting" },
  { value: "marketing", label: "Marketing / Advertising" },
  { value: "media", label: "Media / Entertainment" },
  { value: "nonprofit", label: "Non-profit" },
  { value: "government", label: "Government" },
  { value: "real_estate", label: "Real Estate" },
  { value: "student", label: "Student" },
  { value: "other", label: "Other" },
];

export function EssentialsForm({ onComplete, onSkip, loading }: EssentialsFormProps) {
  const [formData, setFormData] = useState<EssentialsFormData>({
    name: "",
    occupation: "",
    industry: undefined,
    age_range: undefined,
  });
  const [errors, setErrors] = useState<Partial<Record<keyof EssentialsFormData, string>>>({});

  const validate = (): boolean => {
    const newErrors: typeof errors = {};

    if (!formData.name.trim()) {
      newErrors.name = "Please enter your name";
    }
    if (!formData.occupation.trim()) {
      newErrors.occupation = "Please enter your occupation";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validate()) {
      onComplete(formData);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-md mx-auto"
    >
      <Card className="border-2">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <User className="w-6 h-6 text-primary" />
          </div>
          <CardTitle className="text-xl">Let&apos;s get acquainted</CardTitle>
          <CardDescription className="text-sm">
            Help me understand you better so I can provide more personalized guidance
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="flex items-center gap-2">
                <User className="w-4 h-4 text-muted-foreground" />
                What should I call you?
              </Label>
              <Input
                id="name"
                placeholder="Your name"
                value={formData.name}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, name: e.target.value }))
                }
                className={errors.name ? "border-red-500" : ""}
              />
              {errors.name && (
                <p className="text-xs text-red-500">{errors.name}</p>
              )}
            </div>

            {/* Occupation */}
            <div className="space-y-2">
              <Label htmlFor="occupation" className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-muted-foreground" />
                What do you do?
              </Label>
              <Input
                id="occupation"
                placeholder="e.g., Product Manager, Student, Entrepreneur"
                value={formData.occupation}
                onChange={(e) =>
                  setFormData((prev) => ({ ...prev, occupation: e.target.value }))
                }
                className={errors.occupation ? "border-red-500" : ""}
              />
              {errors.occupation && (
                <p className="text-xs text-red-500">{errors.occupation}</p>
              )}
            </div>

            {/* Industry (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="industry" className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-muted-foreground" />
                Industry
                <span className="text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Select
                value={formData.industry}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, industry: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select your industry" />
                </SelectTrigger>
                <SelectContent>
                  {INDUSTRIES.map((industry) => (
                    <SelectItem key={industry.value} value={industry.value}>
                      {industry.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Age Range (Optional) */}
            <div className="space-y-2">
              <Label htmlFor="age_range" className="flex items-center gap-2">
                <GraduationCap className="w-4 h-4 text-muted-foreground" />
                Age range
                <span className="text-xs text-muted-foreground">(optional)</span>
              </Label>
              <Select
                value={formData.age_range}
                onValueChange={(value) =>
                  setFormData((prev) => ({ ...prev, age_range: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select your age range" />
                </SelectTrigger>
                <SelectContent>
                  {AGE_RANGES.map((range) => (
                    <SelectItem key={range.value} value={range.value}>
                      {range.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Submit */}
            <div className="pt-4 space-y-3">
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? (
                  "Saving..."
                ) : (
                  <>
                    Continue
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
              {onSkip && (
                <Button
                  type="button"
                  variant="ghost"
                  className="w-full text-muted-foreground"
                  onClick={onSkip}
                  disabled={loading}
                >
                  Skip for now
                </Button>
              )}
            </div>
          </form>

          {/* Privacy Note */}
          <p className="text-xs text-center text-muted-foreground mt-4">
            This information helps personalize your experience. You can update it
            anytime in settings.
          </p>
        </CardContent>
      </Card>
    </motion.div>
  );
}
