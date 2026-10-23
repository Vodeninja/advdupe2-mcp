"""MCP stdio entrypoint. stdout is reserved exclusively for MCP messages."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Any, Literal

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from .build import BuildSpec, Triple, make_build, summary, transform
from .codec import from_document, to_document
from .models import ModelCatalog
from .storage import DEFAULT_DUPE_DIR, DupeStore

READ = {"readOnlyHint": True, "destructiveHint": False}


def create_server(dupe_dir: Path | None = None) -> FastMCP:
    store = DupeStore(dupe_dir or Path(os.environ.get("ADV2MCP_DUPE_DIR", str(DEFAULT_DUPE_DIR))))
    game_dir = Path(os.environ.get("ADV2MCP_GAME_DIR", str(store.root.parent.parent))).resolve()
    catalog = ModelCatalog(game_dir)
    default_revision = int(os.environ.get("ADV2MCP_REVISION", "4"))
    if default_revision not in (4, 5):
        raise ValueError("ADV2MCP_REVISION must be 4 or 5")
    mcp = FastMCP("adv2mcp", instructions=(
        "Create Garry's Mod builds as Advanced Duplicator 2 files. First search_models and model_info "
        "to select model paths and hull dimensions. Construct a BuildSpec and call create_build. "
        "Use preview_only=true to validate without saving. Coordinates are Source units; pos is a model origin; "
        "angle is [pitch,yaw,roll] in degrees. Set ground_z for the ground plane. Props are frozen by default. "
        "weld_to_head connects the entire build for later copying. Files are written under the configured "
        "advdupe2 directory, then the user loads them with AdvDupe2 in-game. Existing files require overwrite=true "
        "and receive a backup. Use read_dupe/write_dupe for lossless edits, including addon fields. "
        "Search defaults to server-allowed props. A server prop profile is required for saving by default; "
        "get_prop_policy explains how to import a server list or export it from the game. "
        "No in-game spawning, Lua execution or network access is provided."
    ))

    @mcp.tool(annotations=READ)
    def get_status() -> dict[str, Any]:
        """Show configured game/dupe paths, format versions and filesystem availability."""
        return {"dupe_directory": str(store.root), "directory_exists": store.root.is_dir(),
                "game_directory": str(game_dir), "game_directory_exists": game_dir.is_dir(),
                "read_revisions": [4, 5], "default_write_revision": default_revision,
                "transport": "stdio", "spawns_in_game": False, "prop_policy": store.policy.status()}

    @mcp.tool(annotations=READ)
    def get_prop_policy() -> dict[str, Any]:
        """Show the server allowed-prop profile, reloaded on each call. Missing profiles block writes. Never infer server permission from local installation or a screenshot."""
        return {**store.policy.status(), "export_command": "adv2mcp_export_props",
                "import_command": "adv2mcp import-props FILE",
                "custom_tab_command": "adv2mcp_capture_props",
                "capture_instructions": "Run capture, close console, hold Q and select an Allowed props tab within 5 seconds. Repeat for each allowed tab. Profiles merge only for the same server."}

    @mcp.tool(annotations=READ)
    def list_dupes(query: str = "", limit: Annotated[int, Field(ge=1, le=500)] = 100,
                   offset: Annotated[int, Field(ge=0)] = 0) -> dict[str, Any]:
        """List .txt duplications recursively, filtered by filename, without decoding every file."""
        return store.list(query, limit, offset)

    @mcp.tool(annotations=READ)
    def inspect_dupe(name: str, offset: Annotated[int, Field(ge=0)] = 0,
                     limit: Annotated[int, Field(ge=1, le=500)] = 100) -> dict[str, Any]:
        """Read metadata, model counts and paginated positions/angles from an existing dupe."""
        root, info = store.read(name)
        entities = root.get("Entities")
        rows = []
        for index, ent in entities.entries[offset:offset+limit]:
            bone = ent.get("PhysicsObjects").get(0)
            pos, angle = bone.get("Pos"), bone.get("Angle")
            rows.append({"id": index, "model": ent.get("Model"), "class": ent.get("Class"),
                         "pos": [pos.x, pos.y, pos.z], "angle": [angle.p, angle.y, angle.r],
                         "frozen": not bool(bone.get("Frozen", False))})
        return {"name": name, "info": info, **summary(root), "entities": rows, "offset": offset}

    @mcp.tool(annotations=READ)
    def read_dupe(name: str) -> dict[str, Any]:
        """Return a lossless adv2mcp-json-v1 document. Tables have typed keys and IDs; vectors/angles are tagged. Large dupes may produce large responses; inspect_dupe is paginated."""
        root, info = store.read(name)
        return to_document(root, info)

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": True})
    def write_dupe(name: str, document: dict, overwrite: bool = False,
                   revision: Literal[4, 5] | None = None) -> dict[str, Any]:
        """Save a lossless document returned by read_dupe, preserving unknown addon data. Revision defaults to the source document or the server default. Overwrites create backups."""
        root, info = from_document(document)
        output_revision = revision or int(info.get("revision", default_revision))
        return store.save(name, root, info, output_revision, overwrite)

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": True})
    def create_build(name: str, build: BuildSpec, overwrite: bool = False,
                     revision: Literal[4, 5] | None = None, preview_only: bool = False) -> dict[str, Any]:
        """Build prop_physics entities with positions, angles, color, material and Weld/NoCollide. Use weld_to_head for a connected contraption. preview_only validates and reports counts without writing. Unknown models are reported, since Workshop GMA/external mounts may supply them."""
        root = make_build(build)
        known = catalog.all()
        missing = sorted({p.model for p in build.props if p.model not in known})
        if preview_only:
            result = {"name": name, "preview_only": True, "prop_policy": store.policy.check(root), **summary(root)}
        else:
            result = store.save(name, root, revision=revision or default_revision, overwrite=overwrite)
        result["models_not_in_catalog"] = missing
        return result

    @mcp.tool(annotations={"readOnlyHint": False, "destructiveHint": True})
    def transform_dupe(source: str, destination: str, offset: Triple = (0, 0, 0),
                       yaw: Annotated[float, Field(allow_inf_nan=False)] = 0,
                       overwrite: bool = False, revision: Literal[4, 5] | None = None) -> dict[str, Any]:
        """Rotate simple prop builds around the copy origin, then translate their local positions. Supports single-body prop_physics with Weld/NoCollide only. Saves a new file unless explicitly overwriting."""
        root, info = store.read(source)
        transform(root, offset, yaw)
        return store.save(destination, root, info, revision or int(info["revision"]), overwrite)

    @mcp.tool(annotations=READ)
    def search_models(query: str = "", limit: Annotated[int, Field(ge=1, le=500)] = 50,
                      offset: Annotated[int, Field(ge=0)] = 0, refresh: bool = False,
                      allowed_only: bool = True) -> dict[str, Any]:
        """Find server-allowed models by default (all query words must match). allowed_only=false searches installed models without implying permission. Captured profiles can include Workshop models absent from the local VPK index."""
        if refresh:
            catalog.refresh()
        if allowed_only:
            return store.policy.search(query, limit, offset)
        return catalog.search(query, limit, offset)

    @mcp.tool(annotations=READ)
    def model_info(model: str) -> dict[str, Any]:
        """Read unrotated MDL hull bounds and dimensions in Source units for accurate prop placement."""
        from .policy import normalize
        model = normalize(model)
        profile = store.policy.load()
        exported = profile["models"].get(model) if profile else None
        if exported and "hull_min" in exported and "hull_max" in exported:
            lo, hi = exported["hull_min"], exported["hull_max"]
            if isinstance(lo, list) and isinstance(hi, list) and len(lo) == len(hi) == 3:
                return {"model": model, "hull_min": lo, "hull_max": hi,
                        "size": [hi[i]-lo[i] for i in range(3)], "source": "GMod client export",
                        "allowed": True, "available": exported.get("available"),
                        "note": "Model bounds exported by the client; collision mesh may differ."}
        result = catalog.info(model)
        result["allowed"] = model in profile["models"] if profile else None
        return result

    @mcp.resource("adv2mcp://build-schema")
    def build_schema() -> str:
        """JSON Schema for the build parameter of create_build."""
        return json.dumps(BuildSpec.model_json_schema(), ensure_ascii=False)

    @mcp.prompt()
    def design_build(description: str) -> str:
        """Plan and save a Garry's Mod construction using installed models."""
        return (f"Create this Garry's Mod build: {description}\n"
                "Use search_models and model_info. Design in Source units with Z up and angles [pitch,yaw,roll]. "
                "Account for hull_min/hull_max when placing models on ground_z. Validate using create_build "
                "with preview_only=true, then save a .txt file with the same tool. Explain how to load it in AdvDupe2.")

    return mcp


def run() -> None:
    create_server().run(transport="stdio")

