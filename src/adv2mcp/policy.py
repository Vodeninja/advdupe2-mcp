"""Server-specific allowlist, exported from the game's allowed-prop menu."""

from __future__ import annotations

import json
from pathlib import Path

from .codec import Table


def normalize(model: str) -> str:
    value = model.replace("\\", "/").lower()
    if not value.startswith("models/") or not value.endswith(".mdl") or ".." in value or any(ord(c) < 32 for c in value):
        raise ValueError(f"Invalid model path: {model!r}")
    return value


class PropPolicy:
    def __init__(self, path: Path, required: bool = True):
        self.path = path
        self.required = required

    def load(self) -> dict | None:
        if not self.path.exists():
            return None
        if self.path.stat().st_size > 8_000_000:
            raise ValueError("Server prop profile exceeds 8 MB")
        data = json.loads(self.path.read_text(encoding="utf-8-sig"))
        if data.get("format") != "adv2mcp-props-v1" or not isinstance(data.get("models"), list):
            raise ValueError("Invalid server prop profile; expected adv2mcp-props-v1")
        models = {}
        for item in data["models"]:
            if isinstance(item, str):
                item = {"model": item}
            if not isinstance(item, dict) or not isinstance(item.get("model"), str):
                raise ValueError("Invalid model in server profile")
            model = normalize(item["model"])
            models[model] = {**item, "model": model}
        if not models:
            raise ValueError("Server prop profile is empty")
        return {**data, "models": models}

    def status(self) -> dict:
        profile = self.load()
        return {"path": str(self.path), "required": self.required,
                "loaded": profile is not None, "model_count": len(profile["models"]) if profile else 0,
                "server": profile.get("server") if profile else None,
                "source": profile.get("source") if profile else None,
                "note": "User-supplied server lists or menu export; role-specific limits and server changes still apply."}

    def check(self, root: Table) -> dict:
        profile = self.load()
        if profile is None:
            if self.required:
                raise ValueError("Server allowlist is missing. Import the server list with adv2mcp import-props FILE, or export the allowed-prop menu from GMod. Then retry; no MCP restart needed.")
            return {"enforced": False, "unknown_models": []}
        models = profile["models"]
        blocked, unavailable = set(), set()
        entities = root.get("Entities")
        if not isinstance(entities, Table):
            raise ValueError("Missing Entities table")
        for _, entity in entities.entries:
            model = entity.get("Model") if isinstance(entity, Table) else None
            if not isinstance(model, str):
                raise ValueError("Every entity needs a model to check the server allowlist")
            normalized = normalize(model)
            if normalized not in models:
                blocked.add(normalized)
            elif models[normalized].get("available") is False:
                unavailable.add(normalized)
        if blocked:
            raise ValueError("Models are absent from the server allowlist: " + ", ".join(sorted(blocked)))
        if unavailable:
            raise ValueError("Allowed models are missing from the game client (ERROR icons): " + ", ".join(sorted(unavailable)))
        return {"enforced": True, "profile": str(self.path), "server": profile.get("server")}

    def search(self, query: str, limit: int, offset: int) -> dict:
        profile = self.load()
        if profile is None:
            raise ValueError("Server prop profile is not loaded; import a server Lua list or export it from GMod first")
        terms = query.lower().split()
        matches = sorted(k for k, v in profile["models"].items() if all(t in k for t in terms) and v.get("available") is not False)
        return {"total": len(matches), "models": matches[offset:offset+limit], "allowed_only": True,
                "server": profile.get("server"), "profile": str(self.path)}

