import { createFileRoute } from "@tanstack/react-router"
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Loader2, Github, Check, X } from "lucide-react"

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
  languages: Record<string, number> | null
  commit_count: number | null
  first_commit_at: string | null
  last_commit_at: string | null
}

const confidenceColor: Record<string, string> = {
  high: "bg-green-100 text-green-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-muted text-muted-foreground",
}

function GithubInsightsPage() {
  const qc = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ["github-insights"],
    queryFn: () => apiClient.get("/api/github/profile").then((r) => r.data),
  })

  const act = useMutation({
    mutationFn: ({ action, id }: { action: "confirm" | "reject"; id: string }) =>
      apiClient.post(`/api/github/skills/${action}`, { evidence_ids: [id] }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["github-insights"] }),
  })

  if (isLoading) {
    return <div className="flex justify-center p-12"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
  }

  const profile = data?.profile
  const repos: RepoRow[] = data?.repositories || []
  const evidence: SkillEvidence[] = data?.skill_evidence || []

  if (!profile && evidence.length === 0) {
    return (
      <div className="container max-w-2xl py-12 text-center space-y-4">
        <Github className="w-10 h-10 mx-auto text-muted-foreground" />
        <p className="text-muted-foreground">No GitHub analysis yet. Connect and analyze repositories first.</p>
        <Button onClick={() => (window.location.href = "/github")}>Go to GitHub</Button>
      </div>
    )
  }

  return (
    <div className="container max-w-3xl py-12 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Github className="w-7 h-7" /> GitHub Insights</h1>
        <p className="text-muted-foreground mt-2">
          Skills inferred from your repositories stay <strong>suggestions</strong> until you confirm them.
          Only confirmed skills count toward your profile and gap analysis.
        </p>
      </div>

      {profile && (
        <Card>
          <CardHeader>
            <CardTitle>Profile Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>{profile.analysis_summary}</p>
            {profile.coding_behavior && (
              <p className="text-muted-foreground"><strong>Coding behavior:</strong> {profile.coding_behavior}</p>
            )}
          </CardContent>
        </Card>
      )}

      {evidence.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Suggested Skills</CardTitle>
            <CardDescription>Each skill is backed by evidence from your code. Confirm the ones you want on your profile.</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y">
              {evidence.map((e) => (
                <div key={e.id} className="flex items-start justify-between gap-4 p-4">
                  <div className="flex-1 space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{e.skill}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${confidenceColor[e.confidence || "low"]}`}>
                        {e.confidence || "low"}
                      </span>
                      {e.confirmed && <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary">Confirmed</span>}
                    </div>
                    <p className="text-xs text-muted-foreground">
                      {e.evidence}{e.source_repo ? ` — ${e.source_repo}` : ""}
                    </p>
                  </div>
                  {!e.confirmed && (
                    <div className="flex gap-2 shrink-0">
                      <Button size="sm" variant="outline" disabled={act.isPending}
                        onClick={() => act.mutate({ action: "confirm", id: e.id })}>
                        <Check className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" disabled={act.isPending}
                        onClick={() => act.mutate({ action: "reject", id: e.id })}>
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {repos.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold">Repositories</h2>
          {repos.map((repo) => (
            <Card key={repo.repo_name}>
              <CardHeader>
                <CardTitle className="text-base">{repo.repo_name}</CardTitle>
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
                {repo.commit_count != null && (
                  <p className="text-xs text-muted-foreground">
                    {repo.commit_count}{repo.commit_count >= 100 ? "+" : ""} owner-authored commits
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
