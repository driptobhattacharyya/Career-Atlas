import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  OnboardingPipeline,
  PIPELINE_STORAGE_KEY,
  isPipelineActive,
  isPipelineComplete,
  resolveOnboardingStatus,
  stepPhase,
  type OnboardingSignals,
  type PipelineDeps,
  type StepId,
} from "./onboarding-pipeline";

// ── helpers ────────────────────────────────────────────────────────────────

function deferred<T = void>() {
  let resolve!: (v: T) => void;
  let reject!: (e: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

const flush = () => new Promise((r) => setTimeout(r, 0));

function memoryStorage() {
  const map = new Map<string, string>();
  return {
    getItem: (k: string) => map.get(k) ?? null,
    setItem: (k: string, v: string) => void map.set(k, v),
    removeItem: (k: string) => void map.delete(k),
    map,
  };
}

/** Deps whose calls resolve immediately unless overridden. */
function makeDeps(overrides: Partial<PipelineDeps> = {}) {
  const deps = {
    ensureProfile: vi.fn(async () => {}),
    saveTargetRole: vi.fn(async () => {}),
    runGaps: vi.fn(async () => {}),
    hasRoadmap: vi.fn(async () => false),
    runRoadmap: vi.fn(async () => {}),
    hasJobs: vi.fn(async () => false),
    runJobs: vi.fn(async () => {}),
    storage: memoryStorage(),
    ...overrides,
  };
  return deps;
}

const ROLE = { id: "role-uuid-1", title: "ML Engineer" };
const statuses = (p: OnboardingPipeline) =>
  Object.fromEntries(
    (["profile", "gaps", "roadmap", "jobs"] as StepId[]).map((id) => [
      id,
      p.getSnapshot().steps[id].status,
    ]),
  );

// ── pipeline ───────────────────────────────────────────────────────────────

describe("OnboardingPipeline", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("runs profile first, then gaps and jobs in parallel, then roadmap after gaps", async () => {
    const profile = deferred();
    const gaps = deferred();
    const jobs = deferred();
    const deps = makeDeps({
      ensureProfile: vi.fn(() => profile.promise),
      runGaps: vi.fn(() => gaps.promise),
      runJobs: vi.fn(() => jobs.promise),
    });
    const p = new OnboardingPipeline(deps);

    p.start(ROLE);
    expect(statuses(p)).toEqual({
      profile: "running",
      gaps: "pending",
      roadmap: "pending",
      jobs: "pending",
    });
    expect(deps.runGaps).not.toHaveBeenCalled();

    profile.resolve();
    await flush();
    expect(deps.saveTargetRole).toHaveBeenCalledWith("role-uuid-1", "ML Engineer");
    expect(statuses(p)).toEqual({
      profile: "done",
      gaps: "running",
      roadmap: "pending",
      jobs: "running",
    });
    expect(deps.runGaps).toHaveBeenCalledWith("ML Engineer");
    expect(deps.runJobs).toHaveBeenCalledWith("role-uuid-1");
    expect(deps.runRoadmap).not.toHaveBeenCalled();

    gaps.resolve();
    await flush();
    expect(deps.runRoadmap).toHaveBeenCalledWith("role-uuid-1");
    expect(p.getSnapshot().steps.roadmap.status).toBe("done");
    expect(isPipelineComplete(p.getSnapshot())).toBe(false); // jobs still running

    jobs.resolve();
    await flush();
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);
    expect(isPipelineActive(p.getSnapshot())).toBe(false);
  });

  it("does not start a duplicate run for the same role while one is in flight", async () => {
    const gaps = deferred();
    const deps = makeDeps({ runGaps: vi.fn(() => gaps.promise) });
    const p = new OnboardingPipeline(deps);

    expect(p.start(ROLE)).toBe(true);
    expect(p.start(ROLE)).toBe(false);
    await flush();
    expect(p.start({ ...ROLE })).toBe(false);
    expect(p.resume()).toBe(false); // e.g. provider effect re-running in strict mode

    gaps.resolve();
    await flush();
    expect(deps.ensureProfile).toHaveBeenCalledTimes(1);
    expect(deps.runGaps).toHaveBeenCalledTimes(1);
    expect(deps.runRoadmap).toHaveBeenCalledTimes(1);
    expect(deps.runJobs).toHaveBeenCalledTimes(1);
  });

  it("starts a new run (and ignores the old one's results) when the role changes", async () => {
    const firstGaps = deferred();
    const runGaps = vi
      .fn<PipelineDeps["runGaps"]>()
      .mockImplementationOnce(() => firstGaps.promise)
      .mockResolvedValue(undefined);
    const deps = makeDeps({ runGaps });
    const p = new OnboardingPipeline(deps);

    p.start(ROLE);
    await flush();
    const firstRun = p.getSnapshot().runId;
    expect(p.start({ id: "role-uuid-2", title: "Data Engineer" })).toBe(true);
    expect(p.getSnapshot().runId).not.toBe(firstRun);
    await flush();
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);

    firstGaps.reject(new Error("late failure from the old run"));
    await flush();
    expect(p.getSnapshot().steps.gaps.status).toBe("done");
    expect(p.getSnapshot().role?.title).toBe("Data Engineer");
  });

  it("keeps dependents pending on failure, lets independent steps finish, and resumes on retry", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    const runGaps = vi
      .fn<PipelineDeps["runGaps"]>()
      .mockRejectedValueOnce(new Error("Gap Analysis Error: LLM timeout"))
      .mockResolvedValueOnce(undefined);
    const deps = makeDeps({ runGaps });
    const p = new OnboardingPipeline(deps);

    p.start(ROLE);
    await flush();
    let s = p.getSnapshot();
    expect(s.steps.gaps).toEqual({ status: "failed", error: "Gap Analysis Error: LLM timeout" });
    expect(s.steps.roadmap.status).toBe("pending");
    expect(s.steps.jobs.status).toBe("done");
    expect(deps.runRoadmap).not.toHaveBeenCalled();
    expect(isPipelineActive(s)).toBe(true);
    // Pages: gaps + roadmap show their failure/normal state, not "preparing".
    expect(stepPhase(s, "gaps")).toBe("failed");
    expect(stepPhase(s, "roadmap")).toBe("failed");
    expect(stepPhase(s, "jobs")).toBe("idle");

    p.retry("gaps");
    await flush();
    s = p.getSnapshot();
    expect(runGaps).toHaveBeenCalledTimes(2);
    expect(deps.runRoadmap).toHaveBeenCalledTimes(1);
    expect(deps.runJobs).toHaveBeenCalledTimes(1); // not re-run
    expect(isPipelineComplete(s)).toBe(true);
  });

  it("retry is a no-op for steps that have not failed", async () => {
    const deps = makeDeps();
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    p.retry("gaps");
    await flush();
    expect(deps.runGaps).toHaveBeenCalledTimes(1);
  });

  it("does not fail the profile step when only saving the target role fails", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    const deps = makeDeps({ saveTargetRole: vi.fn(async () => Promise.reject(new Error("500"))) });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    expect(p.getSnapshot().steps.profile.status).toBe("done");
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);
  });

  it("fails the profile step (and blocks everything) when there is no stored resume", async () => {
    const deps = makeDeps({
      ensureProfile: vi.fn(async () => Promise.reject(new Error("no resume"))),
    });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    const s = p.getSnapshot();
    expect(s.steps.profile.status).toBe("failed");
    expect(deps.runGaps).not.toHaveBeenCalled();
    expect(deps.runJobs).not.toHaveBeenCalled();
    expect(stepPhase(s, "jobs")).toBe("failed");
  });

  it("skips roadmap and jobs for a free-text custom role", async () => {
    const deps = makeDeps();
    const p = new OnboardingPipeline(deps);
    p.start({ id: "custom", title: "Pastry Chef" });
    await flush();
    expect(statuses(p)).toEqual({
      profile: "done",
      gaps: "done",
      roadmap: "skipped",
      jobs: "skipped",
    });
    expect(deps.saveTargetRole).not.toHaveBeenCalled();
    expect(deps.runRoadmap).not.toHaveBeenCalled();
    expect(deps.runJobs).not.toHaveBeenCalled();
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);
  });

  it("persists progress and resumes only the unfinished steps after a reload", async () => {
    const storage = memoryStorage();
    const roadmap = deferred();
    const first = makeDeps({
      storage,
      runRoadmap: vi.fn(() => roadmap.promise),
      runJobs: vi.fn(() => new Promise<void>(() => {})),
    });
    const p1 = new OnboardingPipeline(first);
    p1.start(ROLE);
    await flush();
    expect(statuses(p1)).toMatchObject({
      profile: "done",
      gaps: "done",
      roadmap: "running",
      jobs: "running",
    });
    expect(JSON.parse(storage.getItem(PIPELINE_STORAGE_KEY)!)).toMatchObject({
      role: ROLE,
      finished: ["profile", "gaps"],
    });

    // "Reload": new instance, same storage. The roadmap was actually written
    // server-side by the request that was in flight, jobs was not.
    const second = makeDeps({
      storage,
      hasRoadmap: vi.fn(async () => true),
      hasJobs: vi.fn(async () => false),
    });
    const p2 = new OnboardingPipeline(second);
    expect(p2.resume()).toBe(true);
    expect(p2.resume()).toBe(false);
    await flush();
    expect(second.ensureProfile).not.toHaveBeenCalled();
    expect(second.runGaps).not.toHaveBeenCalled();
    expect(second.hasRoadmap).toHaveBeenCalledWith("role-uuid-1");
    expect(second.runRoadmap).not.toHaveBeenCalled();
    expect(second.hasJobs).toHaveBeenCalledWith("ML Engineer");
    expect(second.runJobs).toHaveBeenCalledWith("role-uuid-1");
    expect(isPipelineComplete(p2.getSnapshot())).toBe(true);
    expect(storage.getItem(PIPELINE_STORAGE_KEY)).toBeNull(); // cleared on completion
  });

  it("a fresh start from the wizard does not short-circuit on existing data", async () => {
    const deps = makeDeps({
      hasRoadmap: vi.fn(async () => true),
      hasJobs: vi.fn(async () => true),
    });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    expect(deps.hasRoadmap).not.toHaveBeenCalled();
    expect(deps.runRoadmap).toHaveBeenCalledTimes(1);
    expect(deps.runJobs).toHaveBeenCalledTimes(1);
  });

  it("reset clears state + storage and ignores in-flight results", async () => {
    const gaps = deferred();
    const storage = memoryStorage();
    const deps = makeDeps({ storage, runGaps: vi.fn(() => gaps.promise) });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    expect(storage.getItem(PIPELINE_STORAGE_KEY)).not.toBeNull();
    p.reset();
    expect(p.getSnapshot().runId).toBeNull();
    expect(storage.getItem(PIPELINE_STORAGE_KEY)).toBeNull();
    gaps.resolve();
    await flush();
    expect(p.getSnapshot().runId).toBeNull();
    expect(deps.runRoadmap).not.toHaveBeenCalled();
  });

  it("notifies subscribers on every state change", async () => {
    const p = new OnboardingPipeline(makeDeps());
    const listener = vi.fn();
    const unsubscribe = p.subscribe(listener);
    p.start(ROLE);
    await flush();
    expect(listener).toHaveBeenCalled();
    unsubscribe();
    listener.mockClear();
    p.reset();
    expect(listener).not.toHaveBeenCalled();
  });

  it("reports 'preparing' for steps that are queued or running", async () => {
    const profile = deferred();
    const p = new OnboardingPipeline(makeDeps({ ensureProfile: vi.fn(() => profile.promise) }));
    expect(stepPhase(p.getSnapshot(), "gaps")).toBe("idle"); // no run
    p.start(ROLE);
    expect(stepPhase(p.getSnapshot(), "gaps")).toBe("preparing");
    expect(stepPhase(p.getSnapshot(), "roadmap")).toBe("preparing");
    profile.resolve();
    await flush();
    expect(stepPhase(p.getSnapshot(), "gaps")).toBe("idle"); // done
  });
});

