import { useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  AlertCircle,
  CheckCircle2,
  Circle,
  Github,
  Loader2,
  MinusCircle,
  RotateCcw,
  Sparkles,
  X,
} from "lucide-react";
import { motion } from "motion/react";

import { Button } from "@/components/ui/button";
import { STEP_LABELS, useOnboardingPipeline } from "@/context/onboarding-pipeline-context";
import {
  STEP_DEPENDENCIES,
  STEP_IDS,
  isPipelineComplete,
  type StepId,
  type StepState,
} from "@/lib/onboarding-pipeline";
import { cn } from "@/lib/utils";
import { fadeUp } from "@/lib/motion";

/** Set by the wizard for brand-new users; cleared when the card is dismissed. */
export const GITHUB_OFFER_KEY = "careeratlas:github_offer";

const RUNNING_HINT: Record<StepId, string> = {
  profile: "Checking your resume and saving your target role.",
  gaps: "Comparing your skills with what the role needs.",
  roadmap: "Researching courses and projects — this can take a couple of minutes.",
  jobs: "Searching live openings and ranking them by fit.",
};

function stepHint(id: StepId, st: StepState, steps: Record<StepId, StepState>): string {
  switch (st.status) {
    case "running":
      return RUNNING_HINT[id];
    case "done":
      return "Done";
    case "skipped":
      return "Not available for custom roles yet.";
    case "failed":
      return st.error || "Something went wrong.";
    case "pending": {
      const waitingOn = STEP_DEPENDENCIES[id].find(
        (d) => steps[d].status !== "done" && steps[d].status !== "skipped",
      );
      return waitingOn ? `Waiting for “${STEP_LABELS[waitingOn].toLowerCase()}”.` : "Queued";
    }
  }
}

function StepIcon({ status }: { status: StepState["status"] }) {
  switch (status) {
    case "running":
      return <Loader2 className="h-5 w-5 animate-spin text-primary" aria-hidden />;
    case "done":
      return <CheckCircle2 className="h-5 w-5 text-success" aria-hidden />;
    case "failed":
      return <AlertCircle className="h-5 w-5 text-coral" aria-hidden />;
    case "skipped":
      return <MinusCircle className="h-5 w-5 text-muted-foreground" aria-hidden />;
    default:
      return <Circle className="h-5 w-5 text-muted-foreground/50" aria-hidden />;
  }
}

const STATUS_TEXT: Record<StepState["status"], string> = {
  pending: "pending",
  running: "in progress",
  done: "done",
  failed: "failed",
  skipped: "skipped",
};

/**
 * Dashboard panel showing the real state of each background step. Renders
 * nothing when no pipeline run exists (returning users).
 */
