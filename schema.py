from pydantic import BaseModel, Field

# ---------------- Custom ENTITY types ----------------
class Director(BaseModel):
    """The film's director: the primary human-in-the-loop decision maker who
    drives the creative vision, approves or rejects artifacts at each review
    gate, and whose evolving preferences the living graph must remember across
    sessions. This is the persona the agent is collaborating with."""
    creative_signature: str | None = Field(None, description="The director's recurring stylistic tendencies and authorial fingerprint, e.g. 'non-linear storytelling, natural light, morally grey protagonists'")
    preferred_genres: str | None = Field(None, description="Genres the director gravitates toward, e.g. 'neo-noir, psychological thriller'")

class FilmProject(BaseModel):
    """A single movie being developed through the pre-production pipeline. This
    is the central hub entity that scripts, screenplays, storyboards, scenes,
    characters, locations, themes and constraints all attach to."""
    logline: str | None = Field(None, description="A single compelling sentence summarising the film's premise, protagonist and central conflict")
    title: str | None = Field(None, description="The working or final title of the film, e.g. 'AHAM'")
    genre: str | None = Field(None, description="The primary genre(s) of the project, e.g. 'sci-fi thriller'")
    status: str | None = Field(None, description="The project's current lifecycle stage, e.g. 'development', 'pre-production', 'greenlit'")

class Character(BaseModel):
    """A fictional person appearing in the film, with a defined narrative
    function and arc. Characters are referenced by scripts, screenplays and
    storyboards and can be recast or rewritten as the story evolves."""
    role: str | None = Field(None, description="The character's narrative function, e.g. 'protagonist', 'antagonist', 'mentor', 'love interest'")
    description: str | None = Field(None, description="A short profile of the character's personality, motivation and arc")
    archetype: str | None = Field(None, description="The character archetype, e.g. 'reluctant hero', 'femme fatale', 'trickster'")

class Scene(BaseModel):
    """A discrete dramatic unit of the film occurring in a continuous time and
    place — the building block of the screenplay and the unit that storyboards
    visualise. Scenes carry endings, motifs and staging."""
    synopsis: str | None = Field(None, description="A brief description of what happens in the scene")
    setting: str | None = Field(None, description="Where and when the scene takes place, e.g. 'INT. RAIN-SOAKED WAREHOUSE - NIGHT'")
    sequence_position: str | None = Field(None, description="Where the scene falls in the narrative, e.g. 'opening', 'midpoint', 'climax', 'resolution'")

class Location(BaseModel):
    """A physical, virtual or fictional place where scenes are set or shot.
    Locations carry a time period/era (see the SET_IN edge) so the graph can
    detect when a project's setting is changed or contradicted over time."""
    location_type: str | None = Field(None, description="The kind of place, e.g. 'urban city', 'remote village', 'spaceship interior'")
    real_or_fictional: str | None = Field(None, description="Whether the location is real, fictional, or a real place standing in for another")

class Theme(BaseModel):
    """A central idea, message or emotional throughline the film explores, e.g.
    'memory and identity', 'redemption', 'surveillance vs. freedom'. Themes
    guide creative decisions and connect to genre preferences."""
    description: str | None = Field(None, description="An elaboration of the thematic idea and how the film engages with it")

class Genre(BaseModel):
    """The film's format / marketing category (e.g. 'cyberpunk action
    thriller', 'emotional techno-thriller', 'neo-noir'). Deliberately distinct
    from Theme: a Genre is the *category/format* of the film, while a Theme is
    the emotional/idea throughline (grief, memory, letting go). Keeping them
    separate lets the graph track a genre pivot (cyberpunk -> techno-thriller)
    as a temporal contradiction independently of thematic evolution."""
    descriptor: str | None = Field(None, description="The genre label exactly as stated, e.g. 'cyberpunk action thriller', 'grounded emotional techno-thriller'")
    tone: str | None = Field(None, description="The tonal register, e.g. 'dark', 'grounded', 'stylised'")

class CreativeConstraint(BaseModel):
    """A real-world production limit that bounds creative choices, such as a
    budget ceiling, a shooting schedule, a certification/rating requirement, or
    a technical/logistical restriction that the story must be shaped around."""
    constraint_type: str | None = Field(None, description="The category of constraint, e.g. 'budget', 'schedule', 'rating/censorship', 'technical', 'location access'")
    detail: str | None = Field(None, description="The specific limit, e.g. 'budget capped at 5 crore', 'must wrap shoot in 40 days', 'must be U/A certified'")

