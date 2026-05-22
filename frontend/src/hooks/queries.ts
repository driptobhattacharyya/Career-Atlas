import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/context/auth-context";
import {
  ApiError,
  type ExperiencePatch,
  type JobResult,
  type MilestoneRow,
  type MilestoneStatus,
  type TargetRole,
  addSkill,
  analyzeGaps,
  deleteSkill,
  getGapAnalysis,
  getJobMatches,
  getCachedJobSearchResponse,
  getLatestPathway,
  getLatestResume,
  getTargetRoles,
  listMilestones,
  cacheJobSearchResponse,
  researchJobs,
  startDeepResearch,
  updateExperience,
  updateMilestoneStatus,
  updateTargetRole,
  uploadResume,
} from "@/lib/api";

const disableAuth = (import.meta.env.VITE_DISABLE_AUTH as string | undefined) === "true";

function useEnabled() {
  const { user } = useAuth();
  return !!user || disableAuth;
}

// ── Resume ─────────────────────────────────────────────────────────────────

export function useLatestResume() {
  const { user } = useAuth();
  const enabled = useEnabled();
  return useQuery({
    queryKey: ["latest-resume", user?.id, disableAuth],
    enabled,
    queryFn: async () => {
      const payload = await getLatestResume();
      return payload.resume as any | null;
    },
  });
}

export function useUploadResume() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (file: File) => uploadResume(file),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["latest-resume"] });
    },
  });
}

// ── Profile & derived resume views ─────────────────────────────────────────

export function useProfile() {
  const latestResume = useLatestResume();
  return useQuery({
    queryKey: ["profile-from-resume", latestResume.data?.resume_id],
    enabled: latestResume.isSuccess,
    queryFn: async () => {
      const resume = latestResume.data;
      if (!resume) return null;
      const isBrowser = typeof window !== "undefined";
      const selectedRoleId = isBrowser
        ? window.localStorage.getItem("careeratlas:selected_role_id")
        : null;
      const selectedRoleTitle = isBrowser
        ? window.localStorage.getItem("careeratlas:selected_role_title")
        : null;
      const fullName =
        resume.full_name ||
        resume.contact?.name ||
        (resume.contact?.email ? String(resume.contact.email).split("@")[0] : "") ||
        "Candidate";
      return {
        user_id: resume.resume_id,
        name: fullName,
        email: resume.contact?.email || null,
        headline: resume.headline || "",
        location: resume.contact?.location || "",
        github: resume.contact?.github || "",
        summary: resume.summary || "",
        completeness: 30,
        target_role_id: selectedRoleId || null,
        target_role_title: selectedRoleTitle || null,
      };
    },
  });
}

export function useSkills() {
  const latestResume = useLatestResume();
  return useQuery({
    queryKey: ["skills-from-resume", latestResume.data?.resume_id],
    enabled: latestResume.isSuccess,
    queryFn: async () => {
      const resume = latestResume.data;
      if (!resume) return [];
      const makeSkill = (name: string, category: string, source = "resume") => ({
        name,
        category,
        level: "intermediate",
        source,
        evidence: "",
      });
      const output: Array<{
        name: string;
        category: string;
        level: string;
        source: string;
        evidence: string;
      }> = [];
      const seen = new Set<string>();
      const push = (name: unknown, category: string, source = "resume") => {
        if (typeof name !== "string") return;
        const text = name.trim();
        if (!text) return;
        const key = `${category}:${source}:${text.toLowerCase()}`;
        if (seen.has(key)) return;
        seen.add(key);
        output.push(makeSkill(text, category, source));
      };
      (resume.programming_languages || []).forEach((name: string) => push(name, "Languages"));
      (resume.spoken_languages || []).forEach((name: string) => push(name, "Languages"));
      (resume.skills || []).forEach((name: string) => push(name, "Tools"));
      (resume.keywords || []).forEach((name: string) => push(name, "Keywords"));
      (resume.experience || []).forEach((exp: any) => {
        (exp?.technologies || []).forEach((name: string) => push(name, "Experience"));
      });
      (resume.projects || []).forEach((proj: any) => {
        (proj?.technologies || []).forEach((name: string) => push(name, "Projects"));
      });
      return output;
    },
  });
}

export function useExperience() {
  const latestResume = useLatestResume();
  return useQuery({
    queryKey: ["experience-from-resume", latestResume.data?.resume_id],
    enabled: latestResume.isSuccess,
    queryFn: async () => latestResume.data?.experience || [],
  });
}

export function useEducation() {
  const latestResume = useLatestResume();
  return useQuery({
    queryKey: ["education-from-resume", latestResume.data?.resume_id],
    enabled: latestResume.isSuccess,
    queryFn: async () => latestResume.data?.education || [],
  });
}

export function useProjects() {
  const latestResume = useLatestResume();
  return useQuery({
    queryKey: ["projects-from-resume", latestResume.data?.resume_id],
    enabled: latestResume.isSuccess,
    queryFn: async () => latestResume.data?.projects || [],
  });
}

// ── Profile editing ────────────────────────────────────────────────────────

