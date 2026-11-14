import { describe, it, expect, vi, beforeEach } from "vitest";

import {
  OnboardingPipeline,
  PIPELINE_STORAGE_KEY,
  SAVE_ROLE_ATTEMPTS,
  isPipelineActive,
  isPipelineComplete,
  resolveAppGuard,
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
    retryDelayMs: 0,
    storage: memoryStorage(),
    ...overrides,
  };
  return deps;
}

const ROLE = { id: "role-uuid-1", title: "ML Engineer" };
const statuses = (p: OnboardingPipeline) =>
  Object.fromEntries(
    (["profile", "gaps", "roadmap"] as StepId[]).map((id) => [
      id,
      p.getSnapshot().steps[id].status,
    ]),
  );

// ── pipeline ───────────────────────────────────────────────────────────────

describe("OnboardingPipeline", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("runs profile (saving the role) first, then gaps, then roadmap — no job matching", async () => {
    const profile = deferred();
    const gaps = deferred();
    const deps = makeDeps({
      ensureProfile: vi.fn(() => profile.promise),
      runGaps: vi.fn(() => gaps.promise),
    });
    const p = new OnboardingPipeline(deps);

    p.start(ROLE);
    expect(statuses(p)).toEqual({
      profile: "running",
      gaps: "pending",
      roadmap: "pending",
    });
    expect(deps.runGaps).not.toHaveBeenCalled();
    expect(deps.saveTargetRole).not.toHaveBeenCalled();

    profile.resolve();
    await flush();
    expect(deps.saveTargetRole).toHaveBeenCalledWith("role-uuid-1", "ML Engineer");
    expect(statuses(p)).toEqual({
      profile: "done",
      gaps: "running",
      roadmap: "pending",
    });
    expect(deps.runGaps).toHaveBeenCalledWith("ML Engineer");
    expect(deps.runRoadmap).not.toHaveBeenCalled();
    expect(Object.keys(p.getSnapshot().steps)).toEqual(["profile", "gaps", "roadmap"]);

    gaps.resolve();
    await flush();
    expect(deps.runRoadmap).toHaveBeenCalledWith("role-uuid-1");
    expect(p.getSnapshot().steps.roadmap.status).toBe("done");
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

  it("keeps dependents pending on failure and resumes on retry", async () => {
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
    expect(deps.runRoadmap).not.toHaveBeenCalled();
    expect(isPipelineActive(s)).toBe(true);
    // Pages: gaps + roadmap show their failure/normal state, not "preparing".
    expect(stepPhase(s, "gaps")).toBe("failed");
    expect(stepPhase(s, "roadmap")).toBe("failed");

    p.retry("gaps");
    await flush();
    s = p.getSnapshot();
    expect(runGaps).toHaveBeenCalledTimes(2);
    expect(deps.ensureProfile).toHaveBeenCalledTimes(1); // not re-run
    expect(deps.runRoadmap).toHaveBeenCalledTimes(1);
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

  it("retries a transient failure to save the target role", async () => {
    const saveTargetRole = vi
      .fn<PipelineDeps["saveTargetRole"]>()
      .mockRejectedValueOnce(new Error("500"))
      .mockResolvedValueOnce(undefined);
    const deps = makeDeps({ saveTargetRole });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    await flush();
    expect(saveTargetRole).toHaveBeenCalledTimes(2);
    expect(p.getSnapshot().steps.profile.status).toBe("done");
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);
  });

  it("fails the profile step (retryable) when the target role cannot be saved", async () => {
    vi.spyOn(console, "warn").mockImplementation(() => {});
    const saveTargetRole = vi.fn<PipelineDeps["saveTargetRole"]>().mockRejectedValue(new Error("500"));
    const deps = makeDeps({ saveTargetRole });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    for (let i = 0; i < SAVE_ROLE_ATTEMPTS + 1; i++) await flush();
    expect(saveTargetRole).toHaveBeenCalledTimes(SAVE_ROLE_ATTEMPTS);
    expect(p.getSnapshot().steps.profile).toEqual({
      status: "failed",
      error: "We couldn't save your target role. Please retry.",
    });
    expect(deps.runGaps).not.toHaveBeenCalled();
    // Still "active" (waiting on a retry), so the user counts as onboarded meanwhile.
    expect(isPipelineActive(p.getSnapshot())).toBe(true);

    saveTargetRole.mockResolvedValue(undefined);
    p.retry("profile");
    await flush();
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
    expect(stepPhase(s, "roadmap")).toBe("failed");
  });

  it("skips roadmap for a free-text custom role (and saves no catalog role)", async () => {
    const deps = makeDeps();
    const p = new OnboardingPipeline(deps);
    p.start({ id: "custom", title: "Pastry Chef" });
    await flush();
    expect(statuses(p)).toEqual({
      profile: "done",
      gaps: "done",
      roadmap: "skipped",
    });
    expect(deps.saveTargetRole).not.toHaveBeenCalled();
    expect(deps.runRoadmap).not.toHaveBeenCalled();
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);
  });

  it("persists progress and resumes only the unfinished steps after a reload", async () => {
    const storage = memoryStorage();
    const roadmap = deferred();
    const first = makeDeps({
      storage,
      runRoadmap: vi.fn(() => roadmap.promise),
    });
    const p1 = new OnboardingPipeline(first);
    p1.start(ROLE);
    await flush();
    expect(statuses(p1)).toMatchObject({
      profile: "done",
      gaps: "done",
      roadmap: "running",
    });
    expect(JSON.parse(storage.getItem(PIPELINE_STORAGE_KEY)!)).toMatchObject({
      role: ROLE,
      finished: ["profile", "gaps"],
    });

    // "Reload": new instance, same storage. The roadmap was actually written
    // server-side by the request that was in flight.
    const second = makeDeps({
      storage,
      hasRoadmap: vi.fn(async () => true),
    });
    const p2 = new OnboardingPipeline(second);
    expect(p2.resume()).toBe(true);
    expect(p2.resume()).toBe(false);
    await flush();
    expect(second.ensureProfile).not.toHaveBeenCalled();
    expect(second.runGaps).not.toHaveBeenCalled();
    expect(second.hasRoadmap).toHaveBeenCalledWith("role-uuid-1");
    expect(second.runRoadmap).not.toHaveBeenCalled();
    expect(isPipelineComplete(p2.getSnapshot())).toBe(true);
    expect(storage.getItem(PIPELINE_STORAGE_KEY)).toBeNull(); // cleared on completion
  });

  it("resumes a run persisted by an older build that still had a jobs step", async () => {
    const storage = memoryStorage();
    storage.setItem(
      PIPELINE_STORAGE_KEY,
      JSON.stringify({ runId: "old", role: ROLE, finished: ["profile", "jobs"] }),
    );
    const deps = makeDeps({ storage });
    const p = new OnboardingPipeline(deps);
    expect(p.resume()).toBe(true);
    expect(Object.keys(p.getSnapshot().steps)).toEqual(["profile", "gaps", "roadmap"]);
    await flush();
    expect(deps.runGaps).toHaveBeenCalledTimes(1);
    expect(isPipelineComplete(p.getSnapshot())).toBe(true);
    expect(storage.getItem(PIPELINE_STORAGE_KEY)).toBeNull();
  });

  it("drops a persisted old-build run whose only unfinished step was jobs", async () => {
    const storage = memoryStorage();
    storage.setItem(
      PIPELINE_STORAGE_KEY,
      JSON.stringify({ runId: "old", role: ROLE, finished: ["profile", "gaps", "roadmap"] }),
    );
    const deps = makeDeps({ storage });
    const p = new OnboardingPipeline(deps);
    expect(p.resume()).toBe(false);
    expect(p.getSnapshot().runId).toBeNull();
    expect(isPipelineActive(p.getSnapshot())).toBe(false);
    expect(storage.getItem(PIPELINE_STORAGE_KEY)).toBeNull();
  });

  it("a fresh start from the wizard does not short-circuit on existing data", async () => {
    const deps = makeDeps({
      hasRoadmap: vi.fn(async () => true),
    });
    const p = new OnboardingPipeline(deps);
    p.start(ROLE);
    await flush();
    expect(deps.hasRoadmap).not.toHaveBeenCalled();
    expect(deps.runRoadmap).toHaveBeenCalledTimes(1);
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
    serverOnboarded: false,
    pipelineActive: false,
  };

  it("waits for auth before deciding", () => {
    expect(
      resolveOnboardingStatus({ ...base, authLoading: true, serverOnboarded: true }),
    ).toBe("loading");
  });

  it("sends signed-out visitors to the wizard (account step)", () => {
    expect(resolveOnboardingStatus({ ...base, signedIn: false })).toBe("needs-onboarding");
  });

  it("shows a neutral loading state while the server check is in flight (no wizard flash)", () => {
    expect(resolveOnboardingStatus({ ...base, serverLoading: true })).toBe("loading");
  });

  it("follows the server's verdict (same answer on every device)", () => {
    expect(resolveOnboardingStatus({ ...base, serverOnboarded: true })).toBe("onboarded");
    expect(resolveOnboardingStatus({ ...base, serverOnboarded: false })).toBe("needs-onboarding");
  });

  it("treats a user whose background pipeline is running as onboarded, even mid-check", () => {
    expect(resolveOnboardingStatus({ ...base, serverLoading: true, pipelineActive: true })).toBe(
      "onboarded",
    );
    expect(resolveOnboardingStatus({ ...base, serverError: true, pipelineActive: true })).toBe(
      "onboarded",
    );
  });

  it("surfaces server errors instead of guessing", () => {
    expect(resolveOnboardingStatus({ ...base, serverError: true })).toBe("error");
  });
});

describe("resolveAppGuard", () => {
  it("waits (neutral loader) while the status is being decided", () => {
    expect(resolveAppGuard("loading")).toBe("wait");
  });

  it("sends a signed-in user who is not onboarded to the wizard", () => {
    expect(resolveAppGuard("needs-onboarding")).toBe("to-onboarding");
  });

  it("renders the app for onboarded users (incl. an active pipeline)", () => {
    expect(resolveAppGuard("onboarded")).toBe("render");
  });

  it("fails open on a status error (pages have their own empty states)", () => {
    expect(resolveAppGuard("error")).toBe("render");
  });

  it("never redirects in the same state the gate redirects back from (no loop)", () => {
    // The gate leaves for /dashboard only on "onboarded"; the layout leaves for
    // /onboarding only on "needs-onboarding". No status triggers both.
    const statuses = ["loading", "error", "onboarded", "needs-onboarding"] as const;
    for (const st of statuses) {
      const gateLeaves = st === "onboarded";
      const layoutLeaves = resolveAppGuard(st) === "to-onboarding";
      expect(gateLeaves && layoutLeaves).toBe(false);
    }
  });
});
