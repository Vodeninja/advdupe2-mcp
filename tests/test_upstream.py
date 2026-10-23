"""Interoperability with the UNMODIFIED upstream Lua codec, not our own reader.

GMod Vector/Angle, file and util.Compress APIs are stubbed in a Lua 5.4 runtime.
This checks serialization and CheckValidDupe; it does not run the game's native
LZMA implementation, model spawning or physics engine.
"""

import lzma
from pathlib import Path

import pytest
from lupa import LuaRuntime

from adv2mcp.build import summary
from adv2mcp.codec import decode, encode

FIXTURES = Path(__file__).parent / "fixtures"


def upstream():
    lua = LuaRuntime(encoding=None, unpack_returned_tuples=True)
    lua.globals()[b"py_compress"] = lambda data: lzma.compress(data, format=lzma.FORMAT_ALONE)
    def decompress(data, limit):
        try:
            return lzma.decompress(data, format=lzma.FORMAT_ALONE)
        except lzma.LZMAError:
            # liblzma <=5.2.5 lacks the SDK's known-size + EOPM support.
            return lzma.decompress(data[:5] + b"\xff" * 8 + data[13:], format=lzma.FORMAT_ALONE)
    lua.globals()[b"py_decompress"] = decompress
    lua.execute((FIXTURES / "gmod_stubs.lua").read_bytes())
    lua.execute((FIXTURES / "upstream_sh_codec.lua").read_bytes())
    return lua


@pytest.mark.parametrize("revision", [4, 5])
def test_python_writer_decodes_in_upstream(revision):
    lua = upstream()
    root, _ = decode((FIXTURES / "single_prop_v4.txt").read_bytes())
    data = encode(root, {"name": "Тест", "empty": ""}, revision=revision)
    ok, dupe, info = lua.globals()[b"AdvDupe2"][b"Decode"](data)
    assert ok, dupe
    assert info[b"revision"] == revision
    index = dupe[b"HeadEnt"][b"Index"]
    assert dupe[b"Entities"][index][b"Model"] == b"models/hunter/blocks/cube05x05x05.mdl"


def test_upstream_writer_decodes_in_python():
    lua = upstream()
    lua.execute(b'''
        local shared = {value = "shared"}
        local other = {value = "after reference"}
        local dupe = {
          HeadEnt = {Index=1, Pos=Vector(0,0,12), Z=12},
          Entities = {[1] = {Class="prop_physics", Model="models/a.mdl",
            PhysicsObjects={[0]={Pos=Vector(0,0,0), Angle=Angle(0,90,0)}}}},
          Constraints={}, Description="", Binary="\\255\\0\\254",
          refs={shared, shared, other, other},
        }
        dupe.self = dupe
        AdvDupe2.Encode(dupe, {name="upstream"}, function(data) encoded = data end)
    ''')
    root, info = decode(lua.globals()[b"encoded"])
    assert info["revision"] == "5"
    assert summary(root)["entity_count"] == 1
    assert root.get("Description") == ""
    assert root.get("Binary") == b"\xff\0\xfe"
    assert root.get("self") is root
    refs = root.get("refs")
    assert refs.get(1) is refs.get(2)
    assert refs.get(3) is refs.get(4)

