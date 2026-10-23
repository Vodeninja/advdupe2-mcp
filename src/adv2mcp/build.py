"""Typed building specification and AD2 entity/constraint layout."""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .codec import Angle, CodecError, Table, Vector, table

Triple = tuple[float, float, float]


class SpecModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Prop(SpecModel):
    id: int = Field(ge=1, le=65535)
    model: str
    pos: Triple = (0, 0, 0)
    angle: Triple = (0, 0, 0)
    frozen: bool = True
    skin: int = Field(default=0, ge=0)
    color: tuple[int, int, int, int] | None = None
    material: str | None = None

    @field_validator("model")
    @classmethod
    def model_path(cls, value: str) -> str:
        value = value.replace("\\", "/").lower()
        if not re.fullmatch(r"models/[a-z0-9_ ./+()\-]+\.mdl", value) or ".." in value:
            raise ValueError("Expected relative models/... .mdl path without '..'")
        return value

    @field_validator("color")
    @classmethod
    def rgba(cls, value):
        if value is not None and any(n < 0 or n > 255 for n in value):
            raise ValueError("Color components must be 0..255")
        return value


class Constraint(SpecModel):
    type: Literal["Weld", "NoCollide"] = "Weld"
    ent1: int = Field(ge=1)
    ent2: int = Field(ge=1)
    force_limit: float = Field(default=0, ge=0)
    nocollide: bool = True


class BuildSpec(SpecModel):
    props: list[Prop] = Field(min_length=1, max_length=5000)
    constraints: list[Constraint] = Field(default_factory=list, max_length=20000)
    weld_to_head: bool = False
    head_id: int | None = Field(default=None, ge=1)
    # Coordinates describe model origins relative to the placement point.
    # ground_z is the ground plane in this same coordinate system.
    ground_z: float = 0
    description: str = "Created with adv2mcp"


def make_build(spec: BuildSpec) -> Table:
    ids = [prop.id for prop in spec.props]
    if len(set(ids)) != len(ids):
        raise ValueError("Prop IDs must be unique")
    head_id = spec.head_id or ids[0]
    if head_id not in ids:
        raise ValueError("head_id must refer to an existing prop")
    head_prop = next(p for p in spec.props if p.id == head_id)
    origin = head_prop.pos
    entities = {}
    for prop in spec.props:
        relative = Vector(*(v - o for v, o in zip(prop.pos, origin)))
        mods = {}
        if prop.color is not None:
            r, g, b, a = prop.color
            mods["colour"] = {"Color": {"r": r, "g": g, "b": b, "a": a}, "RenderMode": 0 if a == 255 else 1, "RenderFX": 0}
        if prop.material:
            mods["material"] = {"MaterialOverride": prop.material}
        entities[prop.id] = {
            "Class": "prop_physics", "Model": prop.model, "Skin": prop.skin,
            "CollisionGroup": 0,
            "PhysicsObjects": {0: {"Pos": relative, "Angle": Angle(*prop.angle),
                                     # AdvDupe2 stores moveability under this misleading name.
                                     "Frozen": not prop.frozen}},
            "EntityMods": mods, "BoneMods": {},
        }
    constraints = list(spec.constraints)
    existing = {frozenset((c.ent1, c.ent2)) for c in constraints if c.type == "Weld"}
    if spec.weld_to_head:
        constraints.extend(Constraint(ent1=head_id, ent2=i) for i in ids if i != head_id and frozenset((head_id, i)) not in existing)
    encoded_constraints = []
    for c in constraints:
        if c.ent1 not in entities or c.ent2 not in entities or c.ent1 == c.ent2:
            raise ValueError("Constraints must connect two different existing props")
        result = {"Type": c.type, "Entity": {1: {"Index": c.ent1, "Bone": 0}, 2: {"Index": c.ent2, "Bone": 0}}}
        if c.type == "Weld":
            result.update(forcelimit=c.force_limit, nocollide=c.nocollide, deleteonbreak=False)
        encoded_constraints.append(result)
    return table({"Entities": entities, "Constraints": encoded_constraints,
                  "HeadEnt": {"Index": head_id, "Pos": Vector(*origin), "Z": origin[2] - spec.ground_z},
                  "Description": spec.description})


