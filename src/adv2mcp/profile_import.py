"""Import literal model lists from a server Lua file without evaluating Lua."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .policy import PropPolicy, normalize

DEFAULT_TABLES = ("Props", "NewProps", "Whiteprop")
TOKEN = re.compile(
    r"(?P<space>\s+)|(?P<block>--\[(?P<equals>=*)\[.*?\](?P=equals)\])"
    r"|(?P<comment>--[^\r\n]*)"
    r'''|(?P<string>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')'''
    r"|(?P<name>[a-zA-Z_][a-zA-Z_0-9]*)|(?P<char>.)",
    re.DOTALL,
)


def parse_lists(text: str, names: tuple[str, ...] = DEFAULT_TABLES) -> dict[str, list[str]]:
    tokens = [(m.lastgroup, m.group()) for m in TOKEN.finditer(text)
              if m.lastgroup not in ("space", "block", "comment")]
    result: dict[str, list[str]] = {}
    i = 0
    while i + 2 < len(tokens):
        kind, name = tokens[i]
        if kind != "name" or name not in names or tokens[i+1][1] != "=" or tokens[i+2][1] != "{":
            i += 1
            continue
        i += 3
        models = []
        while i < len(tokens) and tokens[i][1] != "}":
            kind, literal = tokens[i]
            if kind != "string":
                raise ValueError(f"{name} must be a literal array of model paths; Lua expressions are not evaluated")
            raw = literal[1:-1]
            if re.search(r'''\\[^\\'"]''', raw):
                raise ValueError(f"Unsupported escape in {name}; use forward slashes in model paths")
            model = re.sub(r'''\\([\\'"])''', r"\1", raw)
            models.append(normalize(model))
            i += 1
            if i < len(tokens) and tokens[i][1] in (",", ";"):
                i += 1
            elif i >= len(tokens) or tokens[i][1] != "}":
                raise ValueError(f"Missing separator or closing brace in {name}")
        if i >= len(tokens):
            raise ValueError(f"Unclosed {name} table")
        result.setdefault(name, []).extend(models)
        i += 1
    if not result or not any(result.values()):
        raise ValueError("No model lists found; expected tables: " + ", ".join(names))
    return result


def import_profile(source: Path, destination: Path, names: tuple[str, ...] = DEFAULT_TABLES,
                   server: str | None = None) -> dict:
    raw = source.read_bytes()
    if len(raw) > 8_000_000:
        raise ValueError("Source prop list exceeds 8 MB")
    lists = parse_lists(raw.decode("utf-8-sig"), names)
    entries: dict[str, set[str]] = {}
    for category, models in lists.items():
        for model in models:
            entries.setdefault(model, set()).add(category)
    now = datetime.now(timezone.utc)
    profile = {"format": "adv2mcp-props-v1", "server": server,
               "source": "user-provided server Lua lists: " + ", ".join(lists),
               "source_file": source.name, "source_sha256": hashlib.sha256(raw).hexdigest(),
               "imported_at": now.isoformat(),
               "table_counts": {name: len(models) for name, models in lists.items()},
               "models": [{"model": model, "categories": sorted(entries[model])} for model in sorted(entries)]}
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent,
                                     prefix=".adv2mcp-profile-", suffix=".json", delete=False) as f:
        temporary = Path(f.name)
        try:
            json.dump(profile, f, ensure_ascii=False, indent=2)
            f.write("\n")
        except BaseException:
            f.close()
            temporary.unlink(missing_ok=True)
            raise
    backup = None
    try:
        PropPolicy(temporary).load()
        if destination.exists():
            backup = destination.with_name(destination.name + now.strftime(".%Y%m%d-%H%M%S-%f.bak"))
            backup.write_bytes(destination.read_bytes())
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return {"path": str(destination), "model_count": len(entries),
            "table_counts": profile["table_counts"],
            "duplicates_removed": sum(len(v) for v in lists.values()) - len(entries),
            "backup": str(backup) if backup else None}
