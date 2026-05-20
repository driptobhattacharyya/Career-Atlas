import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useAuth } from "@/context/auth-context";
import {
  ApiError,
  type MilestoneRow,
  type MilestoneStatus,
  type TargetRole,
  analyzeGaps,
  getJobMatches,
  getLatestPathway,
  getLatestResume,
  getTargetRoles,
  listMilestones,
  researchJobs,
  startDeepResearch,
  updateMilestoneStatus,
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
      const langs = (resume.programming_languages || []).map((name: string) => ({
        name,
        category: "Languages",
        level: "intermediate",
        source: "resume",
        evidence: "",
      }));
      const skills = (resume.skills || []).map((name: string) => ({
        name,
        category: "Tools",
        level: "intermediate",
        source: "resume",
        evidence: "",
      }));
      return [...langs, ...skills];
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
  // Cached gap response is the authoritative source — populated by onboarding
  // after analyzeGaps() succeeds. We fall back to an empty list rather than
  // querying skill_gaps directly so the backend stays the only data path.
  return useQuery({
    queryKey: ["gap-analysis-cache"],
    queryFn: async () => {
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
      qc.invalidateQueries({ queryKey: ["gap-analysis-cache"] });
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
  return useQuery<any[]>({
    queryKey: ["job-matches", user?.id],
    enabled,
    retry: false,
    queryFn: async () => {
      const data = await getJobMatches();
      return data.jobs ?? [];
    },
  });
}

export function useResearchJobs() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (targetRoleId: string) => researchJobs(targetRoleId),
    onSuccess: (data) => {
      qcSet("job-matches-cached", data.jobs || []);
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
