# AGENTS.md

Operating rules for AI coding agents, and for humans skimming for the sharp
edges. **This is a code repository, and the rules follow from that.**

## What this repo is

The coordination substrate and the lease service built on it. **A wrong claim
here fails a test rather than misleading a reader**, so the burden of evidence
sits on the suite, not on the prose.

That cuts the other way too. **A green suite here means the things it checks
are true, and nothing else.** A control observed only to pass has not been
shown to be a control.

## The rule that matters most here

**A conformance suite that cannot reject is not a suite.**

Every property the contract states must have an implementation that violates
**exactly that property** and is expected to fail. If a violating implementation
passes, the property is not being tested, and the suite is measuring nothing
while reporting success.

- **Add the violating implementation in the same change as the property.** Not
  afterwards: afterwards never comes, and a property with no violator looks
  identical to one with a violator that silently passes.
- **A new backend does not get its own tests.** It runs the existing suite. If
  it needs a special case to pass, either the contract is wrong or the backend
  does not qualify; both are findings, and neither is fixed by a fixture.

## The README describes; the suite decides

The contract is stated in `src/ration/contract.py` and decided by the suite
the package ships, `src/ration/conformance/`. **Where the README and the suite
disagree, the suite is the contract**, and the README is the thing to fix.

- **A change to what the suite decides changes the README in the same pull
  request.** The README describes the mechanism and the reasons the suite
  demonstrates, where a violator that fails is the reason a reader can run, so
  it moves when the suite moves and at no other time.
- **The prose promises nothing the suite does not show:** no guarantee, no
  support commitment, no measurement taken on anyone's deployment. A store's
  guarantee is shown by running the suite against that store.
- **Prose carries no pointer a reader of this repository cannot follow:** no
  private record, host, issue tracker or credential name. A reason is stated,
  with the test that demonstrates it, rather than cited.

## Verification method

A control observed only to pass has not been shown to be a control. Four
moves stand behind that rule, each paid for in this organisation:

- **Calibrate on both arms first.** Before reading an instrument's answer about
  the subject, show it report the defect on a case you built to have it, and
  report clean on a case you built not to, in the shape of the defect it is
  for. A refusal on a day when nothing could have passed is not a calibration.
- **A count is not an attribution.** Before a number names a cause, map it to
  the identities it counts, and ask what else produces the same reading. The
  count that matches the prediction is the one least likely to be checked.
- **Independence lives in the premise, not the author.** A second check that
  shares the first one's assumption agrees with it for the same reason. Vary
  the method: parse a different way, or enumerate a superset and subtract.
- **Empty and blind are the same input.** An empty list, a zero or a missing
  line is also what an unauthorised, filtered or never-run read returns. Run a
  positive control, a query that must return something, before reading
  absence as a fact.

## Change workflow

- **Branch per change** off `main`. Never commit to `main` directly; a ruleset
  enforces this, so a direct push is refused rather than discouraged.
- **Conventional commits** (`feat:`, `fix:`, `test:`, `docs:`, `chore:`) with a
  body explaining why.
- **A title is a git artifact. PR and issue titles take the commit form:**
  `type(scope): summary` - lowercase after the colon, one clause, at most 100
  characters, no trailing period. A PR title becomes the squash commit's
  subject, which history cites as `#N`; the full sentence belongs in the
  body. Issues take the type their fix would take; an issue arguing a fork
  rather than naming work is `argument:`. Probe PRs say `probe:` - a type,
  not an exemption.
  - Checked for PRs by the `pr title` job (`scripts/check_pr_title.py`, its
    self-test first), advisory. Nothing gates issue creation, so for issues
    the rule is this text.
  - Passing the guard is not the convention. The owner reads the title, so it
    is clear and concise, not a thesis: it says what was done to what, in plain
    words and the diff's own nouns, with no contrast clause, no *no X*
    phrasing, no identifier the change itself introduces in the lead, and no
    imperative the owner could take as addressed to them. A title about an
    agent rule names the artifact and the actor. A `fix:` title names the
    process that misbehaves today, its actor, and what it does after the
    change. An `argument:` title is *whether X*, X being the decision in the
    governing document's words. A filing in a repository outside the
    organisation keeps this form as closely as that repository allows. A pull
    request is retitled rather than a pushed commit amended. Ruled by the owner
    from 2026-10-08 to 2026-10-10. In practice titles run about 70 characters,
    and measuring the length before creating one catches a title over the cap.
