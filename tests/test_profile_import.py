import json

import pytest

from adv2mcp.policy import PropPolicy
from adv2mcp.profile_import import import_profile, parse_lists


def test_import_only_explicit_lists_not_comments_or_other_code():
    source = '''
      -- Props = {"models/comment.mdl"}
      --[=[ NewProps = {"models/block-comment.mdl"} ]=]
      Props = {"models/A.mdl", 'models/b.mdl',}
      NewProps = {"models/a.mdl"}
      if CLIENT then
        local Whiteprop = {"models/c.mdl"}
      local unrelated = {"models/unrelated.mdl"}
      local text = "Props = { 'models/in-string.mdl' }"
      error("must never run")
    '''
    assert parse_lists(source) == {"Props": ["models/a.mdl", "models/b.mdl"],
                                   "NewProps": ["models/a.mdl"], "Whiteprop": ["models/c.mdl"]}


@pytest.mark.parametrize("source", [
    'Props = {"models/a.mdl", dynamicFunction()}',
    'Props = {"models/a.mdl" .. "x"}',
    'Props = {"models/a.mdl"',
    'Props = {"models/a.mdl" "models/b.mdl"}',
    'Props = {"models/../../bad.mdl"}',
    'Other = {"models/not-allowed.mdl"}',
])
def test_rejects_expressions_and_bad_input(source):
    with pytest.raises(ValueError):
        parse_lists(source)


def test_profile_deduplicates_preserves_categories_and_backs_up(tmp_path):
    source = tmp_path / "props.txt"
    source.write_text('Props = {"models/a.mdl"}\nNewProps = {"models/a.mdl", "models/b.mdl"}', encoding="utf-8-sig")
    dest = tmp_path / "data/server-props.json"
    result = import_profile(source, dest)
    assert result["model_count"] == 2
    assert result["duplicates_removed"] == 1
    assert PropPolicy(dest).status()["loaded"] is True
    saved = json.loads(dest.read_text(encoding="utf-8"))
    assert saved["models"][0]["categories"] == ["NewProps", "Props"]
    assert "available" not in saved["models"][0]  # No guesses about mounted content.
    original = dest.read_bytes()
    source.write_text('Props = {"models/c.mdl"}')
    result = import_profile(source, dest)
    from pathlib import Path
    assert Path(result["backup"]).read_bytes() == original
    assert PropPolicy(dest).search("", 50, 0)["models"] == ["models/c.mdl"]
