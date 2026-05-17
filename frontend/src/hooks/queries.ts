import { useQuery } from "@tanstack/react-query";

import { useAuth } from "@/context/auth-context";
import { getTargetRoles } from "@/lib/api";
import { supabase } from "@/lib/supabase";

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "http://localhost:8000";
const disableAuth = (import.meta.env.VITE_DISABLE_AUTH as string | undefined) === "true";

async function getAccessToken() {
  if (disableAuth) return "";
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  return data.session?.access_token ?? "";
}

async function fetchLatestResume() {
  const token = await getAccessToken();
  const response = await fetch(`${apiBaseUrl}/api/parse-resume/latest`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Failed to fetch resume: ${response.status}`);
  }
  const payload = await response.json();
  return payload.resume as any | null;
}

export function useLatestResume() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["latest-resume", user?.id, disableAuth],
    enabled: !!user || disableAuth,
    queryFn: fetchLatestResume,
  });
}

export function useProfile() {
  const latestResume = useLatestResume();
  return useQuery({
    queryKey: ["profile-from-resume", latestResume.data?.resume_id],
    enabled: latestResume.isSuccess,
    queryFn: async () => {
      const resume = latestResume.data;
      if (!resume) return null;
      const isBrowser = typeof window !== "undefined";
      const selectedRoleId = isBrowser ? window.localStorage.getItem("careeratlas:selected_role_id") : null;
      const selectedRoleTitle = isBrowser ? window.localStorage.getItem("careeratlas:selected_role_title") : null;
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

export function useGapAnalysis() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["skill_gaps", user?.id],
    enabled: !!user || disableAuth,
    queryFn: async () => {
      const isBrowser = typeof window !== "undefined";
      // Prefer the latest backend response to keep explainability + exact selected-role output.
      const cachedRaw = isBrowser ? window.localStorage.getItem("careeratlas:last_gap_response") : null;
      if (cachedRaw) {
        try {
          const cached = JSON.parse(cachedRaw);
          if (Array.isArray(cached?.gaps)) return cached.gaps;
        } catch {
          // ignore cache parse failure
        }
      }

      const selectedRoleTitle = isBrowser ? window.localStorage.getItem("careeratlas:selected_role_title") : null;
      let query = supabase.from("skill_gaps").select("*");
      if (selectedRoleTitle) {
        query = query.eq("target_role", selectedRoleTitle);
      }
      const { data, error } = await query;
      if (error) throw error;

      // Defensive dedupe by skill name.
      const seen = new Set<string>();
      const deduped = (data ?? []).filter((row: any) => {
        const key = String(row?.skill || "").trim().toLowerCase();
        if (!key || seen.has(key)) return false;
        seen.add(key);
        return true;
      });
      return deduped;
    },
  });
}

export function useRoadmap() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["milestones", user?.id],
    enabled: !!user || disableAuth,
    retry: false,
    queryFn: async () => {
      const { data, error } = await supabase.from("milestones").select("*").order("sort_order", { ascending: true });
      if (error) {
        // Keep UI usable when milestones table is not migrated yet.
        if ((error as any).code === "PGRST205" || (error as any).status === 404) return [];
        throw error;
      }
      return data ?? [];
    },
  });
}

export function useJobMatches() {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["job_matches", user?.id],
    enabled: !!user || disableAuth,
    retry: false,
    queryFn: async () => {
      const { data, error } = await supabase.from("job_matches").select("*");
      if (error) {
        // Job finder backend is still pending integration; treat missing table as empty list.
        if ((error as any).code === "PGRST205" || (error as any).status === 404) return [];
        throw error;
      }
      return data ?? [];
    },
  });
}

export function useTargetRoles() {
  return useQuery({
    queryKey: ["target_roles"],
    queryFn: getTargetRoles,
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
