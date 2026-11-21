"""Every fact a module of `src` holds by construction is checked when it loads, and each check is calibrated here.

A module that holds a fact by construction -- a kind code that fits its byte,
a maximum that fits its field, two names that must differ -- checks it at
import with an explicit `raise`, never an `assert`, which `python -O` strips.
A check observed only to pass has not been shown to be a check, so each one
has a row in `PLANTS` below. The row plants exactly one wrong fact in the
module's own source, and the case runs that source and sees it raise. The
same source, unplanted, runs clean, which is the other arm.

The source is run from its text, as a fresh module of its own name, rather
than by reloading the module: every other test holds the real module, and a
reload would hand them a planted one.

Measures: scripts/check_power_of_ten.py, rule 5
"""

from __future__ import annotations

import ast
import importlib.util
import sys
import types

import pytest

#: One row per load-time check: the module, the line of source a fact sits on,
#: the same line with the fact made wrong, and the message the check raises.
#: Each `stated` line must occur exactly once in the module's source, so a plant
#: that no longer finds its fact is a failure rather than a pass.
PLANTS = [
    pytest.param(
        "ration.frame",
        "ROLE_CLAIM = 5\n",
        "ROLE_CLAIM = 256\n",
        "fit one byte",
        id="frame-kind-code-past-its-byte",
    ),
    pytest.param(
        "ration.frame",
        'ROLE_CLAIM: "role-claim",\n',
        'ROLE_CLAIM: "fingerprint",\n',
        "two kind codes share a name",
        id="frame-two-kinds-one-name",
    ),
    pytest.param(
        "ration.frame",
        "MAX_BODY_LENGTH = 1_048_576\n",
        "MAX_BODY_LENGTH = 1 << 32\n",
        "32-bit length field",
        id="frame-maximum-past-the-length-field",
    ),
    pytest.param(
        "ration.frame",
        "MAX_BODY_LENGTH = 1_048_576\n",
        "MAX_BODY_LENGTH = 0\n",
        "32-bit length field",
        id="frame-maximum-zero",
    ),
    pytest.param(
        "ration.frame",
        'OVERSIZED = "oversized"\n',
        'OVERSIZED = "truncated"\n',
        "two frame controls share a name",
        id="frame-two-controls-one-name",
    ),
    pytest.param(
        "ration.frame",
        '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"\n',
        '"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789--"\n',
        "64 distinct characters",
        id="frame-alphabet-short-a-character",
    ),
    pytest.param(
        "ration.publish",
        'TOPIC_PREFIX = "topic/"\n',
        'TOPIC_PREFIX = "role/topic/"\n',
        "must not nest",
        id="publish-topic-prefix-inside-the-role-prefix",
    ),
    pytest.param(
        "ration.conformance.support.codecs",
        "if FRAME_VERSION != 1:\n",
        "FRAME_VERSION = 2\nif FRAME_VERSION != 1:\n",
        "v1's layout",
        id="codecs-forge-under-another-frame-version",
    ),
]


def source_of(module: str) -> tuple[str, str]:
    """The module's file and its source text, read from where the import system finds it."""
    spec = importlib.util.find_spec(module)
    assert spec is not None and spec.origin is not None, module
    with open(spec.origin, encoding="utf-8") as handle:
        return spec.origin, handle.read()


def run_as_module(text: str, origin: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Execute `text` as a fresh module, registered while it runs because `dataclass` looks it up."""
    module = types.ModuleType("planted_module")
    monkeypatch.setitem(sys.modules, module.__name__, module)
    exec(compile(text, origin, "exec"), module.__dict__)


@pytest.mark.parametrize(("module", "stated", "planted", "message"), PLANTS)
def test_a_planted_wrong_fact_raises_at_import(
    module: str, stated: str, planted: str, message: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    origin, source = source_of(module)
    assert source.count(stated) == 1, f"the plant no longer finds its fact in {module}: {stated!r}"
    run_as_module(source, origin, monkeypatch)
    with pytest.raises(ValueError, match=message):
        run_as_module(source.replace(stated, planted), origin, monkeypatch)


@pytest.mark.parametrize("module", ["ration.frame", "ration.publish", "ration.conformance.support.codecs"])
def test_every_module_with_a_load_time_check_has_a_plant(module: str) -> None:
    """A module whose source raises at top level has at least one row in `PLANTS`.

    Read by a different method from the rows: the source's own top-level `if`
    statements whose body is a `raise`, counted with `ast`, must be matched by
    as many rows for that module. A check added with no row is red here.
    """
    _, source = source_of(module)
    checks = [
        node
        for node in ast.parse(source).body
        if isinstance(node, ast.If) and any(isinstance(child, ast.Raise) for child in node.body)
    ]
    rows = [row for row in PLANTS if row.values[0] == module]
    planted_messages = {str(row.values[3]) for row in rows}
    assert checks, f"{module} has no load-time check, so it does not belong in this list"
    assert len(planted_messages) >= len(checks), (
        f"{module} has {len(checks)} load-time check(s) and plants reach {len(planted_messages)}"
    )