class ReferenceFilm(BaseModel):
    """An existing, inspirational film surfaced as a creative touchstone or
    comparison for tone, visual style, structure or genre — used to align the
    director and agent on a shared reference point."""
    title: str | None = Field(None, description="The title of the reference film, e.g. 'Blade Runner 2049'")
    reason: str | None = Field(None, description="Why it is referenced — what aspect it exemplifies, e.g. 'for its neon-noir cinematography and slow-burn pacing'")

class CreativeDirection(BaseModel):
    """A proposed or approved overarching creative/visual approach for the film
    — the aesthetic and tonal 'north star' (e.g. 'gritty hand-held realism',
    'stylised neon-noir') that downstream artifacts should conform to."""
    style: str | None = Field(None, description="The visual/tonal style being proposed or approved, e.g. 'stylised neon-noir with high-contrast lighting'")
    status: str | None = Field(None, description="Whether the direction is 'proposed', 'approved', or 'rejected'")

class CrewMember(BaseModel):
    """A member of the production team collaborating on the film other than the
    director, such as a producer, cinematographer, writer, editor or production
    designer, who may request changes, approve or reject artifacts."""
    role: str | None = Field(None, description="The crew member's job title, e.g. 'producer', 'cinematographer', 'screenwriter', 'editor'")
    member_name: str | None = Field(None, description="The crew member's name if stated")

class AudienceFeedback(BaseModel):
    """Reactions collected from a test screening, focus group or audience panel
    on a scene, storyboard or cut — an external signal (distinct from the
    director's own notes) that can drive creative revisions."""
    reaction: str | None = Field(None, description="A summary of the audience reaction, e.g. 'panel found the second act too slow but loved the twist ending'")
    sentiment: str | None = Field(None, description="Overall reception: 'positive', 'negative', or 'mixed'")
    source: str | None = Field(None, description="Who gave the feedback, e.g. 'test screening panel', 'focus group', 'preview audience'")

class HumanFeedback(BaseModel):
    """A director/stakeholder note given at a human-in-the-loop review gate — a
    concrete revision request (e.g. 'add a rain sequence to the climax' or
    'shorten the dialogue in scene 4') that the agent must act on and remember.
    This is the primary mechanism through which the living graph learns the
    director's evolving intent."""
    request: str | None = Field(None, description="The specific change or note the director asked for, e.g. 'add a rain sequence to the climax'")
    stage: str | None = Field(None, description="The pipeline stage the feedback was given at, e.g. 'script', 'screenplay', 'storyboard', 'movie_retrieval'")
    sentiment: str | None = Field(None, description="The tone of the feedback: 'positive', 'negative', or 'neutral'")
    priority: str | None = Field(None, description="How urgent/mandatory the change is, e.g. 'must-have', 'nice-to-have'")

class CreativeDecision(BaseModel):
    """A concrete, recorded decision the director approved at a given stage —
    the durable outcome of a review gate (e.g. 'approved noir thriller
    direction'). Decisions can be superseded by later decisions via REPLACES,
    letting the graph track how the creative vision changed over time."""
    decision: str | None = Field(None, description="What was decided/approved, e.g. 'approved noir thriller direction'")
    stage: str | None = Field(None, description="The pipeline stage at which the decision was made, e.g. 'creative direction', 'casting'")
    rationale: str | None = Field(None, description="The reasoning behind the decision, if given")

class VisualMotif(BaseModel):
    """A recurring visual, symbolic or sensory element that threads through the
    film to reinforce theme or mood (e.g. 'falling rain', 'the colour red',
    'mirrors and reflections'). Motifs surface in screenplays, storyboards and
    scenes."""
    motif: str | None = Field(None, description="The recurring element itself, e.g. 'falling rain', 'reflections in glass'")
    meaning: str | None = Field(None, description="What the motif symbolises or evokes, e.g. 'emotional catharsis', 'fractured identity'")

class Script(BaseModel):
    """The written narrative of the film containing scene descriptions, action
    lines and dialogue — the first textual artifact in the pipeline, which is
    later adapted into a formatted screenplay."""
    draft_version: str | None = Field(None, description="The draft/version label, e.g. 'first draft', 'v2', 'polish pass'")
    logline: str | None = Field(None, description="One-line summary of the script's story")
    synopsis: str | None = Field(None, description="A short synopsis of the script's plot and structure")

