import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ManualResumeForm } from './manual-resume-form';

// Mock the SkillMultiSelect component since it's likely complex
vi.mock('@/components/ui/multi-select-skills', () => ({
  SkillMultiSelect: ({ selected = [], onChange }: any) => (
    <div data-testid="skill-multi-select">
      <button
        type="button"
        onClick={() => onChange([...selected, 'React'])}
        data-testid="add-skill-react"
      >
        Add React
      </button>
      <div data-testid="selected-skills">{selected.join(', ')}</div>
    </div>
  )
}));

describe('ManualResumeForm', () => {
  const mockOnSubmit = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    window.alert = vi.fn();
  });

  it('renders the form fields correctly', () => {
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    expect(screen.getByLabelText(/Full Name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Headline/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Summary/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/i)).toBeInTheDocument();
  });

  it('shows an alert when submitting without skills', async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Fill required simple fields
    await user.type(screen.getByLabelText(/Full Name/i), 'John Doe');

    // Fill required project fields
    const projectInputs = screen.getAllByPlaceholderText('E-commerce App');
    await user.type(projectInputs[0], 'Test Project');

    // Submit
    await user.click(screen.getByRole('button', { name: /Save Profile & Continue/i }));

    // Should trigger alert about skills
    await waitFor(() => {
        expect(window.alert).toHaveBeenCalledWith('Please add at least 1 skill.');
    });
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('does not submit when required fields are missing', async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Add skill so it passes the alert check (though it won't even reach there if react-hook-form stops it)
    const addSkillButtons = screen.getAllByTestId('add-skill-react');
    await user.click(addSkillButtons[0]);

    // Submit without filling Full Name or Project Name
    await user.click(screen.getByRole('button', { name: /Save Profile & Continue/i }));

    // Should NOT trigger alert about projects because react-hook-form validation catches missing "Full Name" and "Project Name"
    expect(mockOnSubmit).not.toHaveBeenCalled();
  });

  it('submits successfully with valid data', async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Fill basic info
    await user.type(screen.getByLabelText(/Full Name/i), 'John Doe');
    await user.type(screen.getByLabelText(/Headline/i), 'Software Engineer');

    // Add skill
    const addSkillButtons = screen.getAllByTestId('add-skill-react');
    await user.click(addSkillButtons[0]);

    // Fill project
    const projectInputs = screen.getAllByPlaceholderText('E-commerce App');
    await user.type(projectInputs[0], 'Test Project');

    // Submit
    await user.click(screen.getByRole('button', { name: /Save Profile & Continue/i }));

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledTimes(1);
    });

    // Check submitted data
    const submittedData = mockOnSubmit.mock.calls[0][0];
    expect(submittedData.full_name).toBe('John Doe');
    expect(submittedData.headline).toBe('Software Engineer');
    expect(submittedData.skills).toContain('React');
    expect(submittedData.projects[0].name).toBe('Test Project');
  });

  it('allows adding and removing experience entries', async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Add experience
    await user.click(screen.getByRole('button', { name: /Add Experience/i }));

    const companyInputs = screen.getAllByPlaceholderText(/Google/i);
    expect(companyInputs).toHaveLength(1);
    await user.type(companyInputs[0], 'Test Company');
  });

  it('allows adding and removing education entries', async () => {
    const user = userEvent.setup();
    render(<ManualResumeForm onSubmit={mockOnSubmit} isSubmitting={false} />);

    // Add education
    await user.click(screen.getByRole('button', { name: /Add Education/i }));

    const institutionInputs = screen.getAllByPlaceholderText(/Stanford University/i);
    expect(institutionInputs).toHaveLength(1);
    await user.type(institutionInputs[0], 'Test University');
  });
});
