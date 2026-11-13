import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useSyncExternalStore,
} from "react";
import { useQueryClient, type QueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useAuth } from "@/context/auth-context";
import {
  ApiError,
  analyzeGaps,
  cacheJobSearchResponse,
  getJobMatches,
  getLatestResume,
  listMilestones,
  researchJobs,
  startDeepResearch,
  updateTargetRole,
} from "@/lib/api";
import {
  EMPTY_SNAPSHOT,
  OnboardingPipeline,
  STEP_IDS,
  isPipelineActive,
  isPipelineComplete,
  stepPhase,
  type PipelineDeps,
  type PipelineRole,
  type PipelineSnapshot,
  type StepId,
  type StepStatus,
} from "@/lib/onboarding-pipeline";

export const STEP_LABELS: Record<StepId, string> = {
  profile: "Evaluating your profile",
  gaps: "Finding your skill gaps",
  roadmap: "Building your roadmap",
  jobs: "Matching jobs",
};

/** Real API calls behind each pipeline step, plus the cache invalidation that
 * lets open pages pick up the result without a reload. */
export function createPipelineDeps(qc: QueryClient): PipelineDeps {
  const storage = typeof window !== "undefined" ? window.localStorage : null;
  return {
    storage,
    ensureProfile: async () => {
      const { resume } = await getLatestResume();
      if (!resume) throw new Error("We couldn't find your saved profile. Re-upload your resume.");
      await qc.invalidateQueries({ queryKey: ["latest-resume"] });
      await qc.invalidateQueries({ queryKey: ["profile-from-resume"] });
    },
    saveTargetRole: async (roleId) => {
      await updateTargetRole(roleId);
    },
    runGaps: async (roleTitle) => {
      const data = await analyzeGaps(roleTitle, false);
      storage?.setItem("careeratlas:last_gap_response", JSON.stringify(data));
      await qc.invalidateQueries({ queryKey: ["gap-analysis"] });
    },
    hasRoadmap: async (roleId) => {
      try {
        const data = await listMilestones(roleId);
        const found = (data.milestones?.length ?? 0) > 0;
        if (found) await qc.invalidateQueries({ queryKey: ["milestones"] });
        return found;
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return false;
        throw err;
      }
    },
    runRoadmap: async (roleId) => {
      await startDeepResearch(roleId, 3);
      await qc.invalidateQueries({ queryKey: ["pathway-latest"] });
      await qc.invalidateQueries({ queryKey: ["milestones"] });
    },
    hasJobs: async (roleTitle) => {
      const data = await getJobMatches();
      const found = data.jobs.length > 0 && data.query_role === roleTitle;
      if (found) {
        cacheJobSearchResponse(data);
        await qc.invalidateQueries({ queryKey: ["job-matches"] });
      }
      return found;
    },
    runJobs: async (roleId) => {
      const data = await researchJobs(roleId);
      cacheJobSearchResponse(data);
      await qc.invalidateQueries({ queryKey: ["job-matches"] });
    },
  };
}

interface PipelineContextValue {
  snapshot: PipelineSnapshot;
  start: (role: PipelineRole) => boolean;
  retry: (id: StepId) => void;
  dismiss: () => void;
}

const PipelineContext = createContext<PipelineContextValue | undefined>(undefined);

export function OnboardingPipelineProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();
  const { user } = useAuth();
  const [pipeline] = useState(() => new OnboardingPipeline(createPipelineDeps(qc)));
  const snapshot = useSyncExternalStore(
    pipeline.subscribe,
    pipeline.getSnapshot,
    () => EMPTY_SNAPSHOT,
  );

  // Pick up a run persisted by an earlier page load; drop it when the
  // signed-in user changes (auth-context also wipes careeratlas:* storage).
  const uid = user?.id ?? null;
  const prevUid = useRef<string | null>(null);
  useEffect(() => {
    if (prevUid.current && prevUid.current !== uid) pipeline.reset();
    prevUid.current = uid;
    if (uid) pipeline.resume();
  }, [uid, pipeline]);

  // Surface failures/completion on whatever page the user is on.
  const prev = useRef<PipelineSnapshot>(snapshot);
  useEffect(() => {
    const before = prev.current;
    prev.current = snapshot;
    if (!snapshot.runId || before.runId !== snapshot.runId) return;
    for (const id of STEP_IDS) {
      if (before.steps[id].status !== "failed" && snapshot.steps[id].status === "failed") {
        toast.error(`${STEP_LABELS[id]} failed`, {
          description: "You can retry it from your dashboard.",
        });
      }
    }
    if (!isPipelineComplete(before) && isPipelineComplete(snapshot)) {
      toast.success("Your atlas is ready", {
        description: "Skill gaps, roadmap and job matches are up to date.",
      });
    }
  }, [snapshot]);

  const value: PipelineContextValue = {
    snapshot,
    start: (role) => pipeline.start(role),
    retry: (id) => pipeline.retry(id),
    dismiss: () => pipeline.reset(),
  };

  return <PipelineContext.Provider value={value}>{children}</PipelineContext.Provider>;
}

const NOOP: PipelineContextValue = {
  snapshot: EMPTY_SNAPSHOT,
  start: () => false,
  retry: () => {},
  dismiss: () => {},
};

export function useOnboardingPipeline(): PipelineContextValue {
  // Fall back to an inert value so isolated component tests (and any tree
  // rendered without the provider) keep working.
  return useContext(PipelineContext) ?? NOOP;
}

/** "preparing" while the pipeline is generating this step's data. */
export function useStepPhase(id: StepId) {
  const { snapshot } = useOnboardingPipeline();
  return stepPhase(snapshot, id);
}

export function usePipelineActive() {
  return isPipelineActive(useOnboardingPipeline().snapshot);
}

export type { StepId, StepStatus };
