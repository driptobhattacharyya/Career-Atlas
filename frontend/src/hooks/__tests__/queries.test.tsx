import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { vi, describe, it, expect, beforeEach } from "vitest";

import { useLatestResume } from "../queries";
import { useAuth } from "@/context/auth-context";
import { getLatestResume } from "@/lib/api";

// Mock the API and auth context
vi.mock("@/lib/api", () => ({
  getLatestResume: vi.fn(),
  updateTargetRole: vi.fn(),
  addSkill: vi.fn(),
  deleteSkill: vi.fn(),
  updateExperience: vi.fn(),
  getTargetRoles: vi.fn(),
  getGapAnalysis: vi.fn(),
  analyzeGaps: vi.fn(),
  listMilestones: vi.fn(),
  updateMilestoneStatus: vi.fn(),
  getJobMatches: vi.fn(),
  getCachedJobSearchResponse: vi.fn(),
  cacheJobSearchResponse: vi.fn(),
  researchJobs: vi.fn(),
  getLatestPathway: vi.fn(),
  startDeepResearch: vi.fn(),
  uploadResume: vi.fn(),
  submitManualResume: vi.fn(),
  getAllResumes: vi.fn(),
  selectResume: vi.fn(),
}));

vi.mock("@/context/auth-context", () => ({
  useAuth: vi.fn(),
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // turn off retries for testing
      },
    },
  });

export function createWrapper() {
  const testQueryClient = createTestQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={testQueryClient}>{children}</QueryClientProvider>
  );
}

describe("useLatestResume", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({ user: null } as any);
  });

  it("should fetch and return the latest resume for an authenticated user", async () => {
    // Setup mocks
    const mockUser = { id: "user-123" };
    vi.mocked(useAuth).mockReturnValue({ user: mockUser } as any);

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
    vi.mocked(useAuth).mockReturnValue({ user: null } as any);
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
    vi.mocked(useAuth).mockReturnValue({ user: mockUser } as any);

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
    vi.mocked(useAuth).mockReturnValue({ user: mockUser } as any);

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
