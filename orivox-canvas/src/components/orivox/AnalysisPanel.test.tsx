import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AnalysisPanel } from "./AnalysisPanel";

describe("AnalysisPanel", () => {
  const mockOnFix = vi.fn();
  const mockOnRegenerate = vi.fn();

  const mockSuggestions = [
    {
      id: "1",
      issue: "Headline is too generic and lacks quantifiable achievements.",
      fix_instruction: "Rewrite headline to specify scale, e.g., 'Engineered high-throughput microservices'.",
    },
    {
      id: "2",
      issue: "Call to action is missing from the post closing.",
      fix_instruction: "Add a clear question at the end to encourage audience engagement.",
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the empty state when no suggestions are provided", () => {
    render(
      <AnalysisPanel
        suggestions={[]}
        onFix={mockOnFix}
        onRegenerate={mockOnRegenerate}
      />
    );

    expect(
      screen.getByText(/no suggestions|empty|no analysis available/i)
    ).toBeInTheDocument();
  });

  it("renders suggestions with issue and fix_instruction correctly", () => {
    render(
      <AnalysisPanel
        suggestions={mockSuggestions}
        onFix={mockOnFix}
        onRegenerate={mockOnRegenerate}
      />
    );

    expect(
      screen.getByText("Headline is too generic and lacks quantifiable achievements.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Rewrite headline to specify scale, e.g., 'Engineered high-throughput microservices'.")
    ).toBeInTheDocument();

    expect(
      screen.getByText("Call to action is missing from the post closing.")
    ).toBeInTheDocument();
    expect(
      screen.getByText("Add a clear question at the end to encourage audience engagement.")
    ).toBeInTheDocument();
  });

  it("calls the fix interaction handler when fix button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <AnalysisPanel
        suggestions={mockSuggestions}
        onFix={mockOnFix}
        onRegenerate={mockOnRegenerate}
      />
    );

    const fixButtons = screen.getAllByRole("button", { name: /fix/i });
    expect(fixButtons.length).toBeGreaterThan(0);

    await user.click(fixButtons[0]);

    expect(mockOnFix).toHaveBeenCalledWith(mockSuggestions[0]);
  });

  it("calls the regenerate interaction handler when regenerate button is clicked", async () => {
    const user = userEvent.setup();
    render(
      <AnalysisPanel
        suggestions={mockSuggestions}
        onFix={mockOnFix}
        onRegenerate={mockOnRegenerate}
      />
    );

    const regenerateButton = screen.getByRole("button", { name: /regenerate/i });
    await user.click(regenerateButton);

    expect(mockOnRegenerate).toHaveBeenCalledTimes(1);
  });
});
