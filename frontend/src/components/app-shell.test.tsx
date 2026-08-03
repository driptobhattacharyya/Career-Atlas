import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AppShell } from './app-shell';
import { useAuth } from '@/context/auth-context';
import { ThemeSelector } from '@/components/theme-selector';
import userEvent from '@testing-library/user-event';

// Mock router hooks and components to avoid complex Provider setup
vi.mock('@tanstack/react-router', () => ({
  Link: ({ children, to, className }: any) => (
    <a href={to} className={className}>
      {children}
    </a>
  ),
  useLocation: () => ({ pathname: '/dashboard' }),
  useNavigate: () => vi.fn(),
}));

// Mock ThemeSelector to simplify testing
vi.mock('@/components/theme-selector', () => ({
  ThemeSelector: () => <div data-testid="theme-selector">Theme Selector</div>,
}));

vi.mock('@/context/auth-context', () => ({
  useAuth: vi.fn(),
}));

// ResizeObserver and PointerEvent are needed by Radix UI components
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
global.PointerEvent = class PointerEvent extends Event {
  constructor(type: string, props: any) {
    super(type, props);
  }
} as any;
// Mock matchMedia for Radix UI
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // Deprecated
    removeListener: vi.fn(), // Deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('AppShell', () => {
  const mockSignOut = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();

    (useAuth as any).mockReturnValue({
      user: {
        email: 'test@example.com',
        user_metadata: { full_name: 'Test User' },
      },
      signOut: mockSignOut,
    });
  });

  it('renders children correctly', () => {
    render(
      <AppShell>
        <div data-testid="child-content">Main Content</div>
      </AppShell>
    );

    expect(screen.getByTestId('child-content')).toBeInTheDocument();
    expect(screen.getByText('Main Content')).toBeInTheDocument();
  });

  it('displays core navigation items', () => {
    render(<AppShell>Content</AppShell>);

    const expectedLabels = ['Dashboard', 'Profile', 'Roadmap', 'Gaps', 'Jobs', 'GitHub'];

    expectedLabels.forEach((label) => {
      // The nav labels are rendered twice (desktop and mobile)
      const elements = screen.getAllByText(label);
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows targeting role if set in localStorage', () => {
    const mockRole = 'Senior Frontend Engineer';

    const getItemSpy = vi.spyOn(window.localStorage.__proto__, 'getItem');
    getItemSpy.mockImplementation((key) => {
      if (key === 'careeratlas:selected_role_title') {
        return mockRole;
      }
      return null;
    });

    render(<AppShell>Content</AppShell>);

    expect(screen.getByText('Targeting')).toBeInTheDocument();
    expect(screen.getByText(mockRole)).toBeInTheDocument();

    getItemSpy.mockRestore();
  });

  it('shows account dropdown and can trigger signout', async () => {
    const user = userEvent.setup();
    render(<AppShell>Content</AppShell>);

    // User initial 'T' (from 'Test User')
    const trigger = screen.getByText('T', { selector: 'button' });
    expect(trigger).toBeInTheDocument();

    // Open dropdown
    await user.click(trigger);

    // Verify dropdown content
    const signOutBtn = await screen.findByText('Sign out');
    expect(signOutBtn).toBeInTheDocument();

    // Test sign out interaction
    mockSignOut.mockResolvedValueOnce(undefined);
    await user.click(signOutBtn);
    expect(mockSignOut).toHaveBeenCalled();
  });
});