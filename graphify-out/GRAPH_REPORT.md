# Graph Report - Career-Atlas  (2026-07-17)

## Corpus Check
- 151 files · ~200,535 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 780 nodes · 1146 edges · 62 communities detected
- Extraction: 64% EXTRACTED · 36% INFERRED · 0% AMBIGUOUS · INFERRED: 414 edges (avg confidence: 0.65)
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
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 28|Community 28]]
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
- [[_COMMUNITY_Community 154|Community 154]]
- [[_COMMUNITY_Community 155|Community 155]]
- [[_COMMUNITY_Community 156|Community 156]]
- [[_COMMUNITY_Community 157|Community 157]]
- [[_COMMUNITY_Community 158|Community 158]]

## God Nodes (most connected - your core abstractions)
1. `ResumeExtraction` - 26 edges
2. `ValidationResult` - 22 edges
3. `Pathway` - 19 edges
4. `request()` - 17 edges
5. `Gap Analysis Agent — API Router.  POST /api/analyze-gaps/   - Fetches user sk` - 14 edges
6. `GapIn` - 13 edges
7. `JudgeVerdict` - 13 edges
8. `GitHubOAuthCallback` - 13 edges
9. `RepoSelection` - 13 edges
10. `SkillAction` - 13 edges

## Surprising Connections (you probably didn't know these)
- `CareerAtlas Platform` --references--> `CareerAtlas Proposal (Documentation)`  [INFERRED]
  README.md → Documentation/CareerAtlas_Proposal.pdf
- `node_validate()` --calls--> `validate_pathway()`  [INFERRED]
  backend\app\deep_researcher\agent.py → backend\app\deep_researcher\validation.py
- `_build_job_result()` --calls--> `test_build_job_result_maps_scores_and_explanation()`  [INFERRED]
  backend\app\job_hunter\agent.py → backend\tests\test_job_hunter_agent.py
- `JobResult` --uses--> `Unit tests for app.job_hunter.agent (pure scoring / parsing logic).`  [INFERRED]
  backend\app\job_hunter\schemas.py → backend\tests\test_job_hunter_agent.py
- `ResumeExtraction` --uses--> `Unit tests for app.resume_extraction.service (pure normalization / parsing).`  [INFERRED]
  backend\app\resume_extraction\schemas.py → backend\tests\test_resume_extraction_service.py

## Hyperedges (group relationships)
- **Core AI Processing Pipeline** — readme_resume_extraction, readme_gap_analysis, readme_roadmap_generation [EXTRACTED 0.90]
- **LLM Provider Integrations in Backend** — requirements_langchain_google_genai, requirements_langchain_groq, requirements_langchain_huggingface [EXTRACTED 0.95]
- **Tests Blocked by OAuth-Only Auth** — testsprite_tc002, testsprite_tc003, testsprite_bug_oauth_lock [EXTRACTED 0.90]

## Communities

