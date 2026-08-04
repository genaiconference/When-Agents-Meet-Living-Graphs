from __future__ import annotations
import asyncio
import json
import re
import inspect
from schema import edge_types, edge_type_map
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF
from graphiti_core import graphiti


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


# =========================================================================
# HTML helpers — beautified summary of what Graphiti extracted per episode
# =========================================================================
# Schema-driven colour palette: every custom entity type from schema.py gets
# its own consistent colour, so (for example) ALL Character nodes are the same
# colour, all Location nodes another, etc. Update here if the schema grows.
ENTITY_COLORS = {
    "Director":            "#dc2626",  # red
    "FilmProject":         "#0f172a",  # near-black (the central hub)
    "Character":           "#2563eb",  # blue — all characters share this
    "Scene":               "#0891b2",  # cyan
    "Location":            "#059669",  # green
    "Theme":               "#7c3aed",  # violet
    "Genre":               "#c026d3",  # fuchsia
    "CreativeConstraint":  "#b45309",  # amber/brown
    "ReferenceFilm":       "#4f46e5",  # indigo
    "CreativeDirection":   "#db2777",  # pink
    "CrewMember":          "#ea580c",  # orange
    "AudienceFeedback":    "#65a30d",  # lime
    "HumanFeedback":       "#0d9488",  # teal
    "CreativeDecision":    "#9333ea",  # purple
    "VisualMotif":         "#e11d48",  # rose
    "Script":              "#475569",  # slate
    "Screenplay":          "#334155",  # dark slate
    "Storyboard":          "#7c2d12",  # brown
    "PreProduction":       "#1d4ed8",  # strong blue
    "WildIdea":            "#f59e0b",  # gold
}
# Fallback colour for a node whose type isn't in the schema map.
DEFAULT_ENTITY_COLOR = "#64748b"  # slate grey


def _chip(text, bg: str, fg: str = "#fff") -> str:
    """Render a single rounded, coloured "chip" (pill) span for a label."""
    import html as _html
    return (
        f'<span style="display:inline-block;margin:3px 4px;padding:4px 10px;'
        f'border-radius:12px;background:{bg};color:{fg};font-size:12px;'
        f'font-weight:600;font-family:Segoe UI,Arial,sans-serif;">'
        f'{_html.escape(str(text))}</span>'
    )


def node_entity_type(node) -> str | None:
    """Best-effort resolution of a Graphiti node's custom entity type name.

    Graphiti's EntityNode stores its type in `.labels` (e.g.
    ["Entity", "Character"]); we return the first label that matches a type
    declared in schema.py, otherwise None."""
    labels = getattr(node, "labels", None) or []
    for lbl in labels:
        if lbl in ENTITY_COLORS:
            return lbl
    # Some versions expose the type differently — try a few fallbacks.
    for attr in ("label", "entity_type", "type"):
        val = getattr(node, attr, None)
        if val in ENTITY_COLORS:
            return val
    return None


def node_color(node) -> str:
    """Return the schema-driven colour for a node based on its entity type."""
    return ENTITY_COLORS.get(node_entity_type(node), DEFAULT_ENTITY_COLOR)


def _legend_html(types_present) -> str:
    """Build a small colour legend for the entity types present in the card."""
    if not types_present:
        return ""
    items = "".join(
        f'<span style="display:inline-flex;align-items:center;margin:2px 8px 2px 0;'
        f'font-size:11px;color:#475569;font-family:Segoe UI,Arial,sans-serif;">'
        f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
        f'background:{ENTITY_COLORS.get(t, DEFAULT_ENTITY_COLOR)};margin-right:5px;"></span>'
        f'{t}</span>'
        for t in types_present
    )
    return (
        '<div style="margin-top:6px;padding-top:6px;border-top:1px dashed #e2e8f0;">'
        f'{items}</div>'
    )


