import type { SkillGap } from "./types";

export const mockGaps: SkillGap[] = [
  {
    skill: "MLOps & Model Deployment",
    category: "Cloud & DevOps",
    relevance: 95,
    difficulty: "Medium",
    prerequisites: ["Docker", "Python"],
    why: "Almost every ML Engineer JD asks for experience deploying models — not just training them.",
  },
  {
    skill: "Deep Learning with PyTorch",
    category: "Frameworks",
    relevance: 90,
    difficulty: "Hard",
    prerequisites: ["Python", "NumPy", "Linear algebra basics"],
    why: "You have intro-level PyTorch — bringing it to intermediate unlocks transformer & vision roles.",
  },
  {
    skill: "AWS (S3, SageMaker, Lambda)",
    category: "Cloud & DevOps",
    relevance: 82,
    difficulty: "Medium",
    prerequisites: ["Linux", "Docker"],
    why: "60% of ML Engineer postings in your region list AWS as required or preferred.",
  },
  {
    skill: "Data Structures & Algorithms",
    category: "Languages",
    relevance: 78,
    difficulty: "Medium",
    prerequisites: ["Python or Java"],
    why: "Required for the technical screen at most product companies.",
  },
  {
    skill: "Experiment Design & A/B Testing",
    category: "Data",
    relevance: 65,
    difficulty: "Easy",
    prerequisites: ["Statistics basics"],
    why: "Differentiates a model-builder from someone who can ship measurable wins.",
  },
  {
    skill: "System Design (ML systems)",
    category: "Soft Skills",
    relevance: 60,
    difficulty: "Hard",
    prerequisites: ["Backend basics", "Databases"],
    why: "Asked in mid-level ML interviews — start exposure now to be ready in 12 months.",
  },
];