- Open the PR as a draft, with `gh pr create --draft`.
- **A pull request carries exactly one `deploy:` label, and here it is
  required.** The label says what merging does to a running system, which is a
  fact about the change. None is unclassified and reads red; two is two claims
  about one merge and reads red. A merge here deploys nothing, so `deploy:none`
  is the usual value; which value fits is in each label's description, not in
  this file. The `review:` clock is applied by hand and read by no guard.
  - Checked by the `pr-hygiene` job (`.github/workflows/pr-hygiene.yml`,
    `scripts/check_deploy_label.py`, its self-test first), which is a required
    check, so a pull request without the label cannot merge.
  - The remedy for a red is to apply the label: the workflow listens for
    `labeled` and `unlabeled`, so the job re-runs by itself. The red run stays
    on the commit beside the green one; read the latest run of the job.
  - Applying a label takes triage access, so a pull request from a fork reads
    red on that step until the maintainer labels it. That red is expected.
  - Dependabot is exempt by author, and the exemption prints its closing
    condition at every firing: a `labels:` key in `.github/dependabot.yml`.
  - **The template's label line is a shared line with its link sentence cut,
    and nothing else changed.** The shared label line ends with a link to a
    private record. A reader of this repository cannot follow that link, so
    here the line ends after its first sentence. The line beneath it is this repository's own: its two values,
    and what a contributor from a fork should expect. Do not re-add the link,
    and do not merge the two lines: the first stays a byte-identical prefix of
    the shared one.
  - Check a label set before uploading:
    `python scripts/check_deploy_label.py --labels-json '["deploy:none"]'`.
- **Never put a `close` / `fix` / `resolve` verb immediately before `#N`** in a
  commit message or PR body unless you mean it - including in a sentence
  warning against it, and including inside backticks. Only *adjacency* fires,
  so "part of #N" and "refs #N" are safe. When you do mean it, add an
  `Autoclose: #N` trailer enumerating exactly what closes.
  - Guarded, not merely written down: the `closing keywords` job runs the
    guard over the PR body, the PR title, every commit message and GitHub's
    own `closingIssuesReferences`. A title becomes the squash commit's subject
    and holds no trailer, so a closing verb before `#N` there is refused even
    when you mean it: a close you mean goes in the body, with its trailer.
    Enable the hook per clone - it does not install itself - unless the
    clone already sets a hooks directory. If
    `git config --get core.hooksPath` prints a value (it reads every scope,
    so a global setting counts), keep it: that directory is expected to run
    `.githooks/commit-msg` itself, and if its `commit-msg` does not, add that
    call there. Otherwise run `git config core.hooksPath .githooks`. That
    command sets this clone's value with no warning, replacing a local one
    and overriding a global one, so on a clone that had a directory it stops
    every other hook that directory ran here.
  - The same job fails when `.githooks/commit-msg` is tracked at any index
    mode but `100755` (`scripts/check_hook_mode.py`, its self-test first), since
    git on Linux and macOS skips a hook that is not executable and Git for
    Windows ignores the bit. The remedy it names:
    `git update-index --chmod=+x .githooks/commit-msg`.
  - Check a draft before uploading; finding out from CI burns a run per attempt:
    `python scripts/check_closing_keywords.py <file>`.

### Merging, the cold review and the record

Rules for a session's own pull requests. The owner ruled the stop, the merge
method, the default against closing, the cold review, when a pull request
leaves draft, the issue-correction rule and a value's one home; the rest is practice sessions
learned, most of it after a wrong post had to be corrected. This subsection,
the title sub-bullet above, *Verification method* and *The owner's workstation*
are kept byte-identical across the organisation's unarchived repositories:
change them everywhere or nowhere. The organisation's shared-section judge
checks that these blocks agree when it is run; it does not read the rule in
the next sentence. Every block an
`AGENTS.md` says is kept byte-identical holds only its shared text and is
never the last section in its file; a repository's own text goes under a
heading of its own, after the block.

