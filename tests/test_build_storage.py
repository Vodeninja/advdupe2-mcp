import pytest

from adv2mcp.build import BuildSpec, make_build, summary, transform
from adv2mcp.codec import Vector, table
from adv2mcp.storage import DupeStore
from adv2mcp.policy import PropPolicy


def sample():
    return make_build(BuildSpec(props=[
        {"id": 1, "model": "models/hunter/blocks/cube05x05x05.mdl", "pos": [10, 20, 12]},
        {"id": 2, "model": "models/hunter/blocks/cube05x05x05.mdl", "pos": [34, 20, 12], "frozen": False},
    ], weld_to_head=True))


def test_positions_frozen_and_constraints():
    root = sample()
    assert root.get("HeadEnt").get("Z") == 12
    assert root.get("Entities").get(1).get("PhysicsObjects").get(0).get("Pos") == Vector()
    assert root.get("Entities").get(2).get("PhysicsObjects").get(0).get("Pos") == Vector(24, 0, 0)
    assert root.get("Entities").get(1).get("PhysicsObjects").get(0).get("Frozen") is False
    assert root.get("Entities").get(2).get("PhysicsObjects").get(0).get("Frozen") is True
    constraint = root.get("Constraints").get(1)
    assert constraint.get("Entity").get(1).get("Index") == 1
    assert constraint.get("Entity").get(2).get("Index") == 2
    assert constraint.get("nocollide") is True


def test_transform_and_rejection():
    root = sample()
    transform(root, (100, 0, 5), 90)
    pos = root.get("Entities").get(2).get("PhysicsObjects").get(0).get("Pos")
    assert (pos.x, pos.y, pos.z) == pytest.approx((100, 24, 5))
    assert root.get("HeadEnt").get("Z") == 12
    root.get("Constraints").set(2, table({"Type": "Rope"}))
    with pytest.raises(ValueError, match="Weld"):
        transform(root, (0, 0, 0), 45)


def test_write_refuse_overwrite_and_backup(tmp_path):
    store = DupeStore(tmp_path, policy=PropPolicy(tmp_path / "no-profile.json", required=False))
    result = store.save("mcp/demo.txt", sample())
    assert result["entity_count"] == 2
    original = store.path("mcp/demo.txt").read_bytes()
    with pytest.raises(FileExistsError):
        store.save("mcp/demo.txt", sample())
    assert store.path("mcp/demo.txt").read_bytes() == original
    store.save("mcp/demo.txt", sample(), overwrite=True, revision=5)
    assert list((tmp_path / "mcp").glob("*.bak"))[0].read_bytes() == original
    assert store.read("mcp/demo.txt")[1]["revision"] == "5"


@pytest.mark.parametrize("name", ["../escape.txt", "a/../../escape.txt", "C:/escape.txt", "/escape.txt", "x.json", "a:stream.txt", "NUL.txt", "a/CON.txt", "a./x.txt"])
def test_path_restrictions(tmp_path, name):
    with pytest.raises(ValueError):
        DupeStore(tmp_path).path(name)


def test_invalid_builds():
    with pytest.raises(ValueError, match="unique"):
        make_build(BuildSpec(props=[{"id": 1, "model": "models/a.mdl"}, {"id": 1, "model": "models/a.mdl"}]))
    with pytest.raises(ValueError, match="existing"):
        make_build(BuildSpec(props=[{"id": 1, "model": "models/a.mdl"}], constraints=[{"ent1": 1, "ent2": 2}]))

