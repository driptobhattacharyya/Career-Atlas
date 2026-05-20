/**
 * Career-Atlas backend client.
 *
 * Auth: pulls JWT from the Supabase session and sends it as Bearer.
 * In dev mode (VITE_DISABLE_AUTH=true), the backend reads DEV_USER_ID
 * via DEV_BYPASS_AUTH and accepts requests without a token.
 *
 * Always go through this module — never call the backend or Supabase tables
 * from a component directly. Hooks in @/hooks/queries.ts wrap each call.
 */
import { supabase } from "./supabase";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  "http://localhost:8000"
) as string;

const disableAuth = (import.meta.env.VITE_DISABLE_AUTH as string | undefined) === "true";

export class ApiError extends Error {
  status: number;
  body: string;
  detail: string;
  constructor(status: number, body: string, message?: string) {
    let detail = "";
    try {
      const parsed = JSON.parse(body);
      if (typeof parsed?.detail === "string") detail = parsed.detail;
    } catch {
      // body is not JSON — leave detail empty
    }
    super(message || detail || `API ${status}: ${body || "no body"}`);
    this.status = status;
    this.body = body;
    this.detail = detail;
  }
}

async function authHeaders(extra: Record<string, string> = {}): Promise<Record<string, string>> {
  const headers: Record<string, string> = { ...extra };
  if (disableAuth) return headers;
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

async function request<T = any>(
  path: string,
  init: RequestInit & { jsonBody?: unknown; isMultipart?: boolean } = {},
): Promise<T> {
  const { jsonBody, isMultipart, headers: extraHeaders, ...rest } = init;
  const headers = await authHeaders(
    isMultipart ? {} : { "Content-Type": "application/json" },
  );
  Object.assign(headers, extraHeaders || {});
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers,
    body: jsonBody !== undefined ? JSON.stringify(jsonBody) : init.body,
  });
  const text = await res.text();
  if (!res.ok) throw new ApiError(res.status, text);
  return (text ? JSON.parse(text) : null) as T;
}

// ── Resume ─────────────────────────────────────────────────────────────────

export interface ParseResumeResult {
  success: boolean;
  resume_id: string;
  message?: string;
}

export async function uploadResume(file: File): Promise<ParseResumeResult> {
  const form = new FormData();
  form.append("file", file);
  return request<ParseResumeResult>("/api/parse-resume/", {
    method: "POST",
    body: form,
    isMultipart: true,
  });
}

export async function getLatestResume() {
  return request<{ success: boolean; resume: any | null }>(
    "/api/parse-resume/latest",
    { method: "GET" },
  );
}

// ── Target roles ───────────────────────────────────────────────────────────

export interface TargetRole {
  id: string;
  title: string;
  category: string;
  blurb: string;
  emoji: string;
  popular_skills: string[];
}

export async function getTargetRoles(): Promise<TargetRole[]> {
  const data = await request<{ success: boolean; roles: TargetRole[] }>(
    "/api/target-roles/",
    { method: "GET" },
  );
  return data.roles || [];
}

// ── Gap analysis ───────────────────────────────────────────────────────────

export async function analyzeGaps(targetRoleTitle: string) {
  return request("/api/analyze-gaps/", {
    method: "POST",
    jsonBody: { target_role_title: targetRoleTitle },
  });
}

// ── Roadmap (M1) ───────────────────────────────────────────────────────────

export type MilestoneStatus = "locked" | "in_progress" | "completed" | "skipped";

export interface MilestoneRow {
  id: string;
  user_id?: string | null;
  target_role?: string | null;
  target_role_id?: string | null;
  resume_id?: string | null;
  phase?: string | null;
  title?: string | null;
  skill?: string | null;
  status: MilestoneStatus;
  estimated_weeks?: number | null;
  description?: string | null;
  courses: any[];
  project: any;
  checklist: string[];
  sort_order: number;
  completed_at?: string | null;
  updated_at?: string | null;
}

export async function listMilestones(targetRoleId?: string) {
  const qs = targetRoleId ? `?target_role_id=${encodeURIComponent(targetRoleId)}` : "";
  return request<{ success: boolean; milestones: MilestoneRow[] }>(
    `/api/generate-roadmap/${qs}`,
    { method: "GET" },
  );
}

export async function updateMilestoneStatus(milestoneId: string, status: MilestoneStatus) {
  return request<MilestoneRow>(`/api/generate-roadmap/milestones/${milestoneId}`, {
    method: "PATCH",
    jsonBody: { status },
  });
}

// ── Jobs ───────────────────────────────────────────────────────────────────

export async function getJobMatches() {
  return request<{ success: boolean; jobs: any[] }>("/api/research-jobs/", {
    method: "GET",
  });
}

export async function researchJobs(targetRoleId: string) {
  return request<{ success: boolean; jobs: any[] }>("/api/research-jobs/", {
    method: "POST",
    jsonBody: { target_role_id: targetRoleId },
  });
}

// ── Deep research / Pathways (M2) ──────────────────────────────────────────

export interface PathwayPayload {
  target_role: string;
  milestones: any[];
  rationale: string;
}

export interface JudgeScore {
  criterion: string;
  score: number;
  rationale: string;
}

export interface JudgeVerdict {
  overall_score: number;
  pass_fail: "pass" | "fail";
  strengths: string[];
  weaknesses: string[];
  improvement_actions: string[];
  rubric_scores: JudgeScore[];
  confidence: "low" | "medium" | "high";
}

export interface ValidationResult {
  checked: number;
  kept: number;
  dropped: { milestone_skill: string; title: string; url: string; reason: string }[];
}

export async function startDeepResearch(targetRoleId: string, maxIter = 3) {
  return request<{
    success: boolean;
    target_role: string;
    role_slug: string;
    pathway: PathwayPayload;
    iterations_used: number;
    sources: string[];
    quality_score: number | null;
    quality_passed: boolean | null;
    verdict: JudgeVerdict | null;
    validation: ValidationResult | null;
  }>("/api/deep-research/", {
    method: "POST",
    jsonBody: { target_role_id: targetRoleId, max_iter: maxIter },
  });
}

export async function getLatestPathway(roleId?: string) {
  const qs = roleId ? `?target_role_id=${encodeURIComponent(roleId)}` : "";
  return request<{
    success: boolean;
    role_slug: string;
    target_role: string;
    pathway: PathwayPayload;
    sources: string[];
    iterations_used: number;
    quality_score: number | null;
    quality_verdict: JudgeVerdict | null;
    validation: ValidationResult | null;
    created_at: string;
  }>(`/api/deep-research/latest${qs}`, { method: "GET" });
}

export const API_BASE = API_BASE_URL;
