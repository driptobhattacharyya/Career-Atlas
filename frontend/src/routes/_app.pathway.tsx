import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  Loader2,
  Sparkles,
  BookOpen,
  ListChecks,
  Wand2,
  ExternalLink,
  ShieldCheck,
  ShieldAlert,
} from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { useLatestPathway, useStartDeepResearch } from "@/hooks/queries";
import type { JudgeVerdict, ValidationResult } from "@/lib/api";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/pathway")({
  head: () => ({
    meta: [
      { title: "Pathway — CareerAtlas" },
      {
        name: "description",
        content:
          "Deep research-backed learning pathway with cited resources, projects, and milestones.",
      },
    ],
  }),
  component: PathwayPage,
});

const phaseStyles: Record<string, string> = {
  Foundations: "bg-success/15 text-success border-success/30",
  Intermediate: "bg-primary-soft text-primary border-primary/20",
  Advanced: "bg-coral/15 text-coral border-coral/30",
};

function selectedRoleSlug() {
  if (typeof window === "undefined") return undefined;
  const title = window.localStorage.getItem("careeratlas:selected_role_title");
  if (!title) return undefined;
  return title
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

function PathwayPage() {
  const roleSlug = selectedRoleSlug();
  const roleId =
    (typeof window !== "undefined" &&
      window.localStorage.getItem("careeratlas:selected_role_id")) ||
    undefined;
  const { data, isLoading, refetch } = useLatestPathway(roleSlug);
  const startMutation = useStartDeepResearch();
  const [busy, setBusy] = useState(false);

  const runResearch = async () => {
    if (!roleId) {
      toast.error("Pick a target role first");
      return;
    }
    setBusy(true);
    try {
      await startMutation.mutateAsync({ roleId, maxIter: 3 });
      toast.success("Deep research complete");
      await refetch();
    } catch (err: any) {
      toast.error("Research failed", { description: err?.message });
    } finally {
      setBusy(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const pathway = data?.pathway;
  const sources = data?.sources ?? [];
  const verdict = data?.quality_verdict ?? null;
  const validation = data?.validation ?? null;

  return (
    <div className="space-y-8">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Learning pathway
          </h1>
          <p className="mt-2 text-muted-foreground">
            Web-grounded, citation-backed plan for{" "}
            <span className="font-medium text-foreground">
              {pathway?.target_role || "your target role"}
            </span>
            .
          </p>
        </div>
        <Button
          onClick={runResearch}
          disabled={busy || startMutation.isPending}
          className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm"
        >
          {busy || startMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Researching…
            </>
          ) : (
            <>
              <Wand2 className="mr-2 h-4 w-4" /> {pathway ? "Re-run research" : "Run deep research"}
            </>
          )}
        </Button>
      </div>

      {!pathway && (
        <div className="rounded-3xl border border-dashed border-border bg-card p-10 text-center">
          <Sparkles className="mx-auto h-8 w-8 text-coral" />
          <p className="mt-3 text-sm text-muted-foreground">
            No pathway generated yet. Deep research takes ~60s and produces a citation-backed plan.
          </p>
        </div>
      )}

      {pathway && (
        <>
          <div className="rounded-3xl border border-border bg-card p-6 shadow-soft">
            <h2 className="font-display text-lg font-semibold">Why this ordering</h2>
            <p className="mt-2 text-sm text-muted-foreground">{pathway.rationale}</p>
          </div>

          {verdict && <QualityPanel verdict={verdict} validation={validation} />}

          <ol className="space-y-6">
            {(pathway.milestones || []).map((m: any, i: number) => (
              <PathwayMilestoneCard key={`${m.skill}-${i}`} milestone={m} index={i + 1} />
            ))}
          </ol>

          {sources.length > 0 && (
            <section className="rounded-3xl border border-border bg-card p-6 shadow-soft">
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
        </>
      )}
    </div>
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
    <div className="rounded-3xl border border-border bg-card p-6 shadow-soft">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={cn(
            "grid h-12 w-12 place-items-center rounded-2xl text-lg font-bold",
            passed
              ? "bg-success/15 text-success"
              : "bg-coral/15 text-coral",
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
            LLM-as-judge rubric · {verdict.pass_fail.toUpperCase()} · confidence {verdict.confidence}
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

function PathwayMilestoneCard({
  milestone,
  index,
}: {
  milestone: any;
  index: number;
}) {
  return (
    <li className="rounded-3xl border border-border bg-card p-6 shadow-soft">
      <div className="flex flex-wrap items-center gap-3">
        <span
          className={cn(
            "rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
            phaseStyles[milestone.phase] || phaseStyles["Intermediate"],
          )}
        >
          {milestone.phase}
        </span>
        <span className="text-xs text-muted-foreground">Step {index}</span>
        <span className="ml-auto text-xs text-muted-foreground">
          ~{milestone.estimated_weeks} weeks
        </span>
      </div>

      <h3 className="mt-3 font-display text-xl font-semibold">{milestone.skill}</h3>
      <p className="mt-1 text-sm text-muted-foreground">{milestone.objective}</p>

      <div className="mt-5 grid gap-4 lg:grid-cols-2">
        {milestone.resources?.length > 0 && (
          <div className="rounded-2xl border border-border/60 bg-background p-4">
            <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              <BookOpen className="h-3.5 w-3.5" /> Resources
            </h4>
            <ul className="mt-3 space-y-2">
              {milestone.resources.map((r: any, idx: number) => (
                <li key={`${r.url}-${idx}`} className="text-sm">
                  <a
                    href={r.url}
                    target="_blank"
                    rel="noreferrer"
                    className="font-medium hover:underline"
                  >
                    {r.title}
                  </a>
                  <p className="text-xs text-muted-foreground">
                    {r.kind} · {r.provider}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground">{r.why}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="rounded-2xl border border-border/60 bg-background p-4">
          <h4 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <ListChecks className="h-3.5 w-3.5" /> Checklist
          </h4>
          <ul className="mt-3 space-y-1.5">
            {(milestone.checklist || []).map((item: string) => (
              <li
                key={item}
                className="flex items-start gap-2 text-xs text-muted-foreground"
              >
                <span className="mt-0.5 h-4 w-4 shrink-0 rounded border border-border" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
          {milestone.mini_project && (
            <div className="mt-4 rounded-xl border border-border/60 bg-muted/40 p-3">
              <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Mini project
              </p>
              <p className="mt-1 text-sm">{milestone.mini_project}</p>
            </div>
          )}
        </div>
      </div>
    </li>
  );
}
