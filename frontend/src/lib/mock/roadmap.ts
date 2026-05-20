import type { Milestone } from "./types";

export const mockRoadmap: Milestone[] = [
  {
    id: "m1",
    phase: "Foundations",
    title: "Tighten Python & DSA fundamentals",
    skill: "Data Structures & Algorithms",
    status: "completed",
    estimatedWeeks: 3,
    description: "Refresh core data structures and practice 60 problems across arrays, hashmaps, trees, and graphs.",
    courses: [
      { title: "Grokking Algorithms", provider: "Manning", duration: "8h", url: "#" },
      { title: "NeetCode 150", provider: "NeetCode", duration: "Self-paced", url: "#" },
    ],
    project: {
      title: "Mini interview-prep tracker",
      description: "Build a small CLI that logs problems you've solved and surfaces weak topics.",
    },
    checklist: [
      "Solve 60 LeetCode problems",
      "Write a blog post on one tricky pattern",
      "Mock interview with a friend",
    ],
  },
  {
    id: "m2",
    phase: "Foundations",
    title: "Containerize one of your projects",
    skill: "Docker",
    status: "in-progress",
    estimatedWeeks: 2,
    description: "Get comfortable writing Dockerfiles, multi-stage builds, and docker-compose for a real app.",
    courses: [
      { title: "Docker for the Absolute Beginner", provider: "KodeKloud", duration: "5h", url: "#" },
      { title: "Play with Docker labs", provider: "Docker", duration: "Self-paced", url: "#" },
    ],
    project: {
      title: "Dockerize LeafID",
      description: "Wrap your LeafID FastAPI service in a clean image and push it to Docker Hub.",
    },
    checklist: [
      "Write a multi-stage Dockerfile",
      "Add a docker-compose.yml with a Postgres sidecar",
      "Publish image to Docker Hub",
    ],
  },
  {
    id: "m3",
    phase: "Intermediate",
    title: "Deep learning with PyTorch",
    skill: "PyTorch",
    status: "locked",
    estimatedWeeks: 6,
    description: "Move from notebook tutorials to building, training, and evaluating real models from scratch.",
    courses: [
      { title: "Practical Deep Learning for Coders", provider: "fast.ai", duration: "40h", url: "#" },
      { title: "PyTorch in 60 Minutes", provider: "PyTorch.org", duration: "1h", url: "#" },
    ],
    project: {
      title: "Build a transformer from scratch",
      description: "Implement a small character-level transformer and train it on Shakespeare.",
    },
    checklist: [
      "Train one CNN end to end",
      "Train one transformer from scratch",
      "Publish a write-up with metrics",
    ],
  },
  {
    id: "m4",
    phase: "Intermediate",
    title: "Ship a model to AWS",
    skill: "AWS",
    status: "locked",
    estimatedWeeks: 4,
    description: "Learn the minimum AWS surface area to deploy and serve a model behind an API.",
    courses: [
      { title: "AWS Cloud Practitioner Essentials", provider: "AWS", duration: "6h", url: "#" },
      { title: "SageMaker Studio Lab Quickstart", provider: "AWS", duration: "3h", url: "#" },
    ],
    project: {
      title: "LeafID on AWS",
      description: "Deploy LeafID behind API Gateway + Lambda + S3, with logging and basic monitoring.",
    },
    checklist: [
      "Set up an IAM-secured S3 bucket",
      "Deploy via Lambda + API Gateway",
      "Write a cost & latency report",
    ],
  },
  {
    id: "m5",
    phase: "Advanced",
    title: "MLOps: pipelines & monitoring",
    skill: "MLOps",
    status: "locked",
    estimatedWeeks: 6,
    description: "Build a reproducible training-to-serving pipeline with experiment tracking and drift monitoring.",
    courses: [
      { title: "Made With ML — MLOps", provider: "Made With ML", duration: "Self-paced", url: "#" },
      { title: "MLflow + Weights & Biases tutorials", provider: "Various", duration: "10h", url: "#" },
    ],
    project: {
      title: "End-to-end MLOps capstone",
      description: "Take one model from data ingestion → training → deploy → monitor with a CI pipeline.",
    },
    checklist: [
      "Track 10 experiments in W&B",
      "Add a GitHub Actions training pipeline",
      "Add a drift-detection alert",
    ],
  },
  {
    id: "m6",
    phase: "Advanced",
    title: "ML system design interview prep",
    skill: "System Design",
    status: "locked",
    estimatedWeeks: 4,
    description: "Practice designing recsys, search, and ranking systems at a whiteboard level.",
    courses: [
      { title: "Designing ML Systems", provider: "Chip Huyen (book)", duration: "Read", url: "#" },
      { title: "ML System Design Mock Interviews", provider: "YouTube", duration: "10h", url: "#" },
    ],
    project: {
      title: "Write 3 design docs",
      description: "Pick 3 products you use and write 1-page ML system design docs for them.",
    },
    checklist: [
      "Read 'Designing ML Systems'",
      "Write 3 design docs",
      "Do 2 mock interviews",
    ],
  },
];