def validate_dupe(root: Table) -> None:
    head, entities, constraints = (root.get(k) for k in ("HeadEnt", "Entities", "Constraints"))
    if not all(isinstance(v, Table) for v in (head, entities, constraints)):
        raise CodecError("Missing HeadEnt, Entities or Constraints table")
    if not isinstance(head.get("Pos"), Vector) or not isinstance(head.get("Z"), (float, int)):
        raise CodecError("HeadEnt requires Vector Pos and numeric Z")
    if head.get("Index") is None or entities.get(head.get("Index")) is None:
        raise CodecError("HeadEnt.Index does not exist in Entities")
    for entity_id, entity in entities.entries:
        if not isinstance(entity, Table):
            raise CodecError(f"Entity {entity_id} must be a table")
        physics = entity.get("PhysicsObjects")
        bone = physics.get(0) if isinstance(physics, Table) else None
        if not isinstance(bone, Table) or not isinstance(bone.get("Pos"), Vector) or not isinstance(bone.get("Angle"), Angle):
            raise CodecError(f"Entity {entity_id} needs PhysicsObjects[0].Pos/Angle")


def summary(root: Table) -> dict:
    validate_dupe(root)
    entities, constraints, head = (root.get(k) for k in ("Entities", "Constraints", "HeadEnt"))
    points = [e.get("PhysicsObjects").get(0).get("Pos") for _, e in entities.entries]
    return {"entity_count": len(entities), "constraint_count": len(constraints),
            "head_id": head.get("Index"), "ground_offset": head.get("Z"),
            "description": root.get("Description", ""),
            "models": dict(Counter(str(e.get("Model", "")) for _, e in entities.entries)),
            "classes": dict(Counter(str(e.get("Class", "")) for _, e in entities.entries)),
            "origin_bounds": {"min": [min(getattr(p, a) for p in points) for a in "xyz"],
                              "max": [max(getattr(p, a) for p in points) for a in "xyz"]}}


def transform(root: Table, offset: Triple, yaw: float) -> None:
    """Rotate around the saved copy origin, then translate local prop positions."""
    validate_dupe(root)
    if not all(math.isfinite(v) for v in (*offset, yaw)):
        raise ValueError("Transform values must be finite")
    entities = root.get("Entities")
    constraints = root.get("Constraints")
    for _, entity in entities.entries:
        if entity.get("Class") != "prop_physics" or len(entity.get("PhysicsObjects")) != 1:
            raise ValueError("Transform supports single-body prop_physics only")
        if entity.get("BuildDupeInfo"):
            raise ValueError("Transform does not support parenting or custom BuildDupeInfo")
    for _, constraint in constraints.entries:
        if not isinstance(constraint, Table) or constraint.get("Type") not in ("Weld", "NoCollide"):
            raise ValueError("Transform supports Weld and NoCollide constraints only")
    theta = math.radians(yaw)
    co, si = math.cos(theta), math.sin(theta)

    def rotate(v: Vector) -> Vector:
        return Vector(co*v.x - si*v.y, si*v.x + co*v.y, v.z)

    for _, entity in entities.entries:
        physics = entity.get("PhysicsObjects")
        for _, bone in physics.entries:
            if isinstance(bone.get("Pos"), Vector):
                pos = rotate(bone.get("Pos"))
                bone.set("Pos", Vector(pos.x + offset[0], pos.y + offset[1], pos.z + offset[2]))
            angle = bone.get("Angle")
            if isinstance(angle, Angle):
                bone.set("Angle", Angle(angle.p, angle.y + yaw, angle.r))
        # Optional world Pos/Angle fields are overwritten by AdvDupe2 on paste.
    for _, constraint in constraints.entries:
        # Rebuild these optional alignment hints from the new prop geometry.
        constraint.entries = [(k, v) for k, v in constraint.entries if k != "BuildDupeInfo"]

