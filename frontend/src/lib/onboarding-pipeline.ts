/**
 * Post-onboarding "build my atlas" pipeline.
 *
 * The backend runs on Lambda: every endpoint does its work inside the request
 * and returns, so there is no server-side background worker. "Background" here
 * means: the client starts the requests once, keeps them alive in a singleton
 * that outlives page navigation (owned by OnboardingPipelineProvider at the
 * root), and reports their real state to the UI.
 *
 * Steps (dependencies in brackets):
 *   profile  []          confirm the resume is stored + persist the target role
 *   gaps     [profile]   POST /api/analyze-gaps/  (server-cached per resume+role)
 *   roadmap  [gaps]      POST /api/deep-research/ (reads the stored gaps)
 *
 * Job matching is not part of the pipeline: it runs on demand from the Jobs
 * page. roadmap needs a catalog target_role_id, so it is "skipped" for a
 * free-text custom role. A failed step leaves its dependents pending until it
 * is retried. Progress (which steps are done) is persisted so a reload resumes
 * the remaining steps instead of starting over.
 *
 * This module is framework-free so it can be unit-tested without React.
 */

export const STEP_IDS = ["profile", "gaps", "roadmap"] as const;
export type StepId = (typeof STEP_IDS)[number];
export type StepStatus = "pending" | "running" | "done" | "failed" | "skipped";

export interface StepState {
  status: StepStatus;
  error?: string;
}

export interface PipelineRole {
  /** Catalog target_roles.id, or "custom" for a free-text role. */
  id: string;
  title: string;
}

export interface PipelineSnapshot {
  runId: string | null;
  role: PipelineRole | null;
  steps: Record<StepId, StepState>;
}

export interface PipelineDeps {
  /** Throws if the user has no stored resume. */
  ensureProfile: () => Promise<void>;
  /**
   * Persist the target role server-side. Returning-user recognition depends
   * on it, so it is retried and, if it still fails, fails the profile step.
   */
  saveTargetRole: (roleId: string, roleTitle: string) => Promise<void>;
  runGaps: (roleTitle: string) => Promise<void>;
  /** True when a roadmap for this role already exists (used when resuming). */
  hasRoadmap: (roleId: string) => Promise<boolean>;
  runRoadmap: (roleId: string) => Promise<void>;
  /** Delay between saveTargetRole attempts (tests pass 0). */
  retryDelayMs?: number;
  storage?: Pick<Storage, "getItem" | "setItem" | "removeItem"> | null;
}

export const PIPELINE_STORAGE_KEY = "careeratlas:onboarding_pipeline";

export const STEP_DEPENDENCIES: Record<StepId, StepId[]> = {
  profile: [],
  gaps: ["profile"],
  roadmap: ["gaps"],
};

/** saveTargetRole attempts before the profile step fails. */
export const SAVE_ROLE_ATTEMPTS = 3;

export const isCatalogRole = (role: PipelineRole | null) =>
  !!role && !!role.id && role.id !== "custom";

const freshSteps = (): Record<StepId, StepState> => ({
  profile: { status: "pending" },
  gaps: { status: "pending" },
  roadmap: { status: "pending" },
});

export const EMPTY_SNAPSHOT: PipelineSnapshot = {
  runId: null,
  role: null,
  steps: freshSteps(),
};

const TERMINAL: StepStatus[] = ["done", "skipped"];

/** Every step finished (done or skipped). */
export function isPipelineComplete(s: PipelineSnapshot): boolean {
  return !!s.runId && STEP_IDS.every((id) => TERMINAL.includes(s.steps[id].status));
}

/** A run exists and has not finished (it may be waiting on a retry). */
export function isPipelineActive(s: PipelineSnapshot): boolean {
  return !!s.runId && !isPipelineComplete(s);
}

function upstreamFailed(s: PipelineSnapshot, id: StepId): boolean {
  return STEP_DEPENDENCIES[id].some(
    (dep) => s.steps[dep].status === "failed" || upstreamFailed(s, dep),
  );
}

/**
 * How a page should treat its data source:
 *  - "preparing": the pipeline is (or will shortly be) generating it
 *  - "failed":    the step, or something it depends on, failed
 *  - "idle":      no pipeline involvement — render the page normally
 */
