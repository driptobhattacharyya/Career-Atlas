import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { useRoadmap, useGapAnalysis, useTargetRoles, useLatestResume } from "./queries";
import { useAuth } from "@/context/auth-context";
import * as api from "@/lib/api";
import { renderHookWithClient, createTestQueryClient } from "../test-utils";

// Single shared mock for the auth context — each describe below configures
// the return value it needs via `mockUseAuth.mockReturnValue(...)`.
vi.mock("@/context/auth-context", () => ({
  useAuth: vi.fn(),
}));

// Single shared partial mock for the API module. Only the functions each
// hook below actually calls are replaced; everything else (including the
// real `ApiError` class, used by the useRoadmap retry-logic assertions)
// passes through untouched.
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    listMilestones: vi.fn(),
    getGapAnalysis: vi.fn(),
    getTargetRoles: vi.fn(),
    getLatestResume: vi.fn(),
  };
});

const { listMilestones, getGapAnalysis, getTargetRoles, getLatestResume, ApiError } = api;
const mockUseAuth = vi.mocked(useAuth);

// ── useRoadmap ───────────────────────────────────────────────────────────
// Source: origin/test/use-roadmap-retry-logic-10771475914975728175

describe("useRoadmap", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({ user: { id: "test-user-id" } } as any);
  });

  it("should not retry on 404 error", async () => {
    const error404 = new ApiError(404, "Not Found", "Not Found");
    vi.mocked(listMilestones).mockRejectedValueOnce(error404);

    const { result } = renderHookWithClient(() => useRoadmap("role-id"));

    await waitFor(() => expect(result.current.isFetching).toBe(false));

    // Verify listMilestones was called only once (no retries)
    expect(listMilestones).toHaveBeenCalledTimes(1);

    // Verify it resolved to an empty array (isSuccess: true, data: [])
    // This happens because queryFn catches the 404, not because of the retry config.
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it("should retry once on non-404 errors (like 500) before failing", async () => {
    const error500 = new ApiError(500, "Server Error", "Server Error");
    vi.mocked(listMilestones)
      .mockRejectedValueOnce(error500) // First try fails with 500
      .mockResolvedValueOnce({ milestones: [{ id: "m1", title: "Milestone 1", status: "pending" }] } as any); // Retry succeeds

    const queryClient = createTestQueryClient();
    queryClient.setDefaultOptions({
      queries: {
        retryDelay: 0, // Instant retry for fast tests
      },
    });

    const { result } = renderHook(() => useRoadmap("role-id"), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    });

    // Wait for success on the retry
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 2000 });

    // Verify listMilestones was called twice (1 initial + 1 retry)
    expect(listMilestones).toHaveBeenCalledTimes(2);
    expect(result.current.data).toEqual([{ id: "m1", title: "Milestone 1", status: "pending" }]);
  });

  it("should fail after 1 retry if error persists", async () => {
    const error500 = new ApiError(500, "Server Error", "Server Error");
    vi.mocked(listMilestones).mockRejectedValue(error500); // Always fail

    const queryClient = createTestQueryClient();
    queryClient.setDefaultOptions({
      queries: {
        retryDelay: 0, // Instant retry for fast tests
      },
    });

    const { result } = renderHook(() => useRoadmap("role-id"), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
      ),
    });

    // Wait for failure
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 2000 });

    // Verify listMilestones was called exactly twice (1 initial + 1 retry)
    expect(listMilestones).toHaveBeenCalledTimes(2);
    expect(result.current.error).toBe(error500);
  });
});

// ── useGapAnalysis ───────────────────────────────────────────────────────
// Source: origin/frontend-usegapanalysis-test-11443187918029242146

describe("useGapAnalysis", () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // disable retries to test errors directly
      },
    },
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
    mockUseAuth.mockReturnValue({ user: { id: "test-user-id" } } as any);
    window.localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return gap analysis data on successful API response", async () => {
    const mockGaps = [{ gap: "Testing", category: "Skills" }];
    vi.mocked(getGapAnalysis).mockResolvedValue({ gaps: mockGaps } as any);

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockGaps);
    expect(getGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should fallback to valid localStorage data on API error", async () => {
    vi.mocked(getGapAnalysis).mockRejectedValue(new Error("API failed"));

    const fallbackGaps = [{ gap: "LocalStorage Skill", category: "Fallback" }];
    window.localStorage.setItem(
      "careeratlas:last_gap_response",
      JSON.stringify({ gaps: fallbackGaps })
    );

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(fallbackGaps);
    expect(getGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should return empty array on API error if localStorage is empty", async () => {
    vi.mocked(getGapAnalysis).mockRejectedValue(new Error("API failed"));
    // localStorage is empty because of beforeEach

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
    expect(getGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should return empty array on API error if localStorage data is invalid JSON", async () => {
    vi.mocked(getGapAnalysis).mockRejectedValue(new Error("API failed"));
    window.localStorage.setItem("careeratlas:last_gap_response", "invalid-json-data");

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
    expect(getGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should return empty array on API error if localStorage data is not an array of gaps", async () => {
    vi.mocked(getGapAnalysis).mockRejectedValue(new Error("API failed"));
    window.localStorage.setItem(
      "careeratlas:last_gap_response",
      JSON.stringify({ gaps: "not-an-array" })
    );

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
    expect(getGapAnalysis).toHaveBeenCalledTimes(1);
  });
});

