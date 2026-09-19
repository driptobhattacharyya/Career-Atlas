import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// @ts-expect-error MarkdownView module is not provided in this codebase
import { MarkdownView } from "./MarkdownView";

vi.mock("@/lib/api", () => ({
  fetchCitation: vi.fn(),
}));

describe("MarkdownView Component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders headings correctly", () => {
    const markdownContent = "# Heading 1\n## Heading 2\n### Heading 3";
    render(<MarkdownView content={markdownContent} />);

    const h1 = screen.getByRole("heading", { level: 1, name: /Heading 1/i });
    const h2 = screen.getByRole("heading", { level: 2, name: /Heading 2/i });
    const h3 = screen.getByRole("heading", { level: 3, name: /Heading 3/i });

    expect(h1).toBeInTheDocument();
    expect(h2).toBeInTheDocument();
    expect(h3).toBeInTheDocument();
  });

  it("renders unordered and ordered lists correctly", () => {
    const markdownContent = `
- First bullet item
- Second bullet item

1. First numbered item
2. Second numbered item
`;
    render(<MarkdownView content={markdownContent} />);

    expect(screen.getByText("First bullet item")).toBeInTheDocument();
    expect(screen.getByText("Second bullet item")).toBeInTheDocument();
    expect(screen.getByText("First numbered item")).toBeInTheDocument();
    expect(screen.getByText("Second numbered item")).toBeInTheDocument();

    const listItems = screen.getAllByRole("listitem");
    expect(listItems.length).toBeGreaterThanOrEqual(4);
  });

  it("renders links with safe rel and target attributes", () => {
    const markdownContent = "[Example Link](https://example.com)";
    render(<MarkdownView content={markdownContent} />);

    const link = screen.getByRole("link", { name: /Example Link/i });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute("href", "https://example.com");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", expect.stringContaining("noopener"));
  });

  it("renders citation markers such as [1] and handles user interaction", async () => {
    const user = userEvent.setup();
    const mockOnCitationClick = vi.fn();
    const markdownContent = "This is a statement with a citation [1].";

    render(
      <MarkdownView
        content={markdownContent}
        onCitationClick={mockOnCitationClick}
      />
    );

    const citation = screen.queryByText("[1]") ?? screen.getByRole("button", { name: /1/i });
    expect(citation).toBeInTheDocument();

    await user.click(citation);
    expect(mockOnCitationClick).toHaveBeenCalledWith(1);
  });

  it("ensures raw HTML in input is not rendered as active HTML elements", () => {
    const markdownWithHtml = 'Raw HTML test: <div data-testid="raw-html-element">Unsafe HTML</div> <script>alert("xss")</script>';

    render(<MarkdownView content={markdownWithHtml} />);

    // Raw HTML should be escaped or stripped, so the testid from raw HTML should NOT be in the document
    expect(screen.queryByTestId("raw-html-element")).not.toBeInTheDocument();

    // Text content should be rendered as plain text / sanitized string
    expect(screen.getByText(/Raw HTML test/i)).toBeInTheDocument();
  });
});