def episode_summary_html(name: str, result) -> str:
    """Build the beautified HTML summary of a Graphiti ingest `result`.

    `result` is the object returned by `graphiti.add_episode(...)`; it must
    expose `.nodes` (each with `.uuid`, `.name`, `.labels`) and `.edges` (each
    with `.name`, `.source_node_uuid`, `.target_node_uuid`). Node chips are
    coloured by their schema entity type (all Characters share one colour, all
    Locations another, …). Returns an HTML string (use
    `display_episode_summary` to render it directly in a notebook)."""
    import html as _html

    # Colour each node chip by its schema entity type.
    node_chips = "".join(_chip(n.name, node_color(n)) for n in result.nodes) or \
        '<span style="color:#888;">none</span>'
    edge_chips = "".join(_chip(e.name, "#7c3aed") for e in result.edges) or \
        '<span style="color:#888;">none</span>'

    uuid_to_color = {n.uuid: node_color(n) for n in result.nodes}
    uuid_to_name = {n.uuid: n.name for n in result.nodes}
    pattern_rows = ""
    for e in result.edges:
        # Resolve endpoint names: prefer this episode's nodes, then the
        # cumulative cross-episode registry (reused nodes like the shared
        # `Project AHAM` hub), and only fall back to a short UUID as a last resort.
        src = uuid_to_name.get(e.source_node_uuid) or \
            NODE_NAME_REGISTRY.get(e.source_node_uuid) or \
            f"({str(e.source_node_uuid)[:8]}…)"
        tgt = uuid_to_name.get(e.target_node_uuid) or \
            NODE_NAME_REGISTRY.get(e.target_node_uuid) or \
            f"({str(e.target_node_uuid)[:8]}…)"
        src_color = uuid_to_color.get(e.source_node_uuid, DEFAULT_ENTITY_COLOR)
        tgt_color = uuid_to_color.get(e.target_node_uuid, DEFAULT_ENTITY_COLOR)
        pattern_rows += (
            '<tr>'
            f'<td style="padding:4px 10px;">{_chip(src, src_color)}</td>'
            f'<td style="padding:4px 10px;text-align:center;">{_chip(e.name, "#7c3aed")}'
            '<span style="color:#7c3aed;font-weight:700;">&nbsp;&rarr;</span></td>'
            f'<td style="padding:4px 10px;">{_chip(tgt, tgt_color)}</td>'
            '</tr>'
        )
    patterns_html = (
        '<table style="border-collapse:collapse;margin-top:4px;">'
        '<thead><tr>'
        '<th style="text-align:left;padding:4px 10px;color:#64748b;font-size:11px;">SOURCE</th>'
        '<th style="text-align:center;padding:4px 10px;color:#64748b;font-size:11px;">RELATION</th>'
        '<th style="text-align:left;padding:4px 10px;color:#64748b;font-size:11px;">TARGET</th>'
        f'</tr></thead><tbody>{pattern_rows}</tbody></table>'
    ) if result.edges else '<span style="color:#888;">none</span>'

    # Legend for the entity types actually present in this episode.
    types_present = []
    for n in result.nodes:
        t = node_entity_type(n)
        if t and t not in types_present:
            types_present.append(t)
    legend_html = _legend_html(types_present)

    return (
        '<div style="border:1px solid #e2e8f0;border-radius:10px;padding:14px 18px;'
        'margin:6px 0;font-family:Segoe UI,Arial,sans-serif;'
        'box-shadow:0 1px 4px rgba(0,0,0,0.06);">'
        f'<div style="font-size:15px;font-weight:700;color:#0f172a;margin-bottom:8px;">'
        f'&#10003; Ingested &nbsp;<span style="color:#2563eb;">{_html.escape(name)}</span></div>'
        f'<div style="margin-bottom:8px;"><span style="color:#64748b;font-size:12px;'
        f'font-weight:700;text-transform:uppercase;">Nodes ({len(result.nodes)})</span><br>{node_chips}</div>'
        f'<div style="margin-bottom:8px;"><span style="color:#64748b;font-size:12px;'
        f'font-weight:700;text-transform:uppercase;">Edges ({len(result.edges)})</span><br>{edge_chips}</div>'
        f'<div><span style="color:#64748b;font-size:12px;font-weight:700;'
        f'text-transform:uppercase;">Patterns</span><br>{patterns_html}</div>'
        f'{legend_html}'
        '</div>'
    )


