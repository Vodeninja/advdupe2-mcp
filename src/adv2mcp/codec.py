"""AD2F revision 4/5 serialization, based on wiremod/advdupe2 sh_codec.lua.

Tables retain Lua key types, table identity and revision 5 cycles. This module
does not evaluate Lua or execute anything from a duplication file.
"""

from __future__ import annotations

import base64
import binascii
import lzma
import math
import struct
from dataclasses import dataclass, field
from typing import Any

MAX_SIZE = 32_000_000
MAX_DEPTH = 128
CHECK = "\r\n\t\n"


class CodecError(ValueError):
    pass


@dataclass(frozen=True)
class Vector:
    x: float = 0
    y: float = 0
    z: float = 0


@dataclass(frozen=True)
class Angle:
    p: float = 0
    y: float = 0
    r: float = 0


@dataclass(eq=False)
class Table:
    # A list of pairs also preserves Lua's distinction between true and 1.
    entries: list[tuple[Any, Any]] = field(default_factory=list)

    def get(self, key: Any, default: Any = None) -> Any:
        for k, v in self.entries:
            if type(k) is type(key) and k == key:
                return v
        return default

    def set(self, key: Any, value: Any) -> None:
        for i, (k, _) in enumerate(self.entries):
            if type(k) is type(key) and k == key:
                self.entries[i] = (key, value)
                return
        self.entries.append((key, value))

    def __len__(self) -> int:
        return len(self.entries)


def table(value: Any) -> Any:
    """Convert a simple Python tree to Lua tables; explicit Table stays intact."""
    if isinstance(value, dict):
        return Table([(k, table(v)) for k, v in value.items() if v is not None])
    if isinstance(value, (list, tuple)):
        return Table([(i, table(v)) for i, v in enumerate(value, 1)])
    return value


class Reader:
    def __init__(self, data: bytes, revision: int):
        self.data, self.revision, self.pos = data, revision, 0
        self.references: dict[int, Table] = {}
        self.counter = 0

    def take(self, n: int) -> bytes:
        if n < 0 or self.pos + n > len(self.data):
            raise CodecError(f"Unexpected EOF at offset {self.pos}")
        result = self.data[self.pos : self.pos + n]
        self.pos += n
        return result

    def number(self) -> float | int:
        value = struct.unpack("<d", self.take(8))[0]
        if not math.isfinite(value):
            raise CodecError("Non-finite number in duplication")
        return int(value) if value.is_integer() else value

    def read(self, depth: int = 0) -> Any:
        if depth > MAX_DEPTH:
            raise CodecError("Table nesting exceeds limit")
        tag = self.take(1)[0]
        end = 246 if self.revision == 5 else 0
        if tag == end:
            return None
        if tag in (255, 254):
            result = Table()
            self.counter += 1
            ref = self.counter
            if self.revision == 5:
                self.references[ref] = result
            i = 1
            while True:
                k = self.read(depth + 1)
                if k is None:
                    break
                if tag == 254:
                    result.entries.append((i, k))
                    i += 1
                else:
                    v = self.read(depth + 1)
                    if v is None:
                        raise CodecError("Nil table value")
                    result.entries.append((k, v))
            self.references[ref] = result
            return result
        if tag in (253, 252):
            return tag == 253
        if tag == 251:
            return self.number()
        if tag in (250, 249):
            cls = Vector if tag == 250 else Angle
            return cls(self.number(), self.number(), self.number())
        if tag == 247:
            ref = struct.unpack("<H", self.take(2))[0]
            if self.revision == 4:
                self.counter += 1  # A historical v4 decoder quirk.
            if ref not in self.references:
                raise CodecError(f"Invalid/forward table reference {ref}")
            return self.references[ref]
        if tag == 248:
            if self.revision == 5:
                raw = self.take(struct.unpack("<I", self.take(4))[0])
            else:
                endpos = self.data.find(b"\0", self.pos)
                if endpos < 0:
                    raise CodecError("Unterminated revision 4 string")
                raw = self.take(endpos - self.pos)
                self.take(1)
        elif tag <= (245 if self.revision == 5 else 246):
            raw = self.take(tag)
        else:
            raise CodecError(f"Unknown type tag {tag}")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            return raw


