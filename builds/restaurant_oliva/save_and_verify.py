import asyncio
import json
import os
import runpy
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

async def main():
    cfg = json.loads((ROOT / 'mcp.config.json').read_text())['mcpServers']['adv2mcp']
    params = StdioServerParameters(command=cfg['command'], args=cfg['args'], env={**os.environ, **cfg['env']})
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as client:
            await client.initialize()
            result = await client.call_tool('create_build', {'name': 'mcp/restaurant_oliva.txt', 'build': json.loads((OUT / 'build.json').read_text())})
            assert not result.isError, result.content
            (OUT / 'saved.json').write_text(json.dumps(result.structuredContent, ensure_ascii=False, indent=2), encoding='utf-8')
    path = Path(cfg['env']['ADV2MCP_DUPE_DIR']) / 'mcp/restaurant_oliva.txt'
    lua = runpy.run_path(str(ROOT / 'tests/test_upstream.py'))['upstream']()
    ok, dupe, info = lua.globals()[b'AdvDupe2'][b'Decode'](path.read_bytes())
    assert ok, info
    count = len(dupe[b'Entities'])
    assert count == 218 and count <= 250
    report = {'upstream_decode': True, 'props': count, 'path': str(path), 'bytes': path.stat().st_size}
    (OUT / 'validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))

asyncio.run(main())
