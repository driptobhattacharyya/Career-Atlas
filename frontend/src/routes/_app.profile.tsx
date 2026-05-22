import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import {
  Github,
  MapPin,
  Mail,
  ExternalLink,
  Loader2,
  X,
  Plus,
  Pencil,
  Target,
  Check,
} from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";

import {
  useEducation,
  useExperience,
  useProfile,
  useProjects,
  useSkills,
  useTargetRoles,
  useUpdateTargetRole,
  useAddSkill,
  useRemoveSkill,
  useUpdateExperience,
} from "@/hooks/queries";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
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
  "Keywords",
  "Experience",
  "Projects",
  "Soft Skills",
];

const levelStyles: Record<string, string> = {
  advanced: "bg-success/15 text-success border-success/30",
  intermediate: "bg-primary-soft text-primary border-primary/20",
  beginner: "bg-warm/40 text-warm-foreground border-warm/40",
};

function asStringList(value: unknown): string[] {
  const out: string[] = [];
  const seen = new Set<string>();
  const push = (item: unknown) => {
    if (item == null) return;
    if (typeof item === "string") {
      const text = item.trim();
      if (text && !seen.has(text)) {
        seen.add(text);
        out.push(text);
      }
      return;
    }
    if (Array.isArray(item)) {
      item.forEach(push);
      return;
    }
    if (typeof item === "object") {
      const obj = item as Record<string, unknown>;
      for (const key of ["name", "title", "skill", "value", "label", "text"]) {
        push(obj[key]);
      }
      for (const key of ["technologies", "tech", "skills", "keywords", "tags"]) {
        push(obj[key]);
      }
    }
  };
  push(value);
  return out;
}

function normalizeProject(p: any) {
  const title =
    p?.name ||
    p?.title ||
    p?.project_name ||
    p?.label ||
    "Untitled project";
  const technologies = asStringList(
    p?.technologies || p?.tech || p?.skills || p?.keywords || [],
  );
  return {
    ...p,
    name: title,
    title,
    technologies,
    link: p?.link || p?.url || p?.website || null,
  };
}

