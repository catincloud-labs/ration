# The coordination substrate: what each piece guarantees, what it refuses, and the test that shows it

- **Status:** living
- **Describes:** `src/ration/contract.py`, `src/ration/lease.py`,
  `src/ration/pool.py`, `src/ration/addressing.py`, `src/ration/publish.py`,
  `src/ration/frame.py`, `src/ration/postgres.py`,
  `src/ration/duckdb_store.py`, `src/ration/memory.py`, `tests/conformance/`,
  `tests/support/backends.py`, `tests/support/codecs.py`,
  `tests/violators.py`, `tests/frame_violators.py`, `tests/test_lease.py`,
  `tests/test_pool.py`, `tests/test_addressing.py`,
  `tests/test_addressing_cross_process.py`, `tests/test_publish.py`,
  `tests/test_frame.py`, `tests/test_postgres_conflict_version.py`,
  `tests/test_duckdb_single_process.py`,
  `tests/test_the_suite_discriminates.py`
- **Reviewed:** 2026-11-06 at `73428ba` - first reading: every test this page
  names was run at that commit against the in-memory cases, DuckDB and a real
  Postgres with `RATION_REQUIRE_POSTGRES=1`, and each one passed, failed under
  strict xfail for the violator registered against its property, or was
  skipped where a store has no in-process seam for the deterministic gate

This page **describes and decides nothing.** The contract is stated in
`src/ration/contract.py` and decided by `tests/conformance/`; where this page
and the suite disagree, the suite is the contract and this page is the defect
(`AGENTS.md`, *The README describes; the suite decides*). Its job is narrower
than the README's: to put every guarantee the substrate and its services make
beside the one test that demonstrates it, and beside what the piece refuses,
so a reader can check each sentence by running the test it names. The README
carries the reasons and the history of what building each piece found; this
page does not repeat them.

The header says what the page covers (**Describes**) and the commit it was last
judged against (**Reviewed**). Whether the code has moved since is computed,
not remembered:

```sh
git log --oneline 73428ba..HEAD -- src/ration tests
```

An empty answer means nothing the page describes has moved since its review;
it is a statement about the paths, not about whether the page is true.

## How to read a citation

Every guarantee names a test as `file::function`, which is a pytest node id. Run
one with, for example:

```sh
pytest -rA "tests/test_pool.py::test_a_pool_grants_exactly_its_capacity"
```

**A test under `tests/conformance/` runs against every registered
implementation, not just the correct one.** The correct cases must pass it. An
implementation built wrong on purpose and registered against that test's
property is marked `xfail(strict=True)`, so it must fail, and a violator that
passes is a red run. That is the sense in which a property here is *shown*: a
store that keeps it passes and a store built to break exactly it is rejected.
The registries are the `CASES` list in `tests/support/backends.py` and the
`CODECS` list in `tests/support/codecs.py`; each entry names an implementation
and the properties it is expected to break. Some entries span several lines,
so print each with its following lines:

```sh
grep -n -A3 "_case(" tests/support/backends.py tests/support/codecs.py
```

The Postgres cases are registered only when `RATION_POSTGRES_DSN` names a
server; the README's *Running it* gives the commands. Without one, a run drops
the only store more than one process can share, and the conformance tests
below are then evidence about the in-memory fakes alone.

Tests outside `tests/conformance/` run against a correct store. Where one of
them stands on concurrency, it is a **threaded probe**: claimants churning
against the store, counting any grant made twice. A probe that finds nothing
has not shown there was nothing to find, so each is paired with a **negative
control**, a deterministic gate. The gate parks one claimant inside the gap
between the read and the write of `naive`, a store with nothing joining the
two, runs another to completion, and requires the guarantee to break. The
pool's and the publication's gates then run the same parked interleaving
against a correct store, which must keep it. The lease's gate has no such arm
of its own; its docstring points to the pool's, whose grant is made by
`lease.acquire`. The page names the probe and the gate.

## The substrate: one key, compare-and-set against a version

