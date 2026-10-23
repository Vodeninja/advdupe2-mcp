"""Bounded binary file IO confined to the configured duplication directory."""

from __future__ import annotations

import os
import re
import tempfile
from datetime import datetime
from pathlib import Path

from .build import summary, validate_dupe
from .codec import MAX_SIZE, CodecError, Table, decode, encode
from .policy import PropPolicy

DEFAULT_DUPE_DIR = Path(os.environ.get("ADV2MCP_DUPE_DIR", str(
    Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
    / "Steam/steamapps/common/GarrysMod/garrysmod/data/advdupe2")))


class DupeStore:
    def __init__(self, root: Path, policy: PropPolicy | None = None):
        self.root = root.expanduser().resolve()
        self.policy = policy or PropPolicy(
            Path(os.environ.get("ADV2MCP_PROP_PROFILE", str(self.root / "adv2mcp" / "server-props.json"))),
            required=os.environ.get("ADV2MCP_REQUIRE_ALLOWLIST", "1") != "0")

    def path(self, name: str) -> Path:
        relative = Path(name.replace("\\", "/"))
        if not name or relative.is_absolute() or relative.drive or ".." in relative.parts:
            raise ValueError("Use a relative path inside the advdupe2 directory")
        if relative.suffix.lower() != ".txt":
            raise ValueError("Duplication filenames must end in .txt")
        for part in relative.parts:
            if any(c in part for c in '<>:"|?*') or any(ord(c) < 32 for c in part) or part.endswith((".", " ")):
                raise ValueError("Invalid filename")
            if re.fullmatch(r"(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?", part):
                raise ValueError("Reserved Windows filename")
        target = (self.root / relative).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("Path escapes the advdupe2 directory")
        return target

    def read(self, name: str) -> tuple[Table, dict[str, str]]:
        path = self.path(name)
        with path.open("rb") as f:
            data = f.read(MAX_SIZE + 1)
        root, info = decode(data)
        validate_dupe(root)
        return root, info

    def list(self, query: str = "", limit: int = 100, offset: int = 0) -> dict:
        if not self.root.is_dir():
            raise ValueError(f"Duplication directory does not exist: {self.root}")
        files = []
        for path in sorted(self.root.rglob("*.txt")):
            name = path.relative_to(self.root).as_posix()
            if query.lower() not in name.lower() or not path.resolve().is_relative_to(self.root):
                continue
            stat = path.stat()
            files.append({"name": name, "bytes": stat.st_size, "modified": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat()})
        return {"directory": str(self.root), "total": len(files), "files": files[offset:offset+limit]}

    def save(self, name: str, root: Table, info: dict[str, str] | None = None,
             revision: int = 4, overwrite: bool = False) -> dict:
        path = self.path(name)
        details = summary(root)
        policy_result = self.policy.check(root)
        now = datetime.now().astimezone()
        metadata = {"name": "adv2mcp", "date": now.strftime("%d %B %Y"),
                    "time": now.strftime("%I:%M %p"), "timezone": now.strftime("%z")}
        metadata.update(info or {})
        encoded = encode(root, metadata, revision)
        # Re-read and validate the exact bytes before touching the output.
        restored, _ = decode(encoded)
        validate_dupe(restored)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            raise FileExistsError(f"Already exists: {name}; choose another name or overwrite=true")
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".adv2mcp-", suffix=".tmp", delete=False) as f:
            temporary = Path(f.name)
            try:
                f.write(encoded)
                f.flush()
                os.fsync(f.fileno())
            except BaseException:
                f.close()
                temporary.unlink(missing_ok=True)
                raise
        try:
            if overwrite:
                # Preserve the original bytes in a timestamped backup.
                if path.exists():
                    backup = path.with_name(path.name + now.strftime(".%Y%m%d-%H%M%S-%f.bak"))
                    with path.open("rb") as source, backup.open("xb") as dest:
                        import shutil
                        shutil.copyfileobj(source, dest)
                os.replace(temporary, path)
            else:
                # Hard-link publication is atomic and refuses an existing target.
                os.link(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)
        return {"name": path.relative_to(self.root).as_posix(), "path": str(path),
                "bytes": len(encoded), "revision": revision, "prop_policy": policy_result, **details}