export function PipelineProgressPanel() {
  const { snapshot, retry, dismiss } = useOnboardingPipeline();
  if (!snapshot.runId) return null;
  const complete = isPipelineComplete(snapshot);

  if (complete) {
    return (
      <motion.section
        variants={fadeUp}
        aria-label="Atlas setup"
        className="flex items-center gap-3 rounded-3xl border border-success/30 bg-success/5 p-4 shadow-soft"
      >
        <CheckCircle2 className="h-5 w-5 shrink-0 text-success" aria-hidden />
        <p className="flex-1 text-sm">
          <span className="font-medium">Your atlas is ready.</span>{" "}
          <span className="text-muted-foreground">
            Skill gaps, roadmap and job matches are up to date.
          </span>
        </p>
        <Button size="sm" variant="ghost" className="rounded-full" onClick={dismiss}>
          Dismiss
        </Button>
      </motion.section>
    );
  }

  return (
    <motion.section
      variants={fadeUp}
      aria-label="Atlas setup"
      className="rounded-3xl border border-border bg-card p-6 shadow-soft"
    >
      <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
        <Sparkles className="h-4 w-4 text-coral" /> Building your atlas
      </h2>
      <p className="mt-1 text-sm text-muted-foreground">
        This runs in the background — feel free to explore. Each page fills in as soon as its part
        is ready.
      </p>
      <ol className="mt-5 space-y-3">
        {STEP_IDS.map((id) => {
          const st = snapshot.steps[id];
          return (
            <li
              key={id}
              data-testid={`pipeline-step-${id}`}
              data-status={st.status}
              className={cn(
                "flex items-start gap-3 rounded-2xl border p-3",
                st.status === "failed"
                  ? "border-coral/40 bg-coral/5"
                  : "border-border/60 bg-background",
              )}
            >
              <span className="mt-0.5 shrink-0">
                <StepIcon status={st.status} />
              </span>
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    "text-sm font-medium",
                    st.status === "pending" && "text-muted-foreground",
                  )}
                >
                  {STEP_LABELS[id]}
                  <span className="sr-only"> — {STATUS_TEXT[st.status]}</span>
                </p>
                <p className="mt-0.5 text-xs text-muted-foreground">
                  {stepHint(id, st, snapshot.steps)}
                </p>
              </div>
              {st.status === "failed" && (
                <Button
                  size="sm"
                  variant="outline"
                  className="shrink-0 rounded-full"
                  onClick={() => retry(id)}
                >
                  <RotateCcw className="mr-1.5 h-3.5 w-3.5" /> Retry
                </Button>
              )}
            </li>
          );
        })}
      </ol>
    </motion.section>
  );
}

/** Shown on Gaps / Roadmap / Jobs while the pipeline is generating their data. */
export function PreparingState({ title, description }: { title: string; description: string }) {
  return (
    <div
      role="status"
      className="rounded-3xl border border-dashed border-border bg-card p-10 text-center"
    >
      <Loader2 className="mx-auto h-8 w-8 animate-spin text-coral" aria-hidden />
      <p className="mt-3 font-display text-lg font-semibold">{title}</p>
      <p className="mx-auto mt-1 max-w-md text-sm text-muted-foreground">{description}</p>
      <Link
        to="/dashboard"
        className="mt-4 inline-block text-xs font-medium text-primary hover:underline"
      >
        See progress on your dashboard →
      </Link>
    </div>
  );
}

/** Optional, dismissible GitHub prompt for new users (replaces the old wizard step). */
export function GithubOfferCard() {
  const [visible, setVisible] = useState(
    () => typeof window !== "undefined" && window.localStorage.getItem(GITHUB_OFFER_KEY) === "1",
  );
  if (!visible) return null;
  const dismiss = () => {
    window.localStorage.removeItem(GITHUB_OFFER_KEY);
    setVisible(false);
  };
  return (
    <motion.section
      variants={fadeUp}
      aria-label="Connect GitHub"
      className="relative flex flex-col gap-4 rounded-3xl border border-border bg-card p-6 shadow-soft sm:flex-row sm:items-center"
    >
      <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-primary-soft text-primary">
        <Github className="h-6 w-6" />
      </span>
      <div className="min-w-0 flex-1">
        <h2 className="font-display text-base font-semibold">Add skills proven by your code</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Optional: connect GitHub and we'll read your repositories to find skills and projects. You
          can do this anytime from the GitHub tab.
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <Button
          asChild
          size="sm"
          className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90"
          onClick={dismiss}
        >
          <Link to="/github">
            <Github className="mr-1.5 h-4 w-4" /> Connect GitHub
          </Link>
        </Button>
        <Button size="sm" variant="ghost" className="rounded-full" onClick={dismiss}>
          Not now
        </Button>
      </div>
      <button
        type="button"
        onClick={dismiss}
        aria-label="Dismiss GitHub suggestion"
        className="absolute right-3 top-3 grid h-7 w-7 place-items-center rounded-full text-muted-foreground hover:bg-muted sm:hidden"
      >
        <X className="h-4 w-4" />
      </button>
    </motion.section>
  );
}
