import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  CheckCircle2,
  Circle,
  Lock,
  Clock,
  BookOpen,
  Sparkles,
  Loader2,
  RotateCcw,
  SkipForward,
  Wand2,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import {
  useRoadmap,
  useLatestPathway,
  useStartDeepResearch,
  useUpdateMilestoneStatus,
  useProfile,
} from "@/hooks/queries";
import { NoProfileView } from "@/components/no-profile-view";
import { ApiError } from "@/lib/api";
import type { JudgeVerdict, ValidationResult, MilestoneRow, MilestoneStatus } from "@/lib/api";
import { cn } from "@/lib/utils";
import { listStagger, fadeUpSm } from "@/lib/motion";

export const Route = createFileRoute("/_app/roadmap")({
  head: () => ({
    meta: [
      { title: "Roadmap — CareerAtlas" },
      {
        name: "description",
        content:
          "Web-grounded, citation-backed learning roadmap with progress tracking toward your target role.",
      },
    ],
  }),
  component: Roadmap,
});

const phaseColors: Record<string, string> = {
  Foundations: "bg-success/15 text-success border-success/30",
  Intermediate: "bg-primary-soft text-primary border-primary/20",
  Advanced: "bg-coral/15 text-coral border-coral/30",
};

const selectedRoleId = () =>
  (typeof window !== "undefined" &&
    window.localStorage.getItem("careeratlas:selected_role_id")) ||
  undefined;

const selectedRoleTitle = () =>
  (typeof window !== "undefined" &&
    window.localStorage.getItem("careeratlas:selected_role_title")) ||
  undefined;

function Roadmap() {
  const { data: profile, isLoading: profileLoading } = useProfile();
  const roleId = selectedRoleId();
  const { data: roadmap = [], isLoading } = useRoadmap(roleId);
  const { data: pathwayData } = useLatestPathway(roleId);
  const startMutation = useStartDeepResearch();
  const [busy, setBusy] = useState(false);
  const [gapHint, setGapHint] = useState(false);

  const runResearch = async () => {
    if (!roleId) {
      toast.error("Pick a target role first");
      return;
    }
    setBusy(true);
    try {
      await startMutation.mutateAsync({ roleId, maxIter: 3 });
      setGapHint(false);
      toast.success("Deep research complete");
    } catch (err: any) {
      const noGaps =
        err instanceof ApiError && err.status === 400 && /gap/i.test(err.detail);
      setGapHint(noGaps);
      toast.error("Research failed", { description: err?.message });
    } finally {
      setBusy(false);
    }
  };

  if (isLoading || profileLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!profile) return <NoProfileView feature="your roadmap" />;

  const verdict = pathwayData?.quality_verdict ?? null;
  const validation = pathwayData?.validation ?? null;
  const sources = pathwayData?.sources ?? [];
  const rationale = pathwayData?.pathway?.rationale;
  const targetRole =
    pathwayData?.target_role || selectedRoleTitle() || "your target role";

  const completed = roadmap.filter((m) => m.status === "completed").length;
  const totalWeeks = roadmap.reduce((sum, m) => sum + (m.estimated_weeks ?? 0), 0);
  const researching = busy || startMutation.isPending;

  return (
    <motion.div
      className="space-y-8"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Learning roadmap
          </h1>
          <p className="mt-2 text-muted-foreground">
            Web-grounded, citation-backed plan for{" "}
            <span className="font-medium text-foreground">{targetRole}</span>.
            {roadmap.length > 0 && (
              <>
                {" "}
                {completed} of {roadmap.length} done · ~{totalWeeks} weeks total.
              </>
            )}
          </p>
        </div>
        <Button
          onClick={runResearch}
          disabled={researching}
          className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm"
        >
          {researching ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Researching…
            </>
          ) : (
            <>
              <Wand2 className="mr-2 h-4 w-4" />{" "}
              {roadmap.length > 0 ? "Re-run research" : "Run deep research"}
            </>
          )}
        </Button>
      </div>

      {gapHint && (
        <div className="rounded-3xl border border-coral/40 bg-coral/5 p-6">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
            <ShieldAlert className="h-5 w-5 text-coral" /> Gap analysis needed
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            The roadmap builds on your skill gaps for this role, but none were found.
            Run gap analysis for this target role first, then come back here.
          </p>
          <a
            href="/onboarding"
            className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-coral px-4 py-2 text-sm font-medium text-coral-foreground hover:bg-coral/90"
          >
            <Wand2 className="h-4 w-4" /> Run gap analysis
          </a>
        </div>
      )}

      {roadmap.length === 0 && !gapHint && (
        <div className="rounded-3xl border border-dashed border-border bg-card p-10 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-coral" />
          <p className="mt-3 text-sm text-muted-foreground">
            No roadmap yet. Deep research takes ~60s and produces a citation-backed,
            trackable plan.
          </p>
        </div>
      )}

      {rationale && (
        <div className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft">
          <h2 className="font-display text-lg font-semibold">Why this ordering</h2>
          <p className="mt-2 text-sm text-muted-foreground">{rationale}</p>
        </div>
      )}

      {verdict && <QualityPanel verdict={verdict} validation={validation} />}

      {roadmap.length > 0 && (
        <div className="relative">
          <div
            className="absolute left-5 top-2 bottom-2 w-px bg-border md:left-7"
            aria-hidden
          />
          <motion.ol
            className="space-y-6"
            variants={listStagger}
            initial="hidden"
            animate="show"
          >
            {roadmap.map((m, i) => (
              <MilestoneCard key={m.id} milestone={m} index={i + 1} />
            ))}
          </motion.ol>
        </div>
      )}

      {sources.length > 0 && (
        <section className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft">
          <h2 className="font-display text-lg font-semibold">
            Sources ({sources.length})
          </h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {sources.slice(0, 24).map((url) => (
              <li key={url} className="truncate text-xs">
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1 text-muted-foreground hover:text-foreground hover:underline"
                >
                  <ExternalLink className="h-3 w-3 shrink-0" />
                  <span className="truncate">{url}</span>
                </a>
              </li>
            ))}
          </ul>
        </section>
      )}
    </motion.div>
  );
}

