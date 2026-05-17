import { createFileRoute } from "@tanstack/react-router";
import { Plus, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useGapAnalysis, useProfile, useTargetRoles } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

export const Route = createFileRoute("/_app/gaps")({
  head: () => ({
    meta: [
      { title: "Skill gaps - CareerAtlas" },
      { name: "description", content: "Ranked skill gaps for your target role, with prerequisites and the why behind each." },
    ],
  }),
  component: Gaps,
});

const difficultyStyles: Record<string, string> = {
  Easy: "bg-success/15 text-success",
  Medium: "bg-warm/40 text-warm-foreground",
  Hard: "bg-coral/15 text-coral",
};

function Gaps() {
  const isBrowser = typeof window !== "undefined";
  const { data: profile } = useProfile();
  const { data: roles = [] } = useTargetRoles();
  const { data: gaps = [], isLoading } = useGapAnalysis();

  const explainability = (() => {
    if (!isBrowser) return null;
    const raw = window.localStorage.getItem("careeratlas:last_gap_response");
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw);
      return parsed?.explainability || null;
    } catch {
      return null;
    }
  })();

  const sorted = [...gaps].sort((a: any, b: any) => b.relevance - a.relevance);
  const localRoleTitle = isBrowser ? window.localStorage.getItem("careeratlas:selected_role_title") : null;
  const targetRole =
    roles.find((r: any) => r.id === profile?.target_role_id)?.title ||
    profile?.target_role_title ||
    localRoleTitle ||
    "Target Role";

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Skill gap analysis</h1>
        <p className="mt-2 text-muted-foreground">
          The skills standing between you and a typical <span className="font-medium text-foreground">{targetRole}</span> offer, ranked by impact.
        </p>
      </div>

      <ol className="space-y-4">
        {sorted.map((g: any, i: number) => (
          <li key={g.skill} className="rounded-3xl border border-border bg-card p-6 shadow-soft transition-shadow hover:shadow-warm">
            <div className="flex flex-wrap items-start gap-4">
              <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-primary text-primary-foreground font-display font-bold">
                {i + 1}
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h3 className="font-display text-lg font-semibold">{g.skill}</h3>
                  <span className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                    {g.category}
                  </span>
                  <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider", difficultyStyles[g.difficulty] || difficultyStyles.Medium)}>
                    {g.difficulty}
                  </span>
                </div>
                <p className="mt-2 text-sm text-muted-foreground">{g.why}</p>

                {g.prerequisites && g.prerequisites.length > 0 && (
                  <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                    <span className="text-muted-foreground">Prereqs:</span>
                    {g.prerequisites.map((p: string, idx: number) => (
                      <span key={p} className="flex items-center gap-1">
                        <span className="rounded-full border border-border px-2 py-0.5 text-foreground">{p}</span>
                        {idx < g.prerequisites.length - 1 && <ArrowRight className="h-3 w-3 text-muted-foreground" />}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div className="flex w-full flex-col items-end gap-3 sm:w-auto">
                <RelevanceMeter value={g.relevance} />
                <Button
                  size="sm"
                  className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90"
                  onClick={() => toast.success("Added to roadmap", { description: g.skill })}
                >
                  <Plus className="mr-1 h-4 w-4" /> Add to roadmap
                </Button>
              </div>
            </div>
          </li>
        ))}
        {sorted.length === 0 && (
          <p className="text-sm text-muted-foreground border border-dashed p-8 text-center rounded-xl bg-card">No skill gaps found!</p>
        )}
      </ol>

      {explainability && (
        <section className="rounded-3xl border border-border bg-card p-6 shadow-soft">
          <h2 className="font-display text-xl font-semibold">Why these gaps?</h2>
          <p className="mt-1 text-sm text-muted-foreground">Backend explainability from the gap analysis agent.</p>
          {typeof explainability.input_skill_count === "number" && (
            <p className="mt-2 text-xs text-muted-foreground">Input skills analyzed: {explainability.input_skill_count}</p>
          )}
          {explainability.note && (
            <p className="mt-2 text-xs text-muted-foreground">{explainability.note}</p>
          )}
          {(explainability.retrieved_requirements || []).length > 0 && (
            <ul className="mt-4 space-y-2">
              {(explainability.retrieved_requirements || []).slice(0, 8).map((req: any, idx: number) => (
                <li key={`${req.skill_name}-${idx}`} className="rounded-xl border border-border/60 bg-background p-3">
                  <p className="text-sm font-medium">{req.skill_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {req.category} - {req.level_required} - score {Number(req.relevance_score || 0).toFixed(3)}
                  </p>
                  {req.prerequisites?.length > 0 && (
                    <p className="mt-1 text-xs text-muted-foreground">Prerequisites: {req.prerequisites.join(", ")}</p>
                  )}
                </li>
              ))}
            </ul>
          )}
          {(!explainability.retrieved_requirements || explainability.retrieved_requirements.length === 0) && (
            <p className="mt-3 text-xs text-muted-foreground">
              Retrieval trace is unavailable for this cached run. Re-run analysis to see the full trace.
            </p>
          )}
        </section>
      )}
    </div>
  );
}

function RelevanceMeter({ value }: { value: number }) {
  return (
    <div className="w-full sm:w-44">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">Relevance</span>
        <span className="font-semibold text-coral">{value}%</span>
      </div>
      <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-coral transition-all" style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