class Writer:
    def __init__(self, revision: int):
        self.revision = revision
        self.data = bytearray()
        self.references: dict[int, int] = {}
        self.active: set[int] = set()
        self.counter = 0

    def append(self, data: bytes) -> None:
        if len(self.data) + len(data) > MAX_SIZE:
            raise CodecError("Uncompressed duplication exceeds 32 MB")
        self.data.extend(data)

    def write(self, value: Any, depth: int = 0) -> None:
        if depth > MAX_DEPTH:
            raise CodecError("Table nesting exceeds limit")
        if isinstance(value, Table):
            ident = id(value)
            if ident in self.references:
                if self.revision == 4:
                    if ident in self.active:
                        raise CodecError("Cycles require revision 5")
                    self.counter += 1
                self.append(b"\xf7" + struct.pack("<H", self.references[ident]))
                return
            self.counter += 1
            if self.counter > 32767:
                raise CodecError("Too many table references (maximum 32767)")
            self.references[ident] = self.counter
            self.active.add(ident)
            array = all(type(k) is int and k == i for i, (k, _) in enumerate(value.entries, 1))
            self.append(b"\xfe" if array else b"\xff")
            for k, v in value.entries:
                if k is None or v is None:
                    raise CodecError("Lua table entries cannot contain null")
                if not array:
                    self.write(k, depth + 1)
                self.write(v, depth + 1)
            self.append(b"\xf6" if self.revision == 5 else b"\0")
            self.active.remove(ident)
        elif isinstance(value, bool):
            self.append(b"\xfd" if value else b"\xfc")
        elif isinstance(value, (float, int)):
            try:
                number = float(value)
            except OverflowError as exc:
                raise CodecError("Number outside float64 range") from exc
            if not math.isfinite(number) or (isinstance(value, int) and int(number) != value):
                raise CodecError("Number is non-finite or cannot be represented exactly")
            self.append(b"\xfb" + struct.pack("<d", number))
        elif isinstance(value, (Vector, Angle)):
            components = (value.x, value.y, value.z) if isinstance(value, Vector) else (value.p, value.y, value.r)
            if not all(math.isfinite(v) for v in components):
                raise CodecError("Invalid vector/angle")
            self.append(bytes([250 if isinstance(value, Vector) else 249]) + struct.pack("<ddd", *components))
        elif isinstance(value, (str, bytes)):
            raw = value.encode("utf-8") if isinstance(value, str) else value
            short = len(raw) < (246 if self.revision == 5 else 247)
            if short and (raw or self.revision == 5):
                self.append(bytes([len(raw)]) + raw)
            elif self.revision == 5:
                self.append(b"\xf8" + struct.pack("<I", len(raw)) + raw)
            else:
                if b"\0" in raw:
                    raise CodecError("Long strings containing NUL require revision 5")
                self.append(b"\xf8" + raw + b"\0")
        else:
            raise CodecError(f"Unsupported value type: {type(value).__name__}")


def decode(data: bytes) -> tuple[Table, dict[str, str]]:
    if len(data) > MAX_SIZE:
        raise CodecError("File exceeds 32 MB")
    if len(data) < 7 or data[:4] != b"AD2F":
        raise CodecError("Not an AD2F file (AdvDupe1 and revisions 1–3 are unsupported)")
    revision = data[4]
    if revision not in (4, 5):
        raise CodecError(f"Unsupported AD2F revision {revision}; expected 4 or 5")
    end = data.find(b"\x02", 6, min(len(data), 65536))
    if data[5:6] != b"\n" or end < 0 or data[end + 1 : end + 2] != b"\n":
        raise CodecError("Malformed AD2F header")
    fields = data[6:end].split(b"\x01")
    if fields[-1] != b"" or len(fields) % 2 != 1:
        raise CodecError("Malformed metadata")
    info = {fields[i].decode("utf-8", "replace"): fields[i+1].decode("utf-8", "replace") for i in range(0, len(fields)-1, 2)}
    if info.get("check") != CHECK:
        raise CodecError("Newline check failed; file was changed by a text editor/transfer")
    body = data[end + 2:]
    if len(body) < 13:
        raise CodecError("Missing LZMA header")
    declared = struct.unpack_from("<Q", body, 5)[0]
    if declared != 0xFFFFFFFFFFFFFFFF and declared > MAX_SIZE:
        raise CodecError("Declared uncompressed size exceeds 32 MB")
    try:
        decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=128 * 1024 * 1024)
        raw = decompressor.decompress(body, max_length=MAX_SIZE + 1)
    except lzma.LZMAError as exc:
        # liblzma <=5.2.5 rejects known size + EOPM, although the LZMA SDK
        # (used by GMod) accepts it. Retry with unknown size, then check size.
        try:
            decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE, memlimit=128 * 1024 * 1024)
            raw = decompressor.decompress(body[:5] + b"\xff" * 8 + body[13:], max_length=MAX_SIZE + 1)
        except lzma.LZMAError:
            raise CodecError(f"Invalid LZMA stream: {exc}") from exc
    if len(raw) > MAX_SIZE:
        raise CodecError("Uncompressed duplication exceeds 32 MB")
    if not decompressor.eof or decompressor.unused_data:
        raise CodecError("Incomplete LZMA stream or trailing data")
    if declared != 0xFFFFFFFFFFFFFFFF and len(raw) != declared:
        raise CodecError("LZMA uncompressed size mismatch")
    reader = Reader(raw, revision)
    result = reader.read()
    if not isinstance(result, Table) or reader.pos != len(raw):
        raise CodecError("Expected one root Lua table, without trailing data")
    info["revision"] = str(revision)
    return result, info