def display_episode_summary(name: str, result) -> None:
    """Render the beautified episode summary directly in a notebook cell."""
    from IPython.display import display, HTML
    register_episode(name, result)
    display(HTML(episode_summary_html(name, result)))


# =========================================================================
# Episode registry — map episode UUID -> human episode name so answers can
# CITE which episode a fact came from (e.g. "MON E1 – Original Pitch").
# =========================================================================
EPISODE_REGISTRY: dict[str, str] = {}

# Persistent node UUID -> name registry accumulated across ALL episodes. A new
# episode's `result.nodes` only lists the nodes created/updated in THAT episode,
# so edges that reference a REUSED node from an earlier episode (e.g. the shared
# `Project AHAM` hub) would otherwise fall back to showing a raw UUID. Keeping a
# cumulative map lets us resolve those names too.
NODE_NAME_REGISTRY: dict[str, str] = {}


def register_episode(name: str, result) -> None:
    """Record the episode UUID -> name mapping for an ingested episode so that
    later retrieval can cite the source episode by name. Also accumulate every
    node's UUID -> name so reused nodes render with a name (not a raw UUID)."""
    ep = getattr(result, "episode", None)
    uuid = getattr(ep, "uuid", None)
    if uuid:
        EPISODE_REGISTRY[uuid] = name
    for n in getattr(result, "nodes", None) or []:
        n_uuid = getattr(n, "uuid", None)
        n_name = getattr(n, "name", None)
        if n_uuid and n_name:
            NODE_NAME_REGISTRY[n_uuid] = n_name


def episode_names_for(r) -> list[str]:
    """Return the human episode name(s) a retrieved fact/edge originated from.

    Graphiti edge results expose an `.episodes` list of episode UUIDs; we map
    those back to the names captured in EPISODE_REGISTRY at ingest time. Falls
    back to a short UUID if the name isn't known."""
    uuids = getattr(r, "episodes", None) or []
    names = []
    for u in uuids:
        nm = EPISODE_REGISTRY.get(u)
        if nm and nm not in names:
            names.append(nm)
        elif not nm:
            short = f"episode {str(u)[:8]}"
            if short not in names:
                names.append(short)
    return names


# =========================================================================
# HTML helpers — beautified Q / A / supporting-facts answer card
# =========================================================================
def _supporting_fact_html(r) -> str:
    """Render one retrieved Graphiti fact as a row, colour-coded by whether it
    is still CURRENT or has been INVALIDATED/superseded, and citing the source
    episode name(s) the fact came from."""
    import html as _html
    fact = _html.escape(str(getattr(r, "fact", r)))
    valid = _fmt_ts(getattr(r, "valid_at", None))
    invalid_at = getattr(r, "invalid_at", None)
    if invalid_at is None:
        badge_bg, badge_fg, badge = "#dcfce7", "#166534", "CURRENT"
        window = f"valid from {valid}"
        border = "#22c55e"
    else:
        badge_bg, badge_fg, badge = "#fee2e2", "#991b1b", "SUPERSEDED"
        window = f"valid {valid} &rarr; {_fmt_ts(invalid_at)}"
        border = "#ef4444"
    # Source episode citation chip(s).
    ep_names = episode_names_for(r)
    if ep_names:
        cite = "".join(
            f'<span style="display:inline-block;font-size:10px;font-weight:600;'
            f'padding:1px 7px;margin:2px 4px 0 0;border-radius:8px;'
            f'background:#eef2ff;color:#4338ca;">&#128218; {_html.escape(n)}</span>'
            for n in ep_names
        )
    else:
        cite = ""
    return (
        f'<div style="display:flex;align-items:flex-start;gap:8px;padding:7px 10px;'
        f'margin:4px 0;border-left:3px solid {border};background:#f8fafc;'
        f'border-radius:6px;">'
        f'<span style="flex:0 0 auto;font-size:10px;font-weight:700;padding:2px 7px;'
        f'border-radius:8px;background:{badge_bg};color:{badge_fg};'
        f'text-transform:uppercase;letter-spacing:.3px;margin-top:1px;">{badge}</span>'
        f'<span style="flex:1;font-size:13px;color:#0f172a;line-height:1.4;">{fact}'
        f'<span style="display:block;font-size:11px;color:#94a3b8;margin-top:2px;">'
        f'{window}</span>{cite}</span>'
        f'</div>'
    )


