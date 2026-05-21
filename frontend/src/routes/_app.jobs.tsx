import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, MapPin, X, Check, Loader2, BarChart3, ArrowUpRight } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useJobMatches, useProfile, useTargetRoles } from "@/hooks/queries";
import type { JobResult } from "@/lib/api";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { cacheJobSearchResponse, researchJobs } from "@/lib/api";

export const Route = createFileRoute("/_app/jobs")({
  head: () => ({
    meta: [
      { title: "Jobs - CareerAtlas" },
      { name: "description", content: "Real job matches ranked by fit, with the skills you have and the ones you're missing." },
    ],
  }),
  component: Jobs,
});

const seniorities = ["Intern", "Entry", "Junior", "Mid", "Senior"];

function Jobs() {
  const isBrowser = typeof window !== "undefined";
  const queryClient = useQueryClient();
  const [query, setQuery] = useState("");
  const [remoteOnly, setRemoteOnly] = useState(false);
  const [activeSeniority, setActiveSeniority] = useState<string>("All");
  const [openJob, setOpenJob] = useState<JobResult | null>(null);

  const { data: profile } = useProfile();
  const { data: roles = [] } = useTargetRoles();
  const { data: jobs = [], isLoading } = useJobMatches();
  const runJobResearch = useMutation({
    mutationFn: async () => {
      const selectedRoleId =
        profile?.target_role_id ||
        (isBrowser ? window.localStorage.getItem("careeratlas:selected_role_id") : null);
      if (!selectedRoleId) throw new Error("No target role selected. Complete onboarding first.");
      return researchJobs(selectedRoleId);
    },
    onSuccess: async (data) => {
      cacheJobSearchResponse(data);
      await queryClient.invalidateQueries({ queryKey: ["job-matches"] });
      toast.success("Job matches refreshed", { description: "Fetched the latest jobs from the backend agent." });
    },
    onError: (err: any) => {
      toast.error("Failed to fetch jobs", { description: err?.message || "Job research failed." });
    },
  });

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

  const filtered = jobs
    .filter((j) =>
      [j.title, j.company, j.location].some((f) => f && f.toLowerCase().includes(query.toLowerCase())),
    )
    .filter((j) => (remoteOnly ? Boolean(j.remote) : true))
    .filter((j) => (activeSeniority === "All" ? true : j.seniority === activeSeniority))
    .sort((a, b) => b.score.final - a.score.final);

  const topJob = filtered[0];

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 rounded-3xl border border-border bg-card p-6 shadow-soft sm:flex-row sm:items-end sm:justify-between">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-widest text-muted-foreground">Job search</p>
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Ranked job matches</h1>
          <p className="max-w-2xl text-sm text-muted-foreground">
            Results are scored across semantic fit, skill overlap, experience, and education for{" "}
            <span className="font-medium text-foreground">{targetRole}</span>.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <StatPill label="Matches" value={String(jobs.length)} />
          <StatPill label="Top score" value={topJob ? `${Math.round(topJob.score.final)}%` : "N/A"} />
        </div>
      </div>

      <div className="rounded-3xl border border-border bg-card p-4 shadow-soft">
        <div className="mb-3 flex justify-end">
          <Button
            onClick={() => runJobResearch.mutate()}
            disabled={runJobResearch.isPending}
            className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90"
          >
            {runJobResearch.isPending ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Finding jobs...
              </>
            ) : (
              "Refresh from Job Agent"
            )}
          </Button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search company, role, location..."
            className="h-11 rounded-full pl-10"
          />
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <button
            onClick={() => setActiveSeniority("All")}
            className={cn(
              "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
              activeSeniority === "All"
                ? "border-primary bg-primary text-primary-foreground"
                : "border-border text-muted-foreground hover:bg-muted",
            )}
          >
            All
          </button>
          {seniorities.map((s) => (
            <button
              key={s}
              onClick={() => setActiveSeniority(s)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs font-medium transition-colors",
                activeSeniority === s
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border text-muted-foreground hover:bg-muted",
              )}
            >
              {s}
            </button>
          ))}
          <span className="mx-1 h-5 w-px bg-border" />
          <label className="flex items-center gap-2 rounded-full border border-border px-3 py-1 text-xs font-medium text-muted-foreground">
            <input
              type="checkbox"
              checked={remoteOnly}
              onChange={(e) => setRemoteOnly(e.target.checked)}
              className="h-3.5 w-3.5 accent-coral"
            />
            Remote only
          </label>
        </div>
      </div>

      <div className="grid gap-4">
        {filtered.map((job) => (
          <JobCard key={job.job_id} job={job} onOpen={() => setOpenJob(job)} />
        ))}
        {filtered.length === 0 && (
          <div className="rounded-3xl border border-dashed border-border p-10 text-center text-sm text-muted-foreground">
            No jobs match your filters.
          </div>
        )}
      </div>

      {openJob && <JobDrawer job={openJob} onClose={() => setOpenJob(null)} />}
    </div>
  );
}

function pct(value: number) {
  return Math.max(0, Math.min(100, Math.round(value)));
}

function StatPill({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border bg-background px-4 py-3">
      <p className="text-[11px] uppercase tracking-widest text-muted-foreground">{label}</p>
      <p className="font-display text-xl font-semibold">{value}</p>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium">{pct(value)}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-coral transition-all" style={{ width: `${pct(value)}%` }} />
      </div>
    </div>
  );
}