class Screenplay(BaseModel):
    """The industry-formatted version of the script, structured into scenes,
    sluglines, action and dialogue in standard screenplay format — the
    production-ready document that storyboards are derived from."""
    format: str | None = Field(None, description="Screenplay format/standard, e.g. 'Hollywood standard', 'stage play'")
    act_structure: str | None = Field(None, description="Narrative structure, e.g. 'three-act', 'five-act', 'non-linear'")
    page_count: int | None = Field(None, description="Approximate page count (roughly one page per minute of screen time)")

class Storyboard(BaseModel):
    """A visual pre-visualisation of the film: an ordered sequence of panels or
    frames depicting shots, camera angles, blocking and staging for scenes —
    the bridge between the written screenplay and the planned shoot."""
    shot_count: int | None = Field(None, description="Number of panels/shots in the storyboard")
    style: str | None = Field(None, description="Visual style of the boards, e.g. 'rough sketch', 'colour', 'animatic'")
    scene_coverage: str | None = Field(None, description="Which scenes/sequences the storyboard covers, e.g. 'opening chase and climax'")

class PreProduction(BaseModel):
    """The overarching pre-production phase artifact that tracks all planning
    work before principal photography — casting, scheduling, budgeting,
    location scouting and department readiness — and reflects the project's
    readiness to begin shooting."""
    status: str | None = Field(None, description="Current phase status, e.g. 'in progress', 'complete', 'blocked'")
    milestone: str | None = Field(None, description="Key pre-production milestone reached, e.g. 'casting locked', 'schedule approved', 'budget signed off'")
    readiness: str | None = Field(None, description="Overall readiness to begin the shoot, e.g. '70% ready', 'awaiting location permits'")

class WildIdea(BaseModel):
    """A bold, unconventional or 'blue-sky' creative idea floated during
    brainstorming — a speculative what-if (e.g. 'shoot the whole film in one
    continuous take', 'tell the story backwards') that may be embraced, parked
    or rejected later. Captured so the living graph can preserve the director's
    experimental instincts even when an idea isn't immediately adopted."""
    idea: str | None = Field(None, description="The wild idea itself, e.g. 'set the climax underwater', 'no dialogue for the first 20 minutes'")
    origin: str | None = Field(None, description="Who proposed it and in what context, e.g. 'director during a late-night brainstorm'")
    status: str | None = Field(None, description="What became of the idea, e.g. 'proposed', 'parked', 'adopted', 'rejected'")
    feasibility: str | None = Field(None, description="A rough sense of how practical the idea is, e.g. 'high-risk', 'budget-permitting', 'easily achievable'")

entity_types = {
    "Director": Director,
    "FilmProject": FilmProject,
    "Character": Character,
    "Scene": Scene,
    "Location": Location,
    "Theme": Theme,
    "Genre": Genre,   
    "CreativeConstraint": CreativeConstraint,
    "ReferenceFilm": ReferenceFilm,
    "CreativeDirection": CreativeDirection,
    "CrewMember": CrewMember,
    "AudienceFeedback": AudienceFeedback,
    "HumanFeedback": HumanFeedback,
    "CreativeDecision": CreativeDecision,
    "VisualMotif": VisualMotif,
    "Script": Script,
    "Screenplay": Screenplay,
    "Storyboard": Storyboard,
    "PreProduction": PreProduction,
    "WildIdea": WildIdea,
}

# ---------------- Custom EDGE (relationship) types ----------------
class DIRECTS(BaseModel):
    """Connects a Director to the FilmProject they are helming — the root
    authorship relationship for the project."""

class PREFERS_GENRE(BaseModel):
    """Connects a FilmProject (or Director) to the Genre it adopts (e.g.
    'cyberpunk action thriller' -> 'emotional techno-thriller'). As a temporal
    edge, a new genre invalidates the earlier one when the director pivots the
    film's category."""

class EXPLORES_THEME(BaseModel):
    """Connects a FilmProject to a Theme it explores (e.g. 'grief', 'memory',
    'letting go'). Deliberately distinct from PREFERS_GENRE: genre is the
    marketing/format category (e.g. 'techno-thriller') while a theme is the
    emotional/idea throughline. Keeping them separate lets the graph track
    thematic evolution independently of genre pivots."""