### Community 0 - "Community 0"
Cohesion: 0.06
Nodes (64): node_judge(), Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router], BaseModel, evaluate_pathway(), _gaps_text(), Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a, Run the rubric judge over a pathway. Returns a structured verdict., Run the rubric judge over a pathway. Returns a structured verdict. (+56 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (50): AIService, Retrieves embeddings using Google Gemini Embedding 2 (text-embedding-004)., Reranks documents using Jina Reranker v3 (higher accuracy)., _build_bm25_corpus(), hybrid_retrieve(), Hybrid Retrieval Module for Gap Analysis Agent.  Implements the "Hybrid Retrie, Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role, Converts a display title like "Machine Learning Engineer"     into its Pinecone (+42 more)

### Community 2 - "Community 2"
Cohesion: 0.06
Nodes (62): _backfill_skills(), build_extraction_prompt(), build_repair_prompt(), build_url_manifest(), classify_url(), _dedupe_strings(), _enforce_post_processing(), extract_embedded_urls() (+54 more)

### Community 3 - "Community 3"
Cohesion: 0.05
Nodes (52): latest_resume_id(), Shared resume-lookup helpers.  Several routers need "the user's resumes, newes, All of the user's resume ids, newest first. Strictly scoped to user_id., The user's most recent resume id, or None if they have none., user_resume_ids(), add_skill(), deep_research(), _delete_other_resumes() (+44 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (46): build_bulk_explanation_prompt(), build_compact_resume_for_llm(), build_resume_representation(), cosine_sim(), embed_batch(), _fallback_explanations(), _fallback_jobs(), fetch_jobs() (+38 more)

### Community 5 - "Community 5"
Cohesion: 0.09
Nodes (29): addSkill(), analyzeGaps(), ApiError, authHeaders(), cacheJobSearchResponse(), deleteSkill(), getAllResumes(), getCachedJobSearchResponse() (+21 more)

### Community 6 - "Community 6"
Cohesion: 0.1
Nodes (33): fetch_authenticated_login(), fetch_commit_stats(), fetch_file_content(), fetch_github_graphql(), fetch_languages(), fetch_repo_file_tree(), The viewer's login — needed to filter commits to owner-authored only., GET /languages -> bytes per language, returned as rounded percentages. (+25 more)

### Community 7 - "Community 7"
Cohesion: 0.09
Nodes (13): AppLayout(), useAuth(), useAllResumes(), useEducation(), useEnabled(), useExperience(), useGapAnalysis(), useJobMatches() (+5 more)

### Community 8 - "Community 8"
Cohesion: 0.09
Nodes (34): CareerAtlas Proposal (Documentation), Deep Researcher Agentic System (Documentation), SkillGraph: Resume Extraction and RAG Pipeline (Documentation), Backend (Python FastAPI + uv), CareerAtlas Platform, Decoupled Architecture Design, Environment Variables Configuration, Frontend (Vite + React + Bun) (+26 more)

### Community 9 - "Community 9"
Cohesion: 0.1
Nodes (24): critic_route(), _gaps_brief(), _gaps_detailed(), node_plan(), node_structure(), node_validate(), _notes_brief(), ainvoke_gemini() (+16 more)

### Community 10 - "Community 10"
Cohesion: 0.15
Nodes (27): _build_job_result(), Generates optimal search queries to find job listings., Builds targeted job-board search queries for the role + location., Executes search using Tavily., Runs every planned query through Tavily and aggregates the results., Uses LLM to parse raw search results into JobMatchSchema structures., Uses LLM to parse raw search results into JobMatchSchema structures., _insert_job_match() (+19 more)

### Community 11 - "Community 11"
Cohesion: 0.24
Nodes (18): confirm_github_skills(), get_github_insights(), Powers the insights panel: stored profile + per-repo facts + quarantined     sk, Powers the insights panel: stored profile + per-repo facts + quarantined     sk, Powers the insights panel: stored profile + per-repo facts + quarantined     sk, Promote suggested skills into the verified profile (confirmed=true). Gap     an, The user's most recent resume id, or None if they have none.      Strictly sco, Promote suggested skills into the verified profile (confirmed=true). Gap     an (+10 more)

### Community 12 - "Community 12"
Cohesion: 0.2
Nodes (8): node_search(), Shared Tavily web-search helper.  Wraps `langchain_tavily.TavilySearch` (the mai, Run a Tavily search and return a normalized list:         [{url, title, content,, tavily_search(), Job Hunter — web search (recency-filtered Tavily)., Run a recency-filtered job search; returns normalized result dicts., Run a recency-filtered web search; returns normalized result dicts., search_web()

### Community 13 - "Community 13"
Cohesion: 0.28
Nodes (7): BaseSettings, _get_google_api_keys(), Settings, Unit tests for app.config Google API key discovery., test_get_google_api_keys_collects_main_and_numbered(), test_get_google_api_keys_dedupes_and_strips(), test_get_google_api_keys_empty_when_unset()

### Community 14 - "Community 14"
Cohesion: 0.32
Nodes (6): _decode(), _get_jwks(), Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token, Decode + verify a token against a JWKS dict; return the user id (sub)., Validate the Supabase JWT from the Authorization header.      Returns the user U, verify_token()

### Community 15 - "Community 15"
Cohesion: 0.38
Nodes (5): http_exception_handler(), _is_rate_limit(), Intentionally errors — used to verify Sentry capture end-to-end.      Disabled, sentry_debug(), unhandled_exception_handler()

### Community 19 - "Community 19"
Cohesion: 0.5
Nodes (2): asStringList(), normalizeProject()

### Community 28 - "Community 28"
Cohesion: 1.0
Nodes (1): Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro

### Community 115 - "Community 115"
Cohesion: 1.0
Nodes (1): Intentionally errors — used to verify Sentry capture end-to-end.

### Community 116 - "Community 116"
Cohesion: 1.0
Nodes (1): Like `get_current_user_id`, but rejects unauthenticated requests.      Routes

### Community 117 - "Community 117"
Cohesion: 1.0
Nodes (1): Intentionally errors — used to verify Sentry capture end-to-end.

### Community 118 - "Community 118"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 119 - "Community 119"
Cohesion: 1.0
Nodes (1): Guarantee taxonomy rows exist for this role.      Returns the taxonomy source:

### Community 120 - "Community 120"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 121 - "Community 121"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 122 - "Community 122"
Cohesion: 1.0
Nodes (1): Replace-on-upload: keep one resume per user.      All child tables (skills, ex

### Community 123 - "Community 123"
Cohesion: 1.0
Nodes (1): The user's most recent resume id, or None if they have none.      Strictly sco

### Community 124 - "Community 124"
Cohesion: 1.0
Nodes (1): Change the user's target role (persisted in the `profiles` table).

### Community 125 - "Community 125"
Cohesion: 1.0
Nodes (1): Add a skill to the user's latest resume.

### Community 126 - "Community 126"
Cohesion: 1.0
Nodes (1): Remove a skill (by name) from the user's latest resume.

### Community 127 - "Community 127"
Cohesion: 1.0
Nodes (1): Returns a configured Gemini model instance. Best for complex reasoning and large

### Community 128 - "Community 128"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 129 - "Community 129"
Cohesion: 1.0
Nodes (1): Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op

### Community 130 - "Community 130"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 131 - "Community 131"
Cohesion: 1.0
Nodes (1): Upload a resume file to the private bucket; return its object path.

### Community 132 - "Community 132"
Cohesion: 1.0
Nodes (1): Download a resume file by its storage object path.

### Community 133 - "Community 133"
Cohesion: 1.0
Nodes (1): Intentionally errors — used to verify Sentry capture end-to-end.

### Community 134 - "Community 134"
Cohesion: 1.0
Nodes (1): LLM structured output schema.

### Community 135 - "Community 135"
Cohesion: 1.0
Nodes (1): Full API response returned to the frontend.

### Community 136 - "Community 136"
Cohesion: 1.0
Nodes (1): Replace-on-upload: keep one resume per user.      All child tables (skills, ex

### Community 137 - "Community 137"
Cohesion: 1.0
Nodes (1): Change the user's target role (persisted in the `profiles` table).

### Community 138 - "Community 138"
Cohesion: 1.0
Nodes (1): Add a skill to the user's latest resume.

### Community 139 - "Community 139"
Cohesion: 1.0
Nodes (1): Remove a skill (by name) from the user's latest resume.

### Community 140 - "Community 140"
Cohesion: 1.0
Nodes (1): Edit an experience entry's title / company / dates.

### Community 141 - "Community 141"
Cohesion: 1.0
Nodes (1): LLM structured output schema.

### Community 142 - "Community 142"
Cohesion: 1.0
Nodes (1): Full API response returned to the frontend.

### Community 143 - "Community 143"
Cohesion: 1.0
Nodes (1): Coerce the LLM's free-text 'posted' value into a day count for the int column.

### Community 144 - "Community 144"
Cohesion: 1.0
Nodes (1): Return the current user's persisted job matches (latest search).

### Community 145 - "Community 145"
Cohesion: 1.0
Nodes (1): Replace-on-upload: keep one resume per user.      All child tables (skills, ex

### Community 146 - "Community 146"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 147 - "Community 147"
Cohesion: 1.0
Nodes (1): Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op

### Community 148 - "Community 148"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 149 - "Community 149"
Cohesion: 1.0
Nodes (1): Validates the JWT token coming from the frontend (which signed in via InsForge).

### Community 150 - "Community 150"
Cohesion: 1.0
Nodes (1): Converts a display title like "Machine Learning Engineer"     into its Pinecone

### Community 151 - "Community 151"
Cohesion: 1.0
Nodes (1): Builds a BM25 index from Pinecone taxonomy metadata for a specific role.

### Community 152 - "Community 152"
Cohesion: 1.0
Nodes (1): Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role

### Community 153 - "Community 153"
Cohesion: 1.0
Nodes (1): Returns a configured Tavily search tool for LangGraph agent.

### Community 154 - "Community 154"
Cohesion: 1.0
Nodes (1): Returns a configured Gemini model instance. Best for complex reasoning and large

### Community 155 - "Community 155"
Cohesion: 1.0
Nodes (1): Returns a configured Groq model instance. Best for fast, responsive generation.

### Community 156 - "Community 156"
Cohesion: 1.0
Nodes (1): Returns a configured HuggingFace model instance. Good for auxiliary subtasks.

### Community 157 - "Community 157"
Cohesion: 1.0
Nodes (1): Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.

### Community 158 - "Community 158"
Cohesion: 1.0
Nodes (1): Feeds markdown to Gemini with strict structured output.

## Knowledge Gaps
- **111 isolated node(s):** `Intentionally errors — used to verify Sentry capture end-to-end.      Disabled`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`, `Run a recency-filtered web search; returns normalized result dicts.`, `Auth dependency — verifies Supabase user JWTs.  The Supabase project signs token`, `Decode + verify a token against a JWKS dict; return the user id (sub).` (+106 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 19`** (5 nodes): `asStringList()`, `handleAddSkill()`, `handleRemoveSkill()`, `normalizeProject()`, `_app.profile.tsx`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 28`** (2 nodes): `prompts.py`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 115`** (1 nodes): `Intentionally errors — used to verify Sentry capture end-to-end.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 116`** (1 nodes): `Like `get_current_user_id`, but rejects unauthenticated requests.      Routes`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 117`** (1 nodes): `Intentionally errors — used to verify Sentry capture end-to-end.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 118`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 119`** (1 nodes): `Guarantee taxonomy rows exist for this role.      Returns the taxonomy source:`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 120`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 121`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 122`** (1 nodes): `Replace-on-upload: keep one resume per user.      All child tables (skills, ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 123`** (1 nodes): `The user's most recent resume id, or None if they have none.      Strictly sco`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 124`** (1 nodes): `Change the user's target role (persisted in the `profiles` table).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 125`** (1 nodes): `Add a skill to the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 126`** (1 nodes): `Remove a skill (by name) from the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 127`** (1 nodes): `Returns a configured Gemini model instance. Best for complex reasoning and large`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 128`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 129`** (1 nodes): `Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 130`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 131`** (1 nodes): `Upload a resume file to the private bucket; return its object path.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 132`** (1 nodes): `Download a resume file by its storage object path.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 133`** (1 nodes): `Intentionally errors — used to verify Sentry capture end-to-end.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 134`** (1 nodes): `LLM structured output schema.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 135`** (1 nodes): `Full API response returned to the frontend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 136`** (1 nodes): `Replace-on-upload: keep one resume per user.      All child tables (skills, ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 137`** (1 nodes): `Change the user's target role (persisted in the `profiles` table).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 138`** (1 nodes): `Add a skill to the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 139`** (1 nodes): `Remove a skill (by name) from the user's latest resume.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 140`** (1 nodes): `Edit an experience entry's title / company / dates.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 141`** (1 nodes): `LLM structured output schema.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 142`** (1 nodes): `Full API response returned to the frontend.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 143`** (1 nodes): `Coerce the LLM's free-text 'posted' value into a day count for the int column.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 144`** (1 nodes): `Return the current user's persisted job matches (latest search).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 145`** (1 nodes): `Replace-on-upload: keep one resume per user.      All child tables (skills, ex`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 146`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 147`** (1 nodes): `Returns a ChatOpenAI instance pointed at OpenRouter.     Any model slug from op`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 148`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 149`** (1 nodes): `Validates the JWT token coming from the frontend (which signed in via InsForge).`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 150`** (1 nodes): `Converts a display title like "Machine Learning Engineer"     into its Pinecone`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 151`** (1 nodes): `Builds a BM25 index from Pinecone taxonomy metadata for a specific role.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 152`** (1 nodes): `Full hybrid retrieval pipeline:       1. Semantic search in Pinecone with role`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 153`** (1 nodes): `Returns a configured Tavily search tool for LangGraph agent.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 154`** (1 nodes): `Returns a configured Gemini model instance. Best for complex reasoning and large`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 155`** (1 nodes): `Returns a configured Groq model instance. Best for fast, responsive generation.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 156`** (1 nodes): `Returns a configured HuggingFace model instance. Good for auxiliary subtasks.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 157`** (1 nodes): `Saves bytes to a temporary file and extracts clean markdown using pymupdf4llm.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 158`** (1 nodes): `Feeds markdown to Gemini with strict structured output.`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ResumeExtraction` connect `Community 3` to `Community 0`, `Community 2`, `Community 11`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Why does `get_groq_model()` connect `Community 9` to `Community 0`, `Community 1`, `Community 2`, `Community 6`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Why does `_invoke_llm()` connect `Community 2` to `Community 9`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Are the 24 inferred relationships involving `ResumeExtraction` (e.g. with `ProfileUpdate` and `SkillIn`) actually correct?**
  _`ResumeExtraction` has 24 INFERRED edges - model-reasoned connections that need verification._
- **Are the 20 inferred relationships involving `ValidationResult` (e.g. with `Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router]` and `Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a`) actually correct?**
  _`ValidationResult` has 20 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `Pathway` (e.g. with `Deep Researcher Agent — LangGraph topology.    plan -> search -> [critic router]` and `Deep Researcher — LLM-as-judge evaluation.  Scores a generated Pathway against a`) actually correct?**
  _`Pathway` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Intentionally errors — used to verify Sentry capture end-to-end.      Disabled`, `Deep Researcher — prompt templates.  Planner / Critic / Structurer originate fro`, `Run a recency-filtered web search; returns normalized result dicts.` to the rest of the system?**
  _111 weakly-connected nodes found - possible documentation gaps or missing edges._