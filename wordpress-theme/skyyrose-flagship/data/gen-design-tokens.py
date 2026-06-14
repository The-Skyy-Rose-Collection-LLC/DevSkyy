#!/usr/bin/env python3
"""Generate the [data-collection] token region of design-tokens.css from identity.json.

Writes ONLY between the GENERATED:collection-tokens START/END markers. The :root
globals and all other CSS are hand-authored and untouched. Run after editing any
identity.json. The verifier asserts the live region matches a fresh generation.

Emits the tokens the theme consumes: accent, accent-rgb (computed), accent-dark,
secondary, plus the 2-role font model (font-script = the collection's matched
display font; font-caps = Cinzel; font-display aliases font-caps for the 15 legacy
consumers so interior headings stay legible and uniform). font-gothic is dropped
(no consumers). bg/text inherit from :root (unchanged behaviour).
"""

import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent
sys.path.insert(0, str(DATA))
import sot_common  # noqa: E402

CSS = DATA.parent / "assets/css/design-tokens.css"
START = "/* GENERATED:collection-tokens START"
END = "/* GENERATED:collection-tokens END */"


def hex_to_rgb(hex_: str) -> str:
    h = hex_.lstrip("#")
    return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"


def block(ident: dict) -> str:
    p, f = ident["palette"], ident["fonts"]
    return (
        f'[data-collection="{ident["slug"]}"] {{\n'
        f"\t--skyyrose-accent:       {p['accent']};\n"
        f"\t--skyyrose-accent-rgb:   {hex_to_rgb(p['accent'])};\n"
        f"\t--skyyrose-accent-dark:  {p['accent_dark']};\n"
        f"\t--skyyrose-secondary:    {p['secondary']};\n"
        f"\t--skyyrose-font-script:  '{f['script']['family']}', cursive;\n"
        f"\t--skyyrose-font-caps:    '{f['caps']['family']}', serif;\n"
        f"\t--skyyrose-font-display: var(--skyyrose-font-caps);\n"
        f"}}\n"
    )


def main() -> int:
    idents = sot_common.load_identity()
    body = "\n".join(block(idents[s]) for s in sorted(idents))
    css = CSS.read_text()
    if START not in css or END not in css:
        print(
            f"ERROR: {CSS} is missing the GENERATED:collection-tokens markers "
            f"('{START.strip()}' ... '{END.strip()}') — cannot regenerate the region.",
            file=sys.stderr,
        )
        return 1
    s = css.index(START)
    e = css.index(END)
    line_end = css.index("\n", s) + 1
    css = css[:line_end] + body + css[e:]
    CSS.write_text(css)
    print(f"design-tokens.css: regenerated {len(idents)} collection blocks")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
