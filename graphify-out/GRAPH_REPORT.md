# Graph Report - Career-Atlas  (2026-05-19)

## Corpus Check
- 109 files · ~39,915 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 311 nodes · 314 edges · 14 communities detected
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 62 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 97|Community 97]]
- [[_COMMUNITY_Community 98|Community 98]]

## God Nodes (most connected - your core abstractions)
1. `hybrid_retrieve()` - 8 edges
2. `extract_structured_resume_data()` - 8 edges
3. `Resume Extraction Service` - 8 edges
4. `generate_gaps_for_user()` - 7 edges
5. `extract_pdf_text()` - 7 edges
6. `useAuth()` - 7 edges
7. `useLatestResume()` - 7 edges
8. `GapAnalysisResponse` - 6 edges
9. `ScrapedJobsResponse` - 6 edges
10. `normalize_url()` - 6 edges

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
Cohesion: 0.17
Nodes (21): get_gemini_model(), Returns a configured Gemini model instance. Best for complex reasoning and large, build_extraction_prompt(), build_repair_prompt(), build_url_manifest(), classify_url(), _enforce_post_processing(), extract_embedded_urls() (+13 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (13): AIService, Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004)., Reranks documents using Jina Reranker v3 (higher accuracy)., _build_bm25_corpus(), hybrid_retrieve(), Hybrid Retrieval Module for Gap Analysis Agent.  Implements the "Hybrid Retrie, Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role, Converts a display title like "Machine Learning Engineer"     into its Pinecone (+5 more)

### Community 3 - "Community 3"
Cohesion: 0.17
Nodes (13): analyze_gaps(), Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk, AnalyzeGapsRequest, GapAnalysisResponse, GapAnalysisResult, GapSchema, Pydantic schemas for the Gap Analysis Agent.  GapSchema — single skill gap wit, A single identified skill gap. (+5 more)

### Community 4 - "Community 4"
Cohesion: 0.15
Nodes (12): execute_search(), extract_and_score_jobs(), generate_search_queries(), JobSearchState, Generates optimal search queries to find job listings., Executes search using Tavily., Uses LLM to parse raw search results into JobMatchSchema structures., JobMatchSchema (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.19
Nodes (12): BaseModel, ResearchJobsRequest, CertificationItem, ContactInfo, CourseSchema, EducationItem, ExperienceItem, MilestoneSchema (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.22
Nodes (12): useAuth(), fetchLatestResume(), getAccessToken(), useEducation(), useExperience(), useGapAnalysis(), useJobMatches(), useLatestResume() (+4 more)

### Community 7 - "Community 7"
Cohesion: 0.18
Nodes (8): get_groq_model(), get_huggingface_model(), Returns a configured Groq model instance. Best for fast, responsive generation., Returns a configured HuggingFace model instance. Good for auxiliary subtasks., generate_roadmap(), GenerateRoadmapRequest, create_roadmap_for_gaps(), Constructs an actionable learning roadmap based on identified skill gaps.

### Community 8 - "Community 8"
Cohesion: 0.31
Nodes (7): analyzeGaps(), generateRoadmap(), getAuthHeaders(), parseResume(), researchJobs(), handleFileUpload(), runAnalysis()

### Community 9 - "Community 9"
Cohesion: 0.43
Nodes (7): fetch_full_resume(), get_latest_resume(), insert_full_resume(), _insert_resume_row(), _latest_resume_id(), parse_resume(), _safe_filename()

### Community 12 - "Community 12"
Cohesion: 0.5
Nodes (2): Validates the JWT token coming from the frontend (which signed in via InsForge)., verify_token()

### Community 16 - "Community 16"
Cohesion: 0.67
Nodes (2): BaseSettings, Settings

### Community 97 - "Community 97"
Cohesion: 1.0
Nodes (1): Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.

### Community 98 - "Community 98"
Cohesion: 1.0
Nodes (1): Feeds markdown to Gemini with strict structured output.

## Knowledge Gaps
- **25 isolated node(s):** `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `Pinecone client singleton — shared dependency.  Initialized once and cached. U`, `Returns a cached Pinecone Index object for the careeratlas index.     Called on`, `Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004).`, `Reranks documents using Jina Reranker v3 (higher accuracy).` (+20 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 12`** (4 nodes): `get_current_user_id()`, `Validates the JWT token coming from the frontend (which signed in via InsForge).`, `verify_token()`, `auth.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (3 nodes): `config.py`, `BaseSettings`, `Settings`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 97`** (1 nodes): `Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 98`** (1 nodes): `Feeds markdown to Gemini with strict structured output.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `generate_gaps_for_user()` connect `Community 3` to `Community 1`, `Community 2`, `Community 7`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `get_gemini_model()` connect `Community 1` to `Community 3`, `Community 7`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `extract_structured_resume_data()` connect `Community 1` to `Community 9`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `hybrid_retrieve()` (e.g. with `get_pinecone_index()` and `.get_embeddings()`) actually correct?**
  _`hybrid_retrieve()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `extract_structured_resume_data()` (e.g. with `parse_resume()` and `get_gemini_model()`) actually correct?**
  _`extract_structured_resume_data()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `Resume Extraction Service` (e.g. with `Bug: Missing UI Fallback Controls` and `TC001: Resume Upload with Target Role`) actually correct?**
  _`Resume Extraction Service` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 5 inferred relationships involving `generate_gaps_for_user()` (e.g. with `analyze_gaps()` and `resolve_role_slug()`) actually correct?**
  _`generate_gaps_for_user()` has 5 INFERRED edges - model-reasoned connections that need verification._