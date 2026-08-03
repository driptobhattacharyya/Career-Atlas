import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mocking useAuth context
vi.mock("@/context/auth-context", () => ({
  useAuth: vi.fn(),
}));

// Mocking the getGapAnalysis API function
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<any>();
  return {
    ...actual,
    getGapAnalysis: vi.fn(),
  };
});

import { useAuth } from "@/context/auth-context";
import { getGapAnalysis } from "@/lib/api";
import { useGapAnalysis } from "./queries";

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

describe("useGapAnalysis", () => {
  const mockUseAuth = useAuth as unknown as ReturnType<typeof vi.fn>;
  const mockGetGapAnalysis = getGapAnalysis as unknown as ReturnType<typeof vi.fn>;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient.clear();
    mockUseAuth.mockReturnValue({ user: { id: "test-user-id" } });
    window.localStorage.clear();

    // Explicitly unmock disableAuth behavior by default (via import.meta.env mock if needed, but here we can just rely on the fallback user above being enough to enable the query).
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("should return gap analysis data on successful API response", async () => {
    const mockGaps = [{ gap: "Testing", category: "Skills" }];
    mockGetGapAnalysis.mockResolvedValue({ gaps: mockGaps });

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockGaps);
    expect(mockGetGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should fallback to valid localStorage data on API error", async () => {
    mockGetGapAnalysis.mockRejectedValue(new Error("API failed"));

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
    expect(mockGetGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should return empty array on API error if localStorage is empty", async () => {
    mockGetGapAnalysis.mockRejectedValue(new Error("API failed"));
    // localStorage is empty because of beforeEach

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
    expect(mockGetGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should return empty array on API error if localStorage data is invalid JSON", async () => {
    mockGetGapAnalysis.mockRejectedValue(new Error("API failed"));
    window.localStorage.setItem("careeratlas:last_gap_response", "invalid-json-data");

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
    expect(mockGetGapAnalysis).toHaveBeenCalledTimes(1);
  });

  it("should return empty array on API error if localStorage data is not an array of gaps", async () => {
    mockGetGapAnalysis.mockRejectedValue(new Error("API failed"));
    window.localStorage.setItem("careeratlas:last_gap_response", JSON.stringify({ gaps: "not-an-array" }));

    const { result } = renderHook(() => useGapAnalysis(), { wrapper });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual([]);
    expect(mockGetGapAnalysis).toHaveBeenCalledTimes(1);
  });

});