class HAS_VISUAL_STYLE(BaseModel):
    """Connects a FilmProject to the CreativeDirection / visual style it adopts
    (e.g. 'neon rain', 'intimate humid realism'). As a temporal edge, a new
    style can invalidate an earlier one when the director pivots the look."""

class SET_IN(BaseModel):
    """A project is set in a location during a specific time period/era.

    The `era` field captures the *time period* of the setting (e.g. "2045",
    "present-day", "1990s"). This is crucial: entity resolution collapses
    "Chennai 2045" and "present-day Chennai" into a single `Chennai` location
    node, so without `era` the two settings look structurally identical and
    Graphiti cannot detect that the new setting CONTRADICTS (and should
    invalidate) the old one. Making `era` an explicit attribute lets the
    temporal-contradiction logic invalidate the outdated setting.
    """
    era: str | None = Field(
        default=None,
        description="The time period / era of the setting, e.g. '2045', "
                    "'present-day', '1990s'. Extract exactly as stated.",
    )

class HAS_PROTAGONIST(BaseModel):
    """Connects a FilmProject to the Character who serves as its central
    protagonist / point-of-view lead."""

class HAS_ENDING(BaseModel):
    """Connects a FilmProject to the Scene that constitutes its ending,
    capturing how the story resolves (which may change over revisions)."""
    ending_type: str | None = Field(None, description="The nature of the ending, e.g. 'tragic', 'hopeful', 'twist', 'open-ended'")

class INSPIRED_BY(BaseModel):
    """Connects a FilmProject to a ReferenceFilm that inspires its tone, style
    or structure."""

class APPROVES(BaseModel):
    """The director/crew formally approves an artifact or decision at a review
    gate, marking it as accepted and ready to proceed downstream."""

class REJECTS(BaseModel):
    """A director rejects an artifact or asks to change it — a revision
    request (e.g. 'add a rain sequence', 'make the ending darker')."""
    reason: str | None = Field(None, description="What the director wanted changed and why, e.g. 'wanted a rain sequence added to the climax'")

class PREFERS(BaseModel):
    """A director prefers a particular style, theme, tone or creative approach
    — a soft, standing preference (distinct from a one-off APPROVES decision)
    that the living graph should carry forward across sessions."""
    preference: str | None = Field(None, description="The style, theme or approach the director favours, e.g. 'suspense thriller elements', 'emotional songs'")

class CONSTRAINED_BY(BaseModel):
    """Connects a FilmProject to a CreativeConstraint (budget, schedule, rating
    etc.) that bounds its creative and logistical choices."""

class REPLACES(BaseModel):
    """Marks that a newer fact/decision/artifact supersedes an older one,
    driving the temporal invalidation of the outdated version so the graph
    reflects the current creative truth."""

class REQUESTS(BaseModel):
    """A stakeholder (director or crew member) requests a specific change or
    deliverable — the trigger that a downstream decision RESPONDS_TO."""

class RESPONDS_TO(BaseModel):
    """Links a CreativeDecision (or revised artifact) back to the feedback,
    request or audience reaction that prompted it, preserving the cause→effect
    chain of the creative process."""

class PRESERVES(BaseModel):
    """Indicates that a character, decision or artifact intentionally retains a
    prior trait, element or continuity point across a revision."""

class DESTROYS(BaseModel):
    """A character destroys / eliminates another entity in the story (e.g. the
    protagonist destroys the AI in the ending). Modelled explicitly so that a
    later PRESERVES fact can temporally CONTRADICT and invalidate it — the core
    'Maya destroys Aham' → 'Maya preserves Aham' pivot of the demo."""

# --- Pre-production pipeline edges (Script -> Screenplay -> Storyboard -> PreProduction) ---
class HAS_SCRIPT(BaseModel):
    """Connects a FilmProject to its written Script — the first textual
    artifact in the pre-production pipeline."""

class ADAPTED_INTO(BaseModel):
    """A Script is adapted/formatted into a Screenplay (also used to link a
    FilmProject to its Screenplay), advancing the pipeline one stage."""

class STORYBOARDED_AS(BaseModel):
    """A Screenplay (or an individual Scene) is visualised as a Storyboard,
    bridging the written and visual stages of pre-production."""

class HAS_STORYBOARD(BaseModel):
    """Connects a FilmProject to its Storyboard artifact."""