def _highlight_episode_names(html: str) -> str:
    """Wrap any known episode name appearing in the answer HTML in a highlighted
    'chip' so the source episode citations stand out visually.

    Uses the names captured in EPISODE_REGISTRY at ingest time. Longer names are
    replaced first so a name that is a substring of another isn't broken."""
    import re as _re
    names = sorted(set(EPISODE_REGISTRY.values()), key=len, reverse=True)
    for name in names:
        if not name:
            continue
        chip = (
            '<span style="display:inline-block;font-size:11px;font-weight:700;'
            'padding:1px 8px;border-radius:8px;background:#eef2ff;color:#4338ca;'
            'border:1px solid #c7d2fe;white-space:nowrap;">'
            f'&#128218; {name}</span>'
        )
        # Replace both **bold** and plain occurrences; avoid double-wrapping
        # something already inside our chip by matching the raw name/bolded name.
        for pat in (f"<strong>{_re.escape(name)}</strong>", _re.escape(name)):
            html = _re.sub(pat, chip, html)
    return html


def _markdown_to_html(text: str) -> str:
    """Convert an LLM markdown answer to HTML for inline display.

    Uses the `markdown` package if installed; otherwise falls back to a small
    regex converter handling **bold**, *italic*, `code`, bullet lists and
    line breaks so no raw ** / * markers leak into the rendered card."""
    text = text or ""
    try:
        import markdown as _md  # type: ignore
        html = _md.markdown(text, extensions=["extra", "sane_lists"])
    except Exception:
        import html as _html
        import re as _re
        esc = _html.escape(text)
        esc = _re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", esc)
        esc = _re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", esc)
        esc = _re.sub(r"`(.+?)`", r"<code>\1</code>", esc)
        # Turn "- " / "* " bullet lines into <li> items grouped in a <ul>.
        lines, out, in_list = esc.split("\n"), [], False
        for ln in lines:
            m = _re.match(r"\s*[-*]\s+(.*)", ln)
            if m:
                if not in_list:
                    out.append("<ul style='margin:6px 0;padding-left:22px;'>")
                    in_list = True
                out.append(f"<li style='margin:3px 0;'>{m.group(1)}</li>")
            else:
                if in_list:
                    out.append("</ul>")
                    in_list = False
                if ln.strip():
                    out.append(f"<p style='margin:6px 0;'>{ln}</p>")
        if in_list:
            out.append("</ul>")
        html = "\n".join(out)
    # Highlight any known episode names so citations stand out.
    return _highlight_episode_names(html)