The whole store is two operations, `read` and `compare_and_set`, on one key at
a time (`Store` in `src/ration/contract.py`). Four numbered properties hold of
it, and the operation itself is a fifth:

| Guarantee | What is refused | Shown by | Violators it rejects |
| --- | --- | --- | --- |
| A write applies only at the expected version. Absence is a version (`ABSENT`), so creation is a compare-and-set like any other | An upsert: creating a key that already exists. A write that reports a conflict and lands anyway. A conflict carrying a version the key never held | `tests/conformance/test_compare_and_set.py::test_the_write_lands_only_at_the_expected_version` | `create-always`, `conflict-writes`, `echoes-expected` |
| The comparison and the write are one step: two writers racing from one version do not both apply, and neither do two creators racing from absence | Read-then-write | `tests/conformance/test_atomicity.py::test_two_writers_racing_from_one_version_do_not_both_apply` (a deterministic gate, where a store has an in-process seam), `tests/conformance/test_atomicity.py::test_concurrent_increments_lose_nothing` (a threaded probe, the only instrument where it has none), `tests/conformance/test_atomicity.py::test_two_creators_racing_from_absence_do_not_both_apply` | `naive`, `conflict-writes`, `postgres-naive` |
| 1. The version rises per key and is never reused, not even after the key is deleted | A counter that restarts when the value goes; a counter shared across keys | `tests/conformance/test_version.py::test_versions_rise_per_key_and_are_never_reused` | `recycling`, `global-counter` |
| 2. Expiry is evaluated by the store, against its own clock, at the moment it is asked. `ttl` is a duration; there is no parameter for a caller's deadline | The caller's clock; a store clock read early and acted on later | `tests/conformance/test_expiry.py::test_expiry_is_decided_by_the_store_when_it_is_asked` | `client-expiry`, `stale-clock` |
| 3. A caller that cannot reach the store has acquired nothing: `Unreachable` is raised, not returned | Treating silence as "nothing there" | `tests/conformance/test_unreachable.py::test_a_caller_that_cannot_reach_the_store_acquires_nothing` | `fail-open` |
| 4. A write whose answer was lost is resolvable by reading, because the caller's token is in the store. `resolve` tests the version before the token, so a caller rewriting a key it already holds is not credited with its earlier write | Keeping the payload and losing the token; deciding by token alone | `tests/conformance/test_ambiguity.py::test_a_lost_answer_is_recovered_by_reading`, `tests/conformance/test_ambiguity.py::test_a_rewriters_lost_answer_is_resolved` | `token-dropping` |

**What the substrate refuses by having no place for it.** `Store` has no second
key, no ordering across keys, no watch, no queue and no lock held across a
round trip. These are absences in the Protocol rather than tests: adding any of
them is a change to `src/ration/contract.py`, and so to the contract.

**A conflict's version is not the key's current version.** `Conflict.version`
is a version the key has held. Under concurrency `PostgresStore` reports the
version the loser came *from*, and the contract permits it; a caller that needs
the current version reads. Pinned, deterministically, by
`tests/test_postgres_conflict_version.py::test_a_losing_update_reports_the_version_it_came_from`
and `tests/test_postgres_conflict_version.py::test_a_losing_create_reports_absence`.

**Passing the suite is not being a shared store.** `duckdb` is registered with
no violations and passes every conformance test run against it (the
deterministic atomicity gate is skipped for it, and the threaded probe
decides), and a second process cannot
open its database at all. The suite cannot say so, because the contract does not
govern deployment topology; `tests/test_duckdb_single_process.py` says it, in
`tests/test_duckdb_single_process.py::test_a_second_process_cannot_open_the_database_at_all`,
with `tests/test_duckdb_single_process.py::test_the_file_is_openable_once_this_process_lets_go`
as its control.

## The lease: one holder per key

`src/ration/lease.py`: `acquire`, `renew` and `release`, each one
compare-and-set, and no method added to `Store`. The version a grant landed at
is its **fencing token**.

