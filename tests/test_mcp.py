import asyncio
import json
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


def test_real_stdio_session(tmp_path):
    profile = tmp_path / "adv2mcp" / "server-props.json"
    profile.parent.mkdir()
    profile.write_text(json.dumps({"format": "adv2mcp-props-v1", "server": "test-server",
                                   "models": ["models/props_c17/door01_left.mdl"]}))

    async def check():
        params = StdioServerParameters(command=sys.executable, args=["-m", "adv2mcp"],
            env={**os.environ, "ADV2MCP_DUPE_DIR": str(tmp_path), "ADV2MCP_GAME_DIR": str(tmp_path / "game"),
                 "ADV2MCP_PROP_PROFILE": str(profile), "ADV2MCP_REQUIRE_ALLOWLIST": "1"})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                names = {tool.name for tool in (await client.list_tools()).tools}
                assert {"create_build", "read_dupe", "write_dupe", "search_models", "get_prop_policy"} <= names
                found = await client.call_tool("search_models", {"query": "door"})
                assert not found.isError
                assert found.structuredContent["models"] == ["models/props_c17/door01_left.mdl"]
                spec = {"props": [{"id": 1, "model": "models/props_c17/door01_left.mdl"}]}
                preview = await client.call_tool("create_build", {"name": "demo.txt", "build": spec, "preview_only": True})
                assert not preview.isError
                assert not (tmp_path / "demo.txt").exists()
                saved = await client.call_tool("create_build", {"name": "demo.txt", "build": spec})
                assert not saved.isError, saved.content
                inspected = await client.call_tool("inspect_dupe", {"name": "demo.txt"})
                assert inspected.structuredContent["entity_count"] == 1
                readback = await client.call_tool("read_dupe", {"name": "demo.txt"})
                copied = await client.call_tool("write_dupe", {"name": "copy.txt", "document": readback.structuredContent})
                assert not copied.isError, copied.content
                rejected = await client.call_tool("create_build", {"name": "bad.txt", "build": {"props": [{"id": 1, "model": "models/hunter/plates/plate2x2.mdl"}]}})
                assert rejected.isError
                assert not (tmp_path / "bad.txt").exists()
                duplicate = await client.call_tool("create_build", {"name": "demo.txt", "build": spec})
                assert duplicate.isError
                assert (await client.list_resources()).resources
                assert (await client.list_prompts()).prompts

    asyncio.run(check())

