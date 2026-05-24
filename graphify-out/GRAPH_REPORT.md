# Graph Report - Career-Atlas  (2026-05-20)

## Corpus Check
- 122 files · ~46,462 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 431 nodes · 527 edges · 24 communities detected
- Extraction: 75% EXTRACTED · 25% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.66)
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
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 100|Community 100]]
- [[_COMMUNITY_Community 101|Community 101]]
- [[_COMMUNITY_Community 102|Community 102]]
- [[_COMMUNITY_Community 103|Community 103]]
- [[_COMMUNITY_Community 104|Community 104]]
- [[_COMMUNITY_Community 105|Community 105]]
- [[_COMMUNITY_Community 106|Community 106]]
- [[_COMMUNITY_Community 107|Community 107]]
- [[_COMMUNITY_Community 108|Community 108]]
- [[_COMMUNITY_Community 109|Community 109]]

## God Nodes (most connected - your core abstractions)
1. `Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk` - 14 edges
2. `ValidationResult` - 14 edges
3. `Pathway` - 12 edges
4. `request()` - 11 edges
5. `deep_research()` - 9 edges
6. `ScrapedJobsResponse` - 9 edges
7. `get_groq_model()` - 9 edges
8. `useAuth()` - 9 edges
9. `JudgeVerdict` - 8 edges
10. `hybrid_retrieve()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `CareerAtlas Platform` --references--> `CareerAtlas Proposal (Documentation)`  [INFERRED]
  README.md → Documentation/CareerAtlas_Proposal.pdf
- `node_validate()` --calls--> `validate_pathway()`  [INFERRED]
  backend\app\deep_researcher\agent.py → backend\app\deep_researcher\validation.py
- `Resume Extraction Service` --references--> `SkillGraph: Resume Extraction and RAG Pipeline (Documentation)`  [INFERRED]
  README.md → Documentation/SkillGraph_ Resume Extraction and RAG Pipeline.pdf
- `Gap Analysis Service` --conceptually_related_to--> `SkillGraph: Resume Extraction and RAG Pipeline (Documentation)`  [INFERRED]
  README.md → Documentation/SkillGraph_ Resume Extraction and RAG Pipeline.pdf
- `Job Hunter Service (Deep Research Agent)` --references--> `Deep Researcher Agentic System (Documentation)`  [INFERRED]
  README.md → Documentation/Deep Researcher Agentic System.pdf

## Hyperedges (group relationships)
- **Core AI Processing Pipeline** — readme_resume_extraction, readme_gap_analysis, readme_roadmap_generation [EXTRACTED 0.90]
- **LLM Provider Integrations in Backend** — requirements_langchain_google_genai, requirements_langchain_groq, requirements_langchain_huggingface [EXTRACTED 0.95]
- **Tests Blocked by OAuth-Only Auth** — testsprite_tc002, testsprite_tc003, testsprite_bug_oauth_lock [EXTRACTED 0.90]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.09
Nodes (41): Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router], BaseModel, Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a, Run the rubric judge over a pathway. Returns a structured verdict., Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk, All of the user's resume ids, newest first., Most recent gap analysis for this role across all the user's resumes.      skill, update_milestone_status() (+33 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (34): CareerAtlas Proposal (Documentation), Deep Researcher Agentic System (Documentation), SkillGraph: Resume Extraction and RAG Pipeline (Documentation), Backend (Python FastAPI + uv), CareerAtlas Platform, Decoupled Architecture Design, Environment Variables Configuration, Frontend (Vite + React + Bun) (+26 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (24): AIService, Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004)., Reranks documents using Jina Reranker v3 (higher accuracy)., _build_bm25_corpus(), hybrid_retrieve(), Hybrid Retrieval Module for Gap Analysis Agent.  Implements the "Hybrid Retrie, Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role, Converts a display title like "Machine Learning Engineer"     into its Pinecone (+16 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (21): execute_search(), extract_and_score_jobs(), generate_search_queries(), JobSearchState, node_search(), Generates optimal search queries to find job listings., Builds targeted job-board search queries for the role + location., Executes search using Tavily. (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (22): get_gemini_model(), get_huggingface_model(), get_openrouter_model(), Returns a configured Gemini model instance. Best for complex reasoning and large, Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op, Returns a configured HuggingFace model instance. Good for auxiliary subtasks., analyze_gaps(), AnalyzeGapsRequest (+14 more)

### Community 5 - "Community 5"
Cohesion: 0.13
Nodes (12): AppLayout(), useAuth(), useEducation(), useEnabled(), useExperience(), useGapAnalysis(), useJobMatches(), useLatestResume() (+4 more)

### Community 6 - "Community 6"
Cohesion: 0.21
Nodes (18): build_extraction_prompt(), build_repair_prompt(), build_url_manifest(), classify_url(), _enforce_post_processing(), extract_embedded_urls(), extract_pdf_text(), extract_structured_resume_data() (+10 more)

### Community 7 - "Community 7"
Cohesion: 0.16
Nodes (13): analyzeGaps(), ApiError, authHeaders(), getJobMatches(), getLatestPathway(), getLatestResume(), listMilestones(), request() (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.18
Nodes (13): critic_route(), _gaps_brief(), _gaps_detailed(), node_judge(), node_plan(), node_structure(), node_validate(), _notes_brief() (+5 more)

### Community 9 - "Community 9"
Cohesion: 0.33
Nodes (9): _delete_other_resumes(), fetch_full_resume(), get_latest_resume(), insert_full_resume(), _insert_resume_row(), _latest_resume_id(), parse_resume(), Replace-on-upload: keep one resume per user.      All child tables (skills, ex (+1 more)

### Community 10 - "Community 10"
Cohesion: 0.32
Nodes (6): _decode(), _get_jwks(), Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token, Decode + verify a token against a JWKS dict; return the user id (sub)., Validate the Supabase JWT from the Authorization header.      Returns the user U, verify_token()

### Community 11 - "Community 11"
Cohesion: 0.33
Nodes (6): list_job_matches(), _posted_days_to_int(), Coerce the LLM's free-text 'posted' value into a day count for the int column., Return the current user's persisted job matches (latest search)., research_jobs(), ResearchJobsRequest

### Community 18 - "Community 18"
Cohesion: 0.67
Nodes (2): BaseSettings, Settings

### Community 22 - "Community 22"
Cohesion: 1.0
Nodes (1): Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro

### Community 100 - "Community 100"
Cohesion: 1.0
Nodes (1): Validates the JWT token coming from the frontend (which signed in via InsForge).

### Community 101 - "Community 101"
Cohesion: 1.0
Nodes (1): Converts a display title like "Machine Learning Engineer"     into its Pinecone

### Community 102 - "Community 102"
Cohesion: 1.0
Nodes (1): Builds a BM25 index from Pinecone taxonomy metadata for a specific role.

### Community 103 - "Community 103"
Cohesion: 1.0
Nodes (1): Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role

### Community 104 - "Community 104"
Cohesion: 1.0
Nodes (1): Returns a configured Tavily search tool for LangGraph agent.

### Community 105 - "Community 105"
Cohesion: 1.0
Nodes (1): Returns a configured Gemini model instance. Best for complex reasoning and large

### Community 106 - "Community 106"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 107 - "Community 107"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 108 - "Community 108"
Cohesion: 1.0
Nodes (1): Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.

### Community 109 - "Community 109"
Cohesion: 1.0
Nodes (1): Feeds markdown to Gemini with strict structured output.

## Knowledge Gaps
- **47 isolated node(s):** `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`, `Run a recency-filtered web search; returns normalized result dicts.`, `Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token`, `Decode + verify a token against a JWKS dict; return the user id (sub).`, `Validate the Supabase JWT from the Authorization header.      Returns the user U` (+42 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (3 nodes): `config.py`, `BaseSettings`, `Settings`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 22`** (2 nodes): `prompts.py`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 100`** (1 nodes): `Validates the JWT token coming from the frontend (which signed in via InsForge).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 101`** (1 nodes): `Converts a display title like "Machine Learning Engineer"     into its Pinecone`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 102`** (1 nodes): `Builds a BM25 index from Pinecone taxonomy metadata for a specific role.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 103`** (1 nodes): `Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 104`** (1 nodes): `Returns a configured Tavily search tool for LangGraph agent.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 105`** (1 nodes): `Returns a configured Gemini model instance. Best for complex reasoning and large`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 106`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 107`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 108`** (1 nodes): `Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 109`** (1 nodes): `Feeds markdown to Gemini with strict structured output.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `generate_gaps_for_user()` connect `Community 4` to `Community 8`, `Community 2`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `get_groq_model()` connect `Community 8` to `Community 3`, `Community 4`, `Community 6`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `hybrid_retrieve()` connect `Community 2` to `Community 4`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk` (e.g. with `DeepResearchRequest` and `DeepResearchResponse`) actually correct?**
  _`Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `ValidationResult` (e.g. with `Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router]` and `Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a`) actually correct?**
  _`ValidationResult` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `Pathway` (e.g. with `Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router]` and `Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a`) actually correct?**
  _`Pathway` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`, `Run a recency-filtered web search; returns normalized result dicts.`, `Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._