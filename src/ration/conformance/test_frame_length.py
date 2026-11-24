"""Frame property 1: the bytes present honour the declared length, exactly, within the maximum.

Four of the frame's hostile cases land here -- truncated mid-header, truncated
mid-body, a length larger than the bytes present, and a length smaller than
them -- and the reader can only tell two of those four apart. Fewer bytes
than the header promises is one observation whether the body was cut or the
length lied upward, so both carry `truncated` and the reason says which was
seen. More bytes than promised is the other observation, and it is a
refusal rather than a tolerance because HTTP hands the reader one request's
body: nothing past the frame is a second frame.

The maximum is the other half of the same field. A length the four-byte field
can hold is not a length a receiver must accept: past `MAX_BODY_LENGTH` the
frame is refused as `oversized`, whether the header declares too much or the
bytes present are more than the largest frame holds, and a header alone is
enough to say so. The last is what lets a receiver refuse before it buffers:
told `truncated`, it would read on for the body.

Violated by `unchecked-length`, by `ignores-trailing`, and by `no-ceiling`
(`NoCeilingCodec` in `ration.conformance.frame_violators`), which takes
the field's own limit as the frame's. That last violator is the one the
coding standard's rule 3 names for frames read as bytes: `power-of-ten.json`
declares this module as the check that reads the maximum.

Measures: README.md, Frame property 1
Measures: scripts/check_power_of_ten.py, rule 3
"""

from __future__ import annotations

import pytest

from ration.frame import (
    HEADER_SIZE,
    MAX_BODY_LENGTH,
    OVERSIZED,
    TRAILING_BYTES,
    TRUNCATED,
    Frame,
    FrameRefusal,
    Sequence,
)
from ration.conformance.support.codecs import BODY, CodecUnderTest


@pytest.mark.conformance("frame-length")
def test_the_bytes_present_must_honour_the_declared_length(
    codec: CodecUnderTest,
) -> None:
    healthy = codec.healthy(Sequence.start(7))

    # Truncated mid-header: not even enough bytes to say what this is.
    refused = codec.decode(healthy[:10])
    assert isinstance(refused, FrameRefusal), refused
    assert refused.control == TRUNCATED, refused
    assert isinstance(codec.decode(healthy), Frame)

    # Truncated mid-body: the header is intact and promises more than arrived.
    refused = codec.decode(healthy[:-5])
    assert isinstance(refused, FrameRefusal), refused
    assert refused.control == TRUNCATED, (
        "a body cut short is a truncation, and a reader that names it anything "
        f"else is reporting the symptom it noticed last: {refused}"
    )
    assert isinstance(codec.decode(healthy), Frame)

    # A length that lies upward, with a CRC honest about the lie: the length
    # check has to decide this one on its own, before the CRC gets a look.
    refused = codec.decode(codec.forge(healthy, length=len(BODY) + 7))
    assert isinstance(refused, FrameRefusal), refused
    assert refused.control == TRUNCATED, refused
    assert isinstance(codec.decode(healthy), Frame)

    # Trailing garbage after a complete frame.
    refused = codec.decode(healthy + b"\x00garbage")
    assert isinstance(refused, FrameRefusal), (
        "bytes past the declared body were decoded away, so the frame handed "
        f"on is one no sender built: {refused}"
    )
    assert refused.control == TRAILING_BYTES, refused
    assert isinstance(codec.decode(healthy), Frame)

    # A length that lies downward, honestly checksummed over the shorter span:
    # the declared frame is whole and there are still bytes left over.
    refused = codec.decode(codec.forge(healthy, length=len(BODY) - 3))
    assert isinstance(refused, FrameRefusal), refused
    assert refused.control == TRAILING_BYTES, refused
    accepted = codec.decode(healthy)
    assert isinstance(accepted, Frame)
    assert accepted.body == BODY

    # The largest body a receiver must accept is accepted: the bound is the
    # most, not one short of it.
    largest = codec.forge(healthy, body=bytes(MAX_BODY_LENGTH))
    accepted = codec.decode(largest)
    assert isinstance(accepted, Frame), (
        f"a body of exactly the maximum was refused: {accepted}"
    )
    assert len(accepted.body) == MAX_BODY_LENGTH

    # One byte past it, declared and present, with a CRC honest about both:
    # every other check passes, so only the maximum can refuse it.
    refused = codec.decode(codec.forge(healthy, body=bytes(MAX_BODY_LENGTH + 1)))
    assert isinstance(refused, FrameRefusal), (
        "a body past the maximum was accepted, so a receiver must buffer "
        f"whatever the four-byte field declares: {refused!r}"
    )
    assert refused.control == OVERSIZED, refused
    assert isinstance(codec.decode(healthy), Frame)

    # A header alone that declares past the maximum: refused on what it
    # declares, before the body is asked for. `truncated` here would tell the
    # receiver to read on for a body it will refuse.
    declares_too_much = codec.forge(healthy, length=MAX_BODY_LENGTH + 1)[:HEADER_SIZE]
    assert len(declares_too_much) == HEADER_SIZE
    refused = codec.decode(declares_too_much)
    assert isinstance(refused, FrameRefusal), refused
    assert refused.control == OVERSIZED, (
        "a header declaring past the maximum was answered as a frame still "
        f"arriving, so the body is read before it is refused: {refused}"
    )
    assert isinstance(codec.decode(healthy), Frame)

    # An honest header, and more bytes than the largest frame holds: the
    # input is bounded by its own length as well as the declared one, and
    # refused before its CRC is computed over anything.
    flooded = healthy + bytes(MAX_BODY_LENGTH)
    assert len(flooded) > HEADER_SIZE + MAX_BODY_LENGTH
    refused = codec.decode(flooded)
    assert isinstance(refused, FrameRefusal), refused
    assert refused.control == OVERSIZED, (
        "an input past the largest frame was read as a frame with garbage "
        f"after it, which takes a pass over all of it to say: {refused}"
    )
    accepted = codec.decode(healthy)
    assert isinstance(accepted, Frame)
    assert accepted.body == BODY
