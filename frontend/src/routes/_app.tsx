import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/context/auth-context";
import { usePipelineActive } from "@/context/onboarding-pipeline-context";
import { useOnboardingStatus } from "@/hooks/queries";
import { resolveAppGuard } from "@/lib/onboarding-pipeline";

export const Route = createFileRoute("/_app")({
  component: AppLayout,
});

function FullScreenLoader() {
  return (
    <div
      role="status"
      aria-label="Loading"
      className="flex min-h-screen items-center justify-center bg-background"
    >
      <Loader2 className="h-8 w-8 animate-spin text-primary" />
    </div>
  );
}

function AppLayout() {
  const { user, loading } = useAuth();
  const navigate = useNavigate();
  const pipelineActive = usePipelineActive();
  const { status } = useOnboardingStatus({ pipelineActive });
  // A signed-in user who never finished onboarding (e.g. landed on "/" after
  // sign-in) belongs in the wizard, not on empty pages. See resolveAppGuard
  // for why this can't loop with the /onboarding gate.
  const guard = user ? resolveAppGuard(status) : "wait";

  useEffect(() => {
    if (!loading && !user) {
      navigate({ to: "/" });
    }
  }, [loading, user, navigate]);

  useEffect(() => {
    if (guard === "to-onboarding") {
      navigate({ to: "/onboarding", replace: true });
    }
  }, [guard, navigate]);

  if (loading) return <FullScreenLoader />;

  if (!user) {
    return null; // redirecting to landing
  }

  if (guard !== "render") return <FullScreenLoader />;

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  );
}