// ── useTargetRoles ───────────────────────────────────────────────────────
// Source: origin/jules-12573841616739616649-0fe1cb2c

describe("useTargetRoles", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
        },
      },
    });
    vi.clearAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  it("should return initial loading state and then data on success", async () => {
    const mockRoles = [
      { id: "1", title: "Software Engineer", user_id: "user1" },
      { id: "2", title: "Product Manager", user_id: "user1" },
    ] as const;

    vi.mocked(getTargetRoles).mockResolvedValueOnce(mockRoles as any);

    const { result } = renderHook(() => useTargetRoles(), { wrapper });

    // Initial state
    expect(result.current.isLoading).toBe(true);

    // Wait for the query to resolve
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockRoles);
    expect(getTargetRoles).toHaveBeenCalledTimes(1);
  });

  it("should handle errors if the API call fails", async () => {
    const mockError = new Error("Failed to fetch roles");
    vi.mocked(getTargetRoles).mockRejectedValueOnce(mockError);

    const { result } = renderHook(() => useTargetRoles(), { wrapper });

    // Wait for the query to fail
    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
    expect(getTargetRoles).toHaveBeenCalledTimes(1);
  });

  it("should configure staleTime correctly", () => {
    vi.mocked(getTargetRoles).mockResolvedValueOnce([]);

    renderHook(() => useTargetRoles(), { wrapper });

    const queryCache = queryClient.getQueryCache();
    const query = queryCache.find({ queryKey: ["target-roles"] });

    expect(query?.options.staleTime).toBe(60_000);
  });
});

// ── useLatestResume ──────────────────────────────────────────────────────
// Source: origin/testing-improvement-use-latest-resume-3885071726023961889

describe("useLatestResume", () => {
  function createWrapper() {
    const testQueryClient = createTestQueryClient();
    return ({ children }: { children: React.ReactNode }) => (
      <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
    );
  }

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseAuth.mockReturnValue({ user: null } as any);
  });

  it("should fetch and return the latest resume for an authenticated user", async () => {
    const mockUser = { id: "user-123" };
    mockUseAuth.mockReturnValue({ user: mockUser } as any);

    const mockResume = { resume_id: "resume-456", headline: "Software Engineer" };
    vi.mocked(getLatestResume).mockResolvedValue({ resume: mockResume } as any);

    const { result } = renderHook(() => useLatestResume(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    // Wait for the query to resolve
    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    // Verify the API was called and the data is correct
    expect(getLatestResume).toHaveBeenCalledTimes(1);
    expect(result.current.data).toEqual(mockResume);
  });

  it("should be disabled and not fetch if user is unauthenticated (assuming auth is enabled)", async () => {
    // Unauthenticated user
    mockUseAuth.mockReturnValue({ user: null } as any);
    vi.mocked(getLatestResume).mockResolvedValue({ resume: {} } as any);

    const { result } = renderHook(() => useLatestResume(), {
      wrapper: createWrapper(),
    });

    // Wait for a short time to ensure no fetch happens
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(result.current.fetchStatus).toBe("idle");
    expect(result.current.status).toBe("pending");
    expect(getLatestResume).not.toHaveBeenCalled();
  });

  it("should handle API errors gracefully", async () => {
    const mockUser = { id: "user-123" };
    mockUseAuth.mockReturnValue({ user: mockUser } as any);

    // Mock the API to throw an error
    const error = new Error("API Error");
    vi.mocked(getLatestResume).mockRejectedValue(error);

    const { result } = renderHook(() => useLatestResume(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(getLatestResume).toHaveBeenCalledTimes(1);
    expect(result.current.error).toEqual(error);
  });

  it("should return null if the payload does not contain a resume", async () => {
    const mockUser = { id: "user-123" };
    mockUseAuth.mockReturnValue({ user: mockUser } as any);

    // Return null so React Query doesn't complain about undefined query data
    vi.mocked(getLatestResume).mockResolvedValue({ resume: null } as any);

    const { result } = renderHook(() => useLatestResume(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toBeNull();
  });
});
