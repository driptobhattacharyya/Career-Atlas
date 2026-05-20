import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Search, MapPin, X, Check, Loader2 } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useJobMatches, useTargetRoles, useProfile } from "@/hooks/queries";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { researchJobs } from "@/lib/api";

export const Route = createFileRoute("/_app/jobs")({
  head: () => ({
    meta: [
      { title: "Jobs — CareerAtlas" },
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
  const [openJob, setOpenJob] = useState<any | null>(null);

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
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["job-matches"] });
      toast.success("Job matches refreshed", { description: "Fetched latest jobs from the backend agent." });
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
    .filter((j: any) =>
      [j.title, j.company, j.location].some((f) => f && f.toLowerCase().includes(query.toLowerCase())),
    )
    .filter((j: any) => (remoteOnly ? j.remote : true))
    .filter((j: any) => (activeSeniority === "All" ? true : j.seniority === activeSeniority))
    .sort((a: any, b: any) => b.match_pct - a.match_pct);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Job matches</h1>
        <p className="mt-2 text-muted-foreground">
          Ranked by fit for <span className="font-medium text-foreground">{targetRole}</span>.
        </p>
      </div>

      {/* Filters */}
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
            placeholder="Search company, role, location…"
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

      {/* Cards */}
      <div className="grid gap-4">
        {filtered.map((j: any) => (
          <JobCard key={j.id} job={j} onOpen={() => setOpenJob(j)} />
        ))}
        {filtered.length === 0 && (
          <p className="rounded-3xl border border-dashed border-border p-10 text-center text-sm text-muted-foreground">
            No jobs match your filters.
          </p>
        )}
      </div>

      {/* Drawer */}
      {openJob && <JobDrawer job={openJob} onClose={() => setOpenJob(null)} />}
    </div>
  );
}

function JobCard({ job, onOpen }: { job: any; onOpen: () => void }) {
  return (
    <article className="rounded-3xl border border-border bg-card p-5 shadow-soft transition-shadow hover:shadow-warm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="font-display text-lg font-semibold">{job.title}</h3>
          <p className="text-sm text-muted-foreground">
            {job.company} · <MapPin className="inline h-3 w-3" /> {job.location}
            {job.remote && <span className="ml-1 rounded-full bg-success/15 px-1.5 py-0.5 text-[10px] font-medium text-success">Remote</span>}
          </p>
        </div>
        <div className="text-right">
          <div className="rounded-full bg-coral/15 px-3 py-1 text-sm font-bold text-coral">{job.match_pct}% match</div>
          {job.salary && <p className="mt-1 text-xs text-muted-foreground">{job.salary}</p>}
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-success">You have</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {job.matched && job.matched.slice(0, 5).map((s: string) => (
              <span key={s} className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-0.5 text-xs text-success">
                <Check className="h-3 w-3" /> {s}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-coral">You're missing</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {job.missing && job.missing.map((s: string) => (
              <span key={s} className="rounded-full bg-coral/10 px-2.5 py-0.5 text-xs text-coral">{s}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between">
        <span className="text-xs text-muted-foreground">Posted {job.posted_days}d ago · {job.seniority}</span>
        <Button onClick={onOpen} variant="outline" size="sm" className="rounded-full">
          View details
        </Button>
      </div>
    </article>
  );
}

function JobDrawer({ job, onClose }: { job: any; onClose: () => void }) {
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
        <p className="mt-1 text-muted-foreground">{job.company} · {job.location}</p>

        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-full bg-coral px-3 py-1 text-xs font-semibold text-coral-foreground">{job.match_pct}% match</span>
          <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium">{job.seniority}</span>
          {job.remote && <span className="rounded-full bg-success/15 px-3 py-1 text-xs font-medium text-success">Remote</span>}
        </div>

        <p className="mt-6 text-sm leading-relaxed text-muted-foreground">{job.description}</p>

        <div className="mt-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-success">Skills you have</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {job.matched && job.matched.map((s: string) => (
              <span key={s} className="rounded-full bg-success/10 px-2.5 py-1 text-xs text-success">{s}</span>
            ))}
          </div>
        </div>

        <div className="mt-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-coral">Skills to build</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {job.missing && job.missing.map((s: string) => (
              <span key={s} className="rounded-full bg-coral/10 px-2.5 py-1 text-xs text-coral">{s}</span>
            ))}
          </div>
        </div>

        <div className="mt-8 flex flex-col gap-2">
          <Button asChild className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90">
             <a href={job.external_url} target="_blank" rel="noopener noreferrer">Apply now</a>
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