function JobCard({ job, onOpen }: { job: JobResult; onOpen: () => void }) {
  const strengths = job.explanation.strengths.slice(0, 4);
  const gaps = job.explanation.gaps.slice(0, 4);

  return (
    <article className="rounded-3xl border border-border bg-card p-5 shadow-soft transition-shadow hover:shadow-warm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display text-lg font-semibold">{job.title}</h3>
          <p className="text-sm text-muted-foreground">
            {job.company} - <MapPin className="inline h-3 w-3" /> {job.location || "Location not listed"}
            {job.remote && (
              <span className="ml-2 rounded-full bg-success/15 px-1.5 py-0.5 text-[10px] font-medium text-success">
                Remote
              </span>
            )}
          </p>
        </div>
        <div className="text-right">
          <div className="rounded-full bg-coral/15 px-3 py-1 text-sm font-bold text-coral">
            {pct(job.score.final)}% match
          </div>
          {job.salary && <p className="mt-1 text-xs text-muted-foreground">{job.salary}</p>}
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-success">Strengths</p>
          <div className="flex flex-wrap gap-1.5">
            {strengths.length > 0 ? (
              strengths.map((s) => (
                <span key={s} className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-0.5 text-xs text-success">
                  <Check className="h-3 w-3" /> {s}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">No strengths extracted yet.</span>
            )}
          </div>
        </div>
        <div className="space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-coral">Gaps</p>
          <div className="flex flex-wrap gap-1.5">
            {gaps.length > 0 ? (
              gaps.map((s) => (
                <span key={s} className="rounded-full bg-coral/10 px-2.5 py-0.5 text-xs text-coral">
                  {s}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">No major gaps highlighted.</span>
            )}
          </div>
        </div>
      </div>

      <div className="mt-5 grid gap-3 rounded-2xl border border-border/60 bg-background p-4">
        <ScoreBar label="Semantic fit" value={job.score.semantic} />
        <ScoreBar label="Skill overlap" value={job.score.skill_overlap} />
        <ScoreBar label="Experience" value={job.score.experience} />
        <ScoreBar label="Education" value={job.score.education} />
      </div>

      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-xs text-muted-foreground">
          <span className="font-medium text-foreground">Why this ranks here:</span>{" "}
          {job.explanation.reasoning || "The model returned no written reasoning."}
        </div>
        <Button onClick={onOpen} variant="outline" size="sm" className="rounded-full">
          View details
        </Button>
      </div>
    </article>
  );
}

function JobDrawer({ job, onClose }: { job: JobResult; onClose: () => void }) {
  return (
    <div className="fixed inset-0 z-50 flex" onClick={onClose}>
      <div className="absolute inset-0 bg-foreground/30 backdrop-blur-sm" />
      <aside
        onClick={(e) => e.stopPropagation()}
        className="relative ml-auto h-full w-full max-w-md overflow-y-auto bg-card p-6 shadow-warm sm:p-8"
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 grid h-9 w-9 place-items-center rounded-full border border-border bg-background hover:bg-muted"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>

        <h2 className="pr-12 font-display text-2xl font-bold">{job.title}</h2>
        <p className="mt-1 text-muted-foreground">
          {job.company} - {job.location || "Location not listed"}
        </p>

        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-full bg-coral px-3 py-1 text-xs font-semibold text-coral-foreground">
            {pct(job.score.final)}% match
          </span>
          {job.seniority && <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium">{job.seniority}</span>}
          {job.remote && <span className="rounded-full bg-success/15 px-3 py-1 text-xs font-medium text-success">Remote</span>}
        </div>

        <div className="mt-6 space-y-3 rounded-2xl border border-border/60 bg-background p-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <BarChart3 className="h-4 w-4" /> Score breakdown
          </div>
          <ScoreBar label="Semantic fit" value={job.score.semantic} />
          <ScoreBar label="Skill overlap" value={job.score.skill_overlap} />
          <ScoreBar label="Experience" value={job.score.experience} />
          <ScoreBar label="Education" value={job.score.education} />
        </div>

        <div className="mt-6 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-success">Strengths</p>
          <div className="flex flex-wrap gap-1.5">
            {job.explanation.strengths.length > 0 ? (
              job.explanation.strengths.map((s) => (
                <span key={s} className="rounded-full bg-success/10 px-2.5 py-1 text-xs text-success">
                  {s}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">No strengths returned.</span>
            )}
          </div>
        </div>

        <div className="mt-5 space-y-2">
          <p className="text-xs font-semibold uppercase tracking-wider text-coral">Gaps</p>
          <div className="flex flex-wrap gap-1.5">
            {job.explanation.gaps.length > 0 ? (
              job.explanation.gaps.map((s) => (
                <span key={s} className="rounded-full bg-coral/10 px-2.5 py-1 text-xs text-coral">
                  {s}
                </span>
              ))
            ) : (
              <span className="text-xs text-muted-foreground">No gaps returned.</span>
            )}
          </div>
        </div>

        <div className="mt-6 rounded-2xl border border-border/60 bg-background p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Reasoning</p>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            {job.explanation.reasoning || "No reasoning text was generated for this role."}
          </p>
        </div>

        <p className="mt-6 text-sm leading-relaxed text-muted-foreground">{job.description}</p>

        <div className="mt-8 flex flex-col gap-2">
          <Button asChild className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90">
            <a href={job.apply_url || job.external_url || "#"} target="_blank" rel="noopener noreferrer">
              Apply now <ArrowUpRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
          <Button
            variant="outline"
            className="rounded-full"
            onClick={() => {
              toast.success("Saved", { description: `${job.title} added to your saved jobs.` });
              onClose();
            }}
          >
            Save for later
          </Button>
        </div>
      </aside>
    </div>
  );
}
