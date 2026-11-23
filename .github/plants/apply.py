"""Apply one plant of the ration#35 sweep's plant pass to the checkout. Temporary.

Usage: python .github/plants/apply.py <id>

`control` applies nothing. A plant with a patch is applied with `git apply`;
a hand plant is one exact text edit, refused unless its old text occurs once.
This file, the patches and the workflow that runs them are removed from the
branch before it merges.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def main(plant: str) -> int:
    if plant.startswith("control"):
        print("control: nothing planted")
        return 0
    entries = {entry["id"]: entry for entry in json.loads((HERE / "plants.json").read_text())}
    entry = entries[plant]
    print(f"{plant}: {entry['where']}: {entry['what']}")
    edit = entry.get("edit")
    if edit is None:
        subprocess.run(["git", "-C", str(ROOT), "apply", str(HERE / f"{plant}.patch")], check=True)
        return 0
    path = ROOT / edit["file"]
    text = path.read_text(encoding="utf-8")
    if text.count(edit["old"]) != 1:
        print(f"the plant does not find its text exactly once in {edit['file']}")
        return 1
    path.write_bytes(text.replace(edit["old"], edit["new"]).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
