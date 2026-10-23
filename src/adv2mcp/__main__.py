from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .build import BuildSpec, make_build, summary
from .codec import from_document, to_document
from .storage import DEFAULT_DUPE_DIR, DupeStore


def main() -> None:
    parser = argparse.ArgumentParser(description="AdvDupe2 MCP server and local file tools")
    parser.add_argument("--dupe-dir", type=Path, default=None)
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("serve", help="Run the MCP server over stdio (default)")
    sub.add_parser("list", help="List duplication files")
    props = sub.add_parser("import-props", help="Import literal Props/NewProps/Whiteprop lists from a Lua/text file")
    props.add_argument("input", type=Path)
    props.add_argument("--tables", nargs="+", default=["Props", "NewProps", "Whiteprop"])
    props.add_argument("--server", default=None)
    props.add_argument("--profile", type=Path, default=None)
    inspect = sub.add_parser("inspect", help="Summarize a .txt duplication")
    inspect.add_argument("name")
    export = sub.add_parser("decode", help="Export lossless JSON")
    export.add_argument("name")
    export.add_argument("output", type=Path)
    for command, help_text in (("encode", "Import lossless JSON"), ("build", "Create a dupe from a BuildSpec JSON file")):
        cmd = sub.add_parser(command, help=help_text)
        cmd.add_argument("input", type=Path)
        cmd.add_argument("name")
        cmd.add_argument("--revision", type=int, choices=(4, 5), default=None)
        cmd.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    try:
        if args.command in (None, "serve"):
            from .server import create_server
            create_server(args.dupe_dir).run(transport="stdio")
            return
        import os
        store = DupeStore(args.dupe_dir or Path(os.environ.get("ADV2MCP_DUPE_DIR", str(DEFAULT_DUPE_DIR))))
        if args.command == "import-props":
            from .profile_import import import_profile
            result = import_profile(args.input, args.profile or store.policy.path, tuple(args.tables), args.server)
        elif args.command == "list":
            result = store.list()
        elif args.command == "inspect":
            root, info = store.read(args.name)
            result = {"info": info, **summary(root)}
        elif args.command == "decode":
            root, info = store.read(args.name)
            with args.output.open("x", encoding="utf-8") as output:
                json.dump(to_document(root, info), output, ensure_ascii=False, indent=2, allow_nan=False)
                output.write("\n")
            result = {"output": str(args.output.resolve())}
        else:
            document = json.loads(args.input.read_text(encoding="utf-8-sig"))
            if args.command == "build":
                root, info = make_build(BuildSpec.model_validate(document)), {}
            else:
                root, info = from_document(document)
            revision = args.revision or int(info.get("revision", os.environ.get("ADV2MCP_REVISION", "4")))
            result = store.save(args.name, root, info, revision, args.overwrite)
        print(json.dumps(result, ensure_ascii=True, indent=2, allow_nan=False))
    except (ValueError, OSError) as exc:
        print(f"adv2mcp: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
