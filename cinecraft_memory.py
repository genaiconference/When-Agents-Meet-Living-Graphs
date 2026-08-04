# 🔧 run_async (drive an async coroutine to completion from sync node code)
# now lives in utils.py.
from utils import run_async


def build_memory_bridge(get_memory, get_memory_agent, get_graphiti):
    """Factory that wires the memory helpers to the notebook's live objects.

    The MEMORY / MEMORY_AGENT / graphiti objects are created inside the
    notebook (and can be re-created as the session evolves), so this module
    can't import them at load time. Instead the notebook hands us zero-arg
    accessors that read the CURRENT globals at call time. We close over those
    accessors and return four functions whose signatures match exactly what the
    graph nodes expect:

        recall_memory, record_memory, seed_context, get_saga_week_summary
    """

    def recall_memory(stage: str, wild_idea: str) -> str:
        """Node-friendly wrapper: 3-layer memory bundle for `stage` (or '' if off)."""
        memory_agent = get_memory_agent()
        if memory_agent is None:
            return ""
        return run_async(memory_agent.recall(stage, wild_idea))

    def record_memory(stage: str, agent_output: str, human_feedback: str = "",
                      final_decision: str = "") -> None:
        """Node-friendly wrapper: persist `stage` as an immutable saga episode."""
        memory = get_memory()
        if memory is None:
            return
        try:
            run_async(memory.record_stage(stage, agent_output, human_feedback, final_decision))
        except Exception as e:
            print(f"   ⚠️ could not record {stage} episode ({e})")

    def seed_context(memory: str = "") -> str:
        """Prepend the Week-1 saga.summary (seed) onto a stage's recalled memory.

        This is how we SEED THE CLONE: the whole Week-1 evolution (saga.summary)
        is folded into the facts handed to the creative-direction, story and
        screenplay agents, so every new decision is made in the context of the
        WHOLE journey so far — not from scratch."""
        memory_obj = get_memory()
        seed = getattr(memory_obj, "seed_summary", "") if memory_obj is not None else ""
        if not seed:
            return memory
        header = f"Prior saga summary (Week 1 — the story so far):\n{seed}"
        return f"{header}\n\n{memory}" if memory else header

    def get_saga_week_summary(saga_id: str, group_id: str) -> str:
        """Fetch the rolling SUMMARY of a prior week's saga (the whole journey so far).

        Reads the `Saga` node's stored `summary`; if it's empty, resolves the saga
        uuid and calls `graphiti.summarize_saga()` to fold that week into one
        narrative. This single summary is used BOTH as the Week-2 wild idea AND as
        the seed context handed to every downstream stage. Returns '' if not found."""
        graphiti = get_graphiti()
        if graphiti is None:
            return ""

        async def _fetch() -> str:
            rows = await graphiti.driver.execute_query(
                """
                MATCH (s:Saga {name: $name, group_id: $gid})
                RETURN s.uuid AS uuid, s.summary AS summary
                """,
                name=saga_id, gid=group_id,
            )
            records = getattr(rows, "records", None) or (rows[0] if rows else [])
            if not records:
                return ""
            rec = records[0]
            summary = rec.get("summary") if hasattr(rec, "get") else rec["summary"]
            if summary:
                return summary
            # No stored summary yet → generate one from the saga's episode chain.
            uuid = rec.get("uuid") if hasattr(rec, "get") else rec["uuid"]
            if not uuid:
                return ""
            saga = await graphiti.summarize_saga(uuid)
            return getattr(saga, "summary", "") or ""

        try:
            return run_async(_fetch()) or ""
        except Exception as e:
            print(f"   ⚠️ get_saga_week_summary failed ({e})")
            return ""

    return recall_memory, record_memory, seed_context, get_saga_week_summary
