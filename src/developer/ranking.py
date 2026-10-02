"""Transparent, versioned developer navigation preferences; never research scoring."""

import re
from pathlib import PurePosixPath

from src.retrieval.rrf import CANDIDATE_WINDOW, fuse_rankings

RANKING_VERSION = "developer-navigation-v6"
_STOP = frozenset("where is are the a an how what which do does from for to of in and created defined implemented loaded handled".split())
_ALIASES = {"configuration": "config", "authentication": "auth", "connections": "connection",
            "routes": "route", "utility": "utils"}
_GENERIC_RELATIONSHIP_TERMS = _STOP | frozenset(
    "api backend cache code get init load main query run save set store test tests vector".split())


def _terms(text):
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    return {_ALIASES.get(word, word) for word in re.findall(r"[a-z0-9]+", text.casefold()) if word not in _STOP}


def _relationship_matches(symbol, question, query_terms):
    meaningful = (_terms(symbol) & query_terms) - _GENERIC_RELATIONSHIP_TERMS
    if len(meaningful) >= 2:
        return True
    components = [part for part in re.split(r"[.:]", symbol) if part]
    return any(
        bool(_terms(component) - _GENERIC_RELATIONSHIP_TERMS)
        and bool(re.search(rf"(?<![A-Za-z0-9_]){re.escape(component)}(?![A-Za-z0-9_])",
                           question, flags=re.IGNORECASE))
        for component in components
    )


def rank_developer_results(question, dense, lexical, top_k, context=None, settings=None):
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
            if edge.get("symbol") and _relationship_matches(edge["symbol"], question, query_terms)
        })
        relationship_factor = (settings or {}).get("relationship_factor", 1.25) if matching_relationships else 1.0
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
    # Prefer a duplicate candidate that is an explicitly resolved dependency of
    # a query-relevant result. Otherwise an unrelated copy can win on raw rank
    # and suppress the real relationship target during context expansion.
    context_by_id = context or {}
    duplicate_counts = {}
    for details in context_by_id.values():
        digest = details.get("content_sha256")
        if digest:
            duplicate_counts[digest] = duplicate_counts.get(digest, 0) + 1
    preferred_by_digest = {}
    preferred_source_by_digest = {}
    for source in ranked:
        reason = source["ranking_reason"]
        if not (reason["exact_symbol_match"] or reason["matched_metadata_terms"]):
            continue
        for target_id in source["developer_context"].get("related_chunk_ids", []):
            target = context_by_id.get(target_id, {})
            digest = target.get("content_sha256")
            if digest and duplicate_counts.get(digest, 0) > 1:
                preferred_by_digest.setdefault(digest, target_id)
                preferred_source_by_digest.setdefault(digest, source["chunk_id"])
    selected = []
    selected_signatures = {}
    selected_content = {}
    suppressed_by_digest = {}
    while ranked and len(selected) < top_k:
        remaining = []
        for row in ranked:
            signature = (row["file_path"], row["qualified_name"])
            digest = row["developer_context"].get("content_sha256")
            preferred_id = preferred_by_digest.get(digest) if digest else None
            if preferred_id is not None and row["chunk_id"] != preferred_id:
                suppressed_by_digest.setdefault(digest, []).append({
                    "file_path": row["file_path"], "chunk_id": row["chunk_id"],
                    "reason": "unrelated duplicate suppressed in favor of explicit relationship target",
                })
                continue
            duplicate_owner = selected_signatures.get(signature) or (selected_content.get(digest) if digest else None)
            if duplicate_owner is not None:
                duplicate_owner["ranking_reason"].setdefault("duplicate_suppressed", []).append({
                    "file_path": row["file_path"], "chunk_id": row["chunk_id"],
                    "reason": "same file/symbol or identical content already selected",
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
        selected_signatures[(chosen["file_path"], chosen["qualified_name"])] = chosen
        digest = chosen["developer_context"].get("content_sha256")
        if digest:
            selected_content[digest] = chosen
    selected_by_id = {row["chunk_id"]: row for row in selected}
    for digest, suppressed in suppressed_by_digest.items():
        target_id = preferred_by_digest[digest]
        source_id = preferred_source_by_digest[digest]
        owner = selected_by_id.get(source_id) or next((
            row for row in selected
            if target_id in row["developer_context"].get("related_chunk_ids", [])
        ), None)
        if owner is not None:
            owner["ranking_reason"].setdefault("duplicate_suppressed", []).extend(suppressed)
    seen_symbols = set(selected_signatures)
    seen_content = set(selected_content)
    for row in selected:
        details = row.get("developer_context", {})
        edges = {(edge.get("file_path"), edge.get("symbol")): edge.get("kind")
                 for edge in details.get("relationship_edges", [])}
        related, omissions = [], []
        for chunk_id in details.get("related_chunk_ids", []):
            target = context_by_id.get(chunk_id, {})
            symbol = target.get("symbol_name")
            path = target.get("source_region", "").split(":", 1)[0]
            identity = (path, symbol)
            digest = target.get("content_sha256")
            reason = None
            if not symbol or identity not in edges:
                reason = "undeclared relationship"
            elif identity in seen_symbols or (digest and digest in seen_content):
                reason = "duplicate symbol or content"
            elif target.get("context_budget", {}).get("status") == "omitted":
                reason = "context exceeds token budget or is empty"
            elif len(related) >= 5:
                reason = "relationship expansion limit"
            if reason:
                omissions.append({"chunk_id": chunk_id, "symbol_name": symbol,
                                  "file_path": path, "reason": reason})
                continue
            related.append({"chunk_id": chunk_id, "symbol_name": symbol,
                            "file_path": path, "reason": edges[identity],
                            "content_sha256": digest})
            seen_symbols.add(identity)
            if digest:
                seen_content.add(digest)
        row["related_context"] = related
        row["relationship_references"] = details.get("relationship_edges", [])
        row["relationship_diagnostics"] = details.get("relationship_diagnostics", [])
        row["context_omissions"] = omissions
        row["ranking_reason"]["context_expansion_reason"] = (
            "expanded to explicit static relationships" if related
            else details.get("why", "direct retrieval result")
        )
        row["ranking_reason"]["context_suppressed"] = {
            "nearby_only": len(details.get("nearby_chunk_ids", [])),
            "duplicate_symbols": sum(item["reason"] == "duplicate symbol or content" for item in omissions),
        }
    return selected
