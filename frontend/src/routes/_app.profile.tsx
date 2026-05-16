import { createFileRoute } from "@tanstack/react-router";
import { Github, MapPin, Mail, ExternalLink, Loader2 } from "lucide-react";
import { useEducation, useExperience, useProfile, useProjects, useSkills } from "@/hooks/queries";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/profile")({
  head: () => ({
    meta: [
      { title: "Profile — CareerAtlas" },
      { name: "description", content: "Your extracted profile, skills with evidence, education, projects, and GitHub signal." },
    ],
  }),
  component: Profile,
});

const categoryOrder = [
  "Languages",
  "Frameworks",
  "Data",
  "Cloud & DevOps",
  "Tools",
  "Soft Skills",
];

const levelStyles: Record<string, string> = {
  advanced: "bg-success/15 text-success border-success/30",
  intermediate: "bg-primary-soft text-primary border-primary/20",
  beginner: "bg-warm/40 text-warm-foreground border-warm/40",
};

function Profile() {
  const { data: profile, isLoading: loadingProfile } = useProfile();
  const { data: skills = [], isLoading: loadingSkills } = useSkills();
  const { data: experience = [], isLoading: loadingExperience } = useExperience();
  const { data: education = [], isLoading: loadingEducation } = useEducation();
  const { data: projects = [], isLoading: loadingProjects } = useProjects();

  if (loadingProfile || loadingSkills || loadingExperience || loadingEducation || loadingProjects) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (!profile) return <div>No profile data found.</div>;
  const displayName = profile.name || "Candidate";

  const grouped = categoryOrder.map((cat) => ({
    cat,
    skills: skills.filter((s: any) => s.category.toLowerCase() === cat.toLowerCase() || s.category === cat),
  })).filter(g => g.skills.length > 0);

  const githubSkills = skills.filter((s: any) => s.source === "github");

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
          <div className="grid h-20 w-20 shrink-0 place-items-center rounded-3xl bg-coral text-3xl font-bold text-coral-foreground">
            {displayName[0]}
          </div>
          <div className="min-w-0 flex-1">
            <h1 className="font-display text-3xl font-bold tracking-tight">{displayName}</h1>
            <p className="mt-1 text-muted-foreground">{profile.headline}</p>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              {profile.email && <span className="flex items-center gap-1"><Mail className="h-3.5 w-3.5" /> {profile.email}</span>}
              {profile.location && <span className="flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {profile.location}</span>}
              {profile.github && (
                <span className="flex items-center gap-1"><Github className="h-3.5 w-3.5" /> {profile.github}</span>
              )}
            </div>
          </div>
        </div>
        <p className="mt-5 text-sm leading-relaxed text-muted-foreground">{profile.summary}</p>
      </div>

      {/* Skills */}
      <section className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <h2 className="font-display text-xl font-semibold">Skills</h2>
        <p className="mt-1 text-sm text-muted-foreground">Extracted from your resume and GitHub. Hover for evidence.</p>

        <div className="mt-6 space-y-6">
          {grouped.map(({ cat, skills }) => (
            <div key={cat}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{cat}</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {skills.map((s: any) => (
                  <span
                    key={s.name}
                    title={s.evidence ?? `${s.level} · from ${s.source ?? "resume"}`}
                    className={cn(
                      "group relative inline-flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium",
                      levelStyles[s.level.toLowerCase()] || levelStyles["intermediate"],
                    )}
                  >
                    {s.name}
                    <span className="rounded-full bg-background/60 px-1.5 py-0.5 text-[10px] font-semibold uppercase opacity-80">
                      {s.level[0]}
                    </span>
                  </span>
                ))}
              </div>
            </div>
          ))}
          {grouped.length === 0 && <p className="text-muted-foreground text-sm">No skills found.</p>}
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Experience */}
        <section className="lg:col-span-2 rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
          <h2 className="font-display text-xl font-semibold">Experience</h2>
          <ol className="mt-5 space-y-5">
            {experience.map((e: any) => (
              <li key={e.id} className="rounded-2xl border border-border/60 bg-background p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold">{e.role}</h3>
                  <span className="text-xs text-muted-foreground">{e.start_date} — {e.end_date}</span>
                </div>
                <p className="text-sm text-primary">{e.company}</p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {e.bullets && e.bullets.map((b: string, i: number) => <li key={i}>{b}</li>)}
                </ul>
              </li>
            ))}
            {experience.length === 0 && <p className="text-sm text-muted-foreground">No experience details found.</p>}
          </ol>
        </section>

        {/* GitHub signal */}
        <section className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
          <h2 className="flex items-center gap-2 font-display text-xl font-semibold">
            <Github className="h-5 w-5" /> GitHub signal
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">Skills inferred from your public repos.</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {githubSkills.map((s: any) => (
              <span key={s.name} className="rounded-full border border-primary/20 bg-primary-soft px-3 py-1 text-xs font-medium text-primary">
                {s.name}
              </span>
            ))}
            {githubSkills.length === 0 && <span className="text-sm text-muted-foreground">GitHub integration pending.</span>}
          </div>
        </section>
      </div>

      {/* Projects */}
      <section className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <h2 className="font-display text-xl font-semibold">Projects</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((p: any) => (
            <article key={p.id} className="rounded-2xl border border-border/60 bg-background p-5">
              <h3 className="font-display font-semibold">{p.name}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{p.description}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {p.tech && p.tech.map((t: string) => (
                  <span key={t} className="rounded-full bg-muted px-2 py-0.5 text-[10px] font-medium text-muted-foreground">{t}</span>
                ))}
              </div>
              {p.link && (
                <a href={p.link} target="_blank" rel="noreferrer" className="mt-3 inline-flex items-center gap-1 text-xs font-medium text-primary hover:underline">
                  View <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </article>
          ))}
          {projects.length === 0 && <p className="text-sm text-muted-foreground">No projects listed.</p>}
        </div>
      </section>

      {/* Education */}
      <section className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <h2 className="font-display text-xl font-semibold">Education</h2>
        <ul className="mt-4 space-y-3">
          {education.map((ed: any) => (
            <li key={ed.id} className="flex flex-wrap items-baseline justify-between gap-2 rounded-2xl border border-border/60 bg-background p-4">
              <div>
                <p className="font-semibold">{ed.school}</p>
                <p className="text-sm text-muted-foreground">{ed.degree}</p>
              </div>
              <span className="text-xs text-muted-foreground">{ed.start_date} — {ed.end_date}</span>
            </li>
          ))}
          {education.length === 0 && <p className="text-sm text-muted-foreground">No education listed.</p>}
        </ul>
      </section>
    </div>
  );
}