function QualityPanel({
  verdict,
  validation,
}: {
  verdict: JudgeVerdict;
  validation: ValidationResult | null;
}) {
  const passed = verdict.pass_fail === "pass";
  return (
    <div className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={cn(
            "grid h-12 w-12 place-items-center rounded-2xl text-lg font-bold",
            passed ? "bg-success/15 text-success" : "bg-coral/15 text-coral",
          )}
        >
          {verdict.overall_score.toFixed(1)}
        </span>
        <div>
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
            {passed ? (
              <ShieldCheck className="h-4 w-4 text-success" />
            ) : (
              <ShieldAlert className="h-4 w-4 text-coral" />
            )}
            Quality evaluation
          </h2>
          <p className="text-xs text-muted-foreground">
            LLM-as-judge rubric · {verdict.pass_fail.toUpperCase()} · confidence{" "}
            {verdict.confidence}
          </p>
        </div>
        {validation && (
          <span className="ml-auto text-xs text-muted-foreground">
            {validation.kept}/{validation.checked} links verified
            {validation.dropped.length > 0 && ` · ${validation.dropped.length} dropped`}
          </span>
        )}
      </div>

      <div className="mt-5 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {verdict.rubric_scores.map((s) => (
          <div key={s.criterion} className="rounded-xl border border-border/60 bg-background p-3">
            <div className="flex items-center justify-between text-xs">
              <span className="font-medium capitalize">{s.criterion.replace(/_/g, " ")}</span>
              <span
                className={cn(
                  "font-semibold",
                  s.score >= 4 ? "text-success" : s.score >= 3 ? "text-warm-foreground" : "text-coral",
                )}
              >
                {s.score}/5
              </span>
            </div>
            <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-muted">
              <div
                className={cn(
                  "h-full rounded-full",
                  s.score >= 4 ? "bg-success" : s.score >= 3 ? "bg-warm" : "bg-coral",
                )}
                style={{ width: `${(s.score / 5) * 100}%` }}
              />
            </div>
          </div>
        ))}
      </div>

      {verdict.weaknesses.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Weaknesses
          </h3>
          <ul className="mt-2 space-y-1">
            {verdict.weaknesses.map((w) => (
              <li key={w} className="text-xs text-muted-foreground">• {w}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function MilestoneCard({ milestone, index }: { milestone: MilestoneRow; index: number }) {
  const updateMutation = useUpdateMilestoneStatus();

  const setStatus = (status: MilestoneStatus) => {
    updateMutation.mutate(
      { id: milestone.id, status },
      {
        onSuccess: () => {
          toast.success(`Marked ${status.replace("_", " ")}`, {
            description: milestone.skill ?? milestone.title ?? undefined,
          });
        },
        onError: (err: any) =>
          toast.error("Update failed", { description: err?.message }),
      },
    );
  };

  const StatusIcon =
    milestone.status === "completed"
      ? CheckCircle2
      : milestone.status === "in_progress"
      ? Circle
      : milestone.status === "skipped"
      ? SkipForward
      : Lock;

  const statusColor =
    milestone.status === "completed"
      ? "bg-success text-success-foreground"
      : milestone.status === "in_progress"
      ? "bg-coral text-coral-foreground animate-pulse"
      : "bg-muted text-muted-foreground";

  return (
    <motion.li variants={fadeUpSm} className="relative pl-14 md:pl-20">
      <span
        className={cn(
          "absolute left-0 top-1 grid h-10 w-10 place-items-center rounded-full shadow-soft md:h-14 md:w-14",
          statusColor,
        )}
      >
        <StatusIcon className="h-5 w-5 md:h-6 md:w-6" />
      </span>

      <div
        className={cn(
          "rounded-3xl border bg-card p-6 shadow-soft transition-shadow",
          milestone.status === "locked" ? "opacity-70" : "hover:shadow-warm",
        )}
      >
        <div className="flex flex-wrap items-center gap-3">
          <span
            className={cn(
              "rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
              phaseColors[milestone.phase ?? "Intermediate"] || phaseColors["Intermediate"],
            )}
          >
            {milestone.phase}
          </span>
          <span className="text-xs text-muted-foreground">Step {index}</span>
          <span className="ml-auto flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="h-3.5 w-3.5" /> ~{milestone.estimated_weeks ?? 0} weeks
          </span>
        </div>

        <h3 className="mt-3 font-display text-xl font-semibold">{milestone.title}</h3>
        <p className="mt-2 text-sm text-muted-foreground">{milestone.description}</p>

        {milestone.completed_at && milestone.status === "completed" && (
          <p className="mt-2 text-xs text-success">
            Completed {new Date(milestone.completed_at).toLocaleDateString()}
          </p>
        )}

        <div className="mt-5 grid gap-4 lg:grid-cols-2">
          {milestone.courses && milestone.courses.length > 0 && (
            <div className="rounded-2xl border border-border/60 bg-background p-4">
              <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <BookOpen className="h-3.5 w-3.5" /> Resources
              </h4>
              <ul className="mt-3 space-y-2">
                {milestone.courses.map((r: any, idx: number) => (
                  <li key={`${r.url}-${idx}`} className="text-sm">
                    <a
                      href={r.url || "#"}
                      target="_blank"
                      rel="noreferrer"
                      className="font-medium hover:underline"
                    >
                      {r.title}
                    </a>
                    <p className="text-xs text-muted-foreground">
                      {[r.kind, r.provider].filter(Boolean).join(" · ")}
                    </p>
                    {r.why && (
                      <p className="mt-1 text-xs text-muted-foreground">{r.why}</p>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="rounded-2xl border border-border/60 bg-background p-4">
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5" /> Suggested project
            </h4>
            <p className="mt-3 text-sm font-medium">{milestone.project?.title}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {milestone.project?.description}
            </p>

            <ul className="mt-4 space-y-1.5">
              {milestone.checklist?.map((item) => (
                <li
                  key={item}
                  className="flex items-start gap-2 text-xs text-muted-foreground"
                >
                  <span
                    className={cn(
                      "mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded border",
                      milestone.status === "completed"
                        ? "border-success bg-success text-success-foreground"
                        : "border-border",
                    )}
                  >
                    {milestone.status === "completed" && (
                      <CheckCircle2 className="h-3 w-3" />
                    )}
                  </span>
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-2">
          {milestone.status !== "completed" && (
            <Button
              size="sm"
              onClick={() => setStatus("completed")}
              disabled={updateMutation.isPending}
              className="rounded-full bg-success text-success-foreground hover:bg-success/90"
            >
              <CheckCircle2 className="mr-1.5 h-4 w-4" /> Mark complete
            </Button>
          )}
          {milestone.status === "locked" && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setStatus("in_progress")}
              disabled={updateMutation.isPending}
              className="rounded-full"
            >
              <Circle className="mr-1.5 h-4 w-4" /> Start
            </Button>
          )}
          {milestone.status === "in_progress" && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setStatus("locked")}
              disabled={updateMutation.isPending}
              className="rounded-full"
            >
              <Lock className="mr-1.5 h-4 w-4" /> Lock
            </Button>
          )}
          {milestone.status === "completed" && (
            <Button
              size="sm"
              variant="outline"
              onClick={() => setStatus("in_progress")}
              disabled={updateMutation.isPending}
              className="rounded-full"
            >
              <RotateCcw className="mr-1.5 h-4 w-4" /> Reopen
            </Button>
          )}
          {milestone.status !== "skipped" && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setStatus("skipped")}
              disabled={updateMutation.isPending}
              className="rounded-full text-muted-foreground"
            >
              Skip
            </Button>
          )}
        </div>
      </div>
    </motion.li>
  );
}
