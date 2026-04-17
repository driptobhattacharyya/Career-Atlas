import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { ArrowLeft, ArrowRight, Check, Compass, FileText, Sparkles, Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { toast } from "sonner";
import { useAuth } from "@/context/auth-context";
import { useTargetRoles } from "@/hooks/queries";
import { parseResume, analyzeGaps, generateRoadmap, researchJobs } from "@/lib/api";
import { insforge } from "@/lib/insforge";

export const Route = createFileRoute("/onboarding")({
  head: () => ({
    meta: [
      { title: "Get started — CareerAtlas" },
      { name: "description", content: "Upload your resume and pick a target role to build your personal career roadmap." },
    ],
  }),
  component: Onboarding,
});

const STEPS = ["Account", "Resume", "Target role", "Analysis"] as const;

function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  
  // Start at step 1 if already authenticated, else step 0
  const [step, setStep] = useState(0);
  useEffect(() => {
    if (user && step === 0) setStep(1);
  }, [user]);

  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [parsing, setParsing] = useState(false);
  const [roleId, setRoleId] = useState<string>("ml-engineer");
  const [roleQuery, setRoleQuery] = useState("");

  const { data: roles = [] } = useTargetRoles();
  const filteredRoles = roles.filter(
    (r: any) => r.title.toLowerCase().includes(roleQuery.toLowerCase()) || r.category.toLowerCase().includes(roleQuery.toLowerCase()),
  );

  const handleFileUpload = async (file: File) => {
    setResumeFile(file);
    setParsing(true);
    
    try {
      if (!user) throw new Error("Must be logged in");
      
      const fileExt = file.name.split('.').pop();
      const fileName = `${user.id}/${Date.now()}.${fileExt}`;

      // Upload to Storage
      const { error: uploadError } = await insforge.storage
        .from("resumes")
        .upload(fileName, file);
        
      if (uploadError) throw uploadError;

      // Call API
      await parseResume(fileName);
      
      toast.success("Resume parsed", { description: "We extracted your skills and experience." });
    } catch (err: any) {
      toast.error("Failed to parse resume", { description: err.message });
      setResumeFile(null); // Reset on failure
    } finally {
      setParsing(false);
    }
  };

  const next = () => setStep((s) => Math.min(s + 1, STEPS.length - 1));
  const back = () => setStep((s) => Math.max(s - 1, (user ? 1 : 0))); // Don't let users go back to login if they are logged in

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
          {step === 0 && <StepAccount />}
          {step === 1 && (
            <StepResume file={resumeFile} parsing={parsing} onFile={handleFileUpload} />
          )}
          {step === 2 && (
            <StepRole
              query={roleQuery}
              onQuery={setRoleQuery}
              roleId={roleId}
              onSelect={setRoleId}
              roles={filteredRoles}
            />
          )}
          {step === 3 && <StepAnalysis roleId={roleId} onDone={() => navigate({ to: "/dashboard" })} />}
        </div>

        {step > 0 && step < 3 && (
          <div className="mt-6 flex items-center justify-between">
            <Button variant="ghost" onClick={back} disabled={step === 1} className="rounded-full">
              <ArrowLeft className="mr-1 h-4 w-4" /> Back
            </Button>
            <Button
              onClick={next}
              disabled={(step === 1 && (!resumeFile || parsing)) || (step === 2 && !roleId)}
              className="rounded-full bg-coral text-coral-foreground hover:bg-coral/90 shadow-warm"
            >
              {step === 2 ? "Analyze my profile" : "Continue"} <ArrowRight className="ml-1 h-4 w-4" />
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
  onSelect: (id: string) => void;
  roles: any[];
}) {
  return (
    <div>
      <h2 className="font-display text-2xl font-bold sm:text-3xl">Pick a target role</h2>
      <p className="mt-2 text-sm text-muted-foreground">
        Don't overthink it — you can change this anytime.
      </p>
      <Input
        placeholder="Search roles…"
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
              onClick={() => onSelect(r.id)}
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
        {roles.length === 0 && (
          <p className="col-span-full py-6 text-center text-sm text-muted-foreground">Loading specific target roles...</p>
        )}
      </div>
    </div>
  );
}

function StepAnalysis({ roleId, onDone }: { roleId: string; onDone: () => void }) {
  const [progress, setProgress] = useState(0);
  const [stageStr, setStageStr] = useState("Preparing engines...");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let unmounted = false;

    const runAnalysis = async () => {
      try {
        if (unmounted) return;
        setStageStr("Analyzing skill gaps vs target role...");
        setProgress(20);
        await analyzeGaps(roleId);

        if (unmounted) return;
        setStageStr("Generating custom learning roadmap milestones...");
        setProgress(50);
        await generateRoadmap(roleId);

        if (unmounted) return;
        setStageStr("Deep researching active internet jobs via Tavily...");
        setProgress(80);
        await researchJobs(roleId);

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
  }, [roleId]);

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
