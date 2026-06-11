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

export const apiClient = {
  get: (url: string) => request(url, { method: "GET" }).then(data => ({ data })),
  post: (url: string, jsonBody?: any) => request(url, { method: "POST", jsonBody }).then(data => ({ data })),
};

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
  let res: Response;
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers,
      body: jsonBody !== undefined ? JSON.stringify(jsonBody) : init.body,
    });
  } catch {
    // fetch rejects on network failure / backend unreachable / CORS.
    throw new ApiError(
      0,
      "",
      "Can't reach the server. Check your connection and try again.",
    );
  }
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

// ── Profile editing ─────────────────────────────────────────────────────────

export async function updateTargetRole(targetRoleId: string) {
  return request<{ success: boolean; target_role_id: string }>(
    "/api/parse-resume/profile",
    { method: "PATCH", jsonBody: { target_role_id: targetRoleId } },
  );
}

export async function addSkill(skill: string) {
  return request<{ success: boolean; skill: string }>("/api/parse-resume/skills", {
    method: "POST",
    jsonBody: { skill },
  });
}

export async function deleteSkill(skill: string) {
  return request<{ success: boolean; skill: string }>(
    `/api/parse-resume/skills?skill=${encodeURIComponent(skill)}`,
    { method: "DELETE" },
  );
}

export interface ExperiencePatch {
  title?: string;
  company?: string;
  start_date?: string;
  end_date?: string;
}

export async function updateExperience(experienceId: string, fields: ExperiencePatch) {
  return request<{ success: boolean; updated: Record<string, unknown> }>(
    `/api/parse-resume/experiences/${experienceId}`,
    { method: "PATCH", jsonBody: fields },
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

export async function analyzeGaps(targetRoleTitle: string, force = false) {
  return request("/api/analyze-gaps/", {
    method: "POST",
    jsonBody: { target_role_title: targetRoleTitle, force },
  });
}

export async function getGapAnalysis() {
  return request<{ success: boolean; target_role: string | null; gaps: any[] }>(
    "/api/analyze-gaps/",
    { method: "GET" },
  );
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

export interface ScoreBreakdown {
  semantic: number;
  skill_overlap: number;
  experience: number;
  education: number;
  final: number;
}

export interface JobExplanation {
  strengths: string[];
  gaps: string[];
  reasoning: string;
}

export interface JobResult {
  job_id: string;
  title: string;
  company?: string | null;
  location?: string | null;
  apply_url?: string | null;
  score: ScoreBreakdown;
  explanation: JobExplanation;
  remote?: boolean | null;
  seniority?: string | null;
  match_pct?: number | null;
  matched?: string[];
  missing?: string[];
  salary?: string | null;
  posted_days?: number | null;
  description?: string | null;
  external_url?: string | null;
}

export interface JobSearchResponse {
  query_role: string;
  user_location_preference: string;
  total_jobs_fetched: number;
  jobs: JobResult[];
}

function toNumber(value: unknown, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function pct(value: unknown) {
  const n = toNumber(value, 0);
  return n <= 1 ? n * 100 : n;
}

export function normalizeJobResult(job: any): JobResult {
  const scoreSource = job?.score ?? {};
  const explanationSource = job?.explanation ?? {};
  const strengths = Array.isArray(explanationSource?.strengths)
    ? explanationSource.strengths
    : Array.isArray(job?.matched)
      ? job.matched
      : [];
  const gaps = Array.isArray(explanationSource?.gaps)
    ? explanationSource.gaps
    : Array.isArray(job?.missing)
      ? job.missing
      : [];
  const finalScore = scoreSource?.final ?? job?.match_pct ?? 0;
  const normalizedFinal = pct(finalScore);

  return {
    job_id: String(job?.job_id ?? job?.id ?? ""),
    title: String(job?.title ?? "Untitled role"),
    company: job?.company ?? null,
    location: job?.location ?? null,
    apply_url: job?.apply_url ?? job?.external_url ?? null,
    score: {
      semantic: pct(scoreSource?.semantic ?? 0),
      skill_overlap: pct(scoreSource?.skill_overlap ?? 0),
      experience: pct(scoreSource?.experience ?? 0),
      education: pct(scoreSource?.education ?? 0),
      final: normalizedFinal,
    },
    explanation: {
      strengths: strengths.map(String),
      gaps: gaps.map(String),
      reasoning: String(explanationSource?.reasoning ?? job?.description ?? ""),
    },
    remote: job?.remote ?? null,
    seniority: job?.seniority ?? null,
    match_pct: toNumber(job?.match_pct ?? Math.round(normalizedFinal), Math.round(normalizedFinal)),
    matched: Array.isArray(job?.matched) ? job.matched.map(String) : strengths.map(String),
    missing: Array.isArray(job?.missing) ? job.missing.map(String) : gaps.map(String),
    salary: job?.salary ?? null,
    posted_days: job?.posted_days ?? null,
    description: job?.description ?? null,
    external_url: job?.external_url ?? job?.apply_url ?? null,
  };
}

export function normalizeJobSearchResponse(data: any): JobSearchResponse {
  const payload = data?.jobs ? data : data?.success ? data : { jobs: [] };
  const jobs = Array.isArray(payload?.jobs) ? payload.jobs.map(normalizeJobResult) : [];
  return {
    query_role: String(payload?.query_role ?? ""),
    user_location_preference: String(payload?.user_location_preference ?? ""),
    total_jobs_fetched: toNumber(payload?.total_jobs_fetched ?? jobs.length, jobs.length),
    jobs,
  };
}

export async function getJobMatches(): Promise<JobSearchResponse> {
  const data = await request<any>("/api/research-jobs/", {
    method: "GET",
  });
  return normalizeJobSearchResponse(data);
}

export async function researchJobs(targetRoleId: string): Promise<JobSearchResponse> {
  const data = await request<any>("/api/research-jobs/", {
    method: "POST",
    jsonBody: { target_role_id: targetRoleId },
  });
  return normalizeJobSearchResponse(data);
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

type SessionCacheValue = unknown;
const _sessionCache = new Map<string, SessionCacheValue>();

export function qcGet<T = unknown>(key: string): T | undefined {
  return _sessionCache.get(key) as T | undefined;
}

export function qcSet<T = unknown>(key: string, value: T): T {
  _sessionCache.set(key, value);
  return value;
}

export function cacheJobSearchResponse(data: JobSearchResponse): JobSearchResponse {
  return qcSet("job-matches-cached", data);
}

export function getCachedJobSearchResponse(): JobSearchResponse | undefined {
  return qcGet<JobSearchResponse>("job-matches-cached");
}

export const API_BASE = API_BASE_URL;
