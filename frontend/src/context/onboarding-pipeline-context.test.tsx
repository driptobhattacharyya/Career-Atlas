import "@testing-library/jest-dom";
import React, { StrictMode } from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { act, render, screen, waitFor, fireEvent, renderHook } from "@testing-library/react";
import { QueryClientProvider, useQuery } from "@tanstack/react-query";

import { OnboardingPipelineProvider, useOnboardingPipeline } from "./onboarding-pipeline-context";
import { PipelineProgressPanel } from "@/components/onboarding-progress";
import { useOnboardingStatus } from "@/hooks/queries";
import { useAuth } from "@/context/auth-context";
import * as api from "@/lib/api";
import { createTestQueryClient } from "../test-utils";

vi.mock("@/context/auth-context", () => ({ useAuth: vi.fn() }));
vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getLatestResume: vi.fn(),
    updateTargetRole: vi.fn(),
    analyzeGaps: vi.fn(),
    getGapAnalysis: vi.fn(),
    listMilestones: vi.fn(),
    startDeepResearch: vi.fn(),
    getJobMatches: vi.fn(),
    researchJobs: vi.fn(),
    getOnboardingProfile: vi.fn(),
  };
});

const mockUseAuth = vi.mocked(useAuth);
type AuthValue = ReturnType<typeof useAuth>;
const authAs = (user: { id: string } | null) => ({ user, loading: false }) as unknown as AuthValue;
type DeepResearchResult = Awaited<ReturnType<typeof api.startDeepResearch>>;
const deepResearchResult = {} as DeepResearchResult;
const ROLE = { id: "role-uuid-1", title: "ML Engineer" };

function Starter() {
  const { start } = useOnboardingPipeline();
  return <button onClick={() => start(ROLE)}>start</button>;
}

/** Stands in for a page (e.g. Gaps) reading the gap-analysis query. */
function GapsReader() {
  const { data } = useQuery({
    queryKey: ["gap-analysis", "u1", false],
    queryFn: async () => (await api.getGapAnalysis()).gaps,
  });
  return <p data-testid="gap-count">{data ? data.length : "…"}</p>;
}

function renderApp() {
  const qc = createTestQueryClient();
  return render(
    <StrictMode>
      <QueryClientProvider client={qc}>
        <OnboardingPipelineProvider>
          <Starter />
          <GapsReader />
          <PipelineProgressPanel />
        </OnboardingPipelineProvider>
      </QueryClientProvider>
    </StrictMode>,
  );
}

const stepStatus = (id: string) =>
  screen.getByTestId(`pipeline-step-${id}`).getAttribute("data-status");

describe("OnboardingPipelineProvider + PipelineProgressPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    mockUseAuth.mockReturnValue(authAs({ id: "u1" }));
    vi.mocked(api.getLatestResume).mockResolvedValue({
      success: true,
      resume: { resume_id: "r1" },
    });
    vi.mocked(api.updateTargetRole).mockResolvedValue({ success: true, target_role_id: ROLE.id });
    vi.mocked(api.analyzeGaps).mockResolvedValue({ gaps: [{ skill: "PyTorch" }] });
    vi.mocked(api.getGapAnalysis).mockResolvedValue({ success: true, target_role: null, gaps: [] });
    vi.mocked(api.startDeepResearch).mockResolvedValue(deepResearchResult);
  });

  it("runs every step exactly once under StrictMode, even with repeated starts, and refreshes open pages", async () => {
    // Job matching is on demand (Jobs page), never part of the pipeline.
    renderApp();
    expect(screen.queryByText("Building your atlas")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("gap-count")).toHaveTextContent("0"));

    // Server now has gaps; the page must pick them up via invalidation.
    vi.mocked(api.getGapAnalysis).mockResolvedValue({
      success: true,
      target_role: ROLE.title,
      gaps: [{ skill: "PyTorch" }],
    });
    fireEvent.click(screen.getByText("start"));
    fireEvent.click(screen.getByText("start"));

    await waitFor(() => expect(screen.getByText(/Your atlas is ready/)).toBeInTheDocument());
    expect(api.getLatestResume).toHaveBeenCalledTimes(1);
    expect(api.updateTargetRole).toHaveBeenCalledWith(ROLE.id);
    expect(api.analyzeGaps).toHaveBeenCalledTimes(1);
    expect(api.analyzeGaps).toHaveBeenCalledWith(ROLE.title, false);
    expect(api.startDeepResearch).toHaveBeenCalledTimes(1);
    expect(api.startDeepResearch).toHaveBeenCalledWith(ROLE.id, 3);
    expect(api.researchJobs).not.toHaveBeenCalled();
    expect(api.getJobMatches).not.toHaveBeenCalled();
    expect(screen.queryByTestId("pipeline-step-jobs")).not.toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId("gap-count")).toHaveTextContent("1"));

    fireEvent.click(screen.getByText("Dismiss"));
    expect(screen.queryByText(/Your atlas is ready/)).not.toBeInTheDocument();
  });

  it("refreshes the onboarding status once the role is saved, so the app guard sees 'onboarded' after the run", async () => {
    vi.mocked(api.getOnboardingProfile)
      .mockResolvedValueOnce({ success: true, has_resume: true, target_role: null, onboarded: false })
      .mockResolvedValue({
        success: true,
        has_resume: true,
        target_role: { id: ROLE.id, title: ROLE.title },
        onboarded: true,
      });
    function StatusReader() {
      const { snapshot } = useOnboardingPipeline();
      const { status } = useOnboardingStatus({ pipelineActive: false });
      return <p data-testid="status">{snapshot.runId ? `run:${status}` : status}</p>;
    }
    const qc = createTestQueryClient();
    render(
      <QueryClientProvider client={qc}>
        <OnboardingPipelineProvider>
          <Starter />
          <StatusReader />
          <PipelineProgressPanel />
        </OnboardingPipelineProvider>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("needs-onboarding"));
    fireEvent.click(screen.getByText("start"));
    await waitFor(() => expect(screen.getByText(/Your atlas is ready/)).toBeInTheDocument());
    await waitFor(() => expect(screen.getByTestId("status")).toHaveTextContent("run:onboarded"));
  });

  it("shows a failed step with a working Retry, and holds the dependent step until then", async () => {
    let releaseRoadmap!: () => void;
    vi.mocked(api.analyzeGaps)
      .mockRejectedValueOnce(new Error("Gap Analysis Error: upstream timeout"))
      .mockResolvedValueOnce({ gaps: [] });
    vi.mocked(api.startDeepResearch).mockImplementation(
      () => new Promise((res) => (releaseRoadmap = () => res(deepResearchResult))),
    );
    renderApp();
    fireEvent.click(screen.getByText("start"));

    await waitFor(() => expect(stepStatus("gaps")).toBe("failed"));
    expect(screen.getByText("Gap Analysis Error: upstream timeout")).toBeInTheDocument();
    expect(stepStatus("roadmap")).toBe("pending");
    expect(api.startDeepResearch).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: /retry/i }));
    await waitFor(() => expect(stepStatus("roadmap")).toBe("running"));
    expect(stepStatus("gaps")).toBe("done");
    expect(screen.getByText(/Researching courses and projects/)).toBeInTheDocument();

    await act(async () => releaseRoadmap());
    await waitFor(() => expect(screen.getByText(/Your atlas is ready/)).toBeInTheDocument());
    expect(api.analyzeGaps).toHaveBeenCalledTimes(2);
    expect(api.researchJobs).not.toHaveBeenCalled();
  });
});