export function stepPhase(s: PipelineSnapshot, id: StepId): "idle" | "preparing" | "failed" {
  if (!s.runId) return "idle";
  const st = s.steps[id].status;
  if (st === "failed") return "failed";
  if (st === "pending" || st === "running") {
    return upstreamFailed(s, id) ? "failed" : "preparing";
  }
  return "idle";
}

interface PersistedRun {
  runId: string;
  role: PipelineRole;
  /** Steps that reached done/skipped; anything else is re-run on resume. */
  finished: StepId[];
}

let runCounter = 0;
const newRunId = () => `${Date.now().toString(36)}-${(runCounter++).toString(36)}`;

export class OnboardingPipeline {
  private snapshot: PipelineSnapshot = EMPTY_SNAPSHOT;
  private listeners = new Set<() => void>();
  /** Fresh = just started from the wizard; skip "already exists?" checks. */
  private fresh = true;

  constructor(private deps: PipelineDeps) {}

  getSnapshot = (): PipelineSnapshot => this.snapshot;

  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => {
      this.listeners.delete(listener);
    };
  };

  /**
   * Start a run for this role. No-op (returns false) when a run for the same
   * role is already in flight, so double clicks / strict-mode re-invocations /
   * revisits cannot start a duplicate.
   */
  start(role: PipelineRole): boolean {
    const cur = this.snapshot;
    if (isPipelineActive(cur) && cur.role?.id === role.id && cur.role?.title === role.title) {
      return false;
    }
    this.fresh = true;
    this.setSnapshot({ runId: newRunId(), role, steps: freshSteps() });
    this.pump();
    return true;
  }

  /**
   * Resume a run persisted by an earlier page load. Idempotent: does nothing
   * if a run is already loaded or nothing was persisted.
   */
  resume(): boolean {
    if (this.snapshot.runId) return false;
    const saved = this.readPersisted();
    if (!saved) return false;
    const steps = freshSteps();
    // Unknown ids (e.g. the retired "jobs" step from an older build) are ignored.
    for (const id of saved.finished) {
      if ((STEP_IDS as readonly string[]).includes(id)) steps[id] = { status: "done" };
    }
    if (STEP_IDS.every((id) => steps[id].status === "done")) {
      // Only steps that no longer exist were left: nothing to resume.
      this.deps.storage?.removeItem(PIPELINE_STORAGE_KEY);
      return false;
    }
    this.fresh = false;
    this.setSnapshot({ runId: saved.runId, role: saved.role, steps });
    this.pump();
    return true;
  }

  /** Re-run a failed step; its pending dependents follow automatically. */
  retry(id: StepId): void {
    if (this.snapshot.steps[id].status !== "failed") return;
    this.updateStep(this.snapshot.runId, id, { status: "pending" });
    this.pump();
  }

  /** Forget the current run (completion acknowledged, or user changed). */
  reset(): void {
    this.setSnapshot(EMPTY_SNAPSHOT);
    this.deps.storage?.removeItem(PIPELINE_STORAGE_KEY);
  }

  // ── internals ─────────────────────────────────────────────────────────────

  private pump(): void {
    const s = this.snapshot;
    if (!s.runId || !s.role) return;
    for (const id of STEP_IDS) {
      if (this.snapshot.steps[id].status !== "pending") continue;
      const ready = STEP_DEPENDENCIES[id].every((d) =>
        TERMINAL.includes(this.snapshot.steps[d].status),
      );
      if (ready) void this.runStep(s.runId, s.role, id);
    }
  }

  private async runStep(runId: string, role: PipelineRole, id: StepId): Promise<void> {
    // Mark running synchronously so a concurrent pump() can't start it twice.
    this.updateStep(runId, id, { status: "running" });
    try {
      const outcome = await this.execute(role, id);
      this.updateStep(runId, id, { status: outcome });
    } catch (err) {
      const message = err instanceof Error && err.message ? err.message : "Something went wrong.";
      this.updateStep(runId, id, { status: "failed", error: message });
    }
    if (this.snapshot.runId === runId) this.pump();
  }

  private async execute(role: PipelineRole, id: StepId): Promise<"done" | "skipped"> {
    const d = this.deps;
    switch (id) {
      case "profile":
        await d.ensureProfile();
        if (isCatalogRole(role)) await this.saveRoleWithRetry(role);
        return "done";
      case "gaps":
        await d.runGaps(role.title);
        return "done";
      case "roadmap":
        if (!isCatalogRole(role)) return "skipped";
        if (!this.fresh && (await d.hasRoadmap(role.id))) return "done";
        await d.runRoadmap(role.id);
        return "done";
    }
  }

  private async saveRoleWithRetry(role: PipelineRole): Promise<void> {
    const delay = this.deps.retryDelayMs ?? 1000;
    for (let attempt = 1; ; attempt++) {
      try {
        await this.deps.saveTargetRole(role.id, role.title);
        return;
      } catch (err) {
        if (attempt >= SAVE_ROLE_ATTEMPTS) {
          console.warn("Could not save target role", err);
          throw new Error("We couldn't save your target role. Please retry.");
        }
        await new Promise((r) => setTimeout(r, delay * attempt));
      }
    }
  }

  private updateStep(runId: string | null, id: StepId, next: StepState): void {
    // Results from a superseded run (role changed / reset) are ignored.
    if (!runId || this.snapshot.runId !== runId) return;
    this.setSnapshot({
      ...this.snapshot,
      steps: { ...this.snapshot.steps, [id]: next },
    });
  }

  private setSnapshot(next: PipelineSnapshot): void {
    this.snapshot = next;
    this.persist();
    this.listeners.forEach((l) => l());
  }

  private persist(): void {
    const storage = this.deps.storage;
    if (!storage) return;
    const s = this.snapshot;
    try {
      if (!s.runId || !s.role || isPipelineComplete(s)) {
        storage.removeItem(PIPELINE_STORAGE_KEY);
        return;
      }
      const finished = STEP_IDS.filter((id) => TERMINAL.includes(s.steps[id].status));
      const data: PersistedRun = { runId: s.runId, role: s.role, finished };
      storage.setItem(PIPELINE_STORAGE_KEY, JSON.stringify(data));
    } catch {
      // storage full / unavailable — resume just won't survive a reload
    }
  }

  private readPersisted(): PersistedRun | null {
    try {
      const raw = this.deps.storage?.getItem(PIPELINE_STORAGE_KEY);
      if (!raw) return null;
      const parsed = JSON.parse(raw) as PersistedRun;
      if (!parsed?.runId || !parsed.role?.title) return null;
      return { ...parsed, finished: Array.isArray(parsed.finished) ? parsed.finished : [] };
    } catch {
      return null;
    }
  }
}

