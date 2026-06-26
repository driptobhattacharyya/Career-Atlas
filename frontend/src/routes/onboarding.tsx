import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Compass, FileText, Sparkles, Upload, Github } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { useTargetRoles, useUploadResume, useRunGapAnalysis, useLatestResume } from "@/hooks/queries";

export const Route = createFileRoute("/onboarding")({
  head: () => ({
    meta: [
      { title: "Get started — CareerAtlas" },
      { name: "description", content: "Upload your resume and pick a target role to build your personal career roadmap." },
    ],
  }),
  component: Onboarding,
});

const disableAuth = (import.meta.env.VITE_DISABLE_AUTH as string | undefined) === "true";
const STEPS = disableAuth
  ? (["Resume", "Target role", "Analysis", "GitHub"] as const)
  : (["Account", "Resume", "Target role", "Analysis", "GitHub"] as const);

function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Start at step 1 if already authenticated, else step 0
  const [step, setStep] = useState(disableAuth ? 0 : 0);
  useEffect(() => {
    if (!disableAuth && user && step === 0) setStep(1);
  }, [user, step]);

  // Redirect already-onboarded users (a resume existed when this page loaded)
  // straight to the Dashboard. ONE-SHOT: decided on the first resolved fetch —
  // it must NOT fire after the in-flow resume upload, or the user skips the
  // gap-analysis step.
  const latestResume = useLatestResume();
  const uploadMutation = useUploadResume();
  const onboardCheckDone = useRef(false);
  useEffect(() => {
    if (onboardCheckDone.current || disableAuth || !user) return;
    // If an in-flow upload has started, the user is mid-onboarding — never
    // bounce them to the dashboard, even if the initial /latest fetch lands
    // late (after the upload's cache invalidation).
    if (!uploadMutation.isIdle) return;
    if (!latestResume.isSuccess) return;
    onboardCheckDone.current = true;
    if (latestResume.data) {
      navigate({ to: "/dashboard" });
    }
  }, [user, latestResume.isSuccess, latestResume.data, uploadMutation.isIdle, navigate]);

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [roleId, setRoleId] = useState<string>("ml-engineer");
  const [roleTitle, setRoleTitle] = useState<string>("ML Engineer");
  const [roleQuery, setRoleQuery] = useState("");
  const parsing = uploadMutation.isPending;

  const { data: roles = [] } = useTargetRoles();
  const filteredRoles = roles.filter(
    (r: any) => r.title.toLowerCase().includes(roleQuery.toLowerCase()) || r.category.toLowerCase().includes(roleQuery.toLowerCase()),
  );
  useEffect(() => {
    if (!roles.length) return;
    if (roleId === "custom") return; // don't clobber a free-text custom role
    const selected = roles.find((r: any) => r.id === roleId) || roles[0];
    if (selected) {
      setRoleId(selected.id);
      setRoleTitle(selected.title);
    }
  }, [roles]);

  const handleFileUpload = async (file: File) => {
    setResumeFile(file);
    if (!user && !disableAuth) {
      toast.error("Sign in first");
      setResumeFile(null);
      return;
    }
    try {
      await uploadMutation.mutateAsync(file);
      toast.success("Resume parsed", { description: "We extracted your skills and experience." });
    } catch (err: any) {
      toast.error("Failed to parse resume", { description: err.message });
      setResumeFile(null);
    }
  };

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () =>
    setStep((s) => {
      if (disableAuth) return Math.max(s - 1, 0);
      return Math.max(s - 1, user ? 1 : 0);
    }); // Don't let signed-in users go back to login

  return (
    <div className="min-h-screen bg-gradient-hero">
      <header className="mx-auto flex max-w-3xl items-center justify-between px-4 py-5 sm:px-6">
        <a href="/" className="flex items-center gap-2 font-display text-lg font-bold tracking-tight">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary text-primary-foreground shadow-soft">
            <Compass className="h-5 w-5" />
          </span>
          CareerAtlas
        </a>
        <span className="text-xs text-muted-foreground">
          Step {step + 1} of {STEPS.length}
        </span>
      </header>

      <div className="mx-auto max-w-3xl px-4 sm:px-6">
        {/* Stepper */}
        <div className="mb-8 flex items-center gap-2">
          {STEPS.map((label, i) => (
            <div key={label} className="flex flex-1 items-center gap-2">
              <div
                className={cn(
                  "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold transition-colors",
                  i < step
                    ? "bg-success text-success-foreground"
                    : i === step
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground",
                )}
              >
                {i < step || (i === 0 && user) ? <Check className="h-4 w-4" /> : i + 1}
              </div>
              <span
                className={cn(
                  "hidden text-xs font-medium sm:inline",
                  i === step ? "text-foreground" : "text-muted-foreground",
                )}
              >
                {label}
              </span>
              {i < STEPS.length - 1 && <div className="h-px flex-1 bg-border" />}
            </div>
          ))}
        </div>

        <div className="rounded-3xl border border-border bg-card p-6 shadow-soft sm:p-10">
          {!disableAuth && step === 0 && <StepAccount />}
          {step === (disableAuth ? 0 : 1) && (
            <StepResume file={resumeFile} parsing={parsing} onFile={handleFileUpload} />
          )}
      {step === (disableAuth ? 1 : 2) && (
            <StepRole
              query={roleQuery}
              onQuery={setRoleQuery}
              roleId={roleId}
              onSelect={(id, title) => {
                setRoleId(id);
                setRoleTitle(title);
              }}
              roles={filteredRoles}
            />
          )}
          {step === (disableAuth ? 2 : 3) && (
            <StepAnalysis
              roleId={roleId}
              roleTitle={roleTitle}
              onDone={next}
            />
          )}
          {step === (disableAuth ? 3 : 4) && (
            <StepGithub onSkip={() => navigate({ to: "/roadmap" })} />
          )}
        </div>

        {step > (disableAuth ? -1 : 0) && step < (disableAuth ? 2 : 3) && (
          <div className="mt-6 flex items-center justify-between">
            <Button variant="ghost" onClick={back} disabled={step === (disableAuth ? 0 : 1)} className="rounded-full">
              <ArrowLeft className="mr-1 h-4 w-4" /> Back
            </Button>
            <Button
              onClick={next}
              disabled={
                (step === (disableAuth ? 0 : 1) && (!resumeFile || parsing)) ||
                (step === (disableAuth ? 1 : 2) && !roleId)
              }
              className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm"
            >
              {step === (disableAuth ? 1 : 2) ? "Analyze my profile" : "Continue"} <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function StepAccount() {
  const { signInWithGoogle } = useAuth();
  return (
    <div className="text-center py-6">
      <h2 className="font-display text-2xl font-bold sm:text-3xl">Create your account</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Sign in to save your career atlas progress and personalized jobs.
      </p>
      <Button onClick={signInWithGoogle} className="mt-8 rounded-full border border-border px-8" variant="outline">
        <svg className="mr-2 h-4 w-4" aria-hidden="true" focusable="false" data-prefix="fab" data-icon="google" role="img" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 488 512"><path fill="currentColor" d="M488 261.8C488 403.3 391.1 504 248 504 110.8 504 0 393.2 0 256S110.8 8 248 8c66.8 0 123 24.5 166.3 64.9l-67.5 64.9C258.5 52.6 94.3 116.6 94.3 256c0 86.5 69.1 156.6 153.7 156.6 98.2 0 135-70.4 140.8-106.9H248v-85.3h236.1c2.3 12.7 3.9 24.9 3.9 41.4z"></path></svg>
        Sign in with Google
      </Button>
    </div>
  );
}

function StepResume({ file, parsing, onFile }: { file: File | null; parsing: boolean; onFile: (f: File) => void }) {
  const [drag, setDrag] = useState(false);

  return (
    <div>
      <h2 className="font-display text-2xl font-bold sm:text-3xl">Upload your resume</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        PDF works best. We'll extract your skills, projects, and experience — no manual entry.
      </p>

      <label
        onDragOver={(e) => {
          e.preventDefault();
          setDrag(true);
        }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDrag(false);
          const f = e.dataTransfer.files?.[0];
          if (f) onFile(f);
        }}
        className={cn(
          "mt-6 flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed p-10 text-center transition-colors",
          drag ? "border-coral bg-coral/5" : "border-border bg-muted/30 hover:bg-muted/50",
        )}
      >
        <span className="grid h-14 w-14 place-items-center rounded-2xl bg-primary-soft text-primary">
          <Upload className="h-6 w-6" />
        </span>
        <p className="mt-4 font-medium">Drop your resume here, or click to browse</p>
        <p className="mt-1 text-xs text-muted-foreground">PDF, DOCX up to 10 MB</p>
        <input
          type="file"
          accept=".pdf,.doc,.docx"
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFile(f);
          }}
        />
      </label>

      {file && (
        <div className="mt-5 flex items-center gap-3 rounded-2xl border border-border bg-background p-4">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-coral/15 text-coral">
            <FileText className="h-5 w-5" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{file.name}</p>
            <p className="text-xs text-muted-foreground">
              {(file.size / 1024).toFixed(0)} KB • {parsing ? "Parsing via Gemini…" : "Ready"}
            </p>
          </div>
          {parsing ? (
            <span className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent" />
          ) : (
            <Check className="h-5 w-5 text-success" />
          )}
        </div>
      )}
    </div>
  );
}

