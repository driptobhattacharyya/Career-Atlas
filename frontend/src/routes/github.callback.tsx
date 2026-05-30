import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router";
import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { request } from "@/lib/api";
import { z } from "zod";

export const Route = createFileRoute("/github/callback")({
  validateSearch: z.object({
    code: z.string().optional(),
  }),
  component: GithubCallbackPage,
});

function GithubCallbackPage() {
  const { code } = Route.useSearch();
  const navigate = useNavigate();

  useEffect(() => {
    if (!code) {
      navigate({ to: "/profile" });
      return;
    }

    // Exchange code for token
    request("/api/github/oauth/callback", {
      method: "POST",
      body: JSON.stringify({ code }),
    })
      .then(() => {
        navigate({ to: "/github" });
      })
      .catch((err) => {
        console.error("OAuth failed", err);
        navigate({ to: "/profile" });
      });
  }, [code, navigate]);

  return (
    <div className="flex h-screen w-screen items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="animate-spin w-12 h-12 text-primary mx-auto" />
        <h2 className="text-xl font-medium">Connecting your GitHub account...</h2>
      </div>
    </div>
  );
}
