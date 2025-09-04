'use client';

import React, { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, ChevronLeft, Sparkles, Search, Star } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";

/** ---- mock data for now ---- */
const PARENTS = [
  { id: "social", label: "Social Life" },
  { id: "academics", label: "Academics" },
  { id: "residence", label: "Residence" },
  { id: "food", label: "Food" },
  { id: "clubs", label: "Clubs & Opps" },
];

const CHILDREN: Record<string, { id: string; label: string }[]> = {
  social: [
    { id: "party", label: "Party Scene" },
    { id: "events", label: "Campus Events" },
    { id: "intramurals", label: "Intramurals" },
  ],
  residence: [
    { id: "double_rooms", label: "Double Rooms" },
    { id: "lighting", label: "Lighting" },
    { id: "common_spaces", label: "Common Spaces" },
  ],
  academics: [
    { id: "research", label: "Research" },
    { id: "rigor", label: "Rigor" },
    { id: "prof_support", label: "Prof Support" },
  ],
  food: [
    { id: "variety", label: "Variety" },
    { id: "quality", label: "Quality" },
    { id: "hours", label: "Late Hours" },
  ],
  clubs: [
    { id: "count", label: "Many Clubs" },
    { id: "career", label: "Career Societies" },
    { id: "sports", label: "Sports Clubs" },
  ],
};

const MOCK_RESULTS = [
  { id: "trinity",  name: "Trinity College",  score: 0.86, why: ["Residence: Lighting", "Food: Quality", "Social: Moderate"] },
  { id: "innis",    name: "Innis College",    score: 0.79, why: ["Residence: Doubles", "Social: Events"] },
  { id: "victoria", name: "Victoria College", score: 0.72, why: ["Food: Variety", "Clubs: Career"] },
];

const fadeY = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
  transition: { duration: 0.2 },
};

