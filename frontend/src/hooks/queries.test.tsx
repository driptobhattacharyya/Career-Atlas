import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { useTargetRoles } from "./queries";
import { getTargetRoles } from "@/lib/api";
import React from "react";

// Mock the API function
vi.mock("@/lib/api", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/lib/api")>();
  return {
    ...actual,
    getTargetRoles: vi.fn(),
  };
});

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

    vi.mocked(getTargetRoles).mockResolvedValueOnce(
      mockRoles as unknown as ReturnType<typeof getTargetRoles> extends Promise<infer U>
        ? U
        : never,
    );

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