class IN_PREPRODUCTION(BaseModel):
    """Connects a FilmProject (or a completed Storyboard) to the PreProduction
    phase it has entered, signalling planning is underway."""

class DEPICTS_SCENE(BaseModel):
    """A Storyboard depicts a particular Scene, mapping visual panels to the
    dramatic units they cover."""

class FEATURES_MOTIF(BaseModel):
    """A Screenplay, Storyboard or Scene features a recurring VisualMotif,
    reinforcing theme and mood."""

class FEATURES_CHARACTER(BaseModel):
    """A Scene, Script or Screenplay features a particular Character, recording
    where in the narrative a character appears."""

class PROPOSES_DIRECTION(BaseModel):
    """A Director or CrewMember proposes a CreativeDirection (overall visual/
    tonal approach) for consideration at a review gate."""

class GIVES_FEEDBACK(BaseModel):
    """A Director or CrewMember gives HumanFeedback at a human-in-the-loop
    review gate, the primary channel for steering the agent."""

class REVISES(BaseModel):
    """A piece of HumanFeedback revises a Script, Screenplay or Storyboard,
    linking the note to the artifact it changes."""

class RECEIVES_FEEDBACK(BaseModel):
    """An artifact (Scene, Storyboard, Screenplay) receives AudienceFeedback
    from a screening/panel, capturing external reception."""

# --- Wild-idea / brainstorming edges ---
class FLOATS_IDEA(BaseModel):
    """A Director or CrewMember floats a WildIdea during brainstorming — the
    origin link that captures who proposed a speculative what-if."""

class INSPIRES(BaseModel):
    """A WildIdea inspires a FilmProject, CreativeDirection or Scene, recording
    that an experimental idea seeded a concrete creative element."""

class EVOLVES_INTO(BaseModel):
    """A WildIdea evolves into a CreativeDecision (or CreativeDirection) once it
    is embraced, tracing how an experimental spark became an approved choice."""

edge_types = {
    "DIRECTS": DIRECTS, "PREFERS_GENRE": PREFERS_GENRE, "SET_IN": SET_IN,
    "HAS_PROTAGONIST": HAS_PROTAGONIST, "HAS_ENDING": HAS_ENDING,
    "INSPIRED_BY": INSPIRED_BY, "REJECTS": REJECTS, "APPROVES": APPROVES,
    "PREFERS": PREFERS,
    "CONSTRAINED_BY": CONSTRAINED_BY, "REPLACES": REPLACES,
    "REQUESTS": REQUESTS, "RESPONDS_TO": RESPONDS_TO, "PRESERVES": PRESERVES,
    "EXPLORES_THEME": EXPLORES_THEME, "HAS_VISUAL_STYLE": HAS_VISUAL_STYLE,
    "DESTROYS": DESTROYS,
    # Pre-production pipeline + creative-review edges
    "HAS_SCRIPT": HAS_SCRIPT, "ADAPTED_INTO": ADAPTED_INTO,
    "STORYBOARDED_AS": STORYBOARDED_AS, "HAS_STORYBOARD": HAS_STORYBOARD,
    "IN_PREPRODUCTION": IN_PREPRODUCTION, "DEPICTS_SCENE": DEPICTS_SCENE,
    "FEATURES_MOTIF": FEATURES_MOTIF, "FEATURES_CHARACTER": FEATURES_CHARACTER,
    "PROPOSES_DIRECTION": PROPOSES_DIRECTION,
    "GIVES_FEEDBACK": GIVES_FEEDBACK, "REVISES": REVISES,
    "RECEIVES_FEEDBACK": RECEIVES_FEEDBACK,
    # Wild-idea / brainstorming edges
    "FLOATS_IDEA": FLOATS_IDEA, "INSPIRES": INSPIRES, "EVOLVES_INTO": EVOLVES_INTO,
}

