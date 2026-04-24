# Graph Report - .  (2026-04-24)

## Corpus Check
- Corpus is ~35,102 words - fits in a single context window. You may not need a graph.

## Summary
- 276 nodes · 252 edges · 14 communities detected
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 70 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Backend API Routing|Backend API Routing]]
- [[_COMMUNITY_Platform Architecture Docs|Platform Architecture Docs]]
- [[_COMMUNITY_AI Services Documentation|AI Services Documentation]]
- [[_COMMUNITY_Job Search Agent|Job Search Agent]]
- [[_COMMUNITY_API Schema Definitions|API Schema Definitions]]
- [[_COMMUNITY_LLM Service Layer|LLM Service Layer]]
- [[_COMMUNITY_Frontend API Hooks|Frontend API Hooks]]
- [[_COMMUNITY_Auth & React Query|Auth & React Query]]
- [[_COMMUNITY_App Configuration|App Configuration]]
- [[_COMMUNITY_JWT Auth Dependency|JWT Auth Dependency]]
- [[_COMMUNITY_Pydantic Settings Dep|Pydantic Settings Dep]]
- [[_COMMUNITY_HTTPX Dep|HTTPX Dep]]
- [[_COMMUNITY_JWT Cryptography Dep|JWT Cryptography Dep]]
- [[_COMMUNITY_File Upload Dep|File Upload Dep]]

## God Nodes (most connected - your core abstractions)
1. `Resume Extraction Service` - 11 edges
2. `Backend (Python FastAPI + uv)` - 8 edges
3. `InsForgeClient` - 7 edges
4. `Job Hunter Service (Deep Research Agent)` - 7 edges
5. `ScrapedJobsResponse` - 6 edges
6. `parse_resume()` - 6 edges
7. `useAuth()` - 6 edges
8. `CareerAtlas Platform` - 6 edges
9. `Gap Analysis Service` - 6 edges
10. `TestSprite Frontend MCP Test Report` - 6 edges

## Surprising Connections (you probably didn't know these)
- `CareerAtlas Proposal (Documentation)` --references--> `CareerAtlas Platform`  [INFERRED]
  Documentation/CareerAtlas_Proposal.pdf → README.md
- `SkillGraph: Resume Extraction and RAG Pipeline (Documentation)` --references--> `Resume Extraction Service`  [INFERRED]
  Documentation/SkillGraph_ Resume Extraction and RAG Pipeline.pdf → README.md
- `Resume Extraction Service` --implements--> `LangChain Google GenAI`  [INFERRED]
  README.md → backend/requirements.txt
- `SkillGraph: Resume Extraction and RAG Pipeline (Documentation)` --conceptually_related_to--> `Gap Analysis Service`  [INFERRED]
  Documentation/SkillGraph_ Resume Extraction and RAG Pipeline.pdf → README.md
- `Deep Researcher Agentic System (Documentation)` --references--> `Job Hunter Service (Deep Research Agent)`  [INFERRED]
  Documentation/Deep Researcher Agentic System.pdf → README.md

## Hyperedges (group relationships)
- **Core AI Processing Pipeline** — readme_resume_extraction, readme_gap_analysis, readme_roadmap_generation [EXTRACTED 0.90]
- **LLM Provider Integrations in Backend** — requirements_langchain_google_genai, requirements_langchain_groq, requirements_langchain_huggingface [EXTRACTED 0.95]
- **Tests Blocked by OAuth-Only Auth** — testsprite_tc002, testsprite_tc003, testsprite_bug_oauth_lock [EXTRACTED 0.90]

## Communities

### Community 0 - "Backend API Routing"
Cohesion: 0.11
Nodes (13): InsForgeClient, analyze_gaps(), AnalyzeGapsRequest, generate_roadmap(), GenerateRoadmapRequest, parse_resume(), ParseResumeRequest, research_jobs() (+5 more)

### Community 1 - "Platform Architecture Docs"
Cohesion: 0.12
Nodes (24): CareerAtlas Proposal (Documentation), CareerAtlas Platform, Decoupled Architecture Design, Environment Variables Configuration, Frontend (Vite + React + Bun), Google Gemini Pro (LLM), Google OAuth Authentication, InsForge (Database & Auth Provider) (+16 more)

