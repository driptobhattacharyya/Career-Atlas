# Graph Report - Career-Atlas  (2026-07-16)

## Corpus Check
- 141 files · ~198,024 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 642 nodes · 869 edges · 58 communities detected
- Extraction: 72% EXTRACTED · 28% INFERRED · 0% AMBIGUOUS · INFERRED: 247 edges (avg confidence: 0.62)
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
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 114|Community 114]]
- [[_COMMUNITY_Community 115|Community 115]]
- [[_COMMUNITY_Community 116|Community 116]]
- [[_COMMUNITY_Community 117|Community 117]]
- [[_COMMUNITY_Community 118|Community 118]]
- [[_COMMUNITY_Community 119|Community 119]]
- [[_COMMUNITY_Community 120|Community 120]]
- [[_COMMUNITY_Community 121|Community 121]]
- [[_COMMUNITY_Community 122|Community 122]]
- [[_COMMUNITY_Community 123|Community 123]]
- [[_COMMUNITY_Community 124|Community 124]]
- [[_COMMUNITY_Community 125|Community 125]]
- [[_COMMUNITY_Community 126|Community 126]]
- [[_COMMUNITY_Community 127|Community 127]]
- [[_COMMUNITY_Community 128|Community 128]]
- [[_COMMUNITY_Community 129|Community 129]]
- [[_COMMUNITY_Community 130|Community 130]]
- [[_COMMUNITY_Community 131|Community 131]]
- [[_COMMUNITY_Community 132|Community 132]]
- [[_COMMUNITY_Community 133|Community 133]]
- [[_COMMUNITY_Community 134|Community 134]]
- [[_COMMUNITY_Community 135|Community 135]]
- [[_COMMUNITY_Community 136|Community 136]]
- [[_COMMUNITY_Community 137|Community 137]]
- [[_COMMUNITY_Community 138|Community 138]]
- [[_COMMUNITY_Community 139|Community 139]]
- [[_COMMUNITY_Community 140|Community 140]]
- [[_COMMUNITY_Community 141|Community 141]]
- [[_COMMUNITY_Community 142|Community 142]]
- [[_COMMUNITY_Community 143|Community 143]]
- [[_COMMUNITY_Community 144|Community 144]]
- [[_COMMUNITY_Community 145|Community 145]]
- [[_COMMUNITY_Community 146|Community 146]]
- [[_COMMUNITY_Community 147|Community 147]]
- [[_COMMUNITY_Community 148|Community 148]]
- [[_COMMUNITY_Community 149|Community 149]]
- [[_COMMUNITY_Community 150|Community 150]]
- [[_COMMUNITY_Community 151|Community 151]]
- [[_COMMUNITY_Community 152|Community 152]]
- [[_COMMUNITY_Community 153|Community 153]]

## God Nodes (most connected - your core abstractions)
1. `ValidationResult` - 18 edges
2. `ResumeExtraction` - 17 edges
3. `request()` - 17 edges
4. `Pathway` - 16 edges
5. `Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk` - 14 edges
6. `JudgeVerdict` - 12 edges
7. `job_finder_agent()` - 11 edges
8. `get_groq_model()` - 11 edges
9. `deep_research()` - 10 edges
10. `GapIn` - 10 edges

## Surprising Connections (you probably didn't know these)
- `CareerAtlas Platform` --references--> `CareerAtlas Proposal (Documentation)`  [INFERRED]
  README.md → Documentation/CareerAtlas_Proposal.pdf
- `Return the user's latest stored skill gaps so results reload on re-sign-in.` --uses--> `AnalyzeGapsRequest`  [INFERRED]
  backend\app\gap_analysis\router.py → backend\app\gap_analysis\schemas.py
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
Cohesion: 0.08
Nodes (50): node_validate(), Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router], BaseModel, Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a, Run the rubric judge over a pathway. Returns a structured verdict., Run the rubric judge over a pathway. Returns a structured verdict., Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk, Most recent gap analysis for this role across all the user's resumes.      ski (+42 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (35): add_skill(), _delete_other_resumes(), delete_skill(), ExperienceUpdate, fetch_full_resume(), get_latest_resume(), insert_full_resume(), _insert_resume_row() (+27 more)

