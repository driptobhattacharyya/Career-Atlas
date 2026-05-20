export type SkillLevel = "beginner" | "intermediate" | "advanced";

export interface Skill {
  name: string;
  category: "Languages" | "Frameworks" | "Data" | "Cloud & DevOps" | "Tools" | "Soft Skills";
  level: SkillLevel;
  evidence?: string;
  source?: "resume" | "github";
}

export interface ExperienceItem {
  role: string;
  company: string;
  start: string;
  end: string;
  bullets: string[];
}

export interface EducationItem {
  school: string;
  degree: string;
  start: string;
  end: string;
}

export interface ProjectItem {
  name: string;
  description: string;
  tech: string[];
  link?: string;
}

export interface Profile {
  name: string;
  headline: string;
  email: string;
  location: string;
  github?: string;
  summary: string;
  skills: Skill[];
  experience: ExperienceItem[];
  education: EducationItem[];
  projects: ProjectItem[];
  completeness: number; // 0-100
}

export interface TargetRole {
  id: string;
  title: string;
  category: string;
  blurb: string;
  emoji: string;
  popularSkills: string[];
}

export interface SkillGap {
  skill: string;
  category: string;
  relevance: number; // 0-100
  difficulty: "Easy" | "Medium" | "Hard";
  prerequisites: string[];
  why: string;
}

export interface Course {
  title: string;
  provider: string;
  duration: string;
  url: string;
}

export interface Milestone {
  id: string;
  phase: "Foundations" | "Intermediate" | "Advanced";
  title: string;
  skill: string;
  status: "completed" | "in-progress" | "locked";
  estimatedWeeks: number;
  description: string;
  courses: Course[];
  project: { title: string; description: string };
  checklist: string[];
}

export interface JobMatch {
  id: string;
  title: string;
  company: string;
  location: string;
  remote: boolean;
  seniority: "Intern" | "Entry" | "Junior" | "Mid";
  matchPct: number;
  matched: string[];
  missing: string[];
  salary: string;
  postedDays: number;
  description: string;
}
