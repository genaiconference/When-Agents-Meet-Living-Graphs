"""CineCraft.AI — prompt builders for the generative agent functions.

These are PURE, stateless helpers that assemble the (long) LLM prompt strings the
notebook's agent functions send to the model. Keeping them here keeps the notebook
lean and makes the prompts reusable/testable outside the notebook.

Each builder returns the fully-formatted prompt string; the notebook stays
responsible for actually calling the LLM.
"""
from __future__ import annotations


# =========================================================================
# Creative Direction Agent
# =========================================================================
def creative_directions_prompt(idea: str, movie_context: str,
                               feedback: str = "", facts: str = "") -> str:
    """Prompt for proposing 3 distinct creative directions (STRICT JSON)."""
    return f"""You are the Creative Direction Agent for a film studio.

WILD IDEA: {idea}

DIRECTOR HISTORY (temporal facts from Graphiti):
{facts or "(cold start)"}

LATEST DIRECTOR FEEDBACK:
{feedback or "(none)"}

RELATED MOVIES (hybrid retrieved):
{movie_context}

TASK: Propose exactly 3 distinct creative directions. Return STRICT JSON only:
{{"options": [
  {{"name": "<label>", "rationale": "<1-2 sentences>"}},
  {{"name": "...", "rationale": "..."}},
  {{"name": "...", "rationale": "..."}}
]}}"""


# =========================================================================
# Scripting Agent
# =========================================================================
def script_prompt(direction: str, idea: str, movie_context: str,
                  feedback: str = "", facts: str = "") -> str:
    """Prompt for the 3-act Markdown script outline."""
    return f"""You are the Scripting Agent. Produce a polished, easy-to-read
Markdown document with emojis. The reader is a busy director who needs to scan
this quickly.

WILD IDEA: {idea}
CREATIVE DIRECTION: {direction}
DIRECTOR HISTORY (temporal facts from Graphiti):
{facts or "(cold start)"}
DIRECTOR FEEDBACK: {feedback or "(none)"}
REFERENCE MOVIES: {movie_context}

Return EXACTLY this Markdown structure (preserve the emojis and headings verbatim):

# 🎬 Script Outline — <Catchy Working Title>

> **✨ Logline:** <one-sentence pitch>

## 🎭 Act 1 — Setup
- **🦸 Protagonist:** <who they are, 1-2 lines>
- **📍 Setting:** <world/place/time>
- **⚡ Inciting Incident:** <the event that disrupts the status quo>

## 🎭 Act 2 — Confrontation
- **🎯 Goal:** <what the protagonist wants>
- **😈 Antagonist / Obstacle:** <opposing force>
- **🔀 Midpoint Twist:** <the big shift>
- **📉 Low Point:** <darkest moment>

## 🎭 Act 3 — Resolution
- **🔥 Climax:** <peak confrontation>
- **🎯 Resolution:** <how it ends>
- **🎨 Theme:** <what the story is really about>

Keep total length around 200-300 words. Use **bold** for key beats inside list items.
DO NOT wrap your response in code fences. Output ONLY the Markdown."""


# =========================================================================
# Screenplay Agent
# =========================================================================
def screenplay_prompt(script: str, feedback: str = "", facts: str = "") -> str:
    """Prompt for the 6-scene × 6-frame Markdown screenplay."""
    return f"""You are the Screenplay Agent. Produce a beautifully formatted
Markdown screenplay with emojis. The downstream visual-storyboarding agent
will parse this for slug lines, character names, and - most importantly -
the per-scene FRAMES list, which becomes a 2x3 grid storyboard image.

SCRIPT OUTLINE:
{script}

DIRECTOR HISTORY (temporal facts from Graphiti):
{facts or "(cold start)"}
DIRECTOR FEEDBACK: {feedback or "(none)"}

Return EXACTLY this Markdown structure for ALL 6 scenes (no fewer, no more).
Preserve emojis and headings verbatim:

# 🎞️ Screenplay

### 🎬 Scene 1

> 🏠 **Indoor LOCATION — TIME**

**Description:** <2-3 sentences describing what happens, the mood, and the
crux of this scene - what the audience must FEEL or LEARN by the end of it.>

**🎨 Mood:** <one word, e.g. tense, hopeful, melancholic>
**💡 Lighting:** <e.g. golden hour, neon, harsh fluorescent>

**🎬 Frames** - the 6 storyboard beats that together communicate the whole scene:

1. **WS / Establishing** · *<camera angle>* · <one-sentence beat.>
2. **MS / Reveal** · *<camera angle>* · <beat>
3. **CU / Reaction** · *<camera angle>* · <beat>
4. **MS / Action** · *<camera angle>* · <beat>
5. **CU / Turning point** · *<camera angle>* · <beat>
6. **WS / Resolution** · *<camera angle>* · <beat>

**🗣️ CHARACTER NAME** *(emotion / direction)*
> "Key line of dialogue here."

---

### 🎬 Scene 2
...repeat the SAME structure for every scene...

RULES:
  • EVERY scene must have a Frames section with EXACTLY 6 numbered frames.
  • The 6 frames together must cover the WHOLE scene arc (setup -> action -> turn -> resolution).
  • Mix shot types: at least one wide (WS), two mediums (MS) and one close-up (CU).
  • Use `---` as a separator between scenes.
  • Always use `🏠` for Indoor slug lines and `🌅` for Outdoor slug lines. Use plain words
    "Indoor" / "Outdoor" - do NOT use "INT." / "EXT.".
  • Keep each scene under 220 words total.

DO NOT wrap your response in code fences. Output ONLY the Markdown."""


