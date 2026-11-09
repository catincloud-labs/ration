# Changelog

**Not a release log.** The releases are the signed `v*` tags and their GitHub
releases (README, *Versions and releases*). This file holds what this
repository's documents used to say, moved here when each sentence was found
dead and rewritten (`AGENTS.md`, *Repo conventions*). A reader carrying an old
claim finds it here, labelled dead, rather than finding nothing.

**FROZEN, entry by entry: read every date below as "true when written".**
Nothing in this file is current. Each entry quotes the dead text, says when it
was read dead and against what, and names the commit its wording entered with,
from `git log --reverse -S"<phrase>" -- <file>`. Dates are UTC.

## README.md

### Versions and releases

- **`**No release has been cut**: install from a checkout, as below.`** The
  section's first sentence, in this wording from `6b96854`
  (2026-11-01T00:58:19Z); the phrase "No release has been cut" stood there
  from `9ada7a1` (2026-10-29T00:51:42Z), the commit that published the tree. Read dead 2026-11-01 against the signed
  tag `v0.1.0` (tag object `6183190`, naming commit `a386571`) and its GitHub
  release, <https://github.com/catincloud-labs/ration/releases/tag/v0.1.0>,
  published 2026-11-01T01:34:28Z by the run
  <https://github.com/catincloud-labs/ration/actions/runs/41261517505>, which
  verified the tag's signature and passed the suite at `a386571`. The sentence
  now directs a reader to the releases and to a clone at a release's tag.

### The first piece of work, and why it is not the service

- **`The contract requires a conflict to be reported *without writing*, which
  holds, and says nothing about the version it carries.`** The second
  sentence of the paragraph headed "Not a contract defect", in this wording
  from `9ada7a1` (2026-10-29T00:51:42Z), the commit that published the tree.
  Read dead 2026-11-09 against `tests/conformance/test_compare_and_set.py` as
  this entry's commit leaves it: the test requires a conflict's version to be
  one the key has held, as `Conflict` in `src/ration/contract.py` states it.
  Before that commit the test required the key's current version, so the
  sentence understated what the suite decided either way. The sentence now
  says the contract asks only that the key has held the version, and names
  the test that decides it.

### Versions and releases, on what the wheel carries

- **"This package is not published to a registry: the wheel would carry
  `src/ration` and not the suite that judges it, and the suite is the
  point."** The third sentence of the paragraph headed "Do not install by the
  bare name", in this wording from `9ada7a1` (2026-10-29T00:51:42Z), the
  commit that published the tree. Read dead 2026-11-09 against the tree this
  entry's commit leaves, where the conformance suite, its violators and its
  support modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The wheel now carries the suite. The paragraph still
  says the package is not published to a registry, which stays true, and now
  says the wheel carries the suite as `ration.conformance`, with pytest as its
  `conformance` extra.

### Paths to the suite

- **Every `tests/conformance/`, `tests/support/backends.py`,
  `tests/support/codecs.py`, `tests/violators.py`, `tests/frame_violators.py`
  and `tests/permitted.py` in the README, and the one `tests/conformance/` in
  `SECURITY.md`.** Fifteen lines, where the dead text is the path and the
  sentence around it stands. The lines entered with `9ada7a1`
  (2026-10-29T00:51:42Z), `ad14ac6` (2026-10-30T18:28:26Z), `7a2af57`
  (2026-11-09T15:56:32Z), `5f10f67` (2026-11-09T16:19:23Z) and `e0604ee`
  (2026-11-09T19:00:29Z); `git log --reverse -S"<line>" df5d884e -- README.md`
  names the one for each line. Read dead 2026-11-09 against the tree this
  entry's commit leaves, where the conformance suite, its violators and its
  support modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). Each path now reads as it moved:
  `tests/conformance/` as `src/ration/conformance/`,
  `tests/support/<module>.py` as `src/ration/conformance/support/<module>.py`,
  and `tests/<module>.py` as `src/ration/conformance/<module>.py`.

## AGENTS.md

### Merging, the cold review and the record

