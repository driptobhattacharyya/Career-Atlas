import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowRight, Sparkles, Target, Map, Briefcase, CheckCircle2, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useProfile, useRoadmap, useGapAnalysis, useJobMatches, useTargetRoles } from "@/hooks/queries";

export const Route = createFileRoute("/_app/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — CareerAtlas" },
      { name: "description", content: "Your personal career dashboard: skill gaps, roadmap progress, and job matches at a glance." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const isBrowser = typeof window !== "undefined";
  const { data: profile, isLoading: loadingProfile } = useProfile();
  const { data: roadmap = [], isLoading: loadingRoadmap } = useRoadmap();
  const { data: gaps = [], isLoading: loadingGaps } = useGapAnalysis();
  const { data: jobs = [], isLoading: loadingJobs } = useJobMatches();
  const { data: roles = [], isLoading: loadingRoles } = useTargetRoles();

  if (loadingProfile || loadingRoadmap || loadingGaps || loadingJobs || loadingRoles) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-3 text-muted-foreground">Loading your personalized dashboard...</span>
      </div>
    );
  }

  if (!profile) return <div>No profile data found. Please run the onboarding process.</div>;
  const firstName = (profile.name || "Candidate").split(" ")[0];

  const completed = roadmap.filter((m: any) => m.status === "completed").length;
  const inProgress = roadmap.filter((m: any) => m.status === "in-progress").length;
  const total = roadmap.length;
  const roadmapPct = total === 0 ? 0 : Math.round(((completed + inProgress * 0.5) / total) * 100);
  
  const topGaps = [...gaps].sort((a: any, b: any) => b.relevance - a.relevance).slice(0, 3);
  const topJob = [...jobs].sort((a: any, b: any) => b.match_pct - a.match_pct)[0];
  const activeMilestone = roadmap.find((m: any) => m.status === "in-progress") || roadmap[0];
  
  const localRoleTitle = isBrowser ? window.localStorage.getItem("careeratlas:selected_role_title") : null;
  const targetRole =
    roles.find((r: any) => r.id === profile.target_role_id)?.title ||
    profile.target_role_title ||
    localRoleTitle ||
    "your target role";

  return (
    <div className="space-y-8">
      {/* Welcome */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-muted-foreground">Welcome back,</p>
          <h1 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">
            {firstName} 👋
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            You're aiming for <span className="font-medium text-foreground">{targetRole}</span>. Here's where you stand today.
          </p>
        </div>
        <Button asChild className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm sm:self-start">
          <Link to="/roadmap">
            Continue roadmap <ArrowRight className="ml-1 h-4 w-4" />
          </Link>
        </Button>
      </div>

      {/* Top stats */}
      <div className="grid gap-4 sm:grid-cols-3">
        <CompletenessCard value={profile.completeness || 0} />
        <StatCard
          icon={Map}
          label="Roadmap progress"
          value={`${roadmapPct}%`}
          sub={`${completed}/${total} milestones done`}
          accent="text-primary"
        />
        <StatCard
          icon={Briefcase}
          label="Top job match"
          value={topJob ? `${topJob.match_pct}%` : "N/A"}
          sub={topJob ? topJob.title : "No jobs found"}
          accent="text-coral"
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Top gaps */}
        <section className="lg:col-span-2 rounded-3xl border border-border bg-card p-6 shadow-soft">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
              <Target className="h-4 w-4 text-coral" /> Your top 3 gaps
            </h2>
            <Link to="/gaps" className="text-xs font-medium text-primary hover:underline">
              See all →
            </Link>
          </div>
          <ul className="mt-5 space-y-3">
            {topGaps.map((g: any) => (
              <li key={g.skill} className="rounded-2xl border border-border/60 bg-background p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-medium">{g.skill}</p>
                    <p className="mt-1 text-xs text-muted-foreground">{g.why}</p>
                  </div>
                  <span className="shrink-0 rounded-full bg-coral/15 px-2.5 py-1 text-xs font-semibold text-coral">
                    {g.relevance}% relevant
                  </span>
                </div>
              </li>
            ))}
            {topGaps.length === 0 && <p className="text-sm text-muted-foreground">No critical skill gaps found!</p>}
          </ul>
        </section>

        {/* Recommended next */}
        <section className="rounded-3xl border border-border bg-card p-6 shadow-soft">
          <h2 className="flex items-center gap-2 font-display text-lg font-semibold">
            <Sparkles className="h-4 w-4 text-coral" /> Do this next
          </h2>
          
          {activeMilestone ? (
            <div className="mt-4 rounded-2xl bg-primary-soft/60 p-4">
              <p className="text-xs uppercase tracking-wider text-primary">{activeMilestone.phase} Phase</p>
              <h3 className="mt-1 font-display text-base font-semibold">{activeMilestone.title}</h3>
              <p className="mt-2 text-xs text-muted-foreground truncate">
                ~{activeMilestone.estimated_weeks} weeks · {activeMilestone.skill}
              </p>
              <Button asChild size="sm" className="mt-4 w-full rounded-full">
                <Link to="/roadmap">Open milestone</Link>
              </Button>
            </div>
          ) : (
            <p className="mt-4 text-sm text-muted-foreground">You have completed your entire roadmap! Awesome job.</p>
          )}

          <h3 className="mt-6 text-xs uppercase tracking-wider text-muted-foreground">Recent activity</h3>
          <ul className="mt-3 space-y-2 text-sm">
            <li className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-coral" />
              Found <span className="font-medium">{jobs.length} job matches</span>
            </li>
            <li className="flex items-center gap-2">
              <Target className="h-4 w-4 text-primary" />
              Detected <span className="font-medium">{gaps.length} critical gaps</span>
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}

function CompletenessCard({ value }: { value: number }) {
  const radius = 28;
  const c = 2 * Math.PI * radius;
  const offset = c - (value / 100) * c;
  return (
    <div className="rounded-3xl border border-border bg-card p-6 shadow-soft">
      <div className="flex items-center gap-4">
        <svg width="72" height="72" viewBox="0 0 72 72" className="-rotate-90">
          <circle cx="36" cy="36" r={radius} stroke="var(--color-muted)" strokeWidth="8" fill="none" />
          <circle
            cx="36"
            cy="36"
            r={radius}
            stroke="var(--color-coral)"
            strokeWidth="8"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            className="transition-all"
          />
        </svg>
        <div>
          <p className="text-xs uppercase tracking-wider text-muted-foreground">Profile completeness</p>
          <p className="font-display text-3xl font-bold text-coral">{value}%</p>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: typeof Map;
  label: string;
  value: string;
  sub: string;
  accent: string;
}) {
  return (
    <div className="rounded-3xl border border-border bg-card p-6 shadow-soft">
      <div className="flex items-center gap-3">
        <span className="grid h-10 w-10 place-items-center rounded-xl bg-primary-soft text-primary">
          <Icon className="h-5 w-5" />
        </span>
        <p className="text-xs uppercase tracking-wider text-muted-foreground">{label}</p>
      </div>
      <p className={`mt-3 font-display text-3xl font-bold ${accent}`}>{value}</p>
      <p className="mt-1 truncate text-xs text-muted-foreground">{sub}</p>
    </div>
  );
}