def answer_html(question: str, answer_text: str, facts=None) -> str:
    """Build a beautified card with THREE blocks: the QUESTION, the clone's
    ANSWER, and the SUPPORTING FACTS retrieved from Graphiti.

    `facts` is the list of retrieved edge results (each with `.fact`,
    `.valid_at`, `.invalid_at`). Pass None/empty to omit the facts block."""
    import html as _html

    facts = list(facts or [])
    if facts:
        # Current facts first, superseded ones after — matches the answer logic.
        current = [r for r in facts if getattr(r, "invalid_at", None) is None]
        invalid = [r for r in facts if getattr(r, "invalid_at", None) is not None]
        rows = "".join(_supporting_fact_html(r) for r in current + invalid)
        facts_block = (
            f'<div style="padding:12px 18px;">'
            f'<div style="font-size:12px;font-weight:700;color:#64748b;'
            f'text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">'
            f'&#128269; Supporting facts from Graphiti ({len(facts)})</div>'
            f'{rows}</div>'
        )
    else:
        facts_block = (
            '<div style="padding:12px 18px;color:#94a3b8;font-size:13px;">'
            'No supporting facts retrieved.</div>'
        )

    # Render the answer text as MARKDOWN so **bold**, lists, etc. display
    # properly instead of showing raw ** characters.
    answer_body = _markdown_to_html(str(answer_text))

    return (
        '<div style="font-family:Segoe UI,Arial,sans-serif;border:1px solid #e2e8f0;'
        'border-radius:14px;overflow:hidden;margin:10px 0;'
        'box-shadow:0 4px 16px rgba(0,0,0,0.08);">'
        # --- Block 1: QUESTION ---
        '<div style="background:linear-gradient(135deg,#6366f1,#8b5cf6);'
        'padding:14px 18px;color:#fff;">'
        '<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        'letter-spacing:.5px;opacity:.85;">&#10067; Question</div>'
        f'<div style="font-size:15px;font-weight:700;margin-top:3px;">'
        f'{_html.escape(str(question))}</div>'
        '</div>'
        # --- Block 2: ANSWER ---
        '<div style="padding:14px 18px;background:#ffffff;border-bottom:1px solid #f1f5f9;">'
        '<div style="font-size:11px;font-weight:700;text-transform:uppercase;'
        'letter-spacing:.5px;color:#7c3aed;margin-bottom:4px;">'
        '&#127909; Digital Clone Answer</div>'
        f'<div style="font-size:14px;color:#0f172a;line-height:1.65;">{answer_body}</div>'
        '</div>'
        # --- Block 3: SUPPORTING FACTS ---
        f'{facts_block}'
        '</div>'
    )


def display_answer(question: str, answer_text: str, facts=None) -> None:
    """Render the three-block (Question / Answer / Supporting facts) card in a
    notebook cell."""
    from IPython.display import display, HTML
    display(HTML(answer_html(question, answer_text, facts)))
def _fmt_ts(ts):
    """Human-readable timestamp for the LLM, or 'unknown' if missing."""
    if ts is None:
        return "unknown"
    try:
        return ts.strftime("%Y-%m-%d %H:%M")
    except AttributeError:
        return str(ts)


def _fact_with_time(r):
    """Render a fact together with its temporal validity window AND the source
    episode name(s) so the LLM can reason about WHEN a fact was true, WHEN it
    got superseded, and CITE which episode it came from."""
    valid = _fmt_ts(getattr(r, "valid_at", None))
    invalid = getattr(r, "invalid_at", None)
    ep_names = episode_names_for(r)
    source = f" (source episode: {', '.join(ep_names)})" if ep_names else ""
    if invalid is None:
        return f"- {r.fact} [valid from {valid}; still current]{source}"
    return f"- {r.fact} [valid from {valid} until {_fmt_ts(invalid)}; superseded]{source}"

# Cache for the Project AHAM focal node \u2014 set once, reused for reranking so
# project-centric facts (like the setting) reliably surface in retrieval.
_project_center_uuid = None

async def get_project_center(group_id: str) -> str | None:
    """Resolve (and cache) the Project AHAM node uuid to use as a focal/center
    node for reranked search, improving recall of project-centric facts."""
    global _project_center_uuid
    if _project_center_uuid:
        return _project_center_uuid
    try:
        cfg = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        cfg.limit = 5
        res = await graphiti.search_(
            query="Project AHAM film", config=cfg, group_ids=[group_id])
        nodes = getattr(res, "nodes", []) or []
        for n in nodes:
            if "AHAM" in (n.name or "").upper():
                _project_center_uuid = n.uuid
                break
        if _project_center_uuid is None and nodes:
            _project_center_uuid = nodes[0].uuid
    except Exception as e:
        print(f"(focal-node lookup skipped: {e})")
        _project_center_uuid = None
    return _project_center_uuid

def _first_sentence(text):
    """Collapse a docstring to one clean sentence for a compact instruction."""
    if not text:
        return ""
    s = " ".join(text.split())          # flatten whitespace/newlines
    # Split on the first real sentence break, but not on abbreviations like
    # 'e.g.' / 'i.e.' / 'etc.' which also contain '. '.
    protected = s.replace("e.g.", "e\u2024g\u2024").replace("i.e.", "i\u2024e\u2024").replace("etc.", "etc\u2024")
    for end in (". ", "; "):
        if end in protected:
            protected = protected.split(end)[0]
            break
    return protected.replace("\u2024", ".").rstrip(".")