| Guarantee | Shown by |
| --- | --- |
| A held key is refused to a second holder: `acquire` returns `None` | `tests/test_lease.py::test_a_grant_is_exclusive` |
| Under contention, no key is granted to two holders at once | `tests/test_lease.py::test_a_grant_is_never_held_twice_under_load`, with the negative control `tests/test_lease.py::test_a_non_atomic_store_grants_a_key_that_is_already_held` |
| A holder reacquiring under its own token is handed the grant it holds, not refused | `tests/test_lease.py::test_a_holder_reacquiring_its_own_grant_is_told_it_holds_it` |
| Renewing moves the grant to a new version and spends the old one | `tests/test_lease.py::test_renewing_moves_the_grant_forward_and_spends_the_old_one` |
| A holder whose key was taken cannot renew | `tests/test_lease.py::test_a_holder_that_lost_the_key_cannot_renew` |
| Expiry alone does not break the chain: an expired grant nobody took still renews, because its version has not moved | `tests/test_lease.py::test_an_expired_grant_nobody_took_can_still_be_renewed` |
| A released key, and an expired one, are free | `tests/test_lease.py::test_a_released_grant_is_free`, `tests/test_lease.py::test_an_expired_grant_is_free` |
| Releasing a grant already lost does not disturb the new holder | `tests/test_lease.py::test_releasing_a_lost_grant_does_not_disturb_the_new_holder` |
| An unreachable store grants nothing, and is not reported as a key that is taken | `tests/test_lease.py::test_an_unreachable_store_grants_nothing` |
| An ambiguous grant or renew is recovered if it landed and not claimed if it did not | `tests/test_lease.py::test_an_ambiguous_grant_that_landed_is_recovered`, `tests/test_lease.py::test_an_ambiguous_grant_that_never_landed_is_not_claimed`, `tests/test_lease.py::test_an_ambiguous_renew_that_landed_is_recovered`, `tests/test_lease.py::test_an_ambiguous_renew_that_never_landed_is_not_claimed` |
| An ambiguous release reports `False` rather than guessing | `tests/test_lease.py::test_an_ambiguous_release_gives_up_rather_than_guessing` |

**What it refuses.** Waiting: a refusal is returned and the caller writes the
loop. Retrying a conflict from `Conflict.version`, the one number the contract
declines to promise. Distinguishing an applied ambiguous release from a key
someone else took: both read the same, and the lease needs only that the
caller no longer holds the key, so `release` claims the lesser answer.

## The pool: a bounded number of holders, refused rather than overdrawn

`src/ration/pool.py`: a pool of N grants is N keys, each a lease, because the
store expires keys rather than elements inside a value. Capacity is the
number of keys and is written nowhere in the store. The pool adds one
operation, a different way of choosing which key to take, and a read-only
`holders` sample; it has no `renew` and no `release` of its own.

| Guarantee | Shown by |
| --- | --- |
| A pool grants exactly its capacity, and the next claimant is refused: **refused rather than overdrawn** | `tests/test_pool.py::test_a_pool_grants_exactly_its_capacity` |
| Under contention, no slot is held twice | `tests/test_pool.py::test_a_slot_is_never_held_twice_under_load`, with the negative control `tests/test_pool.py::test_a_non_atomic_store_grants_one_slot_to_two_holders` |
| A holder retrying after a lost answer is handed the slot it already holds, even behind a free one, rather than a second slot | `tests/test_pool.py::test_a_holder_retrying_is_handed_the_slot_it_already_has`, `tests/test_pool.py::test_a_retry_finds_its_grant_behind_a_free_slot` |
| A pool grant renews and releases as a lease, through `src/ration/lease.py` unchanged | `tests/test_pool.py::test_a_pool_grant_renews_and_releases_as_a_lease` |
| A released slot, and an expired one, are granted again | `tests/test_pool.py::test_a_released_slot_is_granted_again`, `tests/test_pool.py::test_an_expired_slot_is_granted_again` |
| An unreachable store grants no slot, and is not reported as a full pool | `tests/test_pool.py::test_an_unreachable_store_grants_no_slot` |
| The scan's starting slot is a property of the holder, not of the interpreter that ran it | `tests/test_pool.py::test_the_rotation_does_not_depend_on_the_interpreter` |

