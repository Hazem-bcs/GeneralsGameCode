#!/usr/bin/env python3
"""Generate local-only ten-slot layouts from the owner's extracted retail files.

Input directory must contain the four original .wnd files. No EA assets are
embedded here. Output files must not exist; the online loading layout is untouched.
"""
import argparse
from pathlib import Path
import re
from extend_skirmish_layout import generate, _rect_to


def clone_controls(text, layout, kinds, indent, rows=False, row_start=363, row_step=19, row_height=18):
    pattern = re.compile(r"(?ms)^" + " " * indent + r"WINDOW\n.*?^" + " " * indent + r"END\n")
    for kind in kinds:
        name = f'{layout}:{kind}7"'
        matches = [m for m in pattern.finditer(text) if name in m.group()]
        if len(matches) != 1:
            raise ValueError(f"Expected one original control {name}")
        m = matches[0]
        extra = []
        for slot in (8, 9):
            block = m.group().replace(name, f'{layout}:{kind}{slot}"')
            if rows:
                block = _rect_to(block, row_start + slot * row_step, row_start + slot * row_step + row_height)
            extra.append(" " * indent + "CHILD\n" + block)
        text = text[:m.end()] + "".join(extra) + text[m.end():]
    if rows:
        def resize(match):
            block = match.group()
            for kind in kinds:
                found = re.search(re.escape(layout + ":" + kind) + r'(\d+)"', block)
                if found:
                    slot = int(found[1])
                    return _rect_to(block, row_start + slot * row_step, row_start + slot * row_step + row_height)
            return block
        text = pattern.sub(resize, text)
    for kind in kinds:
        for slot in range(10):
            if text.count(f'{layout}:{kind}{slot}"') != 1:
                raise ValueError(f"Invalid generated {kind}{slot}")
    return text


def create_layouts(source, output):
    names = ("SkirmishGameOptionsMenu.wnd", "SkirmishMapSelectMenu.wnd", "MultiplayerLoadScreen.wnd", "Diplomacy.wnd")
    original = {name: (source / name).read_text(encoding="latin1") for name in names}
    options = generate(original[names[0]])
    selector = clone_controls(original[names[1]], names[1], ("ButtonMapStartPosition",), 4)
    loading = clone_controls(original[names[2]], names[2],
        ("ProgressLoad", "StaticTextTeam", "StaticTextPlayer", "StaticTextSide"), 4, rows=True)
    loading = clone_controls(loading, names[2], ("ButtonMapStartPosition",), 6)
    loading = loading.replace(names[2], "SkirmishLoadScreen.wnd")
    diplomacy = clone_controls(original[names[3]], names[3],
        ("StaticTextPlayer", "StaticTextSide", "StaticTextTeam", "StaticTextStatus", "ButtonMute", "ButtonUnMute"),
        4, rows=True, row_start=94, row_step=25, row_height=23)
    results = {names[0]: options, names[1]: selector, "SkirmishLoadScreen.wnd": loading,
        "SkirmishDiplomacy.wnd": diplomacy}
    if source.resolve() == output.resolve() or any((output / name).exists() for name in results):
        raise ValueError("Refusing to overwrite original or existing layouts")
    output.mkdir(parents=True, exist_ok=True)
    for name, text in results.items():
        (output / name).write_bytes(text.replace("\n", "\r\n").encode("latin1"))
    return list(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print("Generated:", create_layouts(args.source, args.output))
