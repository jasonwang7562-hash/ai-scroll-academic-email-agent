"""Add restrained PowerPoint slide transitions to an existing PPTX package."""

from __future__ import annotations

import shutil
import sys
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


P = "http://schemas.openxmlformats.org/presentationml/2006/main"
ET.register_namespace("a", "http://schemas.openxmlformats.org/drawingml/2006/main")
ET.register_namespace("p", P)
ET.register_namespace("r", "http://schemas.openxmlformats.org/officeDocument/2006/relationships")

# The effect changes with the content: explanation slides fade, process slides move.
EFFECTS = {
    1: ("fade", {}),
    2: ("fade", {}),
    3: ("push", {"dir": "l"}),
    4: ("wipe", {"dir": "r"}),
    5: ("fade", {}),
    6: ("fade", {}),
    7: ("fade", {}),
}


def add_transition(xml: bytes, effect: str, attrs: dict[str, str]) -> bytes:
    root = ET.fromstring(xml)
    existing = root.find(f"{{{P}}}transition")
    if existing is not None:
        root.remove(existing)

    transition = ET.Element(f"{{{P}}}transition", {"spd": "slow", "advClick": "1"})
    ET.SubElement(transition, f"{{{P}}}{effect}", attrs)

    children = list(root)
    insert_at = len(children)
    for index, child in enumerate(children):
        if child.tag in {f"{{{P}}}timing", f"{{{P}}}extLst"}:
            insert_at = index
            break
    root.insert(insert_at, transition)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def main(source: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        temp = Path(temp_dir) / source.name
        with zipfile.ZipFile(source, "r") as zin, zipfile.ZipFile(temp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                payload = zin.read(item.filename)
                if item.filename.startswith("ppt/slides/slide") and item.filename.endswith(".xml"):
                    number = int(Path(item.filename).stem.removeprefix("slide"))
                    if number in EFFECTS:
                        payload = add_transition(payload, *EFFECTS[number])
                zout.writestr(item, payload)
        shutil.copyfile(temp, source)


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())