function StepRole({
  query,
  onQuery,
  roleId,
  onSelect,
  roles,
}: {
  query: string;
  onQuery: (q: string) => void;
  roleId: string;
  onSelect: (id: string, title: string) => void;
  roles: any[];
}) {
  return (
    <div>
      <h2 className="font-display text-2xl font-bold sm:text-3xl">Pick a target role</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Don't overthink it — you can change this anytime.
      </p>
      <Input
        placeholder="Search or type any role…"
        value={query}
        onChange={(e) => onQuery(e.target.value)}
        className="mt-5 h-11 rounded-full"
      />

      <div className="mt-5 grid gap-3 sm:grid-cols-2">
        {roles.map((r) => {
          const selected = r.id === roleId;
          return (
            <button
              key={r.id}
              onClick={() => onSelect(r.id, r.title)}
              className={cn(
                "rounded-2xl border-2 p-5 text-left transition-all",
                selected
                  ? "border-coral bg-coral/5 shadow-warm"
                  : "border-border bg-card hover:border-primary-soft hover:bg-muted/40",
              )}
            >
              <div className="flex items-start justify-between">
                <span className="text-2xl">{r.emoji}</span>
                {selected && (
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-coral text-coral-foreground">
                    <Check className="h-3.5 w-3.5" />
                  </span>
                )}
              </div>
              <h3 className="mt-3 font-display text-base font-semibold">{r.title}</h3>
              <p className="mt-1 text-xs text-muted-foreground">{r.blurb}</p>
            </button>
          );
        })}

        {/* Free-text custom role: works for unlisted tech AND non-tech roles.
            Gap analysis lazily generates the skill map for it (labeled experimental). */}
        {query.trim() &&
          !roles.some((r) => r.title.toLowerCase() === query.trim().toLowerCase()) && (
            <button
              onClick={() => onSelect("custom", query.trim())}
              className={cn(
                "rounded-2xl border-2 border-dashed p-5 text-left transition-all sm:col-span-2",
                roleId === "custom"
                  ? "border-coral bg-coral/5 shadow-warm"
                  : "border-border bg-card hover:border-primary-soft hover:bg-muted/40",
              )}
            >
              <div className="flex items-start justify-between">
                <span className="text-2xl">✨</span>
                {roleId === "custom" && (
                  <span className="grid h-6 w-6 place-items-center rounded-full bg-coral text-coral-foreground">
                    <Check className="h-3.5 w-3.5" />
                  </span>
                )}
              </div>
              <h3 className="mt-3 font-display text-base font-semibold">Use "{query.trim()}"</h3>
              <p className="mt-1 text-xs text-muted-foreground">
                Custom role — we'll map the skills with AI. Works for non-tech roles too.{" "}
                <span className="font-medium text-coral">Experimental.</span>
              </p>
            </button>
          )}

        {roles.length === 0 && !query.trim() && (
          <p className="col-span-full py-6 text-center text-sm text-muted-foreground">Loading specific target roles...</p>
        )}
      </div>
    </div>
  );
}

