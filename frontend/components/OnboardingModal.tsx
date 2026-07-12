"use client";

import { useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { submitOnboarding, OnboardingPayload } from "../lib/api";
import { LogoBadge } from "./Logo";

type AnswerMap = Record<string, string | string[]>;

interface Step {
  key: keyof OnboardingPayload;
  question: string;
  kind: "text" | "choice" | "multi";
  options?: string[];
  placeholder?: string;
}

const STEPS: Step[] = [
  {
    key: "home_airport",
    question: "Which airport do you usually fly from?",
    kind: "text",
    placeholder: "e.g. LHR, or “London”",
  },
  {
    key: "trip_type",
    question: "What kind of trips do you take most?",
    kind: "choice",
    options: ["Leisure", "Business", "Both"],
  },
  {
    key: "budget_band",
    question: "What's your usual travel budget?",
    kind: "choice",
    options: ["Budget", "Mid-range", "Luxury"],
  },
  {
    key: "cabin_class",
    question: "Preferred cabin class?",
    kind: "choice",
    options: ["Economy", "Premium economy", "Business", "First"],
  },
  {
    key: "interests",
    question: "What draws you to a trip?",
    kind: "multi",
    options: [
      "Beaches", "Hiking & outdoors", "City breaks", "Food & drink",
      "Culture & museums", "Nightlife", "Road trips", "Wellness & spas",
    ],
  },
  {
    key: "travel_frequency",
    question: "How often do you travel?",
    kind: "choice",
    options: ["Rarely", "A few times a year", "Monthly or more"],
  },
  {
    key: "constraints",
    question: "Anything else SkyMind should know?",
    kind: "text",
    placeholder: "Dietary needs, accessibility, anything at all — optional",
  },
];

function chipStyle(active: boolean): React.CSSProperties {
  return active
    ? { background: "var(--accent)", color: "var(--on-accent)", borderColor: "var(--accent)" }
    : { background: "var(--surface-2)", color: "var(--text)", borderColor: "var(--border)" };
}

export default function OnboardingModal({ onComplete }: { onComplete: () => void }) {
  const [stepIndex, setStepIndex] = useState(0);
  const [answers, setAnswers] = useState<AnswerMap>({});
  const [submitting, setSubmitting] = useState(false);
  const step = STEPS[stepIndex];
  const isLast = stepIndex === STEPS.length - 1;

  const setAnswer = (value: string | string[]) =>
    setAnswers((a) => ({ ...a, [step.key]: value }));

  const finish = async () => {
    setSubmitting(true);
    try {
      await submitOnboarding(answers as OnboardingPayload);
      onComplete();
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => (isLast ? finish() : setStepIndex((i) => i + 1));

  const textValue = (answers[step.key] as string) || "";
  const multiValue = (answers[step.key] as string[]) || [];

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      style={{ background: "rgba(20, 17, 12, 0.55)" }}
    >
      <motion.div
        initial={{ opacity: 0, scale: 0.96, y: 10 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
        className="w-full max-w-lg rounded-3xl p-7 md:p-8 card max-h-[90vh] overflow-y-auto scrollbar-thin"
      >
        <div className="flex items-center gap-3 mb-7">
          <LogoBadge size={36} className="rounded-xl flex-shrink-0" />
          <div className="flex-1 flex gap-1.5">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className="h-1 flex-1 rounded-full transition-colors duration-300"
                style={{ background: i <= stepIndex ? "var(--accent)" : "var(--border)" }}
              />
            ))}
          </div>
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={stepIndex}
            initial={{ opacity: 0, x: 12 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -12 }}
            transition={{ duration: 0.2 }}
          >
            <h2 className="font-serif-italic text-2xl md:text-3xl mb-6" style={{ color: "var(--text)" }}>
              {step.question}
            </h2>

            {step.kind === "text" && (
              <input
                autoFocus
                value={textValue}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder={step.placeholder}
                className="w-full rounded-xl px-4 py-3.5 text-base outline-none border"
                style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
              />
            )}

            {step.kind === "choice" && (
              <div className="flex flex-wrap gap-2.5">
                {step.options!.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setAnswer(opt)}
                    className="px-4 py-2.5 rounded-full text-sm font-medium border transition-all duration-150"
                    style={chipStyle(textValue === opt)}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            )}

            {step.kind === "multi" && (
              <div className="flex flex-wrap gap-2.5">
                {step.options!.map((opt) => {
                  const active = multiValue.includes(opt);
                  return (
                    <button
                      key={opt}
                      type="button"
                      onClick={() =>
                        setAnswer(active ? multiValue.filter((o) => o !== opt) : [...multiValue, opt])
                      }
                      className="px-4 py-2.5 rounded-full text-sm font-medium border transition-all duration-150"
                      style={chipStyle(active)}
                    >
                      {opt}
                    </button>
                  );
                })}
              </div>
            )}
          </motion.div>
        </AnimatePresence>

        <div className="flex items-center justify-between mt-9">
          <button
            type="button"
            onClick={finish}
            disabled={submitting}
            className="text-sm font-medium disabled:opacity-50"
            style={{ color: "var(--muted)" }}
          >
            Skip for now
          </button>
          <div className="flex items-center gap-2">
            {stepIndex > 0 && (
              <button
                type="button"
                onClick={() => setStepIndex((i) => i - 1)}
                className="px-5 py-2.5 rounded-full text-sm font-semibold border"
                style={{ borderColor: "var(--border)", color: "var(--text)" }}
              >
                Back
              </button>
            )}
            <button
              type="button"
              onClick={handleNext}
              disabled={submitting}
              className="px-6 py-2.5 rounded-full text-sm font-semibold disabled:opacity-50"
              style={{ background: "var(--accent)", color: "var(--on-accent)" }}
            >
              {isLast ? (submitting ? "Saving…" : "Finish") : "Next"}
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