def encode(root: Table, info: dict[str, str] | None = None, revision: int = 4) -> bytes:
    if revision not in (4, 5):
        raise CodecError("Writer supports revisions 4 and 5")
    writer = Writer(revision)
    writer.write(root)
    raw = bytes(writer.data)
    compressed = lzma.compress(raw, format=lzma.FORMAT_ALONE, filters=[{"id": lzma.FILTER_LZMA1, "dict_size": 65536, "lc": 3, "lp": 0, "pb": 2}])
    # GMod expects the real size, not Python's all-ones 'unknown size'.
    compressed = compressed[:5] + struct.pack("<Q", len(raw)) + compressed[13:]
    metadata = {k: str(v) for k, v in (info or {}).items() if k not in ("revision", "size", "check")}
    metadata.update(check=CHECK, size=str(len(compressed)))
    fields = bytearray()
    for k, v in metadata.items():
        if any(c in k or c in v for c in ("\x00", "\x01", "\x02")):
            raise CodecError("Metadata contains reserved control characters")
        fields.extend(k.encode("utf-8") + b"\x01" + v.encode("utf-8") + b"\x01")
    if len(fields) > 65000:
        raise CodecError("Metadata is too large")
    result = b"AD2F" + bytes([revision]) + b"\n" + fields + b"\x02\n" + compressed
    if len(result) > MAX_SIZE:
        raise CodecError("Encoded file exceeds 32 MB")
    return result


def to_document(root: Table, info: dict[str, str]) -> dict:
    """Lossless JSON graph; numeric keys, binary strings and cycles survive."""
    seen: dict[int, int] = {}

    def visit(value: Any, depth: int = 0) -> Any:
        if depth > MAX_DEPTH:
            raise CodecError("JSON nesting exceeds limit")
        if isinstance(value, Table):
            if id(value) in seen:
                return {"$ref": seen[id(value)]}
            ref = len(seen) + 1
            seen[id(value)] = ref
            return {"$type": "table", "id": ref, "entries": [[visit(k, depth+1), visit(v, depth+1)] for k, v in value.entries]}
        if isinstance(value, Vector):
            return {"$type": "vector", "x": value.x, "y": value.y, "z": value.z}
        if isinstance(value, Angle):
            return {"$type": "angle", "p": value.p, "y": value.y, "r": value.r}
        if isinstance(value, bytes):
            return {"$type": "bytes", "base64": base64.b64encode(value).decode("ascii")}
        return value

    return {"format": "adv2mcp-json-v1", "info": info, "dupe": visit(root)}


def from_document(document: dict) -> tuple[Table, dict[str, str]]:
    if document.get("format") != "adv2mcp-json-v1":
        raise CodecError("Expected format adv2mcp-json-v1; use read_dupe to obtain it")
    references: dict[int, Table] = {}

    def visit(value: Any, depth: int = 0) -> Any:
        if depth > MAX_DEPTH:
            raise CodecError("JSON nesting exceeds limit")
        if isinstance(value, dict):
            if "$ref" in value:
                if value["$ref"] not in references:
                    raise CodecError("Unknown/forward JSON table reference")
                return references[value["$ref"]]
            kind = value.get("$type")
            if kind == "table":
                ref = value["id"]
                if type(ref) is not int or ref <= 0 or ref in references:
                    raise CodecError("Invalid/duplicate table ID")
                result = Table()
                references[ref] = result
                for k, v in value["entries"]:
                    key, item = visit(k, depth+1), visit(v, depth+1)
                    if key is None or item is None:
                        raise CodecError("Null table key/value")
                    result.entries.append((key, item))
                return result
            if kind == "vector":
                return Vector(*(float(value[k]) for k in ("x", "y", "z")))
            if kind == "angle":
                return Angle(*(float(value[k]) for k in ("p", "y", "r")))
            if kind == "bytes":
                try:
                    return base64.b64decode(value["base64"], validate=True)
                except (binascii.Error, ValueError) as exc:
                    raise CodecError("Invalid base64") from exc
            raise CodecError(f"Unknown JSON value type {kind}")
        if isinstance(value, (str, bool, int, float)):
            return value
        raise CodecError("Invalid JSON value")

    try:
        root = visit(document["dupe"])
        info = document.get("info", {})
        if not isinstance(root, Table) or not isinstance(info, dict):
            raise CodecError("Expected dupe table and info object")
        return root, {str(k): str(v) for k, v in info.items()}
    except (KeyError, TypeError) as exc:
        raise CodecError(f"Malformed JSON document: {exc}") from exc
