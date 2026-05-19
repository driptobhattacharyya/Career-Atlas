"""
Deep Researcher — prompt templates.

Planner / Critic / Structurer originate from Notebooks/03_deep_researcher.ipynb.
Judge is ported from the notebook's LLM-as-judge cells (0dbeafe3 / 333e7081),
extended with a `recency` criterion. Prompts take `{current_year}` so the
agent never chases a hardcoded stale year.
"""
from langchain_core.prompts import ChatPromptTemplate


PLAN_PROMPT = ChatPromptTemplate.from_template('''You are a research planner for career-skill learning pathways.

TARGET ROLE: {target_role}
CURRENT YEAR: {current_year}

OUTSTANDING GAPS (skill, relevance, difficulty):
{gaps}

NOTES GATHERED SO FAR (from previous searches, newest last):
{notes}

Propose ONE next web search query that will most improve the pathway.
Rules:
- Iteration 0: start with the highest-relevance gap; seek the best CURRENT courses/docs.
- Always bias toward freshness — include "{current_year}" or "latest" in the query so
  results reflect current framework versions, not deprecated ones.
- Later iterations: cover gaps not yet represented in the notes, or drill deeper.
- Prefer concrete queries ("best PyTorch course {current_year} for production ML")
  over vague ones.''')


CRITIC_PROMPT = ChatPromptTemplate.from_template('''You are a research critic.

TARGET ROLE: {target_role}
GAPS TO COVER:
{gaps}

NOTES GATHERED (newest last):
{notes}

Decide:
- "continue" if the notes don't yet give us enough to recommend concrete, current
  resources for EVERY gap.
- "structure" if we can now write a high-quality learning pathway with real,
  recent links for every gap.''')


STRUCTURE_PROMPT = ChatPromptTemplate.from_template('''You are a senior learning-path designer.

TARGET ROLE: {target_role}
CURRENT YEAR: {current_year}

USER'S SKILL GAPS (ordered by relevance, prerequisites first):
{gaps}

RESEARCH NOTES (URLs + extracts + publish dates from authoritative sources):
{notes}

REVISION FEEDBACK (from a prior evaluation — empty on the first attempt):
{feedback}

Produce a Pathway with:
- ONE milestone per gap, in prerequisite-respecting order.
- Each milestone in an appropriate phase (Foundations / Intermediate / Advanced).
- 2-4 resources per milestone. CRITICAL: every resource `url` MUST be a URL that
  appears verbatim in the RESEARCH NOTES above. Do NOT invent or guess URLs —
  ungrounded links are dropped downstream and will fail evaluation.
- Prefer the most recent resources; avoid anything tied to an old framework version.
- A 3-5 item `checklist` of concrete actions.
- A `mini_project` that exercises the skill in context of the target role.
- `rationale`: why this ordering works for this user.
- If REVISION FEEDBACK is non-empty, address every point in it.''')


JUDGE_PROMPT = ChatPromptTemplate.from_template('''You are a strict evaluator of AI-generated career learning pathways.

Score the pathway 1-5 on each rubric criterion (1=poor, 5=excellent):
1) coverage         — every user gap has a concrete milestone.
2) ordering         — milestones respect prerequisite logic.
3) resource_quality — resources are real, relevant, and role-aligned.
4) actionability    — checklists and mini-projects are concrete and doable.
5) personalization  — the plan reflects the target role and the user's specific gaps.
6) grounding        — resource links and claims trace back to the research notes.
7) recency          — resources are current; no deprecated framework versions or
                       expired/old course pages. Use the publish dates in the notes.

PASS RULE: pass only if overall_score >= 4.0 AND no single criterion is below 3.

CURRENT YEAR: {current_year}
TARGET ROLE: {target_role}

USER GAPS:
{gaps}

RESEARCH NOTES (with publish dates where available):
{notes}

LINK VALIDATION SUMMARY (resources already dropped for dead/ungrounded links):
{validation}

PATHWAY JSON:
{pathway_json}

Return a JudgeVerdict. `improvement_actions` must be concrete, specific fixes the
pathway author can apply on a retry (name the milestone and the problem).''')
