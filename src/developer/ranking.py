"""Transparent, versioned developer navigation preferences; never research scoring."""

import re
from pathlib import PurePosixPath

from src.retrieval.rrf import CANDIDATE_WINDOW, fuse_rankings

RANKING_VERSION = "developer-navigation-v2"
_STOP = frozenset("where is are the a an how what which do does from for to of in and created defined implemented loaded handled".split())
_ALIASES = {"configuration": "config", "authentication": "auth", "connections": "connection", "routes": "route"}


def _terms(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return {_ALIASES.get(word, word) for word in re.findall(r"[a-z0-9]+", text.casefold()) if word not in _STOP}


def rank_developer_results(question, dense, lexical, top_k, context=None):
    """Rerank the local candidate union with explainable symbol/graph preferences.

    Prefer exact symbol names, query-matched static relationships, and relevant
    paths. Do not penalize tests when explicitly requested. Suppress overlapping
    ranges and exact duplicate symbol/content copies; distinct methods remain.
    """
    from .local_workflow import _result_to_dict

    query_terms = _terms(question)
    wants_tests = bool(query_terms & {"test", "tests", "testing"})
    candidates = fuse_rankings({"dense": dense, "bm25": lexical}, k=CANDIDATE_WINDOW)
    ranked = []
    for result in candidates:
        row = _result_to_dict(result)
        path_terms = sorted(query_terms & _terms(result.file_path))
        symbol_terms = sorted(query_terms & _terms(result.qualified_name))
        matches = sorted(set(path_terms) | set(symbol_terms))
        metadata_factor = 1 + 0.20 * min(len(matches), 3)
        symbol_leaf = result.qualified_name.rsplit(".", 1)[-1].casefold()
        exact_symbol = bool(result.qualified_name and re.search(
            rf"(?<![A-Za-z0-9_]){re.escape(result.qualified_name)}(?![A-Za-z0-9_])",
            question, flags=re.IGNORECASE,
        ))
        exact_symbol_leaf = symbol_leaf in query_terms
        symbol_factor = 1.50 if exact_symbol else 1.25 if exact_symbol_leaf else 1.0
        relationship_edges = (context or {}).get(result.chunk_id, {}).get("relationship_edges", [])
        matching_relationships = sorted({
            edge.get("symbol", "") for edge in relationship_edges
            if edge.get("symbol") and (
                _terms(edge["symbol"]) & query_terms
                or bool(re.search(
                    rf"(?<![A-Za-z0-9_]){re.escape(edge['symbol'])}(?![A-Za-z0-9_])",
                    question, flags=re.IGNORECASE,
                ))
            )
        })
        relationship_factor = 1.25 if matching_relationships else 1.0
        file_factor = 1 + 0.10 * min(len(path_terms), 3)
        parts = PurePosixPath(result.file_path).parts
        is_test = any(part in {"test", "tests", "testing"} or part.startswith("test_") or part.endswith("_test.py") for part in parts)
        test_factor = 0.70 if is_test and not wants_tests else 1.0
        module_factor = 0.85 if result.entity_type in {"module", "class"} else 1.0
        row["base_rrf_score"] = result.score
        row["score"] = (result.score * metadata_factor * symbol_factor * relationship_factor
                 * file_factor * test_factor * module_factor)
        row["navigation_score"] = row["score"]
        channels = {c.channel for c in result.contributions}
        row["retrieval_source"] = "hybrid" if len(channels) == 2 else "vector" if "dense" in channels else "lexical"
        row["ranking_version"] = RANKING_VERSION
        row["ranking_reason"] = {"matched_metadata_terms": matches, "metadata_factor": metadata_factor,
                     "matched_symbol_terms": symbol_terms,
                     "exact_symbol_match": exact_symbol,
                     "exact_symbol_leaf_match": exact_symbol_leaf,
                     "symbol_factor": symbol_factor,
                     "matching_relationships": matching_relationships,
                     "relationship_factor": relationship_factor,
                     "matched_file_terms": path_terms,
                     "file_relevance_factor": file_factor,
                                 "test_factor": test_factor, "container_factor": module_factor,
                     "formula": "base_rrf_score * metadata_factor * symbol_factor * relationship_factor * file_relevance_factor * test_factor * container_factor * diversity_factor",
                                 "diversity": "non-overlapping ranges; diversity_factor = 1 / (1 + 0.1 * prior results from this file)"}
        details = (context or {}).get(result.chunk_id, {})
        row["developer_context"] = details
        row["ranking_reason"].update({
            "lexical_contribution": sum(item.rrf_score for item in result.contributions if item.channel == "bm25"),
            "vector_contribution": sum(item.rrf_score for item in result.contributions if item.channel == "dense"),
            "symbol_relevance": bool(matches),
            "context_expansion_reason": details.get("why", "direct retrieval result"),
        })
        ranked.append(row)
    ranked.sort(key=lambda row: (-row["score"], row["chunk_id"]))
    selected = []
    selected_signatures = {}
    while ranked and len(selected) < top_k:
        remaining = []
        for row in ranked:
            signature = (row["qualified_name"], row["developer_context"].get("content_sha256"))
            duplicate_owner = selected_signatures.get(signature) if signature[1] else None
            if duplicate_owner is not None and duplicate_owner["file_path"] != row["file_path"]:
                duplicate_owner["ranking_reason"].setdefault("duplicate_suppressed", []).append({
                    "file_path": row["file_path"], "chunk_id": row["chunk_id"],
                    "reason": "same symbol and source content already selected",
                })
                continue
            same_file = [s for s in selected if s["file_path"] == row["file_path"]]
            if any(max(row["start_line"], s["start_line"]) <= min(row["end_line"], s["end_line"]) for s in same_file):
                continue
            factor = 1 / (1 + 0.1 * len(same_file))
            row["ranking_reason"]["diversity_factor"] = factor
            row["score"] = row["navigation_score"] * factor
            remaining.append(row)
        if not remaining:
            break
        remaining.sort(key=lambda row: (-row["score"], row["chunk_id"]))
        chosen, *ranked = remaining
        chosen["rank"] = len(selected) + 1
        selected.append(chosen)
        signature = (chosen["qualified_name"], chosen["developer_context"].get("content_sha256"))
        if signature[1]:
            selected_signatures.setdefault(signature, chosen)
    for row in selected:
        details = row.get("developer_context", {})
        context_by_id = context or {}
        edges_by_symbol = {}
        for edge in details.get("relationship_edges", []):
            edges_by_symbol.setdefault(edge.get("symbol"), edge.get("kind", "indexed relationship"))
        related = []
        seen_symbols = {row["qualified_name"]}
        related_symbols = [context_by_id.get(chunk_id, {}).get("symbol_name")
                           for chunk_id in details.get("related_chunk_ids", [])]
        duplicate_symbols = len([symbol for symbol in related_symbols if symbol]) - len(
            {symbol for symbol in related_symbols if symbol}
        )
        for chunk_id in details.get("related_chunk_ids", []):
            if chunk_id == row["chunk_id"]:
                continue
            target = context_by_id.get(chunk_id, {})
            symbol = target.get("symbol_name")
            if not symbol or symbol in seen_symbols:
                continue
            reason = next((kind for edge_symbol, kind in edges_by_symbol.items()
                           if edge_symbol == symbol or edge_symbol.rsplit(".", 1)[-1] == symbol.rsplit(".", 1)[-1]),
                          "indexed symbol relationship")
            related.append({
                "chunk_id": chunk_id,
                "symbol_name": symbol,
                "file_path": target.get("source_region", "").split(":", 1)[0],
                "reason": reason,
            })
            seen_symbols.add(symbol)
        row["related_context"] = related[:5]
        row["ranking_reason"]["context_expansion_reason"] = (
            "expanded to explicit static relationships" if related
            else details.get("why", "direct retrieval result")
        )
        row["ranking_reason"]["context_suppressed"] = {
            "nearby_only": len(details.get("nearby_chunk_ids", [])),
            "duplicate_symbols": max(0, duplicate_symbols),
        }
    return selected