### Community 2 - "Community 2"
Cohesion: 0.09
Nodes (29): addSkill(), analyzeGaps(), ApiError, authHeaders(), cacheJobSearchResponse(), deleteSkill(), getAllResumes(), getCachedJobSearchResponse() (+21 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (28): Converts a display title like "Machine Learning Engineer"     into its Pinecone, resolve_role_slug(), analyze_gaps(), deep_research(), _extract_sources(), get_saved_gaps(), latest_pathway(), _load_gaps() (+20 more)

### Community 4 - "Community 4"
Cohesion: 0.09
Nodes (13): AppLayout(), useAuth(), useAllResumes(), useEducation(), useEnabled(), useExperience(), useGapAnalysis(), useJobMatches() (+5 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (34): CareerAtlas Proposal (Documentation), Deep Researcher Agentic System (Documentation), SkillGraph: Resume Extraction and RAG Pipeline (Documentation), Backend (Python FastAPI + uv), CareerAtlas Platform, Decoupled Architecture Design, Environment Variables Configuration, Frontend (Vite + React + Bun) (+26 more)

### Community 6 - "Community 6"
Cohesion: 0.09
Nodes (23): AIService, Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004)., Reranks documents using Jina Reranker v3 (higher accuracy)., _build_bm25_corpus(), hybrid_retrieve(), Hybrid Retrieval Module for Gap Analysis Agent.  Implements the "Hybrid Retrie, Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role, Builds a BM25 index from Pinecone taxonomy metadata for a specific role. (+15 more)

### Community 7 - "Community 7"
Cohesion: 0.15
Nodes (25): _build_job_result(), Generates optimal search queries to find job listings., Builds targeted job-board search queries for the role + location., Executes search using Tavily., Runs every planned query through Tavily and aggregates the results., Uses LLM to parse raw search results into JobMatchSchema structures., Uses LLM to parse raw search results into JobMatchSchema structures., _insert_job_match() (+17 more)

### Community 8 - "Community 8"
Cohesion: 0.16
Nodes (25): _backfill_skills(), build_extraction_prompt(), build_repair_prompt(), build_url_manifest(), classify_url(), _dedupe_strings(), _enforce_post_processing(), extract_embedded_urls() (+17 more)

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (20): critic_route(), _gaps_brief(), _gaps_detailed(), node_judge(), node_plan(), node_search(), node_structure(), _notes_brief() (+12 more)

### Community 10 - "Community 10"
Cohesion: 0.13
Nodes (23): fetch_authenticated_login(), fetch_commit_stats(), fetch_file_content(), fetch_github_graphql(), fetch_languages(), fetch_repo_file_tree(), The viewer's login — needed to filter commits to owner-authored only., GET /languages -> bytes per language, returned as rounded percentages. (+15 more)

### Community 11 - "Community 11"
Cohesion: 0.15
Nodes (22): build_bulk_explanation_prompt(), build_compact_resume_for_llm(), build_resume_representation(), cosine_sim(), embed_batch(), _fallback_explanations(), _fallback_jobs(), fetch_jobs() (+14 more)

### Community 12 - "Community 12"
Cohesion: 0.24
Nodes (14): confirm_github_skills(), get_github_insights(), Powers the insights panel: stored profile + per-repo facts + quarantined     sk, Powers the insights panel: stored profile + per-repo facts + quarantined     sk, Promote suggested skills into the verified profile (confirmed=true). Gap     an, Promote suggested skills into the verified profile (confirmed=true). Gap     an, Discard suggested skills. ponytail: reject = delete the row; re-analyze     re-, Discard suggested skills. ponytail: reject = delete the row; re-analyze     re- (+6 more)

### Community 13 - "Community 13"
Cohesion: 0.32
Nodes (6): _decode(), _get_jwks(), Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token, Decode + verify a token against a JWKS dict; return the user id (sub)., Validate the Supabase JWT from the Authorization header.      Returns the user U, verify_token()

### Community 14 - "Community 14"
Cohesion: 0.38
Nodes (5): http_exception_handler(), _is_rate_limit(), Intentionally errors — used to verify Sentry capture end-to-end., sentry_debug(), unhandled_exception_handler()

### Community 18 - "Community 18"
Cohesion: 0.5
Nodes (2): asStringList(), normalizeProject()

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (2): BaseSettings, Settings

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro

### Community 114 - "Community 114"
Cohesion: 1.0
Nodes (1): Guarantee taxonomy rows exist for this role.      Returns the taxonomy source:

### Community 115 - "Community 115"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 116 - "Community 116"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 117 - "Community 117"
Cohesion: 1.0
Nodes (1): Replace-on-upload: keep one resume per user.      All child tables (skills, ex

### Community 118 - "Community 118"
Cohesion: 1.0
Nodes (1): The user's most recent resume id, or None if they have none.      Strictly sco

### Community 119 - "Community 119"
Cohesion: 1.0
Nodes (1): Change the user's target role (persisted in the `profiles` table).

### Community 120 - "Community 120"
Cohesion: 1.0
Nodes (1): Add a skill to the user's latest resume.

### Community 121 - "Community 121"
Cohesion: 1.0
Nodes (1): Remove a skill (by name) from the user's latest resume.

### Community 122 - "Community 122"
Cohesion: 1.0
Nodes (1): Returns a configured Gemini model instance. Best for complex reasoning and large

### Community 123 - "Community 123"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 124 - "Community 124"
Cohesion: 1.0
Nodes (1): Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op

### Community 125 - "Community 125"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 126 - "Community 126"
Cohesion: 1.0
Nodes (1): Upload a resume file to the private bucket; return its object path.

### Community 127 - "Community 127"
Cohesion: 1.0
Nodes (1): Download a resume file by its storage object path.

### Community 128 - "Community 128"
Cohesion: 1.0
Nodes (1): Intentionally errors — used to verify Sentry capture end-to-end.

### Community 129 - "Community 129"
Cohesion: 1.0
Nodes (1): LLM structured output schema.

### Community 130 - "Community 130"
Cohesion: 1.0
Nodes (1): Full API response returned to the frontend.

### Community 131 - "Community 131"
Cohesion: 1.0
Nodes (1): Replace-on-upload: keep one resume per user.      All child tables (skills, ex

### Community 132 - "Community 132"
Cohesion: 1.0
Nodes (1): Change the user's target role (persisted in the `profiles` table).

### Community 133 - "Community 133"
Cohesion: 1.0
Nodes (1): Add a skill to the user's latest resume.

### Community 134 - "Community 134"
Cohesion: 1.0
Nodes (1): Remove a skill (by name) from the user's latest resume.

### Community 135 - "Community 135"
Cohesion: 1.0
Nodes (1): Edit an experience entry's title / company / dates.

### Community 136 - "Community 136"
Cohesion: 1.0
Nodes (1): LLM structured output schema.

### Community 137 - "Community 137"
Cohesion: 1.0
Nodes (1): Full API response returned to the frontend.

### Community 138 - "Community 138"
Cohesion: 1.0
Nodes (1): Coerce the LLM's free-text 'posted' value into a day count for the int column.

### Community 139 - "Community 139"
Cohesion: 1.0
Nodes (1): Return the current user's persisted job matches (latest search).

### Community 140 - "Community 140"
Cohesion: 1.0
Nodes (1): Replace-on-upload: keep one resume per user.      All child tables (skills, ex

### Community 141 - "Community 141"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 142 - "Community 142"
Cohesion: 1.0
Nodes (1): Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op

### Community 143 - "Community 143"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 144 - "Community 144"
Cohesion: 1.0
Nodes (1): Validates the JWT token coming from the frontend (which signed in via InsForge).

### Community 145 - "Community 145"
Cohesion: 1.0
Nodes (1): Converts a display title like "Machine Learning Engineer"     into its Pinecone

### Community 146 - "Community 146"
Cohesion: 1.0
Nodes (1): Builds a BM25 index from Pinecone taxonomy metadata for a specific role.

### Community 147 - "Community 147"
Cohesion: 1.0
Nodes (1): Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role

### Community 148 - "Community 148"
Cohesion: 1.0
Nodes (1): Returns a configured Tavily search tool for LangGraph agent.

### Community 149 - "Community 149"
Cohesion: 1.0
Nodes (1): Returns a configured Gemini model instance. Best for complex reasoning and large

### Community 150 - "Community 150"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 151 - "Community 151"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 152 - "Community 152"
Cohesion: 1.0
Nodes (1): Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.

### Community 153 - "Community 153"
Cohesion: 1.0
Nodes (1): Feeds markdown to Gemini with strict structured output.

## Knowledge Gaps
- **90 isolated node(s):** `Intentionally errors — used to verify Sentry capture end-to-end.`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`, `Run a recency-filtered web search; returns normalized result dicts.`, `Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token`, `Decode + verify a token against a JWKS dict; return the user id (sub).` (+85 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 18`** (5 nodes): `asStringList()`, `handleAddSkill()`, `handleRemoveSkill()`, `normalizeProject()`, `_app.profile.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (4 nodes): `config.py`, `BaseSettings`, `_get_google_api_keys()`, `Settings`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `prompts.py`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 114`** (1 nodes): `Guarantee taxonomy rows exist for this role.      Returns the taxonomy source:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 115`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 116`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 117`** (1 nodes): `Replace-on-upload: keep one resume per user.      All child tables (skills, ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 118`** (1 nodes): `The user's most recent resume id, or None if they have none.      Strictly sco`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 119`** (1 nodes): `Change the user's target role (persisted in the `profiles` table).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 120`** (1 nodes): `Add a skill to the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 121`** (1 nodes): `Remove a skill (by name) from the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 122`** (1 nodes): `Returns a configured Gemini model instance. Best for complex reasoning and large`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 123`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 124`** (1 nodes): `Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 125`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 126`** (1 nodes): `Upload a resume file to the private bucket; return its object path.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 127`** (1 nodes): `Download a resume file by its storage object path.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 128`** (1 nodes): `Intentionally errors — used to verify Sentry capture end-to-end.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 129`** (1 nodes): `LLM structured output schema.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 130`** (1 nodes): `Full API response returned to the frontend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 131`** (1 nodes): `Replace-on-upload: keep one resume per user.      All child tables (skills, ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 132`** (1 nodes): `Change the user's target role (persisted in the `profiles` table).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 133`** (1 nodes): `Add a skill to the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 134`** (1 nodes): `Remove a skill (by name) from the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 135`** (1 nodes): `Edit an experience entry's title / company / dates.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 136`** (1 nodes): `LLM structured output schema.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 137`** (1 nodes): `Full API response returned to the frontend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 138`** (1 nodes): `Coerce the LLM's free-text 'posted' value into a day count for the int column.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 139`** (1 nodes): `Return the current user's persisted job matches (latest search).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 140`** (1 nodes): `Replace-on-upload: keep one resume per user.      All child tables (skills, ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 141`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 142`** (1 nodes): `Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 143`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 144`** (1 nodes): `Validates the JWT token coming from the frontend (which signed in via InsForge).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 145`** (1 nodes): `Converts a display title like "Machine Learning Engineer"     into its Pinecone`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 146`** (1 nodes): `Builds a BM25 index from Pinecone taxonomy metadata for a specific role.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 147`** (1 nodes): `Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 148`** (1 nodes): `Returns a configured Tavily search tool for LangGraph agent.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 149`** (1 nodes): `Returns a configured Gemini model instance. Best for complex reasoning and large`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 150`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 151`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 152`** (1 nodes): `Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 153`** (1 nodes): `Feeds markdown to Gemini with strict structured output.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_groq_model()` connect `Community 9` to `Community 3`, `Community 6`, `Community 8`, `Community 10`, `Community 11`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `_invoke_llm()` connect `Community 8` to `Community 9`, `Community 11`?**
  _High betweenness centrality (0.027) - this node is a cross-community bridge._
- **Why does `ValidationResult` connect `Community 0` to `Community 9`, `Community 3`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `ValidationResult` (e.g. with `Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router]` and `Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a`) actually correct?**
  _`ValidationResult` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `ResumeExtraction` (e.g. with `ProfileUpdate` and `SkillIn`) actually correct?**
  _`ResumeExtraction` has 15 INFERRED edges - model-reasoned connections that need verification._
- **Are the 14 inferred relationships involving `Pathway` (e.g. with `Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router]` and `Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a`) actually correct?**
  _`Pathway` has 14 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Intentionally errors — used to verify Sentry capture end-to-end.`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`, `Run a recency-filtered web search; returns normalized result dicts.` to the rest of the system?**
  _90 weakly-connected nodes found - possible documentation gaps or missing edges._