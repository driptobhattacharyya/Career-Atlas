import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { useEffect } from "react"
import { useQuery } from "@tanstack/react-query"
import { Loader2 } from "lucide-react"
import { apiClient } from "@/lib/api"
import { z } from "zod"

export const Route = createFileRoute("/github/callback")({
  validateSearch: z.object({
    code: z.string().optional(),
    state: z.string().optional(),
  }),
  component: GithubCallbackPage,
})

function GithubCallbackPage() {
  const { code, state } = Route.useSearch()
  const navigate = useNavigate()

  useEffect(() => {
    if (!code) {
      navigate({ to: "/profile" })
      return
    }

    // CSRF protection: the state returned by GitHub must match the one we stored
    // before redirecting. A missing/mismatched state means this callback wasn't
    // initiated by us — abort without exchanging the code.
    const expected = sessionStorage.getItem("gh_oauth_state")
    sessionStorage.removeItem("gh_oauth_state")
    if (!state || !expected || state !== expected) {
      console.error("GitHub OAuth state mismatch — aborting")
      navigate({ to: "/profile" })
      return
    }

    // Exchange code for token
    apiClient.post("/api/github/oauth/callback", { code })
      .then(() => {
        navigate({ to: "/github" })
      })
      .catch((err) => {
        console.error("OAuth failed", err)
        navigate({ to: "/profile" })
      })
  }, [code, state, navigate])

  return (
    <div className="flex h-screen w-screen items-center justify-center">
      <div className="text-center space-y-4">
        <Loader2 className="animate-spin w-12 h-12 text-primary mx-auto" />
        <h2 className="text-xl font-medium">Connecting your GitHub account...</h2>
      </div>
    </div>
  )
}
