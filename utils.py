from __future__ import annotations
import asyncio
import json
import re


# =========================================================================
# JSON extraction
# =========================================================================
def json_slice(raw: str) -> dict:
    """Extract the first {...} JSON object from an LLM response."""
    start, end = raw.find("{"), raw.rfind("}") + 1
    return json.loads(raw[start:end])


# =========================================================================
# Lucene / Neo4j full-text query sanitisation
# =========================================================================
# Lucene reserved characters that break the full-text query parser if passed raw.
_LUCENE_SPECIAL = re.compile(r'([+\-!(){}\[\]^"~*?:\\/]|&&|\|\|)')


def sanitize_for_lucene(text: str) -> str:
    """Make a free-text string safe for Neo4j's full-text (Lucene) index.

    The HybridRetriever feeds `query_text` straight into
    `db.index.fulltext.queryNodes`, whose Lucene parser errors out on reserved
    characters (`:`, `"`, `(`, `)`, `+`, `-`, `~`, `*`, `?`, `/`, `\\`, …) and on
    non-ASCII punctuation like the `·` separator. We drop the exotic punctuation
    and escape the reserved ASCII characters so the parser always gets a valid
    query. (Vector/semantic search is unaffected — this only tames the lexical
    side.)"""
    # Replace non-ASCII punctuation (e.g. the `·` separator) with spaces.
    cleaned = re.sub(r"[^\x00-\x7F]+", " ", text)
    # Escape Lucene reserved characters.
    cleaned = _LUCENE_SPECIAL.sub(r"\\\1", cleaned)
    # Collapse whitespace.
    return re.sub(r"\s+", " ", cleaned).strip()


# =========================================================================
# Graphiti namespace helper
# =========================================================================
def director_group_id(name: str) -> str:
    """Slugify a director name into a Graphiti group_id namespace."""
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "anon").lower()).strip("_")
    return f"director_{slug or 'anon'}"


# =========================================================================
# Screenplay / storyboard helpers
# =========================================================================
def split_scenes(screenplay_md: str) -> list[str]:
    """Split a screenplay markdown blob into individual scene blocks."""
    parts = re.split(r"\n---\n", screenplay_md)
    return [p.strip() for p in parts if "Scene" in p and "Frames" in p]


def build_scene_image_prompt(scene_md: str) -> str:
    """Compose a storyboard-collage prompt for one screenplay scene."""
    return (
        "Black-and-white cinematic STORYBOARD collage, a single image divided into a clean 2x3 grid "
        "of 6 numbered panels (sketch / concept-art style, hand-drawn look with thin panel borders). "
        "Each panel depicts one of the 6 frames below in order, honoring the shot type (WS/MS/CU) and "
        "camera angle. Consistent characters and location across all panels.\n\n"
        f"SCENE:\n{scene_md}\n\n"
        "No text captions inside the image except small panel numbers 1-6."
    )


# =========================================================================
# Async bridge (sync-friendly wrapper around Graphiti coroutines)
# =========================================================================
def run_async(coro):
    """Run an async coroutine to completion from synchronous (node) code.

    Relies on `nest_asyncio` having been applied in the notebook so we can
    drive a coroutine on the already-running event loop."""
    return asyncio.get_event_loop().run_until_complete(coro)


# =========================================================================
# Saga stage config (chronological chain + per-stage memory questions)
# =========================================================================
# The ordered stages of a saga (the NEXT_STAGE chronological chain).
SAGA_STAGES = [
    "wild_idea", "movie_retrieval", "creative_direction",
    "story", "screenplay", "scene_generation", "pre_production",
]

# Per-stage memory questions (the "different question" each stage asks Graphiti).
# `{director}` is filled in at recall time.
STAGE_QUERIES = {
    "wild_idea":          "recurring creative preferences and dislikes when {director} starts a new movie",
    "movie_retrieval":    "reference/inspiration films {director} accepted or rejected for similar ideas",
    "creative_direction": "visual storytelling preferences and feedback {director} consistently gives",
    "story":              "narrative preferences {director} has: pacing, protagonists, endings, exposition",
    "screenplay":         "screenplay/dialogue feedback {director} repeatedly gives across projects",
    "scene_generation":   "scene-level and shot preferences {director} usually gives: shots, lighting, cuts",
    "pre_production":     "production constraints {director} repeatedly approves: budget, locations, cast, CGI",
}