function StepAnalysis({ roleId, roleTitle, onDone }: { roleId: string; roleTitle: string; onDone: () => void }) {
  const [progress, setProgress] = useState(0);
  const [stageStr, setStageStr] = useState("Preparing engines...");
  const [error, setError] = useState<string | null>(null);

  const gapMutation = useRunGapAnalysis();

  useEffect(() => {
    let unmounted = false;

    const runAnalysis = async () => {
      try {
        window.localStorage.setItem("careeratlas:selected_role_id", roleId);
        window.localStorage.setItem("careeratlas:selected_role_title", roleTitle);
        if (unmounted) return;
        setStageStr("Analyzing skill gaps vs target role...");
        setProgress(35);
        await gapMutation.mutateAsync(roleTitle);

        if (unmounted) return;
        setProgress(100);
        setStageStr("All done!");
        setTimeout(() => { if (!unmounted) onDone(); }, 1000);
      } catch (err: any) {
        if (!unmounted) setError(err.message || "Failed to complete AI processing.");
      }
    };

    runAnalysis();

    return () => { unmounted = true; };
  }, [roleId, roleTitle]);

  return (
    <div className="py-6 text-center">
      <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-coral/15 text-coral">
        <Sparkles className="h-7 w-7 animate-pulse" />
      </span>
      <h2 className="mt-5 font-display text-2xl font-bold sm:text-3xl">Building your atlas</h2>
      <p className="mt-2 text-sm text-muted-foreground">{error || stageStr}</p>
      
      {!error && (
        <>
          <Progress value={progress} className="mx-auto mt-6 max-w-md" />
          <p className="mt-3 text-xs text-muted-foreground">{progress}%</p>
        </>
      )}

      {error && (
        <Button onClick={() => window.location.reload()} className="mt-6" variant="destructive">
          Retry
        </Button>
      )}
    </div>
  );
}

