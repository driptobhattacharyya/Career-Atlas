import { createFileRoute } from "@tanstack/react-router"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Github, Check, X, Undo2 } from "lucide-react"

import { apiClient } from "@/lib/api"

export const Route = createFileRoute("/_app/github-insights")({
  component: GithubInsightsPage,
})

interface SkillEvidence {
  id: string
  skill: string
  evidence: string | null
  confidence: string | null
  source_repo: string | null
  confirmed: boolean
}

interface RepoRow {
  repo_name: string
  analysis_summary: string | null
  coding_behavior: string | null
  languages: Record<string, number> | null
  commit_count: number | null
  first_commit_at: string | null
  last_commit_at: string | null
}

// UX-4: plain-language confidence — "high/medium/low" meant nothing to users.
const confLabel: Record<string, string> = { high: "Strong match", medium: "Likely", low: "Possible" }
const confColor: Record<string, string> = {
  high: "bg-green-100 text-green-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-muted text-muted-foreground",
}

function shortRepo(name: string | null) {
  return name ? name.split("/").slice(-1)[0] : ""
}

function GithubInsightsPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["github-insights"],
    queryFn: () => apiClient.get("/api/github/profile").then((r) => r.data),
    refetchOnMount: "always", // UX-1: always pull the persisted server state on entry
  })

  const act = useMutation({
    mutationFn: ({ action, ids }: { action: "confirm" | "reject"; ids: string[] }) =>
      apiClient.post(`/api/github/skills/${action}`, { evidence_ids: ids }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["github-insights"] }),
  })

  if (isLoading) {
    return <div className="flex justify-center p-12"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
  }

  const profile = data?.profile
  const repos: RepoRow[] = data?.repositories || []
  const evidence: SkillEvidence[] = data?.skill_evidence || []
  const added = evidence.filter((e) => e.confirmed)
  const review = evidence.filter((e) => !e.confirmed)

  if (!profile && evidence.length === 0) {
    return (
      <div className="container max-w-2xl py-12 text-center space-y-4">
        <Github className="w-10 h-10 mx-auto text-muted-foreground" />
        <p className="text-muted-foreground">You haven't analyzed any repositories yet. Connect GitHub and we'll match your code to skills.</p>
        <Button onClick={() => (window.location.href = "/github")}>Connect GitHub</Button>
      </div>
    )
  }

  return (
    <div className="container max-w-3xl py-12 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Github className="w-7 h-7" /> GitHub Insights</h1>
        <p className="text-muted-foreground mt-2">
          We matched your repositories to skills. Strong matches were added to your profile automatically —
          review the rest below. Only skills you keep are shown to employers.
        </p>
      </div>

      {profile && (
        <Card>
          <CardHeader>
            <CardTitle>Summary</CardTitle>
            <CardDescription>How you tend to build, based on the code in your repositories.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>{profile.analysis_summary}</p>
            {profile.coding_behavior && <p className="text-muted-foreground">{profile.coding_behavior}</p>}
          </CardContent>
        </Card>
      )}

      {/* UX-3: review only the uncertain ones; bulk "Add all" so nobody ticks 15 boxes */}
      {review.length > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between gap-4">
              <div>
                <CardTitle>Review suggestions</CardTitle>
                <CardDescription>We're less sure about these. Add the ones that fit.</CardDescription>
              </div>
              <Button size="sm" disabled={act.isPending}
                onClick={() => act.mutate({ action: "confirm", ids: review.map((e) => e.id) })}>
                Add all
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {review.map((e) => (
                <div key={e.id} className="flex items-start justify-between gap-4 p-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{e.skill}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${confColor[e.confidence || "low"]}`}>
                        {confLabel[e.confidence || "low"]}
                      </span>
                    </div>
                    {e.evidence && (
                      <p className="text-xs text-muted-foreground">
                        Where we saw it: {e.evidence}{e.source_repo ? ` (${shortRepo(e.source_repo)})` : ""}
                      </p>
                    )}
                  </div>
                  <div className="flex gap-2 shrink-0">
                    <Button size="sm" variant="outline" disabled={act.isPending}
                      onClick={() => act.mutate({ action: "confirm", ids: [e.id] })}>
                      <Check className="w-4 h-4" />
                    </Button>
                    <Button size="sm" variant="ghost" disabled={act.isPending}
                      onClick={() => act.mutate({ action: "reject", ids: [e.id] })}>
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {added.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Added to your profile</CardTitle>
            <CardDescription>Strong matches from your code. Remove any that don't belong.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {added.map((e) => (
                <div key={e.id} className="flex items-start justify-between gap-4 p-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{e.skill}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">On your profile</span>
                    </div>
                    {e.evidence && (
                      <p className="text-xs text-muted-foreground">
                        Where we saw it: {e.evidence}{e.source_repo ? ` (${shortRepo(e.source_repo)})` : ""}
                      </p>
                    )}
                  </div>
                  <Button size="sm" variant="ghost" disabled={act.isPending}
                    onClick={() => act.mutate({ action: "reject", ids: [e.id] })}>
                    <Undo2 className="w-4 h-4 mr-1" /> Remove
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {repos.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Repositories analyzed</h2>
          {repos.map((repo) => (
            <Card key={repo.repo_name}>
              <CardHeader>
                <CardTitle className="text-base">{shortRepo(repo.repo_name)}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {repo.analysis_summary && <p>{repo.analysis_summary}</p>}
                {repo.languages && Object.keys(repo.languages).length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(repo.languages)
                      .sort((a, b) => b[1] - a[1])
                      .map(([lang, pctVal]) => (
                        <span key={lang} className="text-xs bg-muted px-2 py-0.5 rounded-full">{lang} {pctVal}%</span>
                      ))}
                  </div>
                )}
                {repo.commit_count != null && repo.commit_count > 0 && (
                  <p className="text-xs text-muted-foreground">
                    {repo.commit_count}{repo.commit_count >= 100 ? "+" : ""} commits by you
                    {repo.first_commit_at && repo.last_commit_at
                      ? ` (${repo.first_commit_at.slice(0, 10)} → ${repo.last_commit_at.slice(0, 10)})`
                      : ""}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