### Community 2 - "AI Services Documentation"
Cohesion: 0.13
Nodes (21): Deep Researcher Agentic System (Documentation), SkillGraph: Resume Extraction and RAG Pipeline (Documentation), Backend (Python FastAPI + uv), Gap Analysis Service, Job Hunter Service (Deep Research Agent), LangGraph ReAct Agent, Llama-3 via Groq (Fast Inference LLM), Rationale: Groq for Ultra-Fast LLM Inference (+13 more)

### Community 3 - "Job Search Agent"
Cohesion: 0.15
Nodes (12): execute_search(), extract_and_score_jobs(), generate_search_queries(), JobSearchState, Generates optimal search queries to find job listings., Executes search using Tavily., Uses LLM to parse raw search results into JobMatchSchema structures., JobMatchSchema (+4 more)

### Community 4 - "API Schema Definitions"
Cohesion: 0.21
Nodes (12): BaseModel, CourseSchema, EducationSchema, ExperienceSchema, GapAnalysisResponse, GapSchema, MilestoneSchema, ProjectSchema (+4 more)

### Community 5 - "LLM Service Layer"
Cohesion: 0.18
Nodes (9): get_gemini_model(), get_groq_model(), get_huggingface_model(), Returns a configured Groq model instance. Best for fast, responsive generation., Returns a configured HuggingFace model instance. Good for auxiliary subtasks., Returns a configured Gemini model instance. Best for complex reasoning and large, create_roadmap_for_gaps(), generate_gaps_for_user() (+1 more)

### Community 6 - "Frontend API Hooks"
Cohesion: 0.31
Nodes (7): analyzeGaps(), generateRoadmap(), getAuthHeaders(), parseResume(), researchJobs(), handleFileUpload(), runAnalysis()

### Community 7 - "Auth & React Query"
Cohesion: 0.29
Nodes (6): useAuth(), useGapAnalysis(), useJobMatches(), useProfile(), useRoadmap(), useSkills()

### Community 10 - "App Configuration"
Cohesion: 0.5
Nodes (3): BaseSettings, Config, Settings

### Community 11 - "JWT Auth Dependency"
Cohesion: 0.5
Nodes (2): Validates the JWT token coming from the frontend (which signed in via InsForge)., verify_token()

### Community 93 - "Pydantic Settings Dep"
Cohesion: 1.0
Nodes (1): Pydantic Settings

### Community 94 - "HTTPX Dep"
Cohesion: 1.0
Nodes (1): HTTPX (Async HTTP Client)

### Community 95 - "JWT Cryptography Dep"
Cohesion: 1.0
Nodes (1): python-jose (JWT Cryptography)

### Community 96 - "File Upload Dep"
Cohesion: 1.0
Nodes (1): python-multipart (File Upload)

## Knowledge Gaps
- **17 isolated node(s):** `Config`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `Returns a configured Tavily search tool for LangGraph agent.`, `Returns a configured Gemini model instance. Best for complex reasoning and large`, `Returns a configured Groq model instance. Best for fast, responsive generation.` (+12 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `JWT Auth Dependency`** (4 nodes): `get_current_user_id()`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `verify_token()`, `auth.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Pydantic Settings Dep`** (1 nodes): `Pydantic Settings`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `HTTPX Dep`** (1 nodes): `HTTPX (Async HTTP Client)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `JWT Cryptography Dep`** (1 nodes): `python-jose (JWT Cryptography)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `File Upload Dep`** (1 nodes): `python-multipart (File Upload)`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ScrapedJobsResponse` connect `Job Search Agent` to `API Schema Definitions`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Why does `get_groq_model()` connect `LLM Service Layer` to `Job Search Agent`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `Backend (Python FastAPI + uv)` connect `AI Services Documentation` to `Platform Architecture Docs`?**
  _High betweenness centrality (0.009) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `Resume Extraction Service` (e.g. with `PyMuPDF` and `LangChain Google GenAI`) actually correct?**
  _`Resume Extraction Service` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `Job Hunter Service (Deep Research Agent)` (e.g. with `TC005: Start Job Search and View Ranked Listings` and `Deep Researcher Agentic System (Documentation)`) actually correct?**
  _`Job Hunter Service (Deep Research Agent)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `Returns a configured Tavily search tool for LangGraph agent.` to the rest of the system?**
  _17 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Backend API Routing` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._