function Profile() {
  const { data: profile, isLoading: loadingProfile } = useProfile();
  const { data: skills = [], isLoading: loadingSkills } = useSkills();
  const { data: experience = [], isLoading: loadingExperience } = useExperience();
  const { data: education = [], isLoading: loadingEducation } = useEducation();
  const { data: projects = [], isLoading: loadingProjects } = useProjects();
  const { data: roles = [] } = useTargetRoles();

  const addSkill = useAddSkill();
  const removeSkill = useRemoveSkill();

  const [roleModalOpen, setRoleModalOpen] = useState(false);
  const [editExp, setEditExp] = useState<any | null>(null);
  const [newSkill, setNewSkill] = useState("");

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
  const normalizedProjects = projects.map(normalizeProject);

  const currentRole = roles.find((r: any) => r.id === profile.target_role_id);
  const roleTitle = currentRole?.title || profile.target_role_title || "Not set";

  const handleAddSkill = () => {
    const value = newSkill.trim();
    if (!value) return;
    addSkill.mutate(value, {
      onSuccess: () => {
        toast.success("Skill added", { description: value });
        setNewSkill("");
      },
      onError: (err: any) => toast.error("Could not add skill", { description: err?.message }),
    });
  };

  const handleRemoveSkill = (name: string) => {
    removeSkill.mutate(name, {
      onSuccess: () => toast.success("Skill removed", { description: name }),
      onError: (err: any) => toast.error("Could not remove skill", { description: err?.message }),
    });
  };

  return (
    <motion.div
      className="space-y-8"
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
    >
      {/* Header */}
      <div className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
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

        {/* Target role */}
        <div className="mt-5 flex flex-wrap items-center gap-3 border-t border-border/60 pt-4">
          <span className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            <Target className="h-3.5 w-3.5" /> Target role
          </span>
          <span className="rounded-full bg-primary-soft px-3 py-1 text-sm font-medium text-primary">
            {roleTitle}
          </span>
          <Button
            size="sm"
            variant="outline"
            className="ml-auto rounded-full"
            onClick={() => setRoleModalOpen(true)}
          >
            <Pencil className="mr-1.5 h-3.5 w-3.5" /> Change
          </Button>
        </div>
      </div>

      {/* Skills */}
      <section className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <h2 className="font-display text-xl font-semibold">Skills</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Extracted from your resume and GitHub. Add what's missing, remove what's wrong.
        </p>

        <div className="mt-6 space-y-6">
          {grouped.map(({ cat, skills }) => (
            <div key={cat}>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{cat}</h3>
              <div className="mt-3 flex flex-wrap gap-2">
                {skills.map((s: any) => (
                  <span
                    key={s.name}
                    className={cn(
                      "group/skill relative inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium",
                      levelStyles[s.level.toLowerCase()] || levelStyles["intermediate"],
                    )}
                  >
                    {s.name}
                    <button
                      type="button"
                      onClick={() => handleRemoveSkill(s.name)}
                      disabled={removeSkill.isPending}
                      aria-label={`Remove ${s.name}`}
                      className="grid h-4 w-4 place-items-center rounded-full opacity-50 transition-opacity hover:bg-background/60 hover:opacity-100"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            </div>
          ))}
          {grouped.length === 0 && <p className="text-muted-foreground text-sm">No skills found.</p>}
        </div>

        {/* Add skill */}
        <div className="mt-6 flex flex-wrap items-center gap-2">
          <Input
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                handleAddSkill();
              }
            }}
            placeholder="Add a skill…"
            className="h-9 w-56 rounded-full"
          />
          <Button
            size="sm"
            onClick={handleAddSkill}
            disabled={!newSkill.trim() || addSkill.isPending}
            className="rounded-full"
          >
            <Plus className="mr-1 h-4 w-4" /> Add
          </Button>
        </div>
      </section>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Experience */}
        <section className="lg:col-span-2 rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
          <h2 className="font-display text-xl font-semibold">Experience</h2>
          <ol className="mt-5 space-y-5">
            {experience.map((e: any) => (
              <li key={e.id} className="group/exp rounded-2xl border border-border/60 bg-background p-5">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <h3 className="font-semibold">{e.title || e.role}</h3>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-muted-foreground">{e.start_date} — {e.end_date}</span>
                    <button
                      type="button"
                      onClick={() => setEditExp(e)}
                      aria-label="Edit experience"
                      className="grid h-7 w-7 place-items-center rounded-full border border-border opacity-0 transition-opacity hover:bg-muted group-hover/exp:opacity-100"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
                <p className="text-sm text-primary">{e.company}</p>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
                  {(e.description_bullets || e.bullets || []).map((b: string, i: number) => <li key={i}>{b}</li>)}
                </ul>
              </li>
            ))}
            {experience.length === 0 && <p className="text-sm text-muted-foreground">No experience details found.</p>}
          </ol>
        </section>

        {/* GitHub signal */}
        <section className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
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
      <section className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <h2 className="font-display text-xl font-semibold">Projects</h2>
        <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {normalizedProjects.map((p: any) => (
            <article key={p.id} className="rounded-2xl border border-border/60 bg-background p-5">
              <h3 className="font-display font-semibold">{p.name || p.title}</h3>
              <p className="mt-2 text-sm text-muted-foreground">{p.description}</p>
              <div className="mt-3 flex flex-wrap gap-1.5">
                {(p.technologies || p.tech || []).map((t: string) => (
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
      <section className="hover-lift rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-8">
        <h2 className="font-display text-xl font-semibold">Education</h2>
        <ul className="mt-4 space-y-3">
          {education.map((ed: any) => (
            <li key={ed.id} className="flex flex-wrap items-baseline justify-between gap-2 rounded-2xl border border-border/60 bg-background p-4">
              <div>
                <p className="font-semibold">{ed.institution || ed.school}</p>
                <p className="text-sm text-muted-foreground">{ed.degree}</p>
              </div>
              <span className="text-xs text-muted-foreground">{ed.start_date} — {ed.end_date}</span>
            </li>
          ))}
          {education.length === 0 && <p className="text-sm text-muted-foreground">No education listed.</p>}
        </ul>
      </section>

      <RolePickerDialog
        open={roleModalOpen}
        onClose={() => setRoleModalOpen(false)}
        roles={roles}
        currentRoleId={profile.target_role_id ?? undefined}
      />
      <ExperienceEditDialog exp={editExp} onClose={() => setEditExp(null)} />
    </motion.div>
  );
}

function RolePickerDialog({
  open,
  onClose,
  roles,
  currentRoleId,
}: {
  open: boolean;
  onClose: () => void;
  roles: any[];
  currentRoleId?: string;
}) {
  const mutation = useUpdateTargetRole();

  const pick = (role: any) => {
    if (role.id === currentRoleId) {
      onClose();
      return;
    }
    mutation.mutate(
      { roleId: role.id, roleTitle: role.title },
      {
        onSuccess: () => {
          toast.success("Target role updated", { description: role.title });
          onClose();
        },
        onError: (err: any) => toast.error("Could not change role", { description: err?.message }),
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Change target role</DialogTitle>
        </DialogHeader>
        <p className="text-sm text-muted-foreground">
          Your roadmap and gaps are saved per role — switch anytime without losing progress.
        </p>
        <div className="mt-2 grid max-h-[55vh] gap-3 overflow-y-auto sm:grid-cols-2">
          {roles.map((r) => {
            const selected = r.id === currentRoleId;
            return (
              <button
                key={r.id}
                type="button"
                onClick={() => pick(r)}
                disabled={mutation.isPending}
                className={cn(
                  "rounded-2xl border-2 p-4 text-left transition-all disabled:opacity-60",
                  selected
                    ? "border-coral bg-coral/5"
                    : "border-border hover:border-primary-soft hover:bg-muted/40",
                )}
              >
                <div className="flex items-start justify-between">
                  <span className="text-xl">{r.emoji}</span>
                  {selected && <Check className="h-4 w-4 text-coral" />}
                </div>
                <h3 className="mt-2 font-display text-sm font-semibold">{r.title}</h3>
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{r.blurb}</p>
              </button>
            );
          })}
        </div>
      </DialogContent>
    </Dialog>
  );
}

function ExperienceEditDialog({ exp, onClose }: { exp: any | null; onClose: () => void }) {
  return (
    <Dialog open={!!exp} onOpenChange={(o) => !o && onClose()}>
      <DialogContent>
        {exp && <ExperienceEditForm key={exp.id} exp={exp} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  );
}

function ExperienceEditForm({ exp, onClose }: { exp: any; onClose: () => void }) {
  const [title, setTitle] = useState(exp.title || exp.role || "");
  const [company, setCompany] = useState(exp.company || "");
  const [startDate, setStartDate] = useState(exp.start_date || "");
  const [endDate, setEndDate] = useState(exp.end_date || "");
  const mutation = useUpdateExperience();

  const save = () => {
    mutation.mutate(
      {
        id: exp.id,
        fields: { title, company, start_date: startDate, end_date: endDate },
      },
      {
        onSuccess: () => {
          toast.success("Experience updated");
          onClose();
        },
        onError: (err: any) => toast.error("Could not save", { description: err?.message }),
      },
    );
  };

  return (
    <>
      <DialogHeader>
        <DialogTitle>Edit experience</DialogTitle>
      </DialogHeader>
      <div className="space-y-3">
        <label className="block">
          <span className="text-xs font-medium text-muted-foreground">Title</span>
          <Input value={title} onChange={(e) => setTitle(e.target.value)} className="mt-1" />
        </label>
        <label className="block">
          <span className="text-xs font-medium text-muted-foreground">Company</span>
          <Input value={company} onChange={(e) => setCompany(e.target.value)} className="mt-1" />
        </label>
        <div className="grid grid-cols-2 gap-3">
          <label className="block">
            <span className="text-xs font-medium text-muted-foreground">Start date</span>
            <Input value={startDate} onChange={(e) => setStartDate(e.target.value)} className="mt-1" placeholder="Jan 2024" />
          </label>
          <label className="block">
            <span className="text-xs font-medium text-muted-foreground">End date</span>
            <Input value={endDate} onChange={(e) => setEndDate(e.target.value)} className="mt-1" placeholder="Present" />
          </label>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose} disabled={mutation.isPending}>
          Cancel
        </Button>
        <Button onClick={save} disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Save"}
        </Button>
      </DialogFooter>
    </>
  );
}
