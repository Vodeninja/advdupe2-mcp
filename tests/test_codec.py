import lzma
import struct
from pathlib import Path

import pytest

from adv2mcp.build import BuildSpec, make_build, summary
from adv2mcp.codec import Angle, CodecError, Table, Vector, decode, encode, from_document, table, to_document

FIXTURES = Path(__file__).parent / "fixtures"


def test_real_revision4_fixture():
    root, info = decode((FIXTURES / "single_prop_v4.txt").read_bytes())
    assert info["revision"] == "4"
    assert summary(root)["models"] == {"models/hunter/blocks/cube05x05x05.mdl": 1}
    assert root.get("HeadEnt").get("Index") == 3894
    assert root.get("Entities").get(3894).get("PhysicsObjects").get(0).get("Angle").y == pytest.approx(16.28480339050293)


@pytest.mark.parametrize("revision", [4, 5])
def test_values_and_reference_numbering(revision):
    shared = table({"x": "shared"})
    other = table({"v": 123})
    root = table({"empty": "", "long": "Ж" * 400, "binary": b"\xff\xfe\0", "zero": 0,
                  "vector": Vector(1, 2, -3), "angle": Angle(10, 20, 30), "false": False,
                  "shared1": shared, "shared2": shared, "other1": other, "other2": other})
    decoded, _ = decode(encode(root, revision=revision))
    assert to_document(decoded, {}) == to_document(root, {})
    assert decoded.get("shared1") is decoded.get("shared2")
    assert decoded.get("other1") is decoded.get("other2")


def test_cycle_and_typed_keys_in_json():
    root = Table([(True, "bool"), (1, "number"), ("1", "string")])
    root.set("self", root)
    document = to_document(root, {})
    restored, _ = from_document(document)
    assert restored.get(True) == "bool"
    assert restored.get(1) == "number"
    assert restored.get("1") == "string"
    assert restored.get("self") is restored
    reread, _ = decode(encode(restored, revision=5))
    assert reread.get("self") is reread
    with pytest.raises(CodecError, match="Cycles"):
        encode(restored, revision=4)


def test_real_dupe_lossless_json_roundtrip():
    root, info = decode((FIXTURES / "single_prop_v4.txt").read_bytes())
    restored, restored_info = from_document(to_document(root, info))
    reread, _ = decode(encode(restored, restored_info, revision=4))
    assert to_document(root, {}) == to_document(reread, {})


@pytest.mark.parametrize("length", [0, 1, 245, 246, 247, 1024])
@pytest.mark.parametrize("revision", [4, 5])
def test_string_boundaries(length, revision):
    root = table({"str": "a" * length})
    reread, _ = decode(encode(root, revision=revision))
    assert reread.get("str") == "a" * length


def test_invalid_streams_and_limits():
    with pytest.raises(CodecError, match="Not an AD2F"):
        decode(b"not a dupe")
    data = encode(table({"hello": "world"}))
    with pytest.raises(CodecError, match="Newline check"):
        decode(data.replace(b"\r\n\t\n", b"\n\t\n"))
    with pytest.raises(CodecError):
        decode(data[:-5])
    start = data.index(b"\x02\n") + 2
    bad = bytearray(data)
    struct.pack_into("<Q", bad, start+5, 33_000_000)
    with pytest.raises(CodecError, match="exceeds 32 MB"):
        decode(bytes(bad))
    with pytest.raises(CodecError, match="Non-finite|non-finite"):
        encode(table({"nan": float("nan")}))


def test_lzma_has_concrete_size():
    root = make_build(BuildSpec(props=[{"id": 1, "model": "models/hunter/blocks/cube05x05x05.mdl"}]))
    data = encode(root)
    body = data[data.index(b"\x02\n") + 2:]
    raw = lzma.decompress(body[:5] + b"\xff" * 8 + body[13:], format=lzma.FORMAT_ALONE)
    assert struct.unpack_from("<Q", body, 5)[0] == len(raw)

