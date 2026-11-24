"""Where a role is, answered by the lease that already says who holds it.

Reaching a service through its hostname quietly ties that service's role to
one machine. Services here find each other by **role** instead, and a role has
to be turned into a host somewhere. This module does the turning, and it is
kept thin deliberately.

**It adds no state of its own, so it sits in this repository instead of a
separate one.** Pieces are grouped by the state each one owns, and the
substrate travels with its services because their state is the same state.
Which holder has a role at this moment is *already* recorded by the lease, so
addressing is only a **reading** of that record. The endpoint rides as the
lease payload: claiming a role and saying where it is happen in a single
write, and no second record exists to drift.

**The rejected design wrote the address into the network's name service and
had callers look it up through DNS.** That fails for an old reason. The lease
already settles which process holds a role, so a name record would hold
*that fact twice over*, and a duplicate falls behind at the worst instant there
is -- a failover. Two copies of a fact is one fact and one stale claim. A name
record also carries no fencing token, which is the same objection made
concrete: a cached name goes on pointing at a holder whose lease has passed to
someone else, and the caller has no way to notice.

The network still carries the packets. It is the transport, not a ledger of
who holds what; those are separate jobs, and coordination is the second one.

**The cost, written down because it exists.** Resolving a service now needs
the coordination store to be reachable. The store refuses under partition, so
a peer cut off from it could already take no lease; now it cannot resolve a
role either. That enlarges the reach of a failure the lease layer already
accepts instead of adding a new kind -- but it is an enlargement all the same,
and it is stated here so nobody has to find it out.
"""

from __future__ import annotations

from dataclasses import dataclass

from ration.contract import Store
from ration.lease import Lease, acquire

__all__ = ["ROLE_PREFIX", "Address", "announce", "key_for", "resolve"]

#: Namespaced so a role can never collide with a key some other consumer of the
#: contract chose. The prefix is part of the wire format rather than a
#: convenience: two consumers agreeing on a key by accident is a bug that
#: presents as an unrelated service losing its lease.
ROLE_PREFIX = "role/"


@dataclass(frozen=True)
class Address:
    """Where a role is, and the generation that answer belongs to."""

    role: str
    #: Whatever the transport needs -- a host, a `host:port`, a URL. This module
    #: does not parse it, because the moment it does it has an opinion about the
    #: transport, and the constraint this module serves is about roles, not
    #: about protocols.
    endpoint: str
    #: The holder's identity, from the lease token.
    holder: str
    #: **The fencing token, and the reason this is a dataclass rather than a
    #: string.** It is the lease version the address was read at. A caller that
    #: carries it can be refused by a callee that has since seen a newer one,
    #: which is precisely what a cached name record cannot offer. An address
    #: without a generation is a guess with good manners.
    version: int


def key_for(role: str) -> str:
    """The store key a role's address lives at."""
    if not role:
        raise ValueError("a role needs a name")
    if role.startswith(ROLE_PREFIX):
        # Otherwise `key_for(key_for(r))` silently addresses a different role,
        # and the failure is a lookup that succeeds against the wrong thing.
        raise ValueError(f"role {role!r} is already a role key")
    return f"{ROLE_PREFIX}{role}"


def announce(
    store: Store,
    role: str,
    endpoint: str,
    holder: str,
    *,
    ttl: float,
) -> Lease | None:
    """Claim `role` and publish `endpoint` as where it is. `None` if held.

    **`ttl` is required, and that is the whole difference between this and a
    name record.** A lease with no expiry keeps answering for a holder that
    stopped existing, which is the stale-DNS failure arriving through the door
    this module was built to close. The lease layer permits `ttl=None` because
    not every claim is an address; an address is not one of those cases.

    Refusal is a `None`, not an exception, and `Unreachable` is deliberately
    **not** caught -- both inherited from `acquire`, and for its reasons. A
    store that cannot be reached must not read as a role that is free.
    """
    if ttl is None or ttl <= 0:
        raise ValueError("an address needs an expiry; see this function's docstring")
    if not endpoint:
        raise ValueError("a role needs somewhere to be")
    return acquire(
        store, key_for(role), holder, ttl=ttl, payload=endpoint.encode("utf-8")
    )


def resolve(store: Store, role: str) -> Address | None:
    """Where `role` is, or `None` if nobody currently holds it.

    **Every call reads the store. There is no cache here and adding one would
    reintroduce the defect this module exists to avoid** -- see the module
    docstring, and `tests/test_addressing.py`, where a resolver that does cache
    must go on answering for a role whose lease has run out.

    Expiry is not evaluated here. The contract's property 2 puts it in the
    store, so an expired role arrives as an absent record and this function
    cannot accidentally disagree with the thing that granted the lease.
    """
    reading = store.read(key_for(role))
    if reading.record is None:
        return None
    return Address(
        role=role,
        endpoint=reading.record.payload.decode("utf-8"),
        holder=reading.record.token,
        version=reading.version,
    )