// ── returning vs new ───────────────────────────────────────────────────────

describe("resolveOnboardingStatus", () => {
  const base: OnboardingSignals = {
    authLoading: false,
    signedIn: true,
    serverLoading: false,
    serverError: false,
    hasResume: false,
    serverTargetRole: null,
    hasMilestones: false,
    localTargetRole: null,
    pipelineActive: false,
  };

  it("waits for auth before deciding", () => {
    expect(
      resolveOnboardingStatus({
        ...base,
        authLoading: true,
        hasResume: true,
        serverTargetRole: "X",
      }),
    ).toBe("loading");
  });

  it("sends signed-out visitors to the wizard (account step)", () => {
    expect(resolveOnboardingStatus({ ...base, signedIn: false })).toBe("needs-onboarding");
  });

  it("shows a neutral loading state while server checks are in flight (no wizard flash)", () => {
    expect(resolveOnboardingStatus({ ...base, serverLoading: true })).toBe("loading");
  });

  it("treats a user with a resume and a saved analysis as returning (cross-device: no localStorage)", () => {
    expect(
      resolveOnboardingStatus({ ...base, hasResume: true, serverTargetRole: "ML Engineer" }),
    ).toBe("onboarded");
  });

  it("treats a user with a resume and an existing roadmap as returning", () => {
    expect(resolveOnboardingStatus({ ...base, hasResume: true, hasMilestones: true })).toBe(
      "onboarded",
    );
  });

  it("falls back to a role picked on this device (zero-gap analyses store no rows)", () => {
    expect(
      resolveOnboardingStatus({ ...base, hasResume: true, localTargetRole: "ML Engineer" }),
    ).toBe("onboarded");
  });

  it("sends a user with a resume but no role/analysis through the wizard", () => {
    expect(resolveOnboardingStatus({ ...base, hasResume: true })).toBe("needs-onboarding");
  });

  it("requires a resume: a stale local role alone is not enough", () => {
    expect(resolveOnboardingStatus({ ...base, localTargetRole: "ML Engineer" })).toBe(
      "needs-onboarding",
    );
  });

  it("treats a user whose background pipeline is running as onboarded, even mid-check", () => {
    expect(resolveOnboardingStatus({ ...base, serverLoading: true, pipelineActive: true })).toBe(
      "onboarded",
    );
  });

  it("surfaces server errors instead of guessing", () => {
    expect(resolveOnboardingStatus({ ...base, serverError: true })).toBe("error");
  });
});