**What it refuses.** Waiting, for the lease's reason. Taking a slot freed
behind the scan: it is missed until the next call, which over-refuses. A
consistent count of a moving pool: `holders` reads slots one at a time and is a
sample, not a snapshot.

## Addressing: where a role is, read from the lease that holds it

`src/ration/addressing.py`: a role is a lease under the `role/` prefix, and the
address is that lease's payload, so announcing a role and holding it are one
operation. `Address.version` is the lease version the answer was read at, a
fencing token a callee can refuse.

| Guarantee | Shown by |
| --- | --- |
| A role resolves to the endpoint its holder announced, and to nothing when nobody holds it | `tests/test_addressing.py::test_a_role_resolves_to_where_its_holder_said_it_was`, `tests/test_addressing.py::test_a_role_nobody_holds_resolves_to_nothing` |
| A held role is refused to a second announcer | `tests/test_addressing.py::test_a_second_holder_cannot_announce_a_held_role` |
| A released role stops resolving and can move; an expired one stops resolving | `tests/test_addressing.py::test_a_released_role_stops_resolving_and_can_move`, `tests/test_addressing.py::test_an_expired_role_stops_resolving` |
| The expiry assertions measure the store, not the passage of time: a deliberately caching resolver is required to keep answering for an expired role | `tests/test_addressing.py::test_a_caching_resolver_still_answers_for_an_expired_role` |
| The generation moves when the role does | `tests/test_addressing.py::test_the_generation_moves_when_the_role_does` |
| An address must expire: `ttl` is required and must lie in the future | `tests/test_addressing.py::test_an_address_without_a_future_expiry_is_refused` |
| An empty role or endpoint is refused, and so is a role key passed as a role name | `tests/test_addressing.py::test_a_role_without_a_name_or_an_endpoint_is_refused`, `tests/test_addressing.py::test_a_role_key_is_refused_as_a_role_name` |
| Across operating-system processes, each with its own store from a DSN: a role announced in one resolves in another, a second process is refused while it is held, and once it moves the stale holder is fenced | `tests/test_addressing_cross_process.py::test_a_role_announced_in_one_process_resolves_in_another`, `tests/test_addressing_cross_process.py::test_a_second_process_is_refused_while_the_role_is_held`, `tests/test_addressing_cross_process.py::test_the_role_moves_and_the_stale_holder_is_fenced` |

**What it refuses.** A cache: every `resolve` reads the store. Parsing the
endpoint, which is the transport's. An address with no expiry, which the lease
layer itself permits. A process is not a host: the cross-process tests remove
shared in-process state as an explanation, and do not reach a network
partition.

## Publication: a generation pointer that is superseded, never expired

`src/ration/publish.py`: a topic is one key under the `topic/` prefix holding a
pointer to an artefact, and its generation is the store's version for that
key. The artefact is an opaque reference, never parsed; content-named bytes are
immutable and need no coordination.