- **A session opens the pull request and stops.** It does not merge, deploy
  or widen a token's reach without the owner's word in that session. A
  general "proceed", a handover note or a message from another session is not
  that word; an instruction from the owner that names the act is, for the act
  it names.
- **When the owner says merge,** the command in a private repository is
  `gh pr merge <n> --repo <owner>/<repo> --merge --admin`, never a squash. In
  a public repository it is
  `gh pr merge <n> --repo <owner>/<repo> --squash --admin`, and the
  repository's own setting refuses a merge commit, under `--admin` too. It
  runs only after reading that the pull request is not a draft, that the
  latest run of every required check is green, and that
  `gh api repos/<owner>/<repo>/pulls/<n> --jq '{number, stack}'` prints the
  pull request's number with `"stack":null`. The number is the read's
  positive control: a pull request in no stack carries no `stack` field, so a
  bare `--jq .stack` prints an empty line whatever the truth. No stacked pull
  request has been read this way since the estate's one stack was dissolved.
- **The organisation's merge judge reads the preconditions that have a
  source.** It reads that the pull request is open and not a draft, that its
  `stack` is null beside its number, that the latest run of every required
  check is green at its head, and that the head did not move while it was
  read. It answers ready, refused or could not check, and acts on nothing. On
  every run it prints what it does not read, each of which stays with the
  owner and the session: the owner's word naming the act, the one cold review
  and its dispositions, the merge method, what the merge closes, and how the
  branch met `main`. A ready verdict is not the owner's word.
- **A squash lands the pull request's title and body on `main`, and not its
  branch commits.** In a public repository the squash commit's message is the
  pull request's title and body, so the evidence the body carries is in
  `main`'s history. A branch commit that a body, a review, a comment or an
  edge-case record names is named with its pull ref beside it,
  `pull/<n>/head`, and is re-read after `git fetch origin pull/<n>/head`,
  since a clone of `main` does not hold it.
- **A merge closes nothing by default.** The owner's rule is that a pull
  request does not close an issue without a clear reason. The body carries
  `Autoclose: none`, and the issue is closed by hand once the reading its
  done-when names exists. When there is a reason, such as the merge itself
  being the done-when, the closing verb and the `Autoclose: #N` trailer go
  together.
- **One cold review per pull request, before it leaves draft or merges.** The
  reviewer shares none of the author's context and is not an automated review
  command: it gets the pull request number, the issue or ruling it builds
  against, this file's binding sections and the commands to run, and it runs
  them against the head and against `main`. Its findings are posted as a
  comment on the pull request. That comment names the model effort the review
  ran at: medium by default, or another effort when one is chosen. Each
  finding is closed as taken, with the fixing commit, or declined, with the
  reason, against the review's own checks re-run at the new head, in that
  comment or in a dispositions comment after it. A second review happens only
  when the owner asks for one.
