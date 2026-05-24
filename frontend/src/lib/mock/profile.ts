import type { Profile } from "./types";

export const mockProfile: Profile = {
  name: "Maya Patel",
  headline: "Final-year CS student • aspiring ML Engineer",
  email: "maya.patel@example.com",
  location: "Bengaluru, India",
  github: "mayapatel",
  summary:
    "Curious builder with a CS background, internship experience at two startups, and a love for turning messy data into useful products.",
  completeness: 72,
  skills: [
    { name: "Python", category: "Languages", level: "advanced", source: "resume", evidence: "Used in 3 internships and 5 projects." },
    { name: "TypeScript", category: "Languages", level: "intermediate", source: "github", evidence: "Primary language across 4 GitHub repos." },
    { name: "SQL", category: "Languages", level: "intermediate", source: "resume", evidence: "Wrote analytics queries during Acme internship." },
    { name: "Java", category: "Languages", level: "beginner", source: "resume" },

    { name: "React", category: "Frameworks", level: "intermediate", source: "github", evidence: "Built 3 React apps including a portfolio dashboard." },
    { name: "FastAPI", category: "Frameworks", level: "intermediate", source: "resume" },
    { name: "PyTorch", category: "Frameworks", level: "beginner", source: "resume", evidence: "Coursework + 1 image-classification project." },

    { name: "Pandas", category: "Data", level: "advanced", source: "resume" },
    { name: "NumPy", category: "Data", level: "advanced", source: "resume" },
    { name: "scikit-learn", category: "Data", level: "intermediate", source: "resume" },

    { name: "Docker", category: "Cloud & DevOps", level: "beginner", source: "github" },
    { name: "Git", category: "Tools", level: "advanced", source: "github" },
    { name: "Linux", category: "Tools", level: "intermediate", source: "resume" },

    { name: "Communication", category: "Soft Skills", level: "intermediate", source: "resume" },
    { name: "Teamwork", category: "Soft Skills", level: "advanced", source: "resume" },
  ],
  experience: [
    {
      role: "Data Science Intern",
      company: "Acme Analytics",
      start: "May 2024",
      end: "Aug 2024",
      bullets: [
        "Built churn-prediction notebook that surfaced 12 actionable signals.",
        "Owned a Streamlit dashboard used weekly by the growth team.",
        "Cleaned and documented 4 internal datasets for downstream ML use.",
      ],
    },
    {
      role: "Software Engineering Intern",
      company: "BrightLabs",
      start: "Jun 2023",
      end: "Aug 2023",
      bullets: [
        "Shipped 6 React components into the customer portal.",
        "Wrote unit tests covering 85% of new code.",
      ],
    },
  ],
  education: [
    {
      school: "PSG College of Technology",
      degree: "B.E. Computer Science",
      start: "2021",
      end: "2025",
    },
  ],
  projects: [
    {
      name: "LeafID",
      description: "CNN that classifies 38 plant diseases from a phone photo. Deployed as a tiny FastAPI service.",
      tech: ["PyTorch", "FastAPI", "Docker"],
      link: "https://github.com/mayapatel/leafid",
    },
    {
      name: "ReadingLog",
      description: "Personal reading tracker with weekly summaries — 200+ stars on GitHub.",
      tech: ["TypeScript", "React", "SQLite"],
      link: "https://github.com/mayapatel/readinglog",
    },
    {
      name: "CampusBus",
      description: "Real-time bus tracker for campus shuttles with Maps overlay and ETA.",
      tech: ["React", "Node.js", "PostgreSQL"],
    },
  ],
};