| Guarantee | Shown by |
| --- | --- |
| A published topic reads back what its publisher pointed at; a topic never published reads as nothing | `tests/test_publish.py::test_a_published_topic_reads_back_what_its_publisher_pointed_at`, `tests/test_publish.py::test_a_topic_nobody_published_reads_as_nothing` |
| The first publication is fenced like any other: two first publishers from `UNPUBLISHED`, one refused | `tests/test_publish.py::test_the_first_publication_is_fenced_like_any_other` |
| Advancing spends the generation it advanced from, and a stalled publisher cannot overwrite a newer publication | `tests/test_publish.py::test_advancing_spends_the_generation_it_advanced_from`, `tests/test_publish.py::test_a_stalled_publisher_cannot_overwrite_a_newer_publication` |
| A reader can advance from the generation it read | `tests/test_publish.py::test_a_reader_can_advance_from_the_generation_it_read` |
| A publication does not expire: it stands across a clock advance that expires a leased address in the same store | `tests/test_publish.py::test_a_publication_outlives_what_an_address_does_not` |
| An unreachable store publishes nothing, and does not read as a topic never published | `tests/test_publish.py::test_an_unreachable_store_publishes_nothing_and_reads_as_nothing_either` |
| An ambiguous first publication or advance is recovered if it landed, carrying the new artefact, and not claimed if it did not | `tests/test_publish.py::test_an_ambiguous_first_publication_that_landed_is_recovered`, `tests/test_publish.py::test_an_ambiguous_first_publication_that_never_landed_is_not_claimed`, `tests/test_publish.py::test_an_ambiguous_advance_that_landed_carries_the_new_artefact`, `tests/test_publish.py::test_an_ambiguous_advance_that_never_landed_is_not_claimed` |
| An ambiguous republish of the artefact already standing is not claimed, decided by the unmoved version alone | `tests/test_publish.py::test_an_ambiguous_republish_of_the_standing_artefact_is_not_claimed` |
| A publisher racing itself is not handed an artefact it did not publish, decided by the payload | `tests/test_publish.py::test_a_publisher_racing_itself_is_not_handed_an_artefact_it_did_not_publish` |
| An empty topic or artefact is refused, and so is a topic key passed as a topic name | `tests/test_publish.py::test_a_topic_without_a_name_or_an_artefact_is_refused`, `tests/test_publish.py::test_a_topic_key_is_refused_as_a_topic_name` |
| Under contention, no publication is silently destroyed | `tests/test_publish.py::test_no_publication_is_silently_destroyed_under_load`, with the negative control `tests/test_publish.py::test_a_non_atomic_store_advances_twice_from_one_generation` |

**What it refuses.** A TTL: `publish` has no parameter for one. A retract: a
publication is superseded, never deleted. Retrying a refused advance: the
caller reads `current` and decides. A watch: consumers poll, so staleness is
detectable, not pushed. Two keys moving together, such as an artefact and its
index: that is a guarantee the contract refuses, and providing it would change
the contract.

## The frame: a checked carrier, with no state of its own

`src/ration/frame.py`: a fixed big-endian binary header (`HEADER_SIZE`; the
layout table is in the module docstring) around a body the module never looks
inside. It owns no key. It leans on the contract once: a lease version, which
property 1 makes monotonic and never reused, is a sender's epoch. A frame can
also travel as text, base64url with no padding, for a route that takes no
body.

The frame has a conformance suite of its own, run against codecs built wrong on
purpose under the same strict xfail:

| Guarantee | Shown by | Violators it rejects |
| --- | --- | --- |
| The bytes present honour the declared length, exactly: a short header, a short body and trailing bytes are each refused | `tests/conformance/test_frame_length.py::test_the_bytes_present_must_honour_the_declared_length` | `unchecked-length`, `ignores-trailing` |
| A flipped bit anywhere, header or body, is refused as corruption: the CRC-32 covers the header as well as the body | `tests/conformance/test_frame_integrity.py::test_a_flipped_bit_anywhere_is_refused_as_corruption` | `unchecked-crc`, `body-only-crc` |
| An unknown frame version is refused as that, before its layout is assumed | `tests/conformance/test_frame_version.py::test_an_unknown_version_is_refused_before_its_layout_is_assumed` | `unchecked-version`, `crc-before-version` |
| A kind the registry does not name is refused | `tests/conformance/test_frame_kind.py::test_an_unregistered_kind_is_refused` | `unchecked-kind` |
| A receiver accepts exactly the next sequence, or a higher epoch at count zero; a duplicate, a gap, a replay and an older epoch are refused, and the ledger moves on acceptance only | `tests/conformance/test_frame_sequence.py::test_exactly_the_next_sequence_or_a_fresh_epoch_at_zero` | `unchecked-sequence`, `counter-only`, `sequences-before-checking` |
| Only a frame's one canonical text is read; any other string is refused as `malformed-text` before a frame check runs, and a fault in the bytes under a well-formed text is refused by the frame | `tests/conformance/test_frame_text.py::test_only_the_canonical_text_is_read_as_a_frame` | `lenient-text`, `library-strict`, `skips-text-decode`, `accepts-non-canonical`, `drops-dangling-character`, `collapses-layers` |