# =========================================================================
# Presentation helpers (pure HTML builders for the notebook UI)
# =========================================================================
# The pipeline stages shown in the horizontal progress stepper.
PIPELINE_STAGES = [
    ("movie_intel",     "🎞️ Movie Intel"),
    ("directions",      "🧭 Directions"),
    ("script",          "📝 Script"),
    ("screenplay",      "🎭 Screenplay"),
    ("storyboard",      "🖼️ Storyboard"),
    ("production_plan",  "🎬 Production Plan"),
]


def progress_stepper_html(current: str) -> str:
    """Build the HTML for a compact HORIZONTAL progress stepper, highlighting
    the CURRENT stage. Completed stages show ✓, the active one is emphasized,
    and upcoming stages are dimmed."""
    keys = [k for k, _ in PIPELINE_STAGES]
    cur_idx = keys.index(current) if current in keys else -1
    steps = ""
    for i, (key, label) in enumerate(PIPELINE_STAGES):
        done = i < cur_idx
        active = i == cur_idx
        if done:
            dot = ("background:#10b981;color:#fff;border:2px solid #10b981;", "✓")
            txt = "color:#065f46;font-weight:600;"
        elif active:
            dot = ("background:#f59e0b;color:#fff;border:2px solid #f59e0b;"
                   "box-shadow:0 0 0 3px rgba(245,158,11,.25);", "▶")
            txt = "color:#92400e;font-weight:800;"
        else:
            dot = ("background:#fff;color:#cbd5e1;border:2px solid #e2e8f0;", "○")
            txt = "color:#94a3b8;font-weight:500;"
        connector = ("" if i == 0 else
                     f"<div style='flex:0 0 18px;height:2px;margin:0 2px;"
                     f"background:{'#10b981' if i <= cur_idx else '#e2e8f0'};'></div>")
        steps += (
            f"{connector}"
            f"<div style='display:flex;align-items:center;gap:6px;'>"
            f"<div style='flex:0 0 22px;width:22px;height:22px;border-radius:50%;"
            f"display:flex;align-items:center;justify-content:center;font-size:11px;"
            f"font-weight:700;{dot[0]}'>{dot[1]}</div>"
            f"<div style='font-size:12px;white-space:nowrap;{txt}'>{label}</div>"
            f"</div>"
        )
    pct = int(((cur_idx + 1) / len(PIPELINE_STAGES)) * 100) if cur_idx >= 0 else 0
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;width:100%;box-sizing:border-box;
                border:1px solid #e5e7eb;border-radius:12px;padding:8px 14px;margin:6px 0;
                background:linear-gradient(180deg,#ffffff,#f8fafc);
                box-shadow:0 2px 8px rgba(0,0,0,.05);">
      <div style="font-size:10px;font-weight:700;color:#6b7280;text-transform:uppercase;
                  letter-spacing:.5px;margin-bottom:6px;">Pipeline Progress · {pct}%</div>
      <div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">{steps}</div>
    </div>
    """


def card_html(title, subtitle, body_html, accent="#6366f1") -> str:
    """Build the HTML for a clean, modern card for a human-in-the-loop gate."""
    return f"""
    <div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;width:100%;box-sizing:border-box;
                border:1px solid #e5e7eb;border-radius:16px;
                overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.08);margin:12px 0;
                word-wrap:break-word;overflow-wrap:break-word;">
      <div style="background:linear-gradient(135deg,{accent},#8b5cf6);padding:16px 20px;color:#fff;">
        <div style="font-size:18px;font-weight:700;">{title}</div>
        <div style="font-size:13px;opacity:.9;margin-top:2px;">{subtitle}</div>
      </div>
      <div style="padding:18px 20px;color:#111827;font-size:14px;line-height:1.55;
                  word-wrap:break-word;overflow-wrap:break-word;white-space:normal;">{body_html}</div>
    </div>
    """


# =========================================================================
# Backwards-compatible aliases (original notebook names)
# =========================================================================
_json_slice = json_slice
_sanitize_for_lucene = sanitize_for_lucene
_director_group_id = director_group_id
_STAGE_QUERIES = STAGE_QUERIES
