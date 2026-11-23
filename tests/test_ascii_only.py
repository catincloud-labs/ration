"""This repository is ASCII, and here is the thing that checks it.

Two separate reasons, and one check holds both: every tracked file, read as
bytes, so the package metadata and every message the package raises are read
in the files they are built from.

**The encoding one.** Package metadata, exception messages and anything a
caller prints are read in terminals whose encoding nobody controls. A character
that is correct UTF-8 and renders in a browser can still print as a replacement
character on a console at cp1252, so a character that survives a web page is
not automatically one that survives a traceback.

**The register one.** This repository is public. Decorative glyphs and severity
emoji are a private convention for readers who already know it, and they do not
travel to strangers; em dashes in particular are easy to paste and hard to see.

The second reason is a style rule, and a style rule with no control is a
suggestion. This is the control. There is no exemption list: the vendored
copies under `scripts/` are ASCII at their source, so a non-ASCII byte arriving
in one is a defect in the source, and this test is the first thing to see it.
"""

from __future__ import annotations

import os
import pathlib
import subprocess

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent


def _tracked_files(repo: pathlib.Path = REPO) -> list[str]:
    """Ask git, rather than walking the tree.

    A walk would pick up `.venv`, build artifacts and anything else untracked,
    and would then be asserting something about a working directory rather than
    about what this repository actually publishes.

    `-z` makes git print each name as it is stored. Without it, git quotes a
    name holding a byte above 0x7F, a quote, a backslash or a control
    character, and the quoted string names no file on disk, so the file it
    stands for would never be read.
    """

    out = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "-z"],
        capture_output=True,
        check=True,
    )
    return [os.fsdecode(name) for name in out.stdout.split(b"\0") if name]


def _text_files() -> list[str]:
    skip_suffixes = (".png", ".jpg", ".gif", ".ico", ".whl", ".gz")
    return [f for f in _tracked_files() if not f.lower().endswith(skip_suffixes)]


def _offenders_in(name: str, path: pathlib.Path) -> list[str]:
    """Every line of one tracked file that is not ASCII, read as bytes.

    The file is split on LF and each line decoded on its own. A valid
    multi-byte UTF-8 sequence never contains 0x0A, so the split never cuts a
    character, and one undecodable line cannot hide another line.

    A line that decodes is reported by the characters it holds, `U+2014`. A
    line that does not is reported by each byte above 0x7F and that byte's
    offset in the file, counted from 0. Decoding the whole file at once would
    skip a file that does not decode, so the em dash as cp1252 writes it, a lone
    0x97, would pass the check written to refuse em dashes and hide every valid
    one in the same file. A file that cannot be read is reported too: an
    unreadable file is not a clean one.
    """

    try:
        data = path.read_bytes()
    except OSError as exc:
        return [f"{name}: unreadable ({type(exc).__name__})"]
    offenders: list[str] = []
    start = 0
    for lineno, raw in enumerate(data.split(b"\n"), 1):
        try:
            line = raw.decode("utf-8")
        except UnicodeDecodeError:
            shown = ", ".join(
                f"0x{byte:02X} at byte {start + i}"
                for i, byte in enumerate(raw)
                if byte > 127
            )
            offenders.append(f"{name}:{lineno}: {shown} (not UTF-8)")
        else:
            bad = {c for c in line if ord(c) > 127}
            if bad:
                shown = ", ".join(f"U+{ord(c):04X}" for c in sorted(bad))
                offenders.append(f"{name}:{lineno}: {shown}")
        start += len(raw) + 1
    return offenders


@pytest.mark.skipif(
    subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "--git-dir"], capture_output=True
    ).returncode
    != 0,
    reason="not a git checkout, so there is no file list to check",
)
def test_every_tracked_file_is_ascii() -> None:
    """The whole repository, not a hand-maintained list of files to watch.

    Asserting over `git ls-files` rather than a literal list is what makes this
    hold for a file nobody has written yet. A list would have to be updated by
    the same person who is about to paste an em dash into a new document.

    Each file is read as bytes, so one that is not UTF-8 is reported by line
    and byte offset rather than skipped; `_offenders_in` says why that matters.
    """

    offenders: list[str] = []
    for name in _text_files():
        offenders.extend(_offenders_in(name, REPO / name))

    assert not offenders, (
        "non-ASCII characters in tracked files; this repository is public and "
        "ASCII-only (see tests/test_ascii_only.py for both reasons):\n  "
        + "\n  ".join(offenders)
    )


