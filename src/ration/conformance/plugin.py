"""The way a store of your own joins the suite: a pytest plugin, enabled by name.

A project that judges a store enables this module in the `conftest.py` at the
root of the directory it runs pytest from:

    pytest_plugins = ["ration.conformance.plugin"]

or with `-p ration.conformance.plugin` on the command line, and runs the suite
the package ships with `pytest --pyargs ration.conformance`. There is no
`pytest11` entry point, and that is the opt-in: a project that installs
`ration` to hold a lease, not to judge a store, never has this join its runs.

What the plugin does, and nothing else:

- **It asks the caller for its cases** through one hook, `pytest_ration_cases`,
  specified by `CaseSpec` below. A hook rather than a fixture the caller
  overrides, because the cases are needed before any fixture runs: they are the
  parameters every store test is collected over and the ids the report names,
  and the suite's `conftest.py` reads them at collection.
- **It always registers the package's own cases first**: every store in
  `MEMORY_CASES`, the correct ones and the violators, and every frame codec in
  `CODECS`. The suite's `conftest.py` strict-xfails each violator against the
  property it breaks, so a run that judges a stranger's store is red wherever
  a violator passes in the stranger's environment.
- **It refuses two cases with one name**, because a name is how the report and
  the require switch tell cases apart. A case returned that is already
  registered, one of the package's own included, is registered once.
- **It refuses a required case that nothing judged.** `--ration-require NAME`,
  repeatable, names a case of the caller's that the run must judge. When no
  collected test runs a case of the caller's by that name, because none was
  registered or because the suite was not collected or was deselected, the
  run ends as a usage error before any test runs.

It hands both registries to the suite through `support/registry.py`'s
`register`, so the suite's mechanism reads them where it did before there was a
plugin. A run that collects the suite without the plugin still meets that
module's refusal of an empty registry, at collection.

**Frame codecs take no caller's cases.** The frame is a wire format this
package defines and `ration.frame` is its reader; the codec registry decides
whether that reader and the readers built wrong beside it are told apart. A
reader of the frame written elsewhere is not a Python object a case could
hand the suite, and a hook added here is a public name. One can be added later
without breaking a caller; one removed would break every caller that used it.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence

import pytest

from ration.conformance.support.backends import MEMORY_CASES, Case
from ration.conformance.support.codecs import CODECS
from ration.conformance.support.registry import register

#: The caller's cases, kept on the run's config for the collection check.
_CALLERS = pytest.StashKey[tuple[Case, ...]]()


class CaseSpec:
    """The hook a caller implements. pytest reads its name and its argument."""

    def pytest_ration_cases(self, config: pytest.Config) -> Sequence[Case]:
        """Return the stores this run judges beside the package's own.

        Implemented in the `conftest.py` that enables the plugin, which may
        leave out `config`. Every implementation is called once, at
        `pytest_configure`, and its cases are registered after the package's,
        in the order returned. The case contract is in the README, under
        *Running the suite against your own store*.
        """
        raise NotImplementedError("a hook specification is never called")


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    pluginmanager.add_hookspecs(CaseSpec)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.getgroup("ration", "ration conformance").addoption(
        "--ration-require",
        action="append",
        default=[],
        dest="ration_require",
        metavar="NAME",
        help=(
            "end the run as a usage error unless a collected test judges the "
            "caller's case NAME; repeatable"
        ),
    )


def pytest_configure(config: pytest.Config) -> None:
    answers: list[Sequence[Case]] = config.hook.pytest_ration_cases(config=config)
    callers = _callers_cases(answers)
    backend = (*MEMORY_CASES, *callers)
    _refuse_shared_names(backend)
    config.stash[_CALLERS] = callers
    register(backend=backend, codec=CODECS)


def pytest_report_header(config: pytest.Config) -> list[str]:
    callers = config.stash[_CALLERS]
    required = config.getoption("ration_require")
    return [
        "ration.conformance: the package's store cases: "
        + ", ".join(case.name for case in MEMORY_CASES),
        "ration.conformance: the caller's store cases: "
        + (", ".join(case.name for case in callers) or "none"),
        f"ration.conformance: frame codecs: the package's {len(CODECS)}",
        "ration.conformance: required: " + (", ".join(required) or "none"),
    ]


def pytest_collection_finish(session: pytest.Session) -> None:
    required: list[str] = session.config.getoption("ration_require")
    callers = {case.name for case in session.config.stash[_CALLERS]}
    judged = _judged(session.items)
    refusals = [
        _refusal(name, callers) for name in required if name not in judged & callers
    ]
    if refusals:
        raise pytest.UsageError("ration.conformance: " + " ".join(refusals))


def _callers_cases(answers: Iterable[Sequence[Case]]) -> tuple[Case, ...]:
    """Every case the hook returned, less the package's own and repeats."""
    cases: list[Case] = []
    for answer in answers:
        for case in answer:
            if case not in MEMORY_CASES and case not in cases:
                cases.append(case)
    return tuple(cases)


def _refuse_shared_names(cases: Sequence[Case]) -> None:
    names = [case.name for case in cases]
    shared = sorted({name for name in names if names.count(name) > 1})
    if shared:
        raise pytest.UsageError(
            f"ration.conformance: more than one case is named {', '.join(shared)}. "
            "A case is told apart by its name, in the report and by "
            "--ration-require, so a name registers one case. The package's own "
            "are " + ", ".join(case.name for case in MEMORY_CASES) + "."
        )


def _judged(items: Iterable[pytest.Item]) -> set[str]:
    """The name of every store case some collected test runs."""
    names: set[str] = set()
    for item in items:
        callspec = getattr(item, "callspec", None)
        case = callspec.params.get("backend") if callspec is not None else None
        if isinstance(case, Case):
            names.add(case.name)
    return names


def _refusal(name: str, callers: set[str]) -> str:
    if name not in callers:
        registered = ", ".join(sorted(callers)) or "none"
        return (
            f"{name!r} is required and the caller registered no case by that "
            f"name; the caller's cases are: {registered}."
        )
    return (
        f"{name!r} is required and registered, and no collected test runs it. "
        "The suite is collected with `--pyargs ration.conformance`, and a "
        "selection (-k, -m, a node id) can leave a case out."
    )