// UX-6: offered AFTER the gap analysis (first value), fully skippable. We send
// "Connect" into the existing /github flow rather than embedding the OAuth
// redirect round-trip in the stepper — simpler and the user lands on their
// GitHub insights. "Skip" continues to the roadmap; the navbar + Profile keep
// GitHub reachable later either way.
function StepGithub({ onSkip }: { onSkip: () => void }) {
  return (
    <div className="py-6 text-center">
      <span className="mx-auto grid h-16 w-16 place-items-center rounded-2xl bg-primary-soft text-primary">
        <Github className="h-7 w-7" />
      </span>
      <h2 className="mt-5 font-display text-2xl font-bold sm:text-3xl">Add skills proven by your code</h2>
      <p className="mx-auto mt-2 max-w-md text-sm text-muted-foreground">
        Connect GitHub and we'll read your repositories to find skills, projects, and how you build.
        Strong matches are added to your profile — you review the rest. Optional, and you can do this
        anytime from the GitHub tab.
      </p>
      <div className="mt-8 flex flex-col items-center gap-3">
        <Button
          onClick={() => (window.location.href = "/github")}
          className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm px-8"
        >
          <Github className="mr-2 h-4 w-4" /> Connect GitHub
        </Button>
        <Button variant="ghost" onClick={onSkip} className="rounded-full">
          Skip for now
        </Button>
      </div>
    </div>
  );
}
