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
import pathlib
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
        "ROLE_CLAIM = 5\n",
        "ROLE_CLAIM = 4\n",
        "two kinds share a code",
        id="frame-two-kinds-one-code",
    ),
    pytest.param(
        "ration.frame",
        '(ROLE_CLAIM, "role-claim"),\n',
        '(ROLE_CLAIM, "fingerprint"),\n',
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
    pytest.param(
        "ration.conformance.support.codecs",
        '_case("no-ceiling", {"frame-length"}, NoCeilingCodec),\n',
        '_case("ignores-trailing", {"frame-length"}, NoCeilingCodec),\n',
        "two codec cases share a name",
        id="codecs-two-cases-one-name",
    ),
    pytest.param(
        "ration.conformance.support.backends",
        '_memory_case("naive", {"atomicity"}, NaiveStore),\n',
        '_memory_case("correct", {"atomicity"}, NaiveStore),\n',
        "two memory cases share a name",
        id="backends-two-cases-one-name",
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


def load_time_raises(source: str) -> int:
    """How many top-level statements of `source` can raise while the module loads.

    Every statement at module level other than a `def` or a `class` is run at
    import, so one holding a `raise` anywhere inside it -- an `if` body, its
    `else`, a `try`, a loop -- is a load-time check.
    """
    skip = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    return sum(
        1
        for node in ast.parse(source).body
        if not isinstance(node, skip) and any(isinstance(n, ast.Raise) for n in ast.walk(node))
    )


def modules_of_src() -> list[str]:
    """Every module under `src/ration`, by import name, read from the tree rather than from a list."""
    spec = importlib.util.find_spec("ration")
    assert spec is not None and spec.submodule_search_locations, "ration is not importable"
    package = pathlib.Path(next(iter(spec.submodule_search_locations)))
    names = []
    for path in sorted(package.rglob("*.py")):
        parts = path.relative_to(package.parent).with_suffix("").parts
        names.append(".".join(parts[:-1] if parts[-1] == "__init__" else parts))
    return names


def test_every_load_time_check_in_src_has_a_plant() -> None:
    """Every module of `src` that can raise at import has a `PLANTS` row for each check.

    Read by a different method from the rows: every module under `src/ration`
    is enumerated from the tree, its top-level statements that hold a `raise`
    are counted with `ast`, and the count must be matched by as many distinct
    planted messages for that module. A load-time check added anywhere in
    `src` with no plant is red here, and the positive control is that the
    enumeration finds the modules this file plants.
    """
    modules = modules_of_src()
    planted = {str(row.values[0]) for row in PLANTS}
    assert planted <= set(modules), sorted(planted - set(modules))
    short = []
    for module in modules:
        checks = load_time_raises(source_of(module)[1])
        messages = {str(row.values[3]) for row in PLANTS if row.values[0] == module}
        if len(messages) < checks:
            short.append(f"{module}: {checks} load-time check(s), {len(messages)} planted")
    assert not short, short
