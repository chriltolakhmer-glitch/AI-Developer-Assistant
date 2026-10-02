"""Bounded developer configuration excerpts; original source stays untouched."""
from dataclasses import replace
import hashlib
from pathlib import PurePosixPath

from src.chunker import CodeChunker
from src.models.corpus import RepositoryMetadata


def configuration_file(path):
    path = PurePosixPath(path)
    return path.stem in {"config", "configuration", "settings"} or any(
        part in {"config", "configuration", "settings"} for part in path.parts[:-1])


def bound_configuration(parsed, tokenizer):
    """Retain a contiguous, whole-line prefix and report every omitted line.

    Retained excerpts receive provenance-correct IDs for their bounded ranges;
    original identity/hash and retained content hash remain in diagnostics. Exact
    model token counts bound excerpts. An oversized first line is omitted rather
    than cut inside a literal.
    """
    chunks, context, remapped_ids = [], dict(parsed.context), {}

    def count(text):
        return len(tokenizer(text.strip(), add_special_tokens=True, truncation=False,
                             padding=False, verbose=False)["input_ids"])

    for chunk in parsed.chunks:
        if not configuration_file(chunk.file_path):
            chunks.append(chunk)
            remapped_ids[chunk.chunk_id] = chunk.chunk_id
            continue
        tokens = count(chunk.content)
        if tokens <= 256:
            chunks.append(chunk)
            remapped_ids[chunk.chunk_id] = chunk.chunk_id
            continue
        lines = chunk.content.splitlines(keepends=True)
        retained = []
        for line in lines:
            if count("".join(retained) + line) > 256:
                break
            retained.append(line)
        text = "".join(retained)
        last = chunk.start_line + len(retained) - 1
        original_content_sha256 = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
        diagnostics = {
            "oversized": True, "original_token_count": tokens,
            "retained_token_count": count(text) if text.strip() else 0,
            "status": "truncated" if text.strip() else "omitted",
            "reason": "configuration exceeds 256 tokens; retain whole source lines only",
            "original_content_sha256": original_content_sha256,
            "retained_lines": [chunk.start_line, last] if retained else [],
            "omitted_lines": [last + 1, chunk.end_line],
        }
        details = {**context[chunk.chunk_id], "context_budget": diagnostics,
               "original_chunk_id": chunk.chunk_id,
               "original_source_region": context[chunk.chunk_id].get("source_region"),
               "original_content_sha256": original_content_sha256}
        # Do not claim omitted configuration keys as retained evidence.
        details["configuration_keys"] = [key for key in details.get("configuration_keys", [])
                                         if key in text]
        if retained:
            excerpt = CodeChunker._make_chunk(
                RepositoryMetadata(chunk.repository_id, chunk.commit_sha), chunk.commit_sha,
                chunk.file_path, chunk.entity_type, chunk.qualified_name, chunk.start_line, last,
                ["\n"] * (chunk.start_line - 1) + lines,
            )
            remapped_ids[chunk.chunk_id] = excerpt.chunk_id
            details["source_region"] = f"{excerpt.file_path}:{excerpt.start_line}-{excerpt.end_line}"
            details["content_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            chunks.append(excerpt)
        else:
            # Preserve an explicit omission entry without embedding an empty chunk.
            remapped_ids[chunk.chunk_id] = None
        context[chunk.chunk_id] = details

    remapped_context = {}
    for chunk_id, details in context.items():
        mapped_id = remapped_ids.get(chunk_id) or chunk_id
        retained_details = dict(details)
        retained_details["related_chunk_ids"] = sorted({
            (remapped_ids.get(related_id) or related_id)
            for related_id in details.get("related_chunk_ids", [])
        })
        remapped_context[mapped_id] = retained_details
    return replace(parsed, chunks=tuple(chunks), context=remapped_context)
