#!/usr/bin/env python3
"""Generate a local Zero Hour 10-slot Skirmish .wnd from a licensed retail layout.

This program deliberately does NOT embed or distribute EA's original .wnd.
It needs the user's locally extracted SkirmishGameOptionsMenu.wnd as input.
Only use it with the experimental 10-slot build, never retail/online games.
"""
import argparse
import re
from pathlib import Path

WINDOW_BLOCK = re.compile(r"(?ms)^    WINDOW\n.*?^    END\n")
MAP_BUTTON_BLOCK = re.compile(r"(?ms)^      WINDOW\n.*?^      END\n")
RECT = re.compile(
    r"(SCREENRECT = UPPERLEFT: )(\d+) (\d+)(,\s*BOTTOMRIGHT: )(\d+) (\d+)(,)"
)
KINDS = ("ComboBoxPlayer", "ComboBoxTeam", "ComboBoxColor", "ComboBoxPlayerTemplate")


def _rename_slot(block: str, kind: str, old: int, new: int) -> str:
    before = f"SkirmishGameOptionsMenu.wnd:{kind}{old}"
    after = f"SkirmishGameOptionsMenu.wnd:{kind}{new}"
    if block.count(before) != 1:
        raise ValueError(f"Expected exactly one {before} in window block")
    return block.replace(before, after)


def _rect_to(block: str, top: int, bottom: int) -> str:
    def update(match):
        return (match.group(1) + match.group(2) + f" {top}" + match.group(4)
                + match.group(5) + f" {bottom}" + match.group(7))
    changed, num = RECT.subn(update, block, count=1)
    if num != 1:
        raise ValueError("Missing or duplicated window rectangle")
    return changed


def _resize_rows(text: str) -> str:
    """Pack 10 player rows into 200px between y=112 and y=312."""
    def update(match):
        block = match.group()
        name = re.search(r'NAME = "SkirmishGameOptionsMenu.wnd:([^"]+)"', block)
        if not name:
            return block
        short_name = name.group(1)
        if short_name == "TextEntryPlayerName":
            return _rect_to(block, 112, 132)
        for kind in KINDS:
            m = re.fullmatch(re.escape(kind) + r"(\d+)", short_name)
            if m:
                slot = int(m.group(1))
                return _rect_to(block, 112 + slot * 20, 132 + slot * 20)
        return block
    return WINDOW_BLOCK.sub(update, text)


def _clone_extra_rows(text: str) -> str:
    """Clone top-level combo boxes from slot 7 for slots 8 and 9."""
    for kind in KINDS:
        name = f'SkirmishGameOptionsMenu.wnd:{kind}7'
        blocks = [m for m in WINDOW_BLOCK.finditer(text) if name in m.group()]
        if len(blocks) != 1:
            raise ValueError(f"Expected one source control {name}, got {len(blocks)}")
        m = blocks[0]
        template = m.group()
        clones = []
        for slot in (8, 9):
            clone = _rename_slot(template, kind, 7, slot)
            clone = _rect_to(clone, 112 + slot * 20, 132 + slot * 20)
            clones.append("    CHILD\n" + clone)
        text = text[:m.end()] + "".join(clones) + text[m.end():]
    return text


def _clone_map_buttons(text: str) -> str:
    name = "SkirmishGameOptionsMenu.wnd:ButtonMapStartPosition7"
    blocks = [m for m in MAP_BUTTON_BLOCK.finditer(text) if name in m.group()]
    if len(blocks) != 1:
        raise ValueError("Source layout must contain map start-position button 7")
    m = blocks[0]
    template = m.group()
    clones = []
    for slot in (8, 9):
        clone = _rename_slot(template, "ButtonMapStartPosition", 7, slot)
        clone = _rect_to(clone, 194 + 8 * (slot - 8), 211 + 8 * (slot - 8))
        clones.append("      CHILD\n" + clone)
    return text[:m.end()] + "".join(clones) + text[m.end():]


def generate(text: str) -> str:
    text = text.replace("\r\n", "\n")
    for kind in KINDS:
        start = 1 if kind == "ComboBoxPlayer" else 0
        for slot in range(start, 8):
            name = f'SkirmishGameOptionsMenu.wnd:{kind}{slot}"'
            if text.count(name) != 1:
                raise ValueError(f"Expected exactly one {name} in original file")
    text = _resize_rows(text)
    text = _clone_extra_rows(text)
    text = _clone_map_buttons(text)
    for kind in KINDS:
        for slot in range(1 if kind == "ComboBoxPlayer" else 0, 10):
            name = f'SkirmishGameOptionsMenu.wnd:{kind}{slot}"'
            if text.count(name) != 1:
                raise ValueError(f"Generated control invalid: {name}")
    for slot in range(10):
        name = f'SkirmishGameOptionsMenu.wnd:ButtonMapStartPosition{slot}"'
        if text.count(name) != 1:
            raise ValueError(f"Generated start-button invalid: {name}")
    return text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Original licensed .wnd")
    parser.add_argument("output", type=Path, help="Private runtime .wnd output")
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Refusing to replace original or existing .wnd")
    result = generate(args.source.read_bytes().decode("latin1"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(result.replace("\n", "\r\n").encode("latin1"))
    print("Generated 10-slot skirmish .wnd:", args.output)


if __name__ == "__main__":
    main()