# Constrain which edges are allowed between which entity pairs.
# This is important: it stops Graphiti from treating an unrelated edge (e.g. DIRECTS)
# as a "replacement candidate" for a contradicting one (e.g. SET_IN), which was causing
# 'Director Arun directs Project AHAM' to be wrongly invalidated on Day 2.
# A permissive fallback (("*","*")) still lets novel/emergent relations appear.
edge_type_map = {
    ("Director", "FilmProject"): ["DIRECTS", "REJECTS", "APPROVES", "REQUESTS"],
    ("Director", "Theme"): ["PREFERS"],
     ("Director", "Genre"): ["PREFERS_GENRE"],
    ("Director", "CreativeDirection"): ["PROPOSES_DIRECTION", "APPROVES", "REJECTS", "PREFERS"],
    ("FilmProject", "Genre"): ["PREFERS_GENRE"],
    ("FilmProject", "Theme"): ["EXPLORES_THEME"],
    ("FilmProject", "Location"): ["SET_IN"],
    ("FilmProject", "Character"): ["HAS_PROTAGONIST"],
    ("FilmProject", "Scene"): ["HAS_ENDING"],
    ("FilmProject", "CreativeDirection"): ["HAS_VISUAL_STYLE"],
    ("FilmProject", "ReferenceFilm"): ["INSPIRED_BY"],
    ("FilmProject", "CreativeConstraint"): ["CONSTRAINED_BY"],
    ("CrewMember", "FilmProject"): ["REQUESTS", "REJECTS", "APPROVES"],
    ("Director", "CreativeDecision"): ["APPROVES", "REJECTS", "REQUESTS"],
    ("CreativeDecision", "AudienceFeedback"): ["RESPONDS_TO"],
    ("CreativeDecision", "HumanFeedback"): ["RESPONDS_TO"],
    ("Character", "Character"): ["PRESERVES", "DESTROYS"],
    ("CreativeDecision", "CreativeDecision"): ["REPLACES"],
    # --- Pre-production pipeline: Script -> Screenplay -> Storyboard -> PreProduction ---
    ("FilmProject", "Script"): ["HAS_SCRIPT"],
    ("FilmProject", "Screenplay"): ["ADAPTED_INTO"],
    ("FilmProject", "Storyboard"): ["HAS_STORYBOARD"],
    ("FilmProject", "PreProduction"): ["IN_PREPRODUCTION"],
    ("Script", "Screenplay"): ["ADAPTED_INTO"],
    ("Screenplay", "Storyboard"): ["STORYBOARDED_AS"],
    ("Storyboard", "Scene"): ["DEPICTS_SCENE"],
    ("Storyboard", "PreProduction"): ["IN_PREPRODUCTION"],
    # --- Characters appearing across narrative artifacts ---
    ("Scene", "Character"): ["FEATURES_CHARACTER"],
    ("Script", "Character"): ["FEATURES_CHARACTER"],
    ("Screenplay", "Character"): ["FEATURES_CHARACTER"],
    # --- Creative direction, motifs, and human-in-the-loop review ---
    ("CrewMember", "CreativeDirection"): ["PROPOSES_DIRECTION"],
    ("Screenplay", "VisualMotif"): ["FEATURES_MOTIF"],
    ("Storyboard", "VisualMotif"): ["FEATURES_MOTIF"],
    ("Scene", "VisualMotif"): ["FEATURES_MOTIF"],
    ("FilmProject", "VisualMotif"): ["FEATURES_MOTIF"],
    ("Director", "HumanFeedback"): ["GIVES_FEEDBACK"],
    ("CrewMember", "HumanFeedback"): ["GIVES_FEEDBACK"],
    ("HumanFeedback", "Script"): ["REVISES"],
    ("HumanFeedback", "Screenplay"): ["REVISES"],
    ("HumanFeedback", "Storyboard"): ["REVISES"],
    # --- External audience/screening reception on artifacts ---
    ("Scene", "AudienceFeedback"): ["RECEIVES_FEEDBACK"],
    ("Storyboard", "AudienceFeedback"): ["RECEIVES_FEEDBACK"],
    ("Screenplay", "AudienceFeedback"): ["RECEIVES_FEEDBACK"],
    # --- Wild ideas / brainstorming ---
    ("Director", "WildIdea"): ["FLOATS_IDEA", "APPROVES", "REJECTS"],
    ("CrewMember", "WildIdea"): ["FLOATS_IDEA"],
    ("WildIdea", "FilmProject"): ["INSPIRES"],
    ("WildIdea", "CreativeDirection"): ["INSPIRES"],
    ("WildIdea", "Scene"): ["INSPIRES"],
    ("WildIdea", "CreativeDecision"): ["EVOLVES_INTO"],
    # Permissive fallback so unexpected creative relations can still emerge.
    ("*", "*"): list(edge_types.keys()),
}
