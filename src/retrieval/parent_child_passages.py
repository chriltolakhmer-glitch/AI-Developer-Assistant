"""Source-preserving child representations; canonical chunk identities never change."""

from dataclasses import dataclass
import hashlib
import json

from src.models.chunk import CodeChunk

MAX_INPUT_TOKENS = 256
PAYLOAD_TOKENS = 224
OVERLAP_TOKENS = 32
REPRESENTATION_VERSION = "phase14.7-window-v1"


@dataclass(frozen=True, slots=True)
class ChildPassage:
    child_id: str
    parent_chunk_id: str
    char_start: int
    char_end: int
    content: str
    content_sha256: str
    token_count: int


def token_count(tokenizer, text: str) -> int:
    return len(tokenizer(text.strip(), add_special_tokens=True, truncation=False,
                         padding=False, verbose=False)["input_ids"])


def split_parent(parent: CodeChunk, tokenizer) -> tuple[ChildPassage, ...]:
    """Cover the exact source characters, including long lines, without truncation."""
    content = parent.content
    if not content.strip():
        raise ValueError("Empty parent cannot be represented")
    if token_count(tokenizer, content) <= MAX_INPUT_TOKENS:
        spans = [(0, len(content))]
    else:
        offsets = tokenizer(content, add_special_tokens=False, truncation=False,
                            padding=False, return_offsets_mapping=True,
                            verbose=False)["offset_mapping"]
        if not offsets:
            raise ValueError("Tokenizer did not produce source offsets")
        spans, first = [], 0
        while first < len(offsets):
            last = min(first + PAYLOAD_TOKENS, len(offsets))
            start = 0 if first == 0 else offsets[first][0]
            end = len(content) if last == len(offsets) else offsets[last][0]
            while token_count(tokenizer, content[start:end]) > MAX_INPUT_TOKENS:
                last -= 1
                if last <= first:
                    raise ValueError("Cannot fit source passage in encoder budget")
                end = offsets[last][0]
            spans.append((start, end))
            if last == len(offsets):
                break
            first = max(first + 1, last - OVERLAP_TOKENS)
    children, covered = [], 0
    for start, end in spans:
        if not 0 <= start <= covered < end <= len(content):
            raise ValueError("Invalid or incomplete child source coverage")
        text = content[start:end]
        count = token_count(tokenizer, text)
        if not text.strip() or not 0 < count <= MAX_INPUT_TOKENS:
            raise ValueError("Child passage exceeds encoder contract")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        identity = [REPRESENTATION_VERSION, parent.chunk_id, start, end,
                    digest, PAYLOAD_TOKENS, OVERLAP_TOKENS]
        child_id = hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()
        children.append(ChildPassage(child_id, parent.chunk_id, start, end, text, digest, count))
        covered = end
    if covered != len(content):
        raise ValueError("Incomplete parent coverage")
    return tuple(children)
