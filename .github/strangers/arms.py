"""The plugin, judged from an installed wheel by projects shaped like a stranger's.

Run by the `installed wheel` job in `.github/workflows/checks.yml`, and by hand
the same way:

    python .github/strangers/arms.py --python <interpreter> --work <directory>

`--python` is the interpreter of a fresh virtual environment that holds the
wheel built at this commit, installed with its `conformance` extra, and nothing
else of this tree. `--work` is a directory outside the tree. Each arm is a
directory beside this file holding a stranger's root `conftest.py`; it is
copied into `--work` with the files in `common/`, and pytest runs there, under
that interpreter, as a stranger's CI would run it.

Each arm is decided by its exit code first, so the job is red whenever a
refusal does not fire, and then by what its report attributes the outcome to,
because a count is not an attribution: a run can exit 1 for a reason that is
not the stranger's store. The refusing arms run before the passing one, and the
passing arm is trusted only in a run where every refusing arm was seen to
refuse.

Before any arm, a positive control: the interpreter imports `ration` from
outside this tree, imports the plugin, and has no Postgres driver, so the arms
run the suite with pytest alone.

This script imports nothing from `ration`; it reads the runs it starts.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[1]
COMMON = HERE / "common"

#: How a stranger collects the suite the package ships.
SUITE = ("--pyargs", "ration.conformance")

#: Read from the outer environment by pytest or by an arm, so never passed on.
SCRUBBED = ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH", "STRANGER_STORE_ADDRESS")

#: One row per test in a run's JUnit report: (test, case id, outcome).
Row = tuple[str, str, str]

PROBE = (
    "import importlib.util, pytest, ration, ration.conformance.plugin; "
    "print('ration', ration.__file__); "
    "print('pytest', pytest.__version__); "
    "print('psycopg', importlib.util.find_spec('psycopg') is not None)"
)


@dataclass(frozen=True)
class Arm:
    directory: str
    args: tuple[str, ...]
    exit_code: int
    says: tuple[str, ...]
    check: Callable[[list[Row], str], list[str]]


def read_report(junit: Path) -> list[Row]:
    if not junit.is_file():
        return []
    rows: list[Row] = []
    for case in ET.parse(junit).getroot().iter("testcase"):
        test, _, rest = case.get("name", "").partition("[")
        outcome = "passed"
        for child in case:
            if child.tag in ("failure", "error"):
                outcome = "failed"
                break
            if child.tag == "skipped":
                outcome = "xfailed" if child.get("type") == "pytest.xfail" else "skipped"
        rows.append((f"{case.get('classname', '')}::{test}", rest.removesuffix("]"), outcome))
    return rows


def tests_of(rows: list[Row], case: str, outcome: str | None = None) -> set[str]:
    return {test for test, name, got in rows if name == case and outcome in (None, got)}


def nothing_ran(rows: list[Row], output: str) -> list[str]:
    ran = [f"{test}[{case}] {outcome}" for test, case, outcome in rows]
    return [f"the refusal came after tests ran: {ran[:5]}"] if ran else []


def only_collection_errors(rows: list[Row], output: str) -> list[str]:
    """Every row is a module the suite could not collect, and no test ran."""
    if not rows:
        return ["the report records no collection error"]
    ran = [f"{test}[{case}] {outcome}" for test, case, outcome in rows if outcome != "failed" or case]
    return [f"tests ran or were judged: {ran[:5]}"] if ran else []


def failed_where_the_package_xfails(rows: list[Row], output: str) -> list[str]:
    """The stranger's `recycling` fails exactly where the package's is strict-xfailed."""
    failed = tests_of(rows, "stranger-recycling", "failed")
    expected = tests_of(rows, "recycling", "xfailed")
    elsewhere = sorted(
        f"{test}[{case}]" for test, case, outcome in rows
        if outcome == "failed" and case != "stranger-recycling"
    )
    problems = []
    if not failed:
        problems.append("the stranger's violator failed no test")
    if not expected:
        problems.append("the package's `recycling` xfailed no test, so there is nothing to attribute to")
    if failed != expected:
        problems.append(f"the two disagree on: {sorted(failed ^ expected)}")
    if elsewhere:
        problems.append(f"tests failed on other cases: {elsewhere[:10]}")
    return problems


def judged_beside_the_package(rows: list[Row], output: str) -> list[str]:
    """The stranger's case ran the whole suite, and the package's cases ran beside it."""
    header = re.search(r"^ration\.conformance: the package's store cases: (.+)$", output, re.M)
    package = header.group(1).strip().split(", ") if header else []
    outcomes = {name: Counter(got for _, case, got in rows if case == name) for name in package}
    problems = []
    if len(package) < 2:
        problems.append("the report header names fewer than two of the package's cases")
    problems += [f"the report names no test of the package's `{name}`" for name, seen in outcomes.items() if not seen]
    if not tests_of(rows, "stranger-memory", "passed"):
        problems.append("no test passed for the stranger's case")
    # Against `previous-version`, a correct store of the package's, rather than
    # `correct`: a frame codec is named `correct` too, and its tests are not a
    # store's.
    if tests_of(rows, "stranger-memory") != tests_of(rows, "previous-version"):
        problems.append(
            "the stranger's case and the package's `previous-version` ran different tests: "
            f"{sorted(tests_of(rows, 'stranger-memory') ^ tests_of(rows, 'previous-version'))[:10]}"
        )
    if sum(seen["xfailed"] for seen in outcomes.values()) == 0:
        problems.append("no violator of the package's was seen failing its property")
    return problems


ARMS = (
    # Enabled by name only: with no `pytest_plugins` line nothing loads the
    # plugin, so pytest refuses the hook as unknown (an internal error, exit 3)
    # and the suite's registries are empty: the report records each suite
    # module as a collection error, and the internal error stops pytest before
    # it prints them, so the refusal's text is read from the report.
    Arm(
        "without-plugin",
        SUITE,
        3,
        (
            "unknown hook 'pytest_ration_cases'",
            "no case is registered for the `backend` fixture",
        ),
        only_collection_errors,
    ),
    Arm("violator-as-correct", SUITE, 1, ("failed",), failed_where_the_package_xfails),
    # Two names required: the stranger's, which went unregistered, and one of
    # the package's own, which is judged in every run and must not satisfy it.
    Arm(
        "required-unregistered",
        (*SUITE, "--ration-require", "stranger-store", "--ration-require", "correct"),
        4,
        (
            "'stranger-store' is required and the caller registered no case by that name",
            "'correct' is required and the caller registered no case by that name",
        ),
        nothing_ran,
    ),
    Arm(
        "required-uncollected",
        ("--ration-require", "stranger-memory"),
        4,
        ("'stranger-memory' is required and registered, and no collected test runs it",),
        nothing_ran,
    ),
    Arm("shared-name", SUITE, 4, ("more than one case is named correct",), nothing_ran),
    # Last, so it is read only after every refusal above has been seen.
    Arm(
        "correct",
        (*SUITE, "--ration-require", "stranger-memory"),
        0,
        ("ration.conformance: the caller's store cases: stranger-memory",),
        judged_beside_the_package,
    ),
)


def pytest_run(python: Path, project: Path, args: tuple[str, ...]) -> tuple[int, str]:
    env = {key: value for key, value in os.environ.items() if key not in SCRUBBED}
    env["PYTHONIOENCODING"] = "utf-8"
    junit = project / "report.xml"
    command = [str(python), "-m", "pytest", "-p", "no:cacheprovider", "-rA", f"--junitxml={junit}", *args]
    print(f"$ (cd {project}) {' '.join(command)}", flush=True)
    done = subprocess.run(
        command, cwd=project, env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=1200, check=False,
    )
    return done.returncode, done.stdout + done.stderr


def run_arm(arm: Arm, python: Path, work: Path) -> list[str]:
    project = work / arm.directory
    if project.exists():
        shutil.rmtree(project)
    shutil.copytree(HERE / arm.directory, project)
    for shared in COMMON.iterdir():
        shutil.copy2(shared, project / shared.name)
    code, output = pytest_run(python, project, arm.args)
    print(f"::group::{arm.directory}: the run's output", flush=True)
    print(output, flush=True)
    print("::endgroup::", flush=True)
    problems = []
    if code != arm.exit_code:
        problems.append(f"exited {code}, expected {arm.exit_code}")
    junit = project / "report.xml"
    said = output + (junit.read_text(encoding="utf-8", errors="replace") if junit.is_file() else "")
    problems += [f"neither the output nor the report says {text!r}" for text in arm.says if text not in said]
    return problems + arm.check(read_report(junit), output)


def control(python: Path, work: Path) -> list[str]:
    done = subprocess.run(
        [str(python), "-I", "-c", PROBE], cwd=work, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
    )
    print(done.stdout + done.stderr, flush=True)
    found = dict(line.split(" ", 1) for line in done.stdout.splitlines() if " " in line)
    problems = [] if done.returncode == 0 else [f"the probe exited {done.returncode}"]
    where = Path(found.get("ration", str(TREE))).resolve()
    if where.is_relative_to(TREE):
        problems.append(f"`ration` imports from this tree ({where}), not from an installed wheel")
    if found.get("psycopg") != "False":
        problems.append("the environment has a Postgres driver, so the arms would not show pytest is enough")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    args = parser.parse_args(argv)
    work: Path = args.work.resolve()
    if work.is_relative_to(TREE):
        print(f"::error::--work {work} is inside the tree; the arms run outside it.")
        return 2
    work.mkdir(parents=True, exist_ok=True)

    verdicts = {"control": control(args.python, work)}
    if not verdicts["control"]:
        for arm in ARMS:
            verdicts[arm.directory] = run_arm(arm, args.python, work)

    for name, problems in verdicts.items():
        print(f"{'ok  ' if not problems else 'RED '} {name}")
        for problem in problems:
            print(f"::error::{name}: {problem}")
    refusals = [arm.directory for arm in ARMS if arm.exit_code != 0]
    if any(verdicts.get(name, ["not run"]) for name in ["control", *refusals]):
        print("A refusing arm did not refuse as built, so the passing arm is not trusted.")
    return 0 if not any(verdicts.values()) and len(verdicts) == len(ARMS) + 1 else 1


if __name__ == "__main__":
    sys.exit(main())