def _plant(count: int, planted: dict[int, bytes]) -> bytes:
    """`count` lines of 20 ASCII bytes each, with the numbered lines replaced.

    Twenty bytes a line is what lets an offset below be counted by hand.
    """

    return b"".join(
        planted.get(n, b"line %02d: plain text\n" % n) for n in range(1, count + 1)
    )


# Four arms, each placing its bytes where the comment says. Bytes above 0x7F
# are written as escapes, so this file stays ASCII.
# Arm 3: fifteen lines of 20 bytes (300), then 14 bytes into line 16: byte 314.
# Arm 4: two lines (40), a 23-byte line 3 (63), 33 more lines (723), then 34
# bytes into line 37: byte 757.
# Arm 5: fifteen lines (300), then 14 bytes into line 16 the three bytes of a
# U+2014 at 314 to 316, then " and", then a lone byte at 321.
_ARM_VALID = _plant(20, {16: b"line 16: plain\xe2\x80\x94 text\n"})
_ARM_LONE = _plant(20, {16: b"line 16: plain\x97 text\n"})
_ARM_BOTH = _plant(
    40,
    {
        3: b"line 03: plain\xe2\x80\x94 text\n",
        37: b"line 37: plain text, then a byte: \x97\n",
    },
)
_ARM_MIXED = _plant(20, {16: b"line 16: plain\xe2\x80\x94 and\x97 text\n"})


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        pytest.param(_ARM_VALID, ["plant.txt:16: U+2014"], id="2-valid-u2014"),
        pytest.param(
            _ARM_LONE,
            ["plant.txt:16: 0x97 at byte 314 (not UTF-8)"],
            id="3-lone-0x97",
        ),
        pytest.param(
            _ARM_BOTH,
            [
                "plant.txt:3: U+2014",
                "plant.txt:37: 0x97 at byte 757 (not UTF-8)",
            ],
            id="4-valid-then-lone",
        ),
        pytest.param(
            _ARM_MIXED,
            [
                "plant.txt:16: 0xE2 at byte 314, 0x80 at byte 315, "
                "0x94 at byte 316, 0x97 at byte 321 (not UTF-8)"
            ],
            id="5-mixed-line",
        ),
    ],
)
def test_the_file_check_reports_every_arm(
    tmp_path: pathlib.Path, data: bytes, expected: list[str]
) -> None:
    """Calibration of the file check, through the function the real test calls.

    These arms write bytes to disk and go through `_offenders_in`, the same
    call the whole-repository test makes for each tracked file, and that test
    on the clean tree is the quiet arm.

    Arm 3 is the em dash as cp1252 writes it, a lone 0x97, which is the
    likeliest way one reaches this tree from a Windows editor or clipboard.
    Arm 4 is why the check reads line by line: one undecodable line late in a
    file must not hide a valid U+2014 earlier in it. Arm 5 is a line that holds
    both, and pins two things: every byte above 0x7F on an undecodable line is
    listed, not just the first, and a valid U+2014 on such a line is listed as
    its three bytes, because "(not UTF-8)" describes the line.
    """

    path = tmp_path / "plant.txt"
    path.write_bytes(data)
    assert _offenders_in("plant.txt", path) == expected


def test_an_unreadable_tracked_file_is_an_offender(tmp_path: pathlib.Path) -> None:
    """A file the check cannot read is not a file the check found clean.

    `git ls-files` lists the index, not the working tree, so it can list a
    path that does not read as a file. Two are known. A tracked file deleted
    and not yet staged with `git rm` is one, at a desk, and staging the
    deletion is its remedy. A submodule is the other, in CI as anywhere: its
    path is a directory. None is tracked here, and adding one is a decision
    this red would put in front of a reviewer rather than pass in silence.
    """

    gone = tmp_path / "gone.txt"
    assert _offenders_in("gone.txt", gone) == [
        "gone.txt: unreadable (FileNotFoundError)"
    ]


def test_a_name_git_would_quote_is_listed_as_it_is(tmp_path: pathlib.Path) -> None:
    """A tracked file whose name holds a byte above 0x7F is read, not lost.

    By default `git ls-files` quotes such a name and escapes its bytes, which
    names no file on disk, so the file would be skipped as unreadable and its
    contents never read. The name is built with `chr`, so this file stays
    ASCII. Whether a non-ASCII name is itself an offender is a separate
    question this does not answer.
    """

    name = f"caf{chr(0xE9)}.txt"
    (tmp_path / name).write_bytes(b"line \x97\n")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-C", str(tmp_path), "add", name], check=True)
    listed = _tracked_files(tmp_path)
    assert listed == [name]
    assert [o for n in listed for o in _offenders_in(n, tmp_path / n)] == [
        f"{name}:1: 0x97 at byte 5 (not UTF-8)"
    ]
