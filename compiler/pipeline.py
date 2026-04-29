from .lexer import tokenize
from .memory import execute
from .parser_semantic import analyze


# Runs all 3 phases. Phase 3 only runs if Phase 2 has zero errors.
def run_all(source: str) -> dict:
    tokens = tokenize(source)
    errors = analyze(tokens)
    memory_trace = execute(tokens) if not errors else []

    counts: dict[str, int] = {}
    for t in tokens:
        counts[t.type] = counts.get(t.type, 0) + 1

    return {
        "tokens": [t.to_dict() for t in tokens],
        "errors": [e.to_dict() for e in errors],
        "memory": [m.to_dict() for m in memory_trace],
        "counts": counts,
    }
