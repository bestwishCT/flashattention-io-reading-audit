# -*- coding: utf-8 -*-
"""Rebuild the numbered evidence text for FlashAttention-2 pages 1/3/6/8.

Why this script exists
----------------------
Both pypdf and pypdfium2 mis-map or flatten some Type-1 math glyphs in this
PDF:

  * pypdf maps the multiplication sign to U+0002, the minus sign to U+0000,
    the comma to U+0096, the floor/ceiling brackets to unrelated letters, and
    the math-font parentheses to U+00B9 / U+00BA;
  * BOTH extractors split superscript/subscript runs onto their own lines and
    emit them as plain digits, so the FlashAttention complexity
    "Theta(N^2 d^2 M^-1)" is extracted as "Theta(N 2d2 M-1)".

Neither raw extraction is trustworthy for the formulas this study is about.
This script therefore:
  1. keeps pypdf's line segmentation (it keeps each formula on ONE line,
     which pypdfium2 does not);
  2. applies an explicit character-level fix table (step 3);
  3. applies an explicit, line-targeted fix table for the flattened formulas
     (step 4), where every entry was read off the rendered page image
     (work/materials/page6.png, page8.png) and cross-checked against
     pypdfium2's independent reading of the same span.

Step 4 is applied per (page, line number) so a formula edit can never silently
re-target a different line, and the script reports every applied edit.

This is character re-encoding, NOT an experiment: it does not re-run any
paper computation and does not change any number's value.
"""
from pathlib import Path
import json, hashlib
import pypdf

R = Path(__file__).resolve().parent
P = R.parent
PDF = P / "research" / "private-originals" / "flashattention-v2.pdf"
OUT = R / "work" / "materials"
PAGES = [1, 3, 6, 8]
IDS = {1: "FA2-P1", 3: "FA2-P3", 6: "FA2-P6", 8: "FA2-P8"}

# --- step 3: single-character glyph fixes, learned by diffing the pypdf and
#     pypdfium2 readings of the same four pages, then hand-verified. ---
CHAR_FIX = {
    "\x02": "\u00d7",   # multiplication sign
    "\x00": "\u2212",   # minus sign
    "\x14": "\u2264",   # less-than-or-equal
    "\x96": ",",        # comma
    "\x0c": "\u2299",   # circled dot
    "\x9d": "/",        # solidus
    "\xb9": "(",        # math-font left parenthesis
    "\xba": ")",        # math-font right parenthesis
    "\xbb": "[",
    "\xbc": "]",
    "\xb8": "+",        # plus sign
    "\xfb00": "ff", "\xfb01": "fi", "\xfb02": "fl", "\xfb03": "ffi", "\xfb04": "ffl",
}

# --- step 4: line-targeted formula repairs.
#     Key = (page, 1-based line number). Value = the verified correct line.
#     Each value was transcribed from the rendered page image of that page. ---
LINE_FIX = {
    (6, 32): "Theorem 2. Let N be the sequence length, d be the head dimension, and M be size of SRAM with d \u2264 M \u2264 Nd.",
    (6, 33): "Standard attention (Algorithm 0) requires \u0398(Nd + N\u00b2) HBM accesses, while FlashAttention (Algorithm 1)",
    (6, 34): "requires \u0398(N\u00b2d\u00b2M\u207b\u00b9) HBM accesses.",
    (6, 35): "For typical values of d (64-128) and M (around 100KB), d\u00b2 is many times smaller than M, and thus",
    (6, 38): "The main idea of the proof is that given the SRAM size of M, we can load blocks of K, V of size \u0398(M) each",
    (6, 40): "the intermediate values, resulting in \u0398(NdM\u207b\u00b9) passes over Q. Each pass loads \u0398(Nd) elements, which",
    (6, 41): "amounts to \u0398(N\u00b2d\u00b2M\u207b\u00b9) HBM accesses. We similarly prove that the backward pass of standard attention",
    (6, 42): "requires \u0398(Nd + N\u00b2) HBM accesses while the backward pass of FlashAttention requires \u0398(N\u00b2d\u00b2M\u207b\u00b9)",
    (6, 47): "d \u2264 M \u2264 Nd. There does not exist an algorithm to compute exact attention with o(N\u00b2d\u00b2M\u207b\u00b9) HBM accesses",
    (6, 48): "for all M in the range [d, Nd].",
    (6, 49): "The proof relies on the fact that for M = \u0398(Nd) any algorithm must perform \u03a9(N\u00b2d\u00b2M\u207b\u00b9) = \u03a9(Nd)",
    (6, 64): "Given inputs Q, K, V \u2208 R^(N\u00d7d) and a mask matrix M\u0303 \u2208 {0,1}^(N\u00d7N), we want to compute:",
    (6, 65): "S = QK\u1d40 \u2208 R^(N\u00d7N), P = softmax(S \u2299 1_{M\u0303}) \u2208 R^(N\u00d7N), O = PV \u2208 R^(N\u00d7d),",
    (6, 66): "where (S \u2299 1_{M\u0303})_{kl} = S_{kl} if M\u0303_{kl} = 1 and \u2212\u221e if M_{kl} = 0. We require M\u0303 to have block form: for some block sizes",
    (6, 67): "B_r, B_c, for all k, l, M\u0303_{k,l} = M_{ij} with i = \u230ak/B_r\u230b, j = \u230al/B_c\u230b for some M \u2208 {0,1}^(N/B_r \u00d7 N/B_c).",
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    reader = pypdf.PdfReader(str(PDF))
    sources = []
    applied = []
    for pg in PAGES:
        raw = reader.pages[pg - 1].extract_text() or ""
        raw = raw.replace("\r\n", "\n").replace("\r", "\n")
        lines = []
        for idx, line in enumerate(raw.split("\n"), 1):
            fixed = "".join(CHAR_FIX.get(ch, ch) for ch in line)
            if (pg, idx) in LINE_FIX:
                applied.append((pg, idx))
                fixed = LINE_FIX[(pg, idx)]
            lines.append(fixed)
        sources.append({"id": IDS[pg], "page": pg, "text": "\n".join(lines)})

    (OUT / "sources.json").write_text(
        json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf8")

    render = "\n\n".join(
        f"SOURCE {s['id']} PDF physical page {s['page']}\n"
        + "\n".join(f"{i+1:03d}: {l}" for i, l in enumerate(s["text"].split("\n")))
        for s in sources
    )
    (OUT / "numbered.txt").write_text(render, encoding="utf8")

    bad = []
    for s in sources:
        for i, l in enumerate(s["text"].split("\n"), 1):
            for ch in l:
                o = ord(ch)
                if (o < 32 and ch != "\t") or 0x7F <= o <= 0x9F:
                    bad.append((s["id"], i, hex(o)))
    print("line-targeted repairs applied:", len(applied), "of", len(LINE_FIX))
    missing = sorted(set(LINE_FIX) - set(applied))
    print("targets never reached:", missing)
    print("residual control chars:", len(bad))
    for s in sources:
        print(f"  {s['id']}: {len(s['text'].split(chr(10)))} lines, {len(s['text'])} chars")
    print("numbered chars:", len(render))
    print("pdf sha256:", hashlib.sha256(PDF.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
