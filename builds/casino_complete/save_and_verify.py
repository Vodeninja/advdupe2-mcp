import asyncio
import json
import os
import runpy
from pathlib import Path
from mcp import ClientSession,StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent

async def main():
    cfg=json.loads((ROOT/'mcp.config.json').read_text())['mcpServers']['adv2mcp']
    build=json.loads((OUT/'build.json').read_text())
    interior={**build,'props':build['props'][100:],'head_id':101,
        'description':'WINSTAR INTERIOR ONLY | 150 props | align front edge behind the existing casino entrance'}
    (OUT/'interior_build.json').write_text(json.dumps(interior,ensure_ascii=False,indent=2),encoding='utf-8')
    params=StdioServerParameters(command=cfg['command'],args=cfg['args'],env={**os.environ,**cfg['env']})
    results=[]
    lua=runpy.run_path(str(ROOT/'tests/test_upstream.py'))['upstream']()
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as client:
            await client.initialize()
            for name,spec,count in [('mcp/casino_complete_250.txt',build,250),('mcp/casino_interior_150.txt',interior,150)]:
                result=await client.call_tool('create_build',{'name':name,'build':spec,'overwrite':True})
                assert not result.isError,result.content
                path=Path(cfg['env']['ADV2MCP_DUPE_DIR'])/name
                ok,dupe,info=lua.globals()[b'AdvDupe2'][b'Decode'](path.read_bytes())
                assert ok,info
                entities=dupe[b'Entities']
                # The interior deliberately retains original IDs 101..250.
                actual=sum(1 for _ in entities.items())
                assert actual==count,(name,actual)
                results.append({'name':name,'props':actual,'upstream_decode':True,'path':str(path),'bytes':path.stat().st_size})
    (OUT/'validation.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False))

asyncio.run(main())