def build_extraction_instructions(edge_types, edge_type_map):
    # Map each edge name -> list of "Source -> Target" pairs it is allowed on
    # (skipping the ("*","*") permissive fallback so we only show real pairs).
    pairs_for_edge = {}
    for (src, tgt), names in edge_type_map.items():
        if src == "*" or tgt == "*":
            continue
        for name in names:
            pairs_for_edge.setdefault(name, []).append(f"{src} -> {tgt}")

    lines = []
    for name, model in edge_types.items():
        desc = _first_sentence(inspect.getdoc(model))
        pairs = pairs_for_edge.get(name)
        where = f" [{', '.join(sorted(set(pairs)))}]" if pairs else ""
        lines.append(f"- {name}{where}: {desc}.")

    header = (
        "You are extracting facts for a film director's creative knowledge graph.\n"
        "Map each statement onto the MOST SPECIFIC edge type below. When a later\n"
        "statement reverses an earlier one, reuse the SAME edge type and the SAME\n"
        "nodes so the new fact supersedes (invalidates) the old one.\n\n"
        "Available relationships (name [allowed Source -> Target pairs]: meaning):"
    )
    footer = (
        "\nRules: prefer a specific edge over a generic one; model a character's\n"
        "fate as a Character -> Character edge, never as a Scene; extract only what\n"
        "the text states and reuse existing nodes for the same real-world thing.\n"
        "- SETTING/ERA: For a place a project is SET_IN, the Location NODE must be\n"
        "  the bare place name only (e.g. 'Chennai'). NEVER bake the time period\n"
        "  into the node name (do NOT create 'Chennai 2045' or 'present-day\n"
        "  Chennai'). Put the time period on the SET_IN edge's `era` attribute\n"
        "  instead (era='2045', era='present-day').\n"
        "- When the setting's era changes but the place is the same, REUSE the\n"
        "  existing Location node and emit a new SET_IN edge with the new `era` so\n"
        "  it supersedes (invalidates) the earlier SET_IN, rather than creating a\n"
        "  second Location node."
    )
    return header + "\n" + "\n".join(lines) + "\n" + footer

EXTRACTION_INSTRUCTIONS = build_extraction_instructions(edge_types, edge_type_map)

ANSWER_PROMPT = """You are the director's digital clone. Answer the question using ONLY the "
        "facts below. Each fact is numbered like [3] and carries a temporal window "
        "in square brackets: 'valid from' is when the idea became true, and 'until' "
        "is when it was superseded/expired. Treat a fact as abandoned ONLY if it "
        "appears under 'ABANDONED (invalidated) FACTS'. Never call a CURRENT fact "
        "abandoned, and never invent facts. When the question asks how something "
        "evolved or changed over time (e.g. how the location of Project AHAM "
        "evolved), walk through the relevant facts in chronological order using "
        "their validity windows and explicitly mention the dates/times a fact "
        "became valid and when it expired.\n\n"
        "Each fact also names its SOURCE EPISODE in parentheses (e.g. 'source "
        "episode: MON E1 – Original Pitch'). When you use a fact, CITE its source "
        "episode name so the director can see which episode it came from, but do "
        "NOT repeat the same episode name over and over — cite an episode the "
        "FIRST time you use a fact from it, and only mention it again when you "
        "switch to a DIFFERENT episode. Wrap every episode name in double "
        "asterisks so it renders bold, e.g. **MON E1 – Original Pitch**.\n\n"
        "FORMAT THE ANSWER FOR READABILITY using Markdown: use short paragraphs, "
        "'-' bullet points for lists of facts, and **bold** for key terms. Do NOT "
        "return one long run-on paragraph.\n\n"
        "Respond in EXACTLY this format:\n"
        "ANSWER: <your full markdown answer here>\n"
        "USED_FACTS: <comma-separated list of the fact numbers you actually relied "
        "on, e.g. 1, 4, 7>\n\n"""