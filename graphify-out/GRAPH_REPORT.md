# Graph Report - Career-Atlas  (2026-04-24)

## Corpus Check
- 105 files · ~35,102 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 261 nodes · 234 edges · 9 communities detected
- Extraction: 74% EXTRACTED · 26% INFERRED · 0% AMBIGUOUS · INFERRED: 60 edges (avg confidence: 0.77)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]

## God Nodes (most connected - your core abstractions)
1. `Resume Extraction Service` - 8 edges
2. `InsForgeClient` - 7 edges
3. `ScrapedJobsResponse` - 6 edges
4. `parse_resume()` - 6 edges
5. `useAuth()` - 6 edges
6. `CareerAtlas Platform` - 6 edges
7. `Backend (Python FastAPI + uv)` - 6 edges
8. `TestSprite Frontend MCP Test Report` - 6 edges
9. `TestSprite Raw Report` - 6 edges
10. `analyze_gaps()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `CareerAtlas Platform` --references--> `CareerAtlas Proposal (Documentation)`  [INFERRED]
  README.md → Documentation/CareerAtlas_Proposal.pdf
- `Resume Extraction Service` --references--> `SkillGraph: Resume Extraction and RAG Pipeline (Documentation)`  [INFERRED]
  README.md → Documentation/SkillGraph_ Resume Extraction and RAG Pipeline.pdf
- `Gap Analysis Service` --conceptually_related_to--> `SkillGraph: Resume Extraction and RAG Pipeline (Documentation)`  [INFERRED]
  README.md → Documentation/SkillGraph_ Resume Extraction and RAG Pipeline.pdf
- `Job Hunter Service (Deep Research Agent)` --references--> `Deep Researcher Agentic System (Documentation)`  [INFERRED]
  README.md → Documentation/Deep Researcher Agentic System.pdf
- `LangGraph ReAct Agent` --conceptually_related_to--> `Deep Researcher Agentic System (Documentation)`  [INFERRED]
  README.md → Documentation/Deep Researcher Agentic System.pdf

## Hyperedges (group relationships)
- **Core AI Processing Pipeline** — readme_resume_extraction, readme_gap_analysis, readme_roadmap_generation [EXTRACTED 0.90]
- **LLM Provider Integrations in Backend** — requirements_langchain_google_genai, requirements_langchain_groq, requirements_langchain_huggingface [EXTRACTED 0.95]
- **Tests Blocked by OAuth-Only Auth** — testsprite_tc002, testsprite_tc003, testsprite_bug_oauth_lock [EXTRACTED 0.90]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (34): CareerAtlas Proposal (Documentation), Deep Researcher Agentic System (Documentation), SkillGraph: Resume Extraction and RAG Pipeline (Documentation), Backend (Python FastAPI + uv), CareerAtlas Platform, Decoupled Architecture Design, Environment Variables Configuration, Frontend (Vite + React + Bun) (+26 more)

### Community 1 - "Community 1"
Cohesion: 0.16
Nodes (8): InsForgeClient, analyze_gaps(), AnalyzeGapsRequest, generate_roadmap(), GenerateRoadmapRequest, parse_resume(), research_jobs(), ResearchJobsRequest

### Community 2 - "Community 2"
Cohesion: 0.18
Nodes (13): BaseModel, ParseResumeRequest, CourseSchema, EducationSchema, ExperienceSchema, GapAnalysisResponse, GapSchema, MilestoneSchema (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.12
Nodes (13): get_gemini_model(), get_groq_model(), get_huggingface_model(), Returns a configured Groq model instance. Best for fast, responsive generation., Returns a configured HuggingFace model instance. Good for auxiliary subtasks., Returns a configured Gemini model instance. Best for complex reasoning and large, create_roadmap_for_gaps(), extract_structured_resume_data() (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.15
Nodes (12): execute_search(), extract_and_score_jobs(), generate_search_queries(), JobSearchState, Generates optimal search queries to find job listings., Executes search using Tavily., Uses LLM to parse raw search results into JobMatchSchema structures., JobMatchSchema (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.31
Nodes (7): analyzeGaps(), generateRoadmap(), getAuthHeaders(), parseResume(), researchJobs(), handleFileUpload(), runAnalysis()

### Community 6 - "Community 6"
Cohesion: 0.29
Nodes (6): useAuth(), useGapAnalysis(), useJobMatches(), useProfile(), useRoadmap(), useSkills()

### Community 9 - "Community 9"
Cohesion: 0.5
Nodes (3): BaseSettings, Config, Settings

### Community 10 - "Community 10"
Cohesion: 0.5
Nodes (2): Validates the JWT token coming from the frontend (which signed in via InsForge)., verify_token()

## Knowledge Gaps
- **12 isolated node(s):** `Config`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `Returns a configured Tavily search tool for LangGraph agent.`, `Returns a configured Gemini model instance. Best for complex reasoning and large`, `Returns a configured Groq model instance. Best for fast, responsive generation.` (+7 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 10`** (4 nodes): `get_current_user_id()`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `verify_token()`, `auth.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ScrapedJobsResponse` connect `Community 4` to `Community 2`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `get_groq_model()` connect `Community 3` to `Community 4`?**
  _High betweenness centrality (0.012) - this node is a cross-community bridge._
- **Why does `parse_resume()` connect `Community 1` to `Community 2`, `Community 3`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Resume Extraction Service` (e.g. with `Bug: Missing UI Fallback Controls` and `TC001: Resume Upload with Target Role`) actually correct?**
  _`Resume Extraction Service` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `ScrapedJobsResponse` (e.g. with `JobSearchState` and `Generates optimal search queries to find job listings.`) actually correct?**
  _`ScrapedJobsResponse` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `parse_resume()` (e.g. with `.download_file()` and `pdf_bytes_to_markdown()`) actually correct?**
  _`parse_resume()` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Config`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `Returns a configured Tavily search tool for LangGraph agent.` to the rest of the system?**
  _12 weakly-connected nodes found - possible documentation gaps or missing edges._