- **`A pull request body may be corrected in place, with a visible dated note
  saying what changed.`** The second sentence of the bullet on correcting a
  posted claim, in the subsection the organisation's repositories keep
  byte-identical. It stood there from `9ada7a1` (2026-10-29T00:51:42Z), the
  commit that published the tree. Read dead 2026-11-04 against the owner's
  ruling of that day: a draft pull request's body is edited freely, with no
  note of what changed, and the visible dated note applies once a pull
  request has left draft. The sentence now says so.

### The README describes; the suite decides

- **"The contract is stated in `src/ration/contract.py` and decided by
  `tests/conformance/`."** The section's first sentence, in this wording from
  `9ada7a1` (2026-10-29T00:51:42Z), the commit that published the tree. Read
  dead 2026-11-09 against the tree this entry's commit leaves, where the
  conformance suite, its violators and its support modules are the package
  `ration.conformance`, under `src/ration/conformance/`, and this repository's
  registry of stores is `tests/cases.py` (#20). The sentence now names the
  suite the package ships, `src/ration/conformance/`.

### Deliberately absent

- **"A backend is added to `CASES` in `tests/support/backends.py` and runs
  what is already there."** The second sentence of the bullet headed "No
  fixture that makes a backend pass", in this wording from `9ada7a1`
  (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). `CASES` is now this repository's list in
  `tests/cases.py`, and the sentence names it there.

## .github/workflows/release.yml

### The header

- **"Nothing is built or pushed to a registry: the wheel would carry
  `src/ration` and not the suite that judges it (README, "Versions and
  releases")."** The header's third sentence, in this wording from `c65667b`
  (2026-11-01T02:13:19Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The sentence now says nothing is built or pushed to
  a registry and that a release carries no files of its own, which the
  README's *Versions and releases* states, and gives no reason about the
  wheel.

## docs/design/coordination-substrate.md

### Where the registries are

- **"The registries are the `CASES` list in `tests/support/backends.py` and
  the `CODECS` list in `tests/support/codecs.py`; each entry names an
  implementation and the properties it is expected to break."** Under *How to
  read a citation*, with the command after it, `grep -n -A3 "_case("
  tests/support/backends.py tests/support/codecs.py`, both in this wording
  from `b78c76e` (2026-11-06T23:33:50Z). Read dead 2026-11-09 against the tree
  this entry's commit leaves, where the conformance suite, its violators and
  its support modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The sentence now names `CASES` in `tests/cases.py`,
  which starts from the package's `MEMORY_CASES`, and the command reads all
  three files.
- **"Any store not registered in `tests/support/backends.py`."** The bold lead
  of a bullet under *What the suite does not show*, in this wording from
  `634c5cf` (2026-11-06T22:59:16Z). Read dead 2026-11-09 against the tree this
  entry's commit leaves, where the conformance suite, its violators and its
  support modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). It now names `tests/cases.py`.
- **"The repository's root `conftest.py` hands both to the suite."** Under
  *How to read a citation*, after the sentence naming the registries, in this
  wording from `bc4001f` (2026-11-09T21:14:03Z). Read dead 2026-11-09 against
  the tree this entry's commit leaves, where `ration.conformance.plugin` fills
  the suite's registries in every run: the package's own cases and frame
  codecs, and beside them the stores its caller returns from the hook
  `pytest_ration_cases`. This repository's root `conftest.py` enables the
  plugin and returns `CASES` (#21). The root `conftest.py` hands the plugin
  one registry, and the sentence now says so and that the plugin hands the
  suite both.

### Paths to the suite

- **Every other `tests/conformance/`, `tests/support/backends.py`,
  `tests/support/codecs.py`, `tests/violators.py`, `tests/permitted.py` and
  `tests/frame_violators.py` on the page,** including the **Describes** list
  and the test ids in the property tables. Nineteen lines, where the dead text
  is the path, from `634c5cf` (2026-11-06T22:59:16Z), `b78c76e`
  (2026-11-06T23:33:50Z), `5f10f67` (2026-11-09T16:19:23Z) and `93183f4`
  (2026-11-09T18:38:31Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). Each path now reads as it moved, by the rule in the
  README's *Paths to the suite* entry above, and the **Describes** list gains
  `src/ration/conformance/postgres_violators.py` and `tests/cases.py`. The
  **Reviewed** line is unchanged: it is a reading of its own day, and
  re-reading the page at a new head is separate work (#18).

## pyproject.toml

### The pytest options

- **`testpaths = ["tests"]`**, with the comment beneath it, **`The suite
  imports its own support modules by package path, so the repository root has
  to be importable.`** Both in this wording from `9ada7a1`
  (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The suite is collected from `src/ration/conformance`
  before `tests`, and the root stays importable because this repository's
  tests import `tests.cases` and `tests.support`, which the comment now says.

## Docstrings and comments

Moved here as #20's body asks while review finding 4 on #19, whether a
rewritten docstring's old text belongs in this file, is open. Comments that
cited a moved path are listed beside the docstrings.

### Sentences whose meaning moved

- **`Every implementation the suite runs against, and what each is expected to
  fail.`** with **`so the registry below is the suite's actual subject`** and
  **`A new backend is added here and runs what is already written.`** The
  docstring of `tests/support/backends.py`, now
  `src/ration/conformance/support/backends.py`: the first and third from
  `9ada7a1` (2026-10-29T00:51:42Z), the second in this wording from `93183f4`
  (2026-11-09T18:38:31Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The module now builds each case and holds the
  package's `MEMORY_CASES`, and the docstring says a backend is added to a
  caller's registry.
- **"There are two registries and one mechanism. A test that takes `backend`
  runs against every store in `tests/support/backends.py`; a test that takes
  `codec` runs against every frame codec in `tests/support/codecs.py`."** The
  docstring of `tests/conftest.py`, from `9ada7a1` (2026-10-29T00:51:42Z).
  Read dead 2026-11-09 against the tree this entry's commit leaves, where the
  conformance suite, its violators and its support modules are the package
  `ration.conformance`, under `src/ration/conformance/`, and this repository's
  registry of stores is `tests/cases.py` (#20). The mechanism and its
  docstring are now `src/ration/conformance/conftest.py`, where the paragraph
  says each fixture runs what its caller registered. `tests/conftest.py` is
  gone: this repository's cases are registered by the root `conftest.py`, so a
  run of one suite module by path is handed them too.
- **`The conformance suite.`** with **"Every property in `conformance/` ships
  alongside an implementation in `violators.py` that breaks exactly that
  property and is expected to fail it"** The docstring of `tests/__init__.py`,
  from `9ada7a1` (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree
  this entry's commit leaves, where the conformance suite, its violators and
  its support modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). `tests/` is now this repository's tests and its
  caller of the suite, and the docstring says so.
- **"Everything else in `tests/` enforces that rule for the contract."** The
  docstring of `tests/test_the_suite_discriminates.py`, from `9ada7a1`
  (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). It now names the suite in `src/ration/conformance/`.
- **"a test that did `from tests.conftest import ...` could bind a second,
  empty copy"** The docstring of `tests/support/declared.py`, now
  `src/ration/conformance/support/declared.py`, from `9ada7a1`
  (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The state is now filled by the suite's own conftest,
  which this repository's run imports as `ration.conformance.conftest`, so
  that import binds the same module and no longer illustrates the hazard. The
  sentence now states the hazard without an example: the name pytest gives a
  conftest depends on the import mode and the rootdir.
- **"by the mechanism `conftest.py` uses for the contract"** The docstring of
  `tests/test_postgres_killed_connection.py`, from `9ada7a1`
  (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). The `conftest.py` beside it no longer holds the
  mechanism, so the sentence names `src/ration/conformance/conftest.py`.
- **"filtered from the registry in `tests/support/backends.py`"** in the
  docstring of `tests/test_lease.py`, in this wording from `93183f4`
  (2026-11-09T18:38:31Z), and **"registry in `tests/support/backends.py` on
  purpose"** in a comment in `tests/support/crossprocess.py`, from `9ada7a1`
  (2026-10-29T00:51:42Z). Read dead 2026-11-09 against the tree this entry's
  commit leaves, where the conformance suite, its violators and its support
  modules are the package `ration.conformance`, under
  `src/ration/conformance/`, and this repository's registry of stores is
  `tests/cases.py` (#20). Both now name `tests/cases.py`.

### The registries, once a plugin fills them

- **`The cases a run judges, as its caller handed them to the suite.`** with
  **"This repository's caller registers the package's in-memory cases, DuckDB
  where its driver imports, and Postgres where a server is named. The caller
  calls `register` before collection"** The docstring of
  `src/ration/conformance/support/registry.py`, and with them the sentence its
  refusal of an empty registry printed, **"The caller registers its cases with
  `ration.conformance.support.registry.register` before collection."** All
  from `f99e485` (2026-11-09T20:52:08Z). Read dead 2026-11-09 against the tree
  this entry's commit leaves, where `ration.conformance.plugin` fills the
  suite's registries in every run: the package's own cases and frame codecs,
  and beside them the stores its caller returns from the hook
  `pytest_ration_cases`. This repository's root `conftest.py` enables the
  plugin and returns `CASES` (#21). The docstring now names the plugin as what
  calls `register`, and the refusal tells a reader to enable the plugin.
- **"A test that takes `backend` runs against every store its caller
  registered; a test that takes `codec` runs against every frame codec its
  caller registered. Both are read from `support/registry.py`, which the
  caller fills before collection."** The docstring of
  `src/ration/conformance/conftest.py`, from `f99e485` (2026-11-09T20:52:08Z).
  Read dead 2026-11-09 against the tree this entry's commit leaves, where
  `ration.conformance.plugin` fills the suite's registries in every run: the
  package's own cases and frame codecs, and beside them the stores its caller
  returns from the hook `pytest_ration_cases`. This repository's root
  `conftest.py` enables the plugin and returns `CASES` (#21). A caller now
  registers no frame codec, and the paragraph says the plugin fills both
  registries.
- **`This repository's registries, handed to the suite the package ships.`**
  with **"What this file adds is the one choice the package leaves to its
  caller: which cases a run judges. Here that is every store in
  `tests/cases.py` and every frame codec the package defines."** The docstring
  of the root `conftest.py`, from `bc4001f` (2026-11-09T21:14:03Z). Read dead
  2026-11-09 against the tree this entry's commit leaves, where
  `ration.conformance.plugin` fills the suite's registries in every run: the
  package's own cases and frame codecs, and beside them the stores its caller
  returns from the hook `pytest_ration_cases`. This repository's root
  `conftest.py` enables the plugin and returns `CASES` (#21). The package's
  own cases and its codecs are no longer the caller's choice, and the
  docstring says the file enables the plugin and answers its hook.
- **"Which cases a run judges is its caller's registry; this repository's is
  `tests/cases.py` in the source tree."** with **"A caller's registry starts
  from these, so a run that judges any store also shows each violator below
  failing its property beside the correct store passing."** The docstring of
  `src/ration/conformance/support/backends.py` and the comment above
  `MEMORY_CASES` in it, from `f99e485` (2026-11-09T20:52:08Z). Read dead
  2026-11-09 against the tree this entry's commit leaves, where
  `ration.conformance.plugin` fills the suite's registries in every run: the
  package's own cases and frame codecs, and beside them the stores its caller
  returns from the hook `pytest_ration_cases`. This repository's root
  `conftest.py` enables the plugin and returns `CASES` (#21). A caller's own
  list need not start from `MEMORY_CASES`, since the plugin registers them
  first; the two now say so.

### Paths only

- **The moved paths in the docstrings and comments of
  `src/ration/__init__.py`, `contract.py`, `duckdb_store.py`, `frame.py` and
  `lease.py`; of the moved `frame_violators.py`, `permitted.py`,
  `support/preemption.py`, `test_atomicity.py` and `test_frame_text.py`; and
  of `tests/support/crossprocess.py`, `tests/test_duckdb_single_process.py`,
  `tests/test_postgres_conflict_version.py` and
  `tests/test_postgres_cross_process.py`.** Twenty lines, where the dead text
  is the path, from `9ada7a1` (2026-10-29T00:51:42Z), `bdc73ff`
  (2026-10-30T18:13:39Z), `ad14ac6` (2026-10-30T18:28:26Z), `f1ff356`
  (2026-11-09T16:03:05Z) and `93183f4` (2026-11-09T18:38:31Z). Read dead
  2026-11-09 against the tree this entry's commit leaves, where the
  conformance suite, its violators and its support modules are the package
  `ration.conformance`, under `src/ration/conformance/`, and this repository's
  registry of stores is `tests/cases.py` (#20). Each path now reads as it
  moved, by the rule in the README's *Paths to the suite* entry above.