describe("useOnboardingStatus", () => {
  function renderStatus(pipelineActive = false) {
    const qc = createTestQueryClient();
    return renderHook(() => useOnboardingStatus({ pipelineActive }), {
      wrapper: ({ children }) => <QueryClientProvider client={qc}>{children}</QueryClientProvider>,
    });
  }

  const profile = (p: Partial<api.OnboardingProfile>): api.OnboardingProfile => ({
    success: true,
    has_resume: false,
    target_role: null,
    onboarded: false,
    ...p,
  });

  beforeEach(() => {
    vi.clearAllMocks();
    window.localStorage.clear();
    mockUseAuth.mockReturnValue(authAs({ id: "u1" }));
  });

  it("is 'onboarded' from the server's verdict alone (fresh device, empty localStorage)", async () => {
    vi.mocked(api.getOnboardingProfile).mockResolvedValue(
      profile({
        has_resume: true,
        onboarded: true,
        target_role: { id: "ml-engineer", title: "ML Engineer" },
      }),
    );
    const { result } = renderStatus();
    expect(result.current.status).toBe("loading");
    await waitFor(() => expect(result.current.status).toBe("onboarded"));
    expect(result.current.targetRole).toEqual({ id: "ml-engineer", title: "ML Engineer" });
    // The old heuristics are gone: one request decides.
    expect(api.getLatestResume).not.toHaveBeenCalled();
    expect(api.getGapAnalysis).not.toHaveBeenCalled();
    expect(api.listMilestones).not.toHaveBeenCalled();
  });

  it("ignores a locally stored role: the server says 'not onboarded'", async () => {
    window.localStorage.setItem("careeratlas:selected_role_title", "ML Engineer");
    vi.mocked(api.getOnboardingProfile).mockResolvedValue(profile({ has_resume: true }));
    const { result } = renderStatus();
    await waitFor(() => expect(result.current.status).toBe("needs-onboarding"));
  });

  it("is 'needs-onboarding' for a brand-new user", async () => {
    vi.mocked(api.getOnboardingProfile).mockResolvedValue(profile({}));
    const { result } = renderStatus();
    await waitFor(() => expect(result.current.status).toBe("needs-onboarding"));
  });

  it("is 'onboarded' while a pipeline run is active, before the server agrees", async () => {
    vi.mocked(api.getOnboardingProfile).mockResolvedValue(profile({ has_resume: true }));
    const { result } = renderStatus(true);
    expect(result.current.status).toBe("onboarded");
  });

  it("is 'needs-onboarding' when signed out, without hitting the API", async () => {
    mockUseAuth.mockReturnValue(authAs(null));
    const { result } = renderStatus();
    expect(result.current.status).toBe("needs-onboarding");
    expect(api.getOnboardingProfile).not.toHaveBeenCalled();
  });

  it("is 'error' when the server check fails, and recovers on refetch", async () => {
    vi.mocked(api.getOnboardingProfile).mockRejectedValueOnce(new Error("network"));
    const { result } = renderStatus();
    await waitFor(() => expect(result.current.status).toBe("error"));
    vi.mocked(api.getOnboardingProfile).mockResolvedValue(
      profile({ has_resume: true, onboarded: true }),
    );
    act(() => result.current.refetch());
    await waitFor(() => expect(result.current.status).toBe("onboarded"));
  });
});
