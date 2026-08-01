import { describe, it, expect, vi, beforeEach } from "vitest";
import { waitFor, renderHook } from "@testing-library/react";
import { useRoadmap } from "./queries";
import { renderHookWithClient, createTestQueryClient } from "../test-utils";
import * as api from "../lib/api";
import { QueryClientProvider } from "@tanstack/react-query";

// Mock Supabase to avoid warnings
vi.mock("../lib/supabase", () => ({
  supabase: {
    auth: {
      getSession: vi.fn().mockResolvedValue({ data: { session: null } }),
      onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
    }
  }
}));

// Mock the Auth Context
vi.mock("../context/auth-context", () => ({
  useAuth: () => ({
    user: { id: "test-user-id" },
  }),
}));

// Mock the API Module
vi.mock("../lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import('../lib/api')>();
  return {
    ...actual,
    listMilestones: vi.fn(),
  };
});

describe("useRoadmap hook error retry logic", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should not retry on 404 error", async () => {
    const error404 = new api.ApiError(404, "Not Found", "Not Found");
    vi.mocked(api.listMilestones).mockRejectedValueOnce(error404);

    const { result } = renderHookWithClient(() => useRoadmap("role-id"));

    await waitFor(() => expect(result.current.isFetching).toBe(false));

    // Verify listMilestones was called only once (no retries)
    expect(api.listMilestones).toHaveBeenCalledTimes(1);

    // Verify it resolved to an empty array (isSuccess: true, data: [])
    // This happens because queryFn catches the 404, not because of the retry config.
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it("should retry once on non-404 errors (like 500) before failing", async () => {
    const error500 = new api.ApiError(500, "Server Error", "Server Error");
    vi.mocked(api.listMilestones)
      .mockRejectedValueOnce(error500) // First try fails with 500
      .mockResolvedValueOnce({ milestones: [{ id: "m1", title: "Milestone 1", status: "pending" }] }); // Retry succeeds

    const queryClient = createTestQueryClient();
    queryClient.setDefaultOptions({
      queries: {
        retryDelay: 0, // Instant retry for fast tests
      }
    });

    const { result } = renderHook(() => useRoadmap("role-id"), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )
    });

    // Wait for success on the retry
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 2000 });

    // Verify listMilestones was called twice (1 initial + 1 retry)
    expect(api.listMilestones).toHaveBeenCalledTimes(2);
    expect(result.current.data).toEqual([{ id: "m1", title: "Milestone 1", status: "pending" }]);
  });

  it("should fail after 1 retry if error persists", async () => {
    const error500 = new api.ApiError(500, "Server Error", "Server Error");
    vi.mocked(api.listMilestones)
      .mockRejectedValue(error500); // Always fail

    const queryClient = createTestQueryClient();
    queryClient.setDefaultOptions({
      queries: {
        retryDelay: 0, // Instant retry for fast tests
      }
    });

    const { result } = renderHook(() => useRoadmap("role-id"), {
      wrapper: ({ children }) => (
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      )
    });

    // Wait for failure
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 2000 });

    // Verify listMilestones was called exactly twice (1 initial + 1 retry)
    expect(api.listMilestones).toHaveBeenCalledTimes(2);
    expect(result.current.error).toBe(error500);
  });
});
