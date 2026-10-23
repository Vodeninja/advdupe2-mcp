"""Read model names and MDL hull bounds from loose files and Source VPKs."""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ModelEntry:
    path: str
    source: Path
    offset: int = 0
    length: int = 0
    preload: bytes = b""
    packed: bool = False

    def header(self) -> bytes:
        if not self.packed:
            with self.source.open("rb") as f:
                return f.read(160)
        data = self.preload[:160]
        if len(data) < 160 and self.length:
            with self.source.open("rb") as f:
                f.seek(self.offset)
                data += f.read(min(160-len(data), self.length))
        return data


def vpk_models(path: Path):
    with path.open("rb") as f:
        header = f.read(12)
        if len(header) != 12:
            raise ValueError(f"Truncated VPK: {path}")
        signature, version, size = struct.unpack("<III", header)
        if signature != 0x55AA1234 or version not in (1, 2) or size > 64_000_000:
            raise ValueError(f"Unsupported VPK header: {path}")
        header_size = 12 if version == 1 else 28
        f.seek(header_size)
        tree = f.read(size)
    pos = 0

    def cstring() -> str:
        nonlocal pos
        end = tree.find(b"\0", pos)
        if end < 0:
            raise ValueError(f"Malformed VPK tree: {path}")
        value = tree[pos:end].decode("utf-8", "replace")
        pos = end + 1
        return value

    while ext := cstring():
        while folder := cstring():
            while name := cstring():
                if pos + 18 > len(tree):
                    raise ValueError("Truncated VPK entry")
                _, preload_size, archive, offset, length, terminator = struct.unpack_from("<IHHIIH", tree, pos)
                pos += 18
                if terminator != 0xFFFF or pos + preload_size > len(tree):
                    raise ValueError("Malformed VPK entry")
                preload = tree[pos:pos+preload_size]
                pos += preload_size
                if ext != "mdl":
                    continue
                model_path = f"{folder}/{name}.{ext}".lstrip(" /;").lower()
                if archive == 0x7FFF:
                    source = path
                    offset += header_size + size
                else:
                    source = path.with_name(path.name.removesuffix("_dir.vpk") + f"_{archive:03d}.vpk")
                yield ModelEntry(model_path, source, offset, length, preload, True)


class ModelCatalog:
    def __init__(self, game_dir: Path):
        self.game_dir = game_dir
        self.entries: dict[str, ModelEntry] | None = None
        self.errors: list[str] = []

    def refresh(self) -> int:
        entries: dict[str, ModelEntry] = {}
        self.errors = []
        # This is an on-disk catalog, not the running game's mount table.
        for root in (self.game_dir.parent / "sourceengine", self.game_dir):
            for archive in sorted(root.glob("*_dir.vpk")):
                try:
                    for entry in vpk_models(archive):
                        entries[entry.path] = entry
                except (ValueError, OSError, struct.error) as exc:
                    self.errors.append(str(exc))
        roots = [self.game_dir]
        addons = self.game_dir / "addons"
        if addons.is_dir():
            roots.extend(p for p in sorted(addons.iterdir()) if p.is_dir())
        for root in roots:
            model_dir = root / "models"
            if model_dir.is_dir():
                for model in model_dir.rglob("*.mdl"):
                    relative = model.relative_to(root).as_posix().lower()
                    entries[relative] = ModelEntry(relative, model)
        self.entries = entries
        return len(entries)

    def all(self) -> dict[str, ModelEntry]:
        if self.entries is None:
            self.refresh()
        return self.entries

    def search(self, query: str, limit: int = 50, offset: int = 0) -> dict:
        terms = query.lower().split()
        matched = sorted(p for p in self.all() if all(t in p for t in terms))
        return {"total": len(matched), "models": matched[offset:offset+limit],
                "errors": self.errors,
                "coverage": "Base VPKs and unpacked addons; Workshop .gma and external mounts are not indexed."}

    def info(self, model: str) -> dict:
        normalized = model.replace("\\", "/").lower()
        entry = self.all().get(normalized)
        if entry is None:
            raise ValueError("Model not found in catalog; use search_models or refresh the catalog")
        header = entry.header()
        if len(header) < 152 or header[:4] != b"IDST":
            raise ValueError("Unsupported/truncated Source MDL")
        hull = struct.unpack_from("<6f", header, 104)
        return {"model": normalized, "source": str(entry.source),
                "mdl_version": struct.unpack_from("<i", header, 4)[0],
                "hull_min": list(hull[:3]), "hull_max": list(hull[3:]),
                "size": [round(hull[i+3] - hull[i], 6) for i in range(3)],
                "note": "Unrotated model hull bounds in Source units; actual physics mesh and server availability may differ."}
