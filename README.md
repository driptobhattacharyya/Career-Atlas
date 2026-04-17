# 🧭 CareerAtlas

CareerAtlas is an AI-powered early-career development platform designed to catapult junior professionals into their target roles. It ingests user resumes, analyzes skill gaps against a target job title, constructs personalized learning roadmaps, and employs an AI Research Agent to discover highly relevant job opportunities. 

## 🏗 System Architecture
The application runs on a decoupled architecture containing an interactive frontend client, a Python backend acting as the AI orchestrator, and a cloud DB/Auth provider.

- **Frontend:** Built with Vite, React, and Bun. Handles sophisticated user onboarding, global Google authentication via InsForge, and data-rich asynchronous dashboards using `@tanstack/react-query`.
- **Backend:** Built with Python FastAPI and managed by `uv`. Contains four discrete AI domain services: `resume_extraction`, `gap_analysis`, `roadmap_generation`, and `job_hunter`.
- **Database & Auth:** Database schemas, RLS policies, storage, and Auth are handled entirely by InsForge.

## 🚀 Key Features
- **AI Resume Parsing:** Uses `pymupdf4llm` paired with Google's Gemini Pro to effortlessly translate dense PDF resumes into perfectly structured JSON profile parameters.
- **Gap Analysis & Roadmapping:** Leverages ultra-fast Llama-3 models (via Groq) to instantly identify missing technical/soft skills and assemble step-by-step career milestones tracking towards your target role.
- **Deep Research Job Hunter:** Implements a LangGraph ReAct agent equipped with the Tavily search tool to actively scrape the web for live, open job requisitions that fit your exact capability gaps.

## ⚙️ Local Development Setup

### 1. Environment Variables
Before running the system, populate your keys. Update `.env` files in both `/frontend` and `/backend` with your specific API tokens:
- **InsForge**: Submitting database URL, Anon key, and secure JWT service roles.
- **AI Tooling**: `GOOGLE_API_KEY`, `GROQ_API_KEY`, `HUGGINGFACE_API_KEY`, `TAVILY_API_KEY`.

### 2. Backend API
We enforce using `uv` for lightning-fast python virtual environments and dependencies.
```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload
```
*API docs will be available at `http://localhost:8000/docs`*

### 3. Frontend Client
We use `bun` as the Javascript runtime and package manager.
```bash
cd frontend
bun install
bun dev
```
*App will start locally at `http://localhost:5173`*
