import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState, useEffect } from "react"
import { useQuery, useMutation } from "@tanstack/react-query"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Loader2, Github } from "lucide-react"

// Assume we have an apiClient
import { request } from "@/lib/api"

export const Route = createFileRoute("/_app/github")({
  component: GithubConnectPage,
})

function GithubConnectPage() {
  const navigate = useNavigate()
  const [selectedRepos, setSelectedRepos] = useState<string[]>([])

  // 1. Check status
  const { data: statusData, isLoading: statusLoading } = useQuery({
    queryKey: ["github-status"],
    queryFn: () => request("/api/github/status"),
  })

  // 2. If connected, fetch repos
  const { data: reposData, isLoading: reposLoading } = useQuery({
    queryKey: ["github-repos"],
    queryFn: () => request("/api/github/repos"),
    enabled: !!statusData?.connected,
  })

  // 3. Analyze mutation
  const analyzeMutation = useMutation({
    mutationFn: (repos: string[]) => request("/api/github/analyze", { method: "POST", jsonBody: { repos } }),
    onSuccess: () => {
      navigate({ to: "/profile" })
    }
  })

  const handleConnect = () => {
    // Initiate OAuth flow
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
    const redirectUri = window.location.origin + "/github/callback"
    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${redirectUri}&scope=repo,read:user`
  }

  const handleToggleRepo = (repoName: string) => {
    setSelectedRepos(prev =>
      prev.includes(repoName) ? prev.filter(r => r !== repoName) : [...prev, repoName]
    )
  }

  if (statusLoading) {
    return <div className="flex justify-center p-12"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
  }

  if (!statusData?.connected) {
    return (
      <div className="container max-w-2xl py-12">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Github className="w-6 h-6" /> Connect GitHub</CardTitle>
            <CardDescription>Connect your GitHub account to analyze your repositories and technical capabilities.</CardDescription>
          </CardHeader>
          <CardContent>
            <Button onClick={handleConnect} className="w-full">
              <Github className="w-4 h-4 mr-2" /> Continue with GitHub
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container max-w-3xl py-12 space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Select Repositories</h1>
        <p className="text-muted-foreground mt-2">
          We found {reposData?.repos?.length || 0} top repositories you own or contributed to.
          Select up to 10 for deep analysis to enhance your career profile.
        </p>
      </div>

      {reposLoading ? (
        <div className="flex justify-center p-12"><Loader2 className="animate-spin h-8 w-8 text-primary" /></div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {reposData?.repos?.map((repo: any) => (
                <div key={repo.name} className="flex items-start space-x-4 p-4 hover:bg-muted/50 transition-colors">
                  <Checkbox
                    id={`repo-${repo.name}`}
                    checked={selectedRepos.includes(repo.name)}
                    onCheckedChange={() => handleToggleRepo(repo.name)}
                    className="mt-1"
                  />
                  <div className="flex-1 space-y-1">
                    <Label htmlFor={`repo-${repo.name}`} className="text-base font-medium cursor-pointer">
                      {repo.name} {repo.isOwner ? <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded-full">Owner</span> : <span className="ml-2 text-xs bg-secondary text-secondary-foreground px-2 py-0.5 rounded-full">Contributor</span>}
                    </Label>
                    <p className="text-sm text-muted-foreground line-clamp-1">{repo.description || "No description"}</p>
                    <div className="flex items-center gap-4 text-xs text-muted-foreground">
                      {repo.primaryLanguage && <span>{repo.primaryLanguage}</span>}
                      <span>★ {repo.stargazerCount}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
          <CardFooter className="p-4 border-t bg-muted/20 flex justify-between items-center">
            <span className="text-sm text-muted-foreground">{selectedRepos.length} selected</span>
            <Button
              onClick={() => analyzeMutation.mutate(selectedRepos)}
              disabled={selectedRepos.length === 0 || analyzeMutation.isPending}
            >
              {analyzeMutation.isPending ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Analyzing...</> : "Analyze Selected"}
            </Button>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}
