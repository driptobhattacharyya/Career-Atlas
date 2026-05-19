import { createFileRoute } from "@tanstack/react-router";
import { CheckCircle2, Circle, Lock, Clock, BookOpen, Sparkles, Loader2, RotateCcw, SkipForward } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useRoadmap, useUpdateMilestoneStatus } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import type { MilestoneRow, MilestoneStatus } from "@/lib/api";

export const Route = createFileRoute("/_app/roadmap")({
  head: () => ({
    meta: [
      { title: "Roadmap — CareerAtlas" },
      {
        name: "description",
        content:
          "Your phased, week-by-week roadmap of skills, courses, and side projects toward your target role.",
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

function Roadmap() {
  const roleId = selectedRoleId();
  const { data: roadmap = [], isLoading } = useRoadmap(roleId);

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  const completed = roadmap.filter((m) => m.status === "completed").length;
  const totalWeeks = roadmap.reduce(
    (sum, m) => sum + (m.estimated_weeks ?? 0),
    0,
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
          Your roadmap
        </h1>
        <p className="mt-2 text-muted-foreground">
          {completed} of {roadmap.length} milestones complete · ~{totalWeeks} weeks total
        </p>
      </div>

      <div className="relative">
        {roadmap.length > 0 && (
          <div
            className="absolute left-5 top-2 bottom-2 w-px bg-border md:left-7"
            aria-hidden
          />
        )}

        <ol className="space-y-6">
          {roadmap.map((m, i) => (
            <MilestoneCard key={m.id} milestone={m} index={i + 1} />
          ))}
          {roadmap.length === 0 && (
            <p className="text-sm text-muted-foreground border border-dashed p-8 text-center rounded-xl bg-card">
              No roadmap generated yet.
            </p>
          )}
        </ol>
      </div>
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
      : milestone.status === "skipped"
      ? "bg-muted text-muted-foreground"
      : "bg-muted text-muted-foreground";

  return (
    <li className="relative pl-14 md:pl-20">
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
                <BookOpen className="h-3.5 w-3.5" /> Courses
              </h4>
              <ul className="mt-3 space-y-2">
                {milestone.courses.map((c: any) => (
                  <li
                    key={c.title}
                    className="flex items-start justify-between gap-3 text-sm"
                  >
                    <div className="min-w-0">
                      <a
                        href={c.url || "#"}
                        target="_blank"
                        rel="noreferrer"
                        className="truncate font-medium hover:underline"
                      >
                        {c.title}
                      </a>
                      <p className="text-xs text-muted-foreground">{c.provider}</p>
                    </div>
                    <span className="shrink-0 text-xs text-muted-foreground">{c.duration}</span>
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
            <p className="mt-1 text-xs text-muted-foreground">{milestone.project?.description}</p>

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
    </li>
  );
}