function Section({ title, description, children }: { title: string; description?: string; children: React.ReactNode }) {
  return (
    <Card className="w-full shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl">{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function RateMyCollegeWizard() {
  const [step, setStep] = useState<1 | 2 | 3 | 4>(1);
  const [weights, setWeights] = useState<Record<string, number>>({
    social: 60, academics: 55, residence: 80, food: 40, clubs: 50,
  });
  const [chosenParent, setChosenParent] = useState<string | null>("residence");
  const [childAnswers, setChildAnswers] = useState<Record<string, string>>({});
  const [freeText, setFreeText] = useState("");

  const progress = useMemo(() => (step - 1) * 33 + 1, [step]);

  const onWeightChange = (id: string, val: number[]) => {
    setWeights((w) => ({ ...w, [id]: val[0] }));
  };

  const selectParent = (id: string) => setChosenParent(id);

  const answerChild = (childId: string, ans: "yes" | "no" | "skip") => {
    setChildAnswers((c) => ({ ...c, [childId]: ans }));
  };

  const startSession = async () => {
    // later: POST /start_session
    setStep(2);
  };

  const nextStep = () => setStep((s) => Math.min(4, (s + 1) as any));
  const prevStep = () => setStep((s) => Math.max(1, (s - 1) as any));

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          <h1 className="text-2xl font-semibold">RateMyCollege – Guided Recommender</h1>
        </div>
        <div className="w-56"><Progress value={progress} /></div>
      </div>

      <AnimatePresence mode="wait">
        {step === 1 && (
          <motion.div key="step1" {...fadeY}>
            <Section title="What do you care about most?" description="Adjust sliders to tell us how important each area is.">
              <div className="grid md:grid-cols-2 gap-6">
                {PARENTS.map((p) => (
                  <div key={p.id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-medium">{p.label}</span>
                      <Badge variant="secondary">{weights[p.id]}%</Badge>
                    </div>
                    <Slider value={[weights[p.id]]} max={100} step={1} onValueChange={(v) => onWeightChange(p.id, v)} />
                  </div>
                ))}
              </div>

              <div className="flex items-center justify-end gap-3 mt-6">
                <Button variant="outline" onClick={() => setWeights({ social: 50, academics: 50, residence: 50, food: 50, clubs: 50 })}>
                  Reset
                </Button>
                <Button onClick={startSession}>Continue <ChevronRight className="ml-1 h-4 w-4" /></Button>
              </div>
            </Section>
          </motion.div>
        )}

        {step === 2 && (
          <motion.div key="step2" {...fadeY} className="space-y-6">
            <Section title="Drill down" description="Pick a category to refine, then answer a few quick questions.">
              <div className="flex flex-wrap gap-2 mb-4">
                {PARENTS.map((p) => (
                  <Button key={p.id} size="sm" variant={chosenParent === p.id ? "default" : "outline"} onClick={() => selectParent(p.id)}>
                    {p.label}
                  </Button>
                ))}
              </div>

              {chosenParent && (
                <div className="grid gap-4 md:grid-cols-3">
                  {CHILDREN[chosenParent].map((c) => (
                    <Card key={c.id} className="border-dashed">
                      <CardHeader className="pb-2">
                        <CardTitle className="text-base">{c.label}</CardTitle>
                        <CardDescription>Does this matter to you?</CardDescription>
                      </CardHeader>
                      <CardContent className="flex gap-2">
                        <Button size="sm" variant={childAnswers[c.id] === "yes" ? "default" : "secondary"} onClick={() => answerChild(c.id, "yes")}>Yes</Button>
                        <Button size="sm" variant={childAnswers[c.id] === "no" ? "default" : "secondary"} onClick={() => answerChild(c.id, "no")}>No</Button>
                        <Button size="sm" variant={childAnswers[c.id] === "skip" ? "default" : "secondary"} onClick={() => answerChild(c.id, "skip")}>Skip</Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}

              <div className="flex items-center justify-between mt-6">
                <Button variant="ghost" onClick={prevStep}><ChevronLeft className="mr-1 h-4 w-4" />Back</Button>
                <Button onClick={nextStep}>Continue <ChevronRight className="ml-1 h-4 w-4" /></Button>
              </div>
            </Section>
          </motion.div>
        )}

        {step === 3 && (
          <motion.div key="step3" {...fadeY}>
            <Section title="Anything else?" description="Optional: tell us specifics and we'll factor it in.">
              <div className="flex items-center gap-2">
                <Search className="h-4 w-4" />
                <Input placeholder="e.g., bright dorms near the library" value={freeText} onChange={(e) => setFreeText(e.target.value)} />
              </div>

              <div className="flex items-center justify-between mt-6">
                <Button variant="ghost" onClick={prevStep}><ChevronLeft className="mr-1 h-4 w-4" />Back</Button>
                <div className="flex gap-2">
                  <Button variant="secondary" onClick={() => setFreeText("")}>Skip</Button>
                  <Button onClick={nextStep}>See Results <ChevronRight className="ml-1 h-4 w-4" /></Button>
                </div>
              </div>
            </Section>
          </motion.div>
        )}

        {step === 4 && (
          <motion.div key="step4" {...fadeY} className="space-y-6">
            <Section title="Your Matches" description="Top colleges based on your preferences and reviews.">
              <div className="grid gap-4">
                {MOCK_RESULTS.map((r, idx) => (
                  <Card key={r.id} className="hover:shadow-md transition-all">
                    <CardHeader className="pb-3 flex-row items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">{idx + 1}. {r.name}</CardTitle>
                        <CardDescription>Why: {r.why.join(" · ")}</CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Star className="h-4 w-4" />
                        <span className="text-sm font-medium">{(r.score * 100).toFixed(0)}%</span>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-primary" style={{ width: `${r.score * 100}%` }} />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              <div className="flex items-center justify-between mt-4">
                <Button variant="ghost" onClick={() => setStep(2)}><ChevronLeft className="mr-1 h-4 w-4" />Refine</Button>
                <div className="text-sm text-muted-foreground">
                  Transparency: scores combine aspect signals from reviews with your stated preferences.
                </div>
              </div>
            </Section>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Page() {
  return <RateMyCollegeWizard />;
}