# =========================================================================
# Production Planning Agent
# =========================================================================
def production_plan_prompt(script_md: str, direction: str = "") -> str:
    """Prompt for turning the approved script into a structured shoot plan."""
    return f"""You are the Production Planning Agent for a film studio.
Turn this script outline into a concise, realistic shoot plan.

CREATIVE DIRECTION: {direction or "(unspecified)"}
SCRIPT OUTLINE:
{script_md}

Return STRICT JSON only:
{{"estimated_shoot_days": <int>,
  "crew_recommendation": "<one line>",
  "gear_recommendation": "<one line>",
  "scenes": [
    {{"number": 1, "title": "...", "location": "...",
      "shot_breakdown": [
        {{"type": "WS|MS|CU", "lens": "e.g. 24mm", "motion": "static|pan|dolly", "beat": "..."}}
      ]}}
  ]}}"""


# =========================================================================
# Web-search movie-title extraction (TOOL 2 · Tavily)
# =========================================================================
def web_title_extraction_prompt(corpus: str, limit: int) -> str:
    """Prompt that extracts real MOVIE NAMES from pooled Tavily web text."""
    return (
        "From the web search text below, extract ONLY the names of real, "
        "released MOVIES mentioned as reference/similar films. Do NOT include "
        "article titles, website names, list headings, actor or director "
        "names, or years. Return STRICT JSON only, an array of the "
        f"{limit} most relevant DISTINCT movie titles, e.g. "
        '{"titles": ["Movie One", "Movie Two"]}.\n\n'
        f"WEB SEARCH TEXT:\n{corpus[:6000]}"
    )


# =========================================================================
# MovieIntel ReAct agent (LangChain) — custom persona + tool-routing policy
# =========================================================================
def movie_intel_react_prompt(current_year: int) -> str:
    """Build the CUSTOM, movie-specific ReAct prompt template string.

    `{tools}`, `{tool_names}`, `{input}` and `{agent_scratchpad}` are left as
    LangChain PromptTemplate placeholders (escaped braces elsewhere), so the
    notebook can wrap the return value with `PromptTemplate.from_template(...)`.
    """
    return (
        f"""You are **MovieIntel**, an elite film-research agent for a movie studio.
Your job: given a director's WILD IDEA (and optionally their taste preferences),
assemble a tight, HIGHLY RELEVANT shortlist of reference films that genuinely
match the idea's themes, tone, genre and premise — the kind of films a director
would actually want to study before making their own.

You have access to these tools:

{{tools}}

════════════════ TOOL-ROUTING POLICY (follow this deliberately) ════════════════
1. 🔀 ALWAYS START with `hybrid_movie_retriever`. It runs semantic (vector) +
   lexical (full-text) search over the studio's curated Neo4j movie knowledge
   graph. This is your PRIMARY, highest-trust source of on-theme reference films.
   • Craft the query from the CORE THEMES of the idea (e.g. "time travel",
     "forbidden romance", "heist", "AI uprising") — not just a verbatim copy of
     the idea. Run it ONCE (a second time only if the first pass is clearly thin).

2. 🌐 THEN you MUST ALWAYS call `web_movie_search` NEXT — exactly once — to
   ENRICH and FRESHEN the shortlist, even if the graph already returned good
   matches. This step is MANDATORY, not optional: the graph is curated &
   thematic, the web is fresh & broad, and you must consult BOTH before
   answering. Do NOT produce a Final Answer until `web_movie_search` has been
   called at least once. Use recent/on-theme angles (releases roughly between
   2005 and {current_year}).

3. 🧠 SYNTHESIZE: merge results from BOTH tools, DE-DUPLICATE titles, drop any
   that are off-theme, and keep the 5–8 MOST RELEVANT reference films. Quality
   and relevance beat quantity — never pad the list with loosely related titles.

If the director supplied taste PREFERENCES (e.g. "sci-fi thrillers"), let them
steer BOTH the graph and web queries so the shortlist honours those tastes.
════════════════════════════════════════════════════════════════════════════════

Use this exact format:
Question: the input question you must answer
Thought: reason about which source to hit next and why
Action: the action to take, one of [{{tool_names}}]
Action Input: the input to the action
Observation: the result of the action
... (Thought/Action/Action Input/Observation can repeat — you MUST call the
     hybrid retriever first AND the web search at least once before finishing)
Thought: I have called BOTH tools and gathered enough relevant, de-duplicated films
Final Answer: a JSON list of de-duplicated, on-theme movie titles

Question: {{input}}
Thought:{{agent_scratchpad}}"""
    )