function invalidateResumeViews(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: ["latest-resume"] });
  qc.invalidateQueries({ queryKey: ["skills-from-resume"] });
  qc.invalidateQueries({ queryKey: ["experience-from-resume"] });
  qc.invalidateQueries({ queryKey: ["profile-from-resume"] });
}

export function useUpdateTargetRole() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ roleId }: { roleId: string; roleTitle: string }) =>
      updateTargetRole(roleId),
    onSuccess: (_data, { roleId, roleTitle }) => {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("careeratlas:selected_role_id", roleId);
        window.localStorage.setItem("careeratlas:selected_role_title", roleTitle);
      }
      qc.invalidateQueries({ queryKey: ["profile-from-resume"] });
    },
  });
}

export function useAddSkill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (skill: string) => addSkill(skill),
    onSuccess: () => invalidateResumeViews(qc),
  });
}

export function useRemoveSkill() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (skill: string) => deleteSkill(skill),
    onSuccess: () => invalidateResumeViews(qc),
  });
}

export function useUpdateExperience() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, fields }: { id: string; fields: ExperiencePatch }) =>
      updateExperience(id, fields),
    onSuccess: () => invalidateResumeViews(qc),
  });
}

// ── Target roles ───────────────────────────────────────────────────────────

export function useTargetRoles() {
  return useQuery<TargetRole[]>({
    queryKey: ["target-roles"],
    queryFn: getTargetRoles,
    staleTime: 60_000,
  });
}

// ── Gap analysis ───────────────────────────────────────────────────────────

export function useGapAnalysis() {
  // Backend skill_gaps table is the authoritative source — gaps reload on
  // re-sign-in / new device. localStorage is only a same-session fallback for
  // the brief window before the backend query settles.
  const { user } = useAuth();
  const enabled = useEnabled();
  return useQuery({
    queryKey: ["gap-analysis", user?.id, disableAuth],
    enabled,
    queryFn: async () => {
      try {
        const data = await getGapAnalysis();
        if (Array.isArray(data?.gaps) && data.gaps.length > 0) return data.gaps;
      } catch {
        // fall through to localStorage
      }
      if (typeof window === "undefined") return [];
      const raw = window.localStorage.getItem("careeratlas:last_gap_response");
      if (!raw) return [];
      try {
        const parsed = JSON.parse(raw);
        return Array.isArray(parsed?.gaps) ? parsed.gaps : [];
      } catch {
        return [];
      }
    },
  });
}

export function useRunGapAnalysis() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (targetRoleTitle: string) => analyzeGaps(targetRoleTitle),
    onSuccess: (data) => {
      if (typeof window !== "undefined") {
        window.localStorage.setItem("careeratlas:last_gap_response", JSON.stringify(data));
      }
      qc.invalidateQueries({ queryKey: ["gap-analysis"] });
    },
  });
}

// ── Roadmap (M1) ───────────────────────────────────────────────────────────

export function useRoadmap(targetRoleId?: string) {
  const { user } = useAuth();
  const enabled = useEnabled();
  return useQuery<MilestoneRow[]>({
    queryKey: ["milestones", user?.id, targetRoleId ?? null],
    enabled,
    retry: (count, err) =>
      !(err instanceof ApiError && err.status === 404) && count < 1,
    queryFn: async () => {
      try {
        const data = await listMilestones(targetRoleId);
        return data.milestones || [];
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return [];
        throw err;
      }
    },
  });
}

export function useUpdateMilestoneStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: MilestoneStatus }) =>
      updateMilestoneStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["milestones"] });
    },
  });
}

// ── Jobs ───────────────────────────────────────────────────────────────────

export function useJobMatches() {
  const { user } = useAuth();
  const enabled = useEnabled();
  return useQuery<JobResult[]>({
    queryKey: ["job-matches", user?.id],
    enabled,
    retry: false,
    queryFn: async () => {
      const cached = getCachedJobSearchResponse();
      if (cached?.jobs?.length) return cached.jobs;
      const data = await getJobMatches();
      cacheJobSearchResponse(data);
      return data.jobs ?? [];
    },
  });
}

export function useResearchJobs() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (targetRoleId: string) => researchJobs(targetRoleId),
    onSuccess: (data) => {
      cacheJobSearchResponse(data);
      qc.invalidateQueries({ queryKey: ["job-matches"] });
    },
  });
}

// ── Deep research / Pathways (M2) ──────────────────────────────────────────

export function useLatestPathway(roleId?: string) {
  return useQuery({
    queryKey: ["pathway-latest", roleId ?? null],
    retry: (count, err) =>
      !(err instanceof ApiError && err.status === 404) && count < 1,
    queryFn: async () => {
      try {
        return await getLatestPathway(roleId);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
  });
}

export function useStartDeepResearch() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ roleId, maxIter }: { roleId: string; maxIter?: number }) =>
      startDeepResearch(roleId, maxIter ?? 3),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["pathway-latest"] });
      qc.invalidateQueries({ queryKey: ["milestones"] });
    },
  });
}

// ── Tiny session cache (module-scoped) ─────────────────────────────────────

const _sessionCache = new Map<string, unknown>();
function qcGet<T>(key: string): T | undefined {
  return _sessionCache.get(key) as T | undefined;
}
function qcSet<T>(key: string, value: T) {
  _sessionCache.set(key, value);
}