And against the reference codec alone:

| Guarantee | Shown by |
| --- | --- |
| The header is the layout the module states | `tests/test_frame.py::test_the_header_is_eighteen_bytes_in_the_stated_layout` |
| Decoding bytes or text never raises: every fault is a `FrameRefusal` with a control from the closed set `CONTROLS` | `tests/test_frame.py::test_decode_returns_on_anything_and_never_raises`, `tests/test_frame.py::test_decode_text_returns_on_anything_and_never_raises` |
| Encoding raises on a sender's own mistake | `tests/test_frame.py::test_encode_raises_on_a_senders_own_mistake` |
| The frame's refusals cannot be mistaken for a consumer envelope's | `tests/test_frame.py::test_the_frames_refusals_cannot_be_mistaken_for_the_envelopes` |
| An epoch whose count is exhausted refuses to wrap | `tests/test_frame.py::test_an_exhausted_epoch_refuses_to_wrap` |

**What it refuses, and what that costs.** A sender identity in the header: which
sender a frame belongs to is the receiver's knowledge, and a field the frame
cannot verify is not carried. Any opinion about the body. A kind outside
`KINDS`, a closed registry. Authentication: the frame carries a CRC, not a
MAC. The CRC and the sequence say a frame arrived as sent, once; neither says
who may send it. The stated cost:
a receiver whose ledger has seen nothing takes the first frame as its baseline,
so a replay against a fresh ledger is not caught
(`tests/test_frame.py::test_a_fresh_ledger_takes_the_first_frame_as_its_baseline`
pins that behaviour).

## The suite's own bookkeeping

A strict xfail catches a violator that passes its own property. It cannot catch
a property nothing violates, or a violator whose property no longer exists.
`tests/test_the_suite_discriminates.py` does, for the store registry and the
codec registry alike:

| Guarantee | Shown by |
| --- | --- |
| Every conformance test declares the property it decides | `tests/test_the_suite_discriminates.py::test_every_conformance_test_declares_the_property_it_decides` |
| Every property a test decides has a violator expected to fail it | `tests/test_the_suite_discriminates.py::test_every_property_the_suite_tests_has_a_violator` |
| Every violator names a property some test decides | `tests/test_the_suite_discriminates.py::test_every_violator_names_a_property_the_suite_actually_tests` |
| At least one registered implementation is expected to pass everything | `tests/test_the_suite_discriminates.py::test_the_suite_is_run_against_something_expected_to_pass` |
| With `RATION_REQUIRE_POSTGRES=1`, a run without the Postgres case is red rather than green on fakes | `tests/test_the_suite_discriminates.py::test_a_real_backend_is_present_where_one_is_required` |

## What the suite does not show

Stated so each reads as a known absence rather than a discovery:

- **Version reuse after a store is restored from a backup.** Property 1's
  violators are one process misbehaving; a restore is a lifecycle event between
  store instances, which no in-process implementation expresses.
- **That a threaded probe found nothing to find.** Where a store has no
  in-process seam (`postgres`, `postgres-naive`, `duckdb`), atomicity is decided
  by the threaded probe, and a probe that finds nothing has not shown there was
  nothing. A run reports the gate as skipped for those cases.
- **Any store not registered in `tests/support/backends.py`.** A store's
  guarantee is shown by running this suite against that store.
- **A network partition.** The cross-process tests run on one machine.

## When a sentence on this page dies

The change that finds it rewrites the sentence to what is true at `main` and,
in the same commit, moves the dead text into `CHANGELOG.md`, dated in UTC, with
what it was read against and the commit its wording entered with (`AGENTS.md`,
*Repo conventions*). This page has no history file of its own.
