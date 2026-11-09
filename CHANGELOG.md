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
