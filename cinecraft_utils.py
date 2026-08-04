"""CineCraft.AI — retrieval tools (Neo4j GraphRAG hybrid + Tavily web search).

These functions carry real runtime dependencies (the GraphRAG HybridRetriever,
the Tavily client and the `llm` callable), so instead of importing notebook
globals they are produced by a small factory: `build_retrieval_tools(...)`
binds the dependencies once and returns the three ready-to-use functions with
the SAME signatures the notebook already calls, so no call site has to change.

    hybrid_search_movies, search_similar_movies, web_search_movies = \\
        build_retrieval_tools(hybrid=_hybrid, tavily_client=tavily_client, llm=llm)
"""
from __future__ import annotations

import ast

from utils import sanitize_for_lucene, json_slice
from cinecraft_prompts import web_title_extraction_prompt


def build_retrievals(*, hybrid, tavily_client, llm,
                          sanitize=sanitize_for_lucene, parse_json=json_slice):
    """Bind runtime deps and return (hybrid_search_movies, search_similar_movies,
    web_search_movies) closures with the notebook's original signatures.

    Parameters
    ----------
    hybrid        : a neo4j_graphrag HybridRetriever (vector + full-text).
    tavily_client : an initialised TavilyClient.
    llm           : the single-turn chat-completion callable, `llm(prompt) -> str`.
    sanitize      : Lucene sanitiser (defaults to utils.sanitize_for_lucene).
    parse_json    : JSON-slice extractor (defaults to utils.json_slice).
    """

    def hybrid_search_movies(query: str, limit: int = 5) -> list[dict]:
        """Hybrid (vector + full-text) movie search → list of {"title": ...}."""
        if not query or not query.strip():
            return []
        # Sanitize so the Lucene full-text side of the hybrid search never errors
        # on reserved characters (`:`, quotes, parentheses, `·`, …).
        safe_query = sanitize(query)
        if not safe_query:
            return []
        res = hybrid.search(query_text=safe_query, top_k=limit)
        out = []
        for item in res.items:
            data = ast.literal_eval(item.content)
            title = data.get("name") or data.get("title")
            if title:
                out.append({"title": title})
        return out[:limit]

    def search_similar_movies(concept: str, max_results: int = 8):
        """Search the web (Tavily) for movies similar to a user's concept.
        Returns the raw Tavily search response (with AI answer + sources)."""
        # ⚠️ Tavily rejects any query longer than 400 characters with a
        # `400 Bad Request`. The concept passed in can already be padded with
        # recalled "Past taste: ..." notes, so we keep the query compact and
        # clamp the whole thing to a safe length (well under Tavily's 400 limit).
        query = f"Movies similar to: {concept.strip()}. Similar themes, plot, genre, mood, visual style."
        query = query[:380]
        return tavily_client.search(
            query=query,
            topic="general",
            search_depth="advanced",
            max_results=max_results,
            include_answer=True,
            include_raw_content=False,
        )

    def web_search_movies(query: str, limit: int = 3) -> list[dict]:
        """Return reference films discovered on the web via Tavily.

        Tavily returns web-page results (page titles, not film names), so we pool
        the AI `answer` + page `content` and let the LLM extract the real MOVIE
        NAMES. Best-effort; [] on failure."""
        # Guard: skip blank queries entirely.
        if not query or not query.strip():
            return []
        print(f"   🌐 web_search_movies → querying Tavily for: {query.strip()[:80]!r}")
        try:
            response = search_similar_movies(query.strip(), max_results=max(limit, 5))

            # Tavily returns WEB-PAGE results (page titles like "15 Best
            # Time-Travel Movies - IMDb"), NOT movie names. So instead of using
            # r["title"], we pool Tavily's AI `answer` + each result's text
            # `content` and ask the LLM to EXTRACT the actual MOVIE NAMES.
            answer = response.get("answer") or ""
            snippets = "\n".join(
                (r.get("content") or "") for r in response.get("results", []))
            corpus = f"{answer}\n\n{snippets}".strip()
            if not corpus:
                print("   🌐 web_search_movies ← 0 film(s): (empty web corpus)")
                return []

            extract_prompt = web_title_extraction_prompt(corpus, limit)
            titles = []
            try:
                parsed = parse_json(llm(extract_prompt))
                titles = [str(t).strip() for t in parsed.get("titles", []) if str(t).strip()]
            except Exception as e:
                print(f"   ⚠️ movie-title extraction failed ({e})")

            # De-duplicate (case-insensitive), preserve order, clamp to limit.
            seen, results = set(), []
            for t in titles:
                key = t.lower()
                if key in seen:
                    continue
                seen.add(key)
                results.append({"title": t, "overview": "", "url": "",
                                "genres": [], "rating": None, "source": "web"})
                if len(results) >= limit:
                    break

            print(f"   🌐 web_search_movies ← {len(results)} film(s): "
                  + (", ".join(h["title"] for h in results) or "(none)"))
            return results
        except Exception as e:
            print(f"   ⚠️ web search unavailable ({e})")
            return []

    return hybrid_search_movies, search_similar_movies, web_search_movies
