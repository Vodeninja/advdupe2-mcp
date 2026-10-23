import json

import pytest

from adv2mcp.build import BuildSpec, make_build
from adv2mcp.policy import PropPolicy
from adv2mcp.storage import DupeStore


def root(model="models/props_c17/door01_left.mdl"):
    return make_build(BuildSpec(props=[{"id": 1, "model": model}]))


def profile(path, models):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"format": "adv2mcp-props-v1", "server": "test-server", "models": models}), encoding="utf-8")


def test_missing_allowlist_blocks_all_writers(tmp_path):
    store = DupeStore(tmp_path)
    with pytest.raises(ValueError, match="allowlist is missing"):
        store.save("demo.txt", root())
    assert not (tmp_path / "demo.txt").exists()


def test_whitelist_enforced_and_reloaded(tmp_path):
    path = tmp_path / "adv2mcp" / "server-props.json"
    store = DupeStore(tmp_path, PropPolicy(path))
    profile(path, ["models/props_c17/door01_left.mdl"])
    assert store.save("allowed.txt", root())["prop_policy"]["enforced"]
    with pytest.raises(ValueError, match="absent"):
        store.save("blocked.txt", root("models/hunter/plates/plate2x2.mdl"))
    profile(path, ["models/hunter/plates/plate2x2.mdl"])
    assert store.save("now-allowed.txt", root("models/hunter/plates/plate2x2.mdl"))
    with pytest.raises(ValueError, match="absent"):
        store.save("no-longer-allowed.txt", root())


def test_error_models_excluded(tmp_path):
    path = tmp_path / "server-props.json"
    profile(path, [{"model": "models/a.mdl", "available": False}, {"model": "models/b.mdl", "available": True}])
    policy = PropPolicy(path)
    assert policy.search("", 50, 0)["models"] == ["models/b.mdl"]
    with pytest.raises(ValueError, match="ERROR icons"):
        policy.check(root("models/a.mdl"))


def test_malformed_profile_does_not_disable_policy(tmp_path):
    path = tmp_path / "profile.json"
    path.write_text("{}")
    with pytest.raises(ValueError, match="Invalid"):
        PropPolicy(path).check(root())
