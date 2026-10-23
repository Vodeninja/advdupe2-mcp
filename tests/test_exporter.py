import json
from pathlib import Path

from lupa import LuaRuntime

SCRIPT = Path(__file__).parents[1] / "gmod_addon/adv2mcp_export/lua/autorun/client/adv2mcp_export.lua"


def exporter():
    lua = LuaRuntime(unpack_returned_tuples=True)
    lua.globals().py_json_encode = lambda value, pretty: json.dumps(lua_to_python(value))
    lua.globals().py_json_decode = lambda value: lua.table_from(json.loads(value), recursive=True) if value else None
    lua.execute('''
        function isstring(v) return type(v)=="string" end
        function istable(v) return type(v)=="table" end
        function isvector(v) return type(v)=="table" and v.x~=nil end
        function IsValid(v) return type(v)=="table" end
        string.Replace = function(s,a,b) return s:gsub(a,b) end
        table.Count = function(t) local n=0 for _ in pairs(t) do n=n+1 end return n end
        table.GetKeys = function(t) local r={} for k in pairs(t) do r[#r+1]=k end return r end
        math.Clamp = function(v,lo,hi) return math.max(lo,math.min(hi,v)) end
        util = {TableToJSON=py_json_encode, JSONToTable=py_json_decode,
          IsValidModel=function(m) return m~="models/missing.mdl" end,
          GetModelBounds=function(m) return {x=-1,y=-2,z=-3},{x=1,y=2,z=3} end}
        data = {}
        file = {Read=function(p) return data[p] end, Write=function(p,v) data[p]=v end,
          Exists=function(p) return data[p]~=nil end, CreateDir=function() end}
        game = {GetIPAddress=function() return "test-server" end}
        commands = {}
        concommand = {Add=function(name,fn) commands[name]=fn end}
        timer = {Simple=function(delay,fn) pending=fn end}
        spawnmenu = {GetPropTable=function() return categories or {} end,
          GetCustomPropTable=function() return {} end}
        vgui = {GetWorldPanel=function() return world end}
        function panel(children)
          return {GetChildren=function() return children or {} end, IsVisible=function() return true end}
        end
        function icon(model)
          local p=panel(); p.GetModelName=function() return model end; return p
        end
        function sheet(name, contents)
          local tab={GetText=function() return name end}
          local content=panel(contents)
          local p=panel({content}); p.Items={{Tab=tab,Panel=content}}
          p.GetActiveTab=function() return tab end
          return p
        end
        print=function() end
    ''')
    lua.execute(SCRIPT.read_text(encoding="utf-8"))
    return lua


def lua_to_python(value):
    if hasattr(value, "items"):
        items = list(value.items())
        if items and all(type(k) is int for k, _ in items):
            return [lua_to_python(value[i]) for i in range(1, len(items)+1)]
        return {k: lua_to_python(v) for k, v in items}
    return value


def test_only_allowed_categories_and_missing_model_flags():
    lua = exporter()
    lua.execute('''categories = {
      {name="Разрешенные пропы",contents={{type="model",model="models/door.mdl"},{type="model",model="models/missing.mdl"}}},
      {name="History",contents={{type="model",model="models/disallowed.mdl"}}}
    }; commands.adv2mcp_export_props()''')
    profile = json.loads(lua.globals().data["advdupe2/adv2mcp/server-props.json"])
    assert {v["model"] for v in profile["models"]} == {"models/door.mdl", "models/missing.mdl"}
    assert next(v for v in profile["models"] if v["model"] == "models/missing.mdl")["available"] is False


def test_custom_tab_capture_and_merge():
    lua = exporter()
    lua.execute('''
      world=panel({sheet("Разрешенные пропы", {icon("models/one.mdl")}),
                   sheet("History", {icon("models/forbidden.mdl")})})
      commands.adv2mcp_capture_props(nil,nil,{}); pending()
      world=panel({sheet("Разрешенные пропы 2", {icon("models/two.mdl")})})
      commands.adv2mcp_capture_props(nil,nil,{}); pending()
    ''')
    profile = json.loads(lua.globals().data["advdupe2/adv2mcp/server-props.json"])
    assert [entry["model"] for entry in profile["models"]] == ["models/one.mdl", "models/two.mdl"]

