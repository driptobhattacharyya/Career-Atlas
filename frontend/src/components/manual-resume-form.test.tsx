import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ManualResumeForm } from "./manual-resume-form";

// Mock the SkillMultiSelect component since it's likely complex
vi.mock("@/components/ui/multi-select-skills", () => ({
  SkillMultiSelect: ({ selected = [], onChange }: any) => (
    <div data-testid="skill-multi-select">
      <button
        type="button"
        onClick={() => onChange([...selected, "React"])}
        data-testid="add-skill-react"
      >
        Add React
      </button>
      <div data-testid="selected-skills">{selected.join(", ")}</div>
    </div>
  ),
}));

describe("ManualResumeForm", () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    window.alert = vi.fn();
  });

  it("renders the form fields correctly", () => {
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Headline/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Summary/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
  });

  it("shows an alert when submitting without skills", async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Fill required simple fields
    await user.type(screen.getByLabelText(/Full Name/i), "John Doe");

    // Fill required project fields
    const projectInputs = screen.getAllByPlaceholderText("E-commerce App");
    await user.type(projectInputs[0], "Test Project");

    // Submit
    await user.click(screen.getByRole("button", { name: /Save Profile & Continue/i }));

    // Should trigger alert about skills
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith("Please add at least 1 skill.");
    });
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("does not submit when the project name field is left empty", async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Fill Full Name and add a skill so the only unmet condition left is the
    // empty project name.
    await user.type(screen.getByLabelText(/Full Name/i), "John Doe");
    const addSkillButtons = screen.getAllByTestId("add-skill-react");
    await user.click(addSkillButtons[0]);

    // Submit without filling Project Name.
    await user.click(screen.getByRole("button", { name: /Save Profile & Continue/i }));

    // Today react-hook-form's `required` validator on the project-name field
    // blocks handleSubmit before onFormSubmit's manual "at least 1 valid
    // project" guard ever runs, so no alert fires. That manual guard checks
    // the exact same condition on this field, so this test alone can't prove
    // which of the two is responsible — see the dedicated test below for a
    // case the manual guard cannot explain.
    expect(window.alert).not.toHaveBeenCalled();
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it("blocks submission via react-hook-form's required validator when Full Name is empty", async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Satisfy every condition the manual onFormSubmit guard checks (skills,
    // project name) so the only thing left that can block submission is
    // react-hook-form's required validator on Full Name — a field the
    // manual guard never inspects.
    const addSkillButtons = screen.getAllByTestId("add-skill-react");
    await user.click(addSkillButtons[0]);
    const projectInputs = screen.getAllByPlaceholderText("E-commerce App");
    await user.type(projectInputs[0], "Test Project");

    // Submit without filling Full Name.
    await user.click(screen.getByRole("button", { name: /Save Profile & Continue/i }));

    // react-hook-form flags the field and blocks the submit handler outright.
    // The manual guard has no opinion on full_name, so this would fail if
    // `required: true` were ever removed from it — unlike the test above.
    expect(mockOnSubmit).not.toHaveBeenCalled();
    expect(window.alert).not.toHaveBeenCalled();
    expect(screen.getByLabelText(/Full Name/i)).toHaveClass("border-destructive");
  });

  it("submits successfully with valid data", async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Fill basic info
    await user.type(screen.getByLabelText(/Full Name/i), "John Doe");
    await user.type(screen.getByLabelText(/Headline/i), "Software Engineer");

    // Add skill
    const addSkillButtons = screen.getAllByTestId("add-skill-react");
    await user.click(addSkillButtons[0]);

    // Fill project
    const projectInputs = screen.getAllByPlaceholderText("E-commerce App");
    await user.type(projectInputs[0], "Test Project");

    // Submit
    await user.click(screen.getByRole("button", { name: /Save Profile & Continue/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    // Check submitted data
    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.full_name).toBe("John Doe");
    expect(submittedData.headline).toBe("Software Engineer");
    expect(submittedData.skills).toContain("React");
    expect(submittedData.projects[0].name).toBe("Test Project");
  });

  it("allows adding and removing experience entries", async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Add experience
    await user.click(screen.getByRole("button", { name: /Add Experience/i }));

    const companyInputs = screen.getAllByPlaceholderText(/Google/i);
    expect(companyInputs).toHaveLength(1);
    await user.type(companyInputs[0], "Test Company");

    // Remove the entry via its own remove control (the icon-only trash button
    // rendered inside the same row card as the company input).
    const experienceRow = companyInputs[0].closest(".relative") as HTMLElement;
    expect(experienceRow).not.toBeNull();
    const removeButton = within(experienceRow).getByRole("button");
    await user.click(removeButton);

    // The row — and the value typed into it — should be gone.
    expect(screen.queryAllByPlaceholderText(/Google/i)).toHaveLength(0);
    expect(screen.queryByDisplayValue("Test Company")).not.toBeInTheDocument();
  });

  it("allows adding and removing education entries", async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Add education
    await user.click(screen.getByRole("button", { name: /Add Education/i }));

    const institutionInputs = screen.getAllByPlaceholderText(/Stanford University/i);
    expect(institutionInputs).toHaveLength(1);
    await user.type(institutionInputs[0], "Test University");

    // Remove the entry via its own remove control (the icon-only trash button
    // rendered inside the same row card as the institution input).
    const educationRow = institutionInputs[0].closest(".relative") as HTMLElement;
    expect(educationRow).not.toBeNull();
    const removeButton = within(educationRow).getByRole("button");
    await user.click(removeButton);

    // The row — and the value typed into it — should be gone.
    expect(screen.queryAllByPlaceholderText(/Stanford University/i)).toHaveLength(0);
    expect(screen.queryByDisplayValue("Test University")).not.toBeInTheDocument();
  });
});