// ── Returning-vs-new decision ──────────────────────────────────────────────

export type OnboardingStatus = "loading" | "error" | "onboarded" | "needs-onboarding";

export interface OnboardingSignals {
  authLoading: boolean;
  signedIn: boolean;
  /** GET /api/parse-resume/profile still loading. */
  serverLoading: boolean;
  serverError: boolean;
  /** The server's verdict (resume + saved role / gap analysis / roadmap). */
  serverOnboarded: boolean;
  /** A background pipeline run exists for this user (just finished the wizard). */
  pipelineActive: boolean;
}

/**
 * Decide whether a signed-in visitor is a returning user (skip the wizard).
 * The backend is the authority, so the answer is the same on every device;
 * an in-flight pipeline counts as onboarded because its first step is what
 * makes the server say so.
 */
export function resolveOnboardingStatus(s: OnboardingSignals): OnboardingStatus {
  if (s.authLoading) return "loading";
  if (!s.signedIn) return "needs-onboarding";
  if (s.pipelineActive) return "onboarded";
  if (s.serverLoading) return "loading";
  if (s.serverError) return "error";
  return s.serverOnboarded ? "onboarded" : "needs-onboarding";
}

export type AppGuardDecision = "wait" | "render" | "to-onboarding";

/**
 * What the signed-in app layout (/dashboard, /gaps, …) does with the status.
 * Only a definite "needs-onboarding" redirects to the wizard — the gate only
 * redirects back on "onboarded", so the two can never bounce. Errors fail
 * open: pages have their own empty states.
 */
export function resolveAppGuard(status: OnboardingStatus): AppGuardDecision {
  switch (status) {
    case "loading":
      return "wait";
    case "needs-onboarding":
      return "to-onboarding";
    default:
      return "render";
  }
}