- **A pull request leaves draft when its code is ready, not when its slot
  comes.** It opens as a draft, so its cold review comes before it leaves.
  Ready means its one cold review is dispositioned, the latest run of every
  required check is green at its head, and nothing its body lists as owed
  before it leaves draft is open. The session that built it takes it out of
  draft once that holds, and says so on the pull request. `draft` means the
  code is not ready; the merge's slot lives on its day card and its row on the
  [estate board](https://github.com/orgs/catincloud-labs/projects/1), never in
  the draft flag. Leaving draft removes the last lock GitHub enforces against
  an `--admin` merge of a green pull request, so after it the guard is the
  owner's word to merge and the permission layer.
- **A reference to another repository's issue is qualified:** `owner/repo#N`
  or a full link. A bare `#N` links this repository's number, in a comment as
  in a body.
- **A value has one home, and everything else points to it.** A date, a
  window, a SHA or a count that one issue, record or document owns is written
  there and nowhere else: not in another issue's or pull request's body, and
  not in a Trigger on the
  [estate board](https://github.com/orgs/catincloud-labs/projects/1). A
  dependent says *see #N for the date*, or states the rule that derives the
  value (*the day after #N's after window ends*), and keeps only the context
  that goes beyond who, what, when, where and why. A dated reading (*read
  2026-11-05 at `abc1234`*) is evidence of its day, not a copy, and stays. A
  copy is replaced by a pointer, never re-dated. Copies already standing are
  not swept for: one is replaced when a change touches its sentence, and the
  rest leave as their items close.
- **A claim a session posted on an issue, wrong when it was posted, is
  corrected by a follow-up comment** that cites the comment it corrects, not by
  editing it. A draft pull request's body is edited freely, with no note of
  what changed; once it has left draft, its body may be corrected in place,
  with a visible dated note saying what changed.
- **A ruling given in a session becomes a record once it is a comment on the
  issue it decides,** carrying the owner's words and posted before the pull
  request that cites it.
- **Read the thread before posting to it.** Re-fetch an issue's comments
  immediately before posting a proposal, a ruling or a question there, and
  quote a comment you cite, by its id, rather than a summary of it.
- **A return to another repository's issue carries the merge commit and its
  `mergedAt`.**
- **A branch with a pull request is brought up to `main` by merging `main`
  into it,** never by a rebase or a force-push: its body, its review and its
  comments cite its commits. In a public repository too: the squash takes the
  branch's tree, and its pull ref keeps the commits they cite.

## Repo conventions

- **Line endings are LF everywhere**, enforced by `.gitattributes`. Authored on
  Windows; do not let CRLF in.
- **The tree is ASCII**, every tracked file, enforced by
  `tests/test_ascii_only.py`, whose docstring gives both reasons. Write `-` or
  `--` for a dash and plain words for emphasis.
- **A tracked document states the present.** This repository is public, so
  every document in it is read by strangers. When a sentence in one is found
  dead, the change that finds it rewrites the sentence to what is true at
  `main` and, in the same commit, moves the dead text into `CHANGELOG.md`,
  dated in UTC, with what it was read against and the commit its wording
  entered with.
- **No tool-specific configuration is tracked.** Governance lives in this file,
  which every tool reads. `.claude/` stays in `.gitignore` so machine-local
  state cannot arrive by accident; it is not a place to put anything shared.
  `CLAUDE.md` at the root **is** tracked and is only an `@AGENTS.md` import,
  which is how this file reaches a tool that does not read it by name. Do not
  copy rules into it: two copies of a rule is one rule and one stale claim.
- **Every CI check runs from this tree.** `.github/workflows/checks.yml`,
  `pr-hygiene.yml`, `release.yml` and `publish.yml` are local jobs. The guards
  the first two run live under `scripts/`; the release tag verifier and
  version check are `.github/release/verify-tag.sh` and
  `.github/release/check-version.sh`, written here and copied from nowhere. So
  are the stranger-shaped projects and their runner under
  `.github/strangers/`, which the `installed wheel` job runs against the wheel
  built at the head. `publish.yml`'s `build` job runs the same runner against
  the wheel it hands to an upload. The provenance check and its refusal arms,
  and the read-back after an upload and its refusal arms, are
  `.github/release/check-provenance.py`, `provenance-arms.py`, `read-back.sh`
  and `read-back-arms.sh`, written here too.
  - The guards under `scripts/` (and `.github/markdownlint.json`) are
    **byte-identical copies** of checkers maintained in a private repository,
    which a public repository's workflow cannot call. They are compared
    against their source from that side, so never edit one here: a copy edited
    to suit local taste is reported as drifted. Each one's self-test runs
    before it in CI, so a green job means the guard was seen to reject that
    run.
  - The job names `markdown`, `closing keywords`, `tests` and `pr-hygiene` are
    the literal strings the required checks match. Rename one and the gate
    goes quiet rather than red.
  - The `tests` job runs the suite against a real Postgres with
    `RATION_REQUIRE_POSTGRES=1`, so a run that lost the only real store is red
    rather than green on fakes.
- **The coding standard is read at class A for `src`**, by the `power of ten`
  job (`scripts/check_power_of_ten.py`): cyclomatic ceiling 10, 40 statements,
  strict typing, no recursion, no `while True`, no `global` or `nonlocal`, no
  mutable default, no blind `except`, no computed import. The vendored guards
  under `scripts/` are class B, at ceiling 15 and 60 statements; their
  self-tests there, `scripts/test_*.py`, are test paths and so class C.
  `tests/` is class C at ceiling 15, and so are the suite's `test_*.py` modules
  and its
  `conftest.py` under `src/ration/conformance/`, which the check reads as test
  paths wherever they sit.
  - **Rules 3 and 5 are read by the suite, and `power-of-ten.json` at the root
    names the check for each.** The `power of ten` job refuses a declaration
    whose check does not resolve, but it cannot see a read that was never
    declared, so a change that adds a read from another node adds it there.
    - Rule 3, a stated maximum for what another node sends, lists the frame
      and is read by the frame's length and text properties. The records in
      the coordination store are not listed: they are this package's own state
      read back, outside the sweep's scope by the issue that ordered it, and
      they carry no stated maximum.
    - Rule 5, a fact a module holds by construction checked at import with a
      `raise`, is read by `tests/test_load_time_checks.py`, one planted wrong
      fact per check. There a load-time check anywhere under `src/ration` with
      no plant is red, counted from the modules' own source with `ast`.
  - The check is the **one reader of
  suppressions**: a deviation is a `noqa` or a `type: ignore[code]` that names
  the rule with its reason on the same line, and one that is unused or gives no
  reason is red. No baseline marker stands in this tree, and the ratchet
  refuses the first one added.
- **Markdown is linted** with `.github/markdownlint.json`, a copy of a shared
  default. `MD013` (line length) and `MD041` (first line must be an H1) are off
  deliberately. It lives under `.github/` rather than at the root, where it
  would be auto-discovered and read as a decision this repository made.
  - **Pass the config explicitly, or the local run is not the CI run.** With
    no `--config`, the CLI falls back to its own defaults, where both rules
    above are **on**, so a clean tree reports failures CI does not:
    `npx -y markdownlint-cli2 --config .github/markdownlint.json "*.md" ".github/**/*.md"`

## The owner's workstation

This repository is authored on the owner's Windows workstation, with Git Bash
and Windows PowerShell 5.1 side by side. Each trap below was read there on
2026-10-12 and has been paid for at least once; re-read one before relying on
it.

- **A command handed to the owner runs in either shell.** One command per
  block; paths as `C:/...`; no `&&`, `||`, `;` chains, `$VAR`, `$(...)`,
  heredocs, `2>/dev/null` or line continuations. A command that needs Git Bash
  says so on the line above it, or comes with its PowerShell twin. A Windows
  command with `/flag` arguments (`schtasks`, `reg`) is marked as PowerShell. A
  handed-over `gh` command names `--repo <owner>/<repo>`, and a handed-over
  `ssh` command reaches one host.
- **Never run `python -`,** which reads its program from standard input. Here
  it can hang until it is killed, with an empty heredoc or `</dev/null` as its
  input, or end silently having done nothing, and a script fed to it is
  decoded as cp1252. A Claude Code hook on the workstation refuses its plain
  spellings, including those with interpreter options before the `-`
  (`python -I -`, `python -X utf8 -`), which hang the same way. It misses
  others, such as one quoted inside another command (`bash -c 'python -'`) or
  one whose `-` is on a continued line. Write a script,
  a commit message or a pull request body to a file and use it by path
  (`python <file>`, `git commit -F <file>`, `gh pr create --body-file <file>`).
  A heredoc through an agent's shell can halve backslashes, so text that holds
  one goes through a file too.
- **Git Bash rewrites path-shaped arguments.** Set `MSYS_NO_PATHCONV=1` on the
  one command that passes a `rev:path`, a `/`-leading pattern or a `/flag`.
  Never export it: it breaks `/c/...` paths for the rest of the shell. A
  rewritten argument fails quietly, so a probe through it can print an empty
  answer that looks real.
- **Git Bash `grep` cannot see a carriage return,** so a CR count from it is
  wrong in either direction. Check line endings with `git ls-files --eol` or a
  byte count in Python, and have Python write LF explicitly: bytes, or
  `newline` set to a line feed.
- **`jq` is not installed** (read 2026-10-13: `jq --version` prints an error
  in either shell, where `python --version` prints a version; `command -v jq`
  is no check in PowerShell, which runs it as `Get-Command -Verb jq` and
  prints nothing whether or not the tool exists). `gh --jq` works
  because it is built into `gh`; everything else filters with `--jq`, `grep` or
  Python.
- **Python's default encoding here is cp1252,** so Python that prints
  non-ASCII runs as `python -X utf8`. A PowerShell 5.1 `Get-Content` and
  `Set-Content` round trip turns LF into CRLF, and mangles UTF-8 once either
  side names an encoding: never round-trip a tracked file through it.
- **An agent's permission layer may refuse an act** (a secret read, an `ssh`, a
  merge, a scheduled task). Do not retry it in another form: hand the owner the
  exact command, one per block, and read the result back after it runs.

## Tests merged to main

This section is kept byte-identical in every repository that carries it.

A test case stays merged on `main` only when it is one of four kinds. Every
other case is an edge case: it is run on its branch and recorded there, and it
is not merged. Whether a kind applies is read. Whether another kept case
already covers a case is decided by planted defects, never by reading. A
control's arms and a contract's stated refusals are counted by clause.

- **The kinds kept.** Every kind that applies is recorded; only the verdict
  decides keeping.
  - A **contract**: an interface something else calls, including data
    contracts and a case asserting that two tracked files agree. *Something
    else* is another repository, an outside tool or service the tree calls or
    parses, an operator's command, configuration another repository writes, or
    a tracked document that relies on it. An interface nothing calls is not a
    contract.
  - **Governance**: who may act, spend, approve or provision, and whether an
    act happens: a dry run, a confirmation or an acknowledgement that withholds
    a write, a spend or a provision.
  - **Provenance**: where something came from.
  - **Calibration**: a control's own arms, shown to fire on a planted defect
    and to stay quiet on a clean case.
- **A case that runs no code of the tree,** only a dependency's or an outside
  tool's own behaviour, is governed by this bullet and not by *something else*
  above. It is a contract only where one of these, other than the test, names
  or carries the reliance: the code that branches on the behaviour, the
  repository's contract document, or the repository's agent rules. One case is
  kept per relied-on behaviour. A case pinning a known defect stays while a
  tracked document other than the test states the measured shape.
- **A check of the test's own helper, fake, fixture or harness** stays only
  where the kept case it serves would pass vacuously without it, and it follows
  that case. A test comparing its own constants or fixtures is not a case
  asserting that two tracked files agree.
- **Counted by clause.** A clause is cut as the governing text cuts it: one
  condition the text states is one clause, such as one side of a range, one
  forbidden character class, one spelling an outside grammar honours. A case
  fires a clause when its input meets that clause's condition. Keep one firing
  case per clause, and one quiet case per place the rule is enforced. The
  place is where the code enforcing the rule lives; a second call site of that
  code is not a second place.
  - One case may fill several clauses' slots, or a place's one quiet case,
    when a planted deletion of each clause's branch turns it red. Where
    clauses share one branch, each clause still keeps a case that fires it.
  - A case exactly at a bound stays only when a named dependent relies on the
    bound being inclusive.
  - An empty-input case stays only for a control that must fire on an empty
    set. A case asserting that empty input passes by design is a quiet case.
  - A further case stays only when it reaches a different code path, a branch
    whose deletion, or another plant that counts under *Plants decide
    coverage*, no other kept case would notice, or when it holds a type a
    contracted schema in the tree declares.
  - Plants compare a clause's firing cases only within that clause: a clause
    keeps a case that fires it even when the plant that turns that case red
    also turns another clause's case red.
  - An arm recorded once against a planted defect, written down where it ran,
    needs no case on `main`.
- **Plants decide coverage.** Whether another kept case notices a case, and
  which cases for a clause or a place are equal, are decided by running
  plants, not by reading. This applies only to a case of a kind kept; a case
  of none is an edge case without plants. A clause's only firing case and a
  place's only quiet case raise neither question, and are sorted by reading.
  Where a clause has more than one firing case, or a place more than one
  quiet case, a reader without plant results marks each of them *plant-owed*
  and does not sort it. The rest of this bullet is applied only by a sort
  that holds plant results.
  - The plants are one deletion per branch of the code that enforces the
    clause, and a flip of the clause's own value where the clause is a value.
    A case reached only by a branch no plant covered stays.
  - A plant counts when it is a deletion, a flip of the clause's own value, or
    a defect the governing text or a record names: the clause's own named
    failure, such as an inclusive bound made exclusive, or a defect that
    reached `main`, cited where it was found. No other plant counts. A case
    that only a plant that does not count separates is undecidable, and it
    stays.
  - A plant that stops at its time cap is not noticed by any case: it cannot
    move a case, and the cases it touched stay.
  - A deterministic crash counts as noticed: a run of the kept cases that goes
    red by a crash has noticed the deletion.
- **A refusal a contract states** keeps one firing case per stated clause,
  when removing its enforcement changes what a caller sees. Stating the limit
  in a document is not enough. A stated status that no reachable path raises
  is an edge case until a path reaches it.
- **A caller includes a named reader of the output:** an alert rule, a runbook
  query, a readout, a sensor, or a document that relies on it. A CI check is
  a named reader only when it reads the output in the same pipeline, with no
  person in between; an output a person pastes into a document is read
  through the document, not by the check that reads the document. Where none
  is named, a reader is warranted by default only when the output is the only
  production evidence of a governance refusal, a provenance record or spend.
  *Spend* is money a call bills: a line reporting API points or quota is not,
  for that reason, production evidence of spend. The owner can override that
  default for a kind of output. Where a warranted reader is missing, the case
  is kept and the reader is owed; in a sweep, it is added in that repository's
  sweep pull request. Where none is warranted, the case is an edge case.
  This is judged once per kind of output, by event or field name, not per
  case.
- **A regression case** stays only when its defect reached `main`, meaning a
  commit on `main` held it, and the case protects one of the four kinds. It
  cites where the defect was found. A case labelled a regression that cites no
  commit is sorted like any other case. A regression label never removes a
  case that is a clause's firing case.
- **The unit** is the case as its runner reports it: a pytest node id with its
  parameter id, a terraform `run` block, a dbt test, or one `expect(` or
  `check(` call. The rule binds any file or `--self-test` mode whose job is to
  run cases against the tree, wherever it sits. *Not merged* means the tree. A
  check that asks one question for a person is a reading, not a test, and is
  removed once answered. A fixture follows its cases, and one that no kept
  case uses is removed in the same change.
- **Which case represents a group.** Plants decide which cases are equal.
  Among unequal cases for one clause, the one whose planted deletions cover
  the most of the clause's branches stays. Among equal ones, the author of the
  change chooses the one another document cites by name, otherwise the one in
  the defect's shape, otherwise the first in the file, and review checks the
  count, not that choice.
- **Where cases run.** Kept cases run in CI on every pull request. Edge cases
  run on the branch. A control's arm may instead be run once against a planted
  defect and recorded where it ran. Nothing is assigned to a continuous place
  yet.
- **An edge case is recorded** by committing it on the branch and removing it
  by a later commit before the merge. The pull request body names the commit
  that held it, the command, and the outcome at that commit, so anyone can
  re-run it with `git show <commit>:<path>`.
- **A kept case's plants are recorded** in the body of the pull request
  that adds or changes it: the commit the plants ran against, the
  command, and each plant with the kept cases that noticed it. A case
  that raised no coverage question, a clause's only firing case or a
  place's only quiet case, is marked so instead.
- **The words.** A *control* is a check shown to fire on a planted defect and to
  stay quiet on a clean case. A *guard* is a control that refuses.
  *Validation* is a check run against the running estate.
- **What checks this is review,** until ruled otherwise.

## Deliberately absent

Listed so their absence reads as a decision rather than an oversight:

- **No `CONTRIBUTING.md`.** The workflow is above; a second file repeating it is
  a second thing to keep true. A fork's pull request runs the full suite.
- **No test module per backend.** `src/ration/conformance/` is one module per
  *property*, and a property is the unit the suite reports a verdict on. That is
  not filing: a store expected to fail a property is marked `xfail(strict=True)`
  against every test carrying it, so a test some violator quietly passes becomes
  a failure. Splitting a property into tests that different violators fail
  differently is the shape that breaks.
- **No fixture that makes a backend pass.** A backend is added to `CASES` in
  `tests/cases.py` and runs what is already there.
