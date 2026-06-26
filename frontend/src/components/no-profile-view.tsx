import { Link } from "@tanstack/react-router";
import { ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

export function NoProfileView({ feature = "this page" }: { feature?: string }) {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center px-4">
      <h2 className="font-display text-2xl font-bold">No profile found</h2>
      <p className="mt-2 max-w-md text-sm text-muted-foreground">
        You need to complete the onboarding process to view {feature}.
      </p>
      <Button asChild className="mt-6 rounded-full bg-coral px-8 text-coral-foreground hover:bg-coral/90 shadow-warm">
        <Link to="/onboarding">
          Go to Onboarding <ArrowRight className="ml-2 h-4 w-4" />
        </Link>
      </Button>
    </div>
  );
}
