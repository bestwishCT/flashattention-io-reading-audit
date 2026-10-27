# -*- coding: utf-8 -*-
"""Offline, reproducible arithmetic for the FlashAttention reading audit.

WHAT THIS SCRIPT DOES
  It redoes simple arithmetic on values transcribed from the paper's own
  Figure 2 (page 6) and Table 2 (page 8), plus two self-contained teaching
  examples for the complexity expressions.

WHAT THIS SCRIPT DOES NOT DO
  It does NOT re-run any FlashAttention kernel, does NOT train any model, does
  NOT measure runtime on any GPU, and does NOT re-implement an NLI or a
  citation metric. Every number below is either
    (P) a paper value, transcribed from the cited page,
    (A) arithmetic derived from paper values, or
    (T) a made-up teaching example with invented parameters.

Run:  python offline_calc.py
"""
from pathlib import Path
import json

# ---------- (P) paper values: Figure 2 left table, physical page 6 ----------
FIG2 = {
    "GFLOPs":        {"standard": 66.6,  "flash": 75.2},
    "HBM R/W (GB)":  {"standard": 40.3,  "flash": 4.4},
    "Runtime (ms)":  {"standard": 41.7,  "flash": 7.3},
}
FIG2_SETUP = "GPT-2 medium, seq. length 1024, head dim 64, 16 heads, batch size 64, A100 GPU"

# ---------- (P) paper values: Table 2, physical page 8 ----------
TABLE2 = [
    # model, ppl, training_days, speedup
    ("GPT-2 small  - Huggingface", 18.2, 9.5, 1.0),
    ("GPT-2 small  - Megatron-LM", 18.2, 4.7, 2.0),
    ("GPT-2 small  - FlashAttention", 18.2, 2.7, 3.5),
    ("GPT-2 medium - Huggingface", 14.2, 21.0, 1.0),
    ("GPT-2 medium - Megatron-LM", 14.3, 11.5, 1.8),
    ("GPT-2 medium - FlashAttention", 14.3, 6.9, 3.0),
]

lines = []


def emit(s=""):
    print(s)
    lines.append(s)


def head(s):
    emit()
    emit("== " + s + " ==")


def main():
    emit("FlashAttention-2 reading audit - offline arithmetic")
    emit("Setup (P): " + FIG2_SETUP)
    emit("All values below are arithmetic on values transcribed from the paper.")
    emit("No GPU was used, no kernel was run, no model was trained.")

    # ---------- 1. Figure 2 left: the three quantities move in different directions
    head("1. Figure 2 (left): FLOPs up, HBM down, runtime down  [P + A]")
    for metric in ("GFLOPs", "HBM R/W (GB)", "Runtime (ms)"):
        s, f = FIG2[metric]["standard"], FIG2[metric]["flash"]
        ratio = s / f
        direction = "higher" if f > s else "lower"
        emit(f"  {metric:16s} standard={s:6.1f}  flash={f:6.1f}  "
             f"flash is {direction};  standard/flash = {ratio:.2f}x  [A]")

    emit("")
    emit("  Reading check (A):")
    emit(f"    FlashAttention GFLOPs ratio   = {FIG2['GFLOPs']['flash']}/{FIG2['GFLOPs']['standard']}"
         f" = {FIG2['GFLOPs']['flash']/FIG2['GFLOPs']['standard']:.3f}  (>1 => MORE flops)")
    emit(f"    HBM R/W reduction factor      = {FIG2['HBM R/W (GB)']['standard']}/{FIG2['HBM R/W (GB)']['flash']}"
         f" = {FIG2['HBM R/W (GB)']['standard']/FIG2['HBM R/W (GB)']['flash']:.2f}x fewer bytes moved")
    emit(f"    Runtime speedup               = {FIG2['Runtime (ms)']['standard']}/{FIG2['Runtime (ms)']['flash']}"
         f" = {FIG2['Runtime (ms)']['standard']/FIG2['Runtime (ms)']['flash']:.2f}x faster")

    # A consistency check: if runtime tracked GFLOPs, a 1.13x higher flop count
    # would predict a slower FlashAttention. It is 5.71x faster instead.
    flop_ratio = FIG2["GFLOPs"]["flash"] / FIG2["GFLOPs"]["standard"]
    time_ratio = FIG2["Runtime (ms)"]["standard"] / FIG2["Runtime (ms)"]["flash"]
    emit("")
    emit("  Directionality check (A): flops grew by "
         f"{flop_ratio:.3f}x, yet wall-clock improved by {time_ratio:.2f}x.")
    emit("  => The quantity that moved in the SAME direction as the runtime win")
    emit("     is HBM traffic, not FLOPs. This is the paper's central claim [P: p.6 l.53-56].")

    # ---------- 2. Theorem 2 arithmetic
    head("2. Theorem 2 expression, evaluated at paper-typical parameters  [P + A]")
    emit("  Standard attention : Theta(N*d + N^2)      HBM accesses")
    emit("  FlashAttention     : Theta(N^2*d^2*M^-1)   HBM accesses")
    emit("  Paper-typical (P): d = 64..128, M ~ 100KB, and d^2 is 'many times smaller than M'.")
    emit("")
    emit("  (T) Teaching example, invented parameters: N = 1024, d = 64, M = 100_000 (elements).")
    N, d, M = 1024, 64, 100_000
    std = N * d + N ** 2
    fla = N ** 2 * d ** 2 / M
    emit(f"    standard  = N*d + N^2          = {N}*{d} + {N}^2 = {std:,.0f}  [A]")
    emit(f"    flash     = N^2*d^2/M          = {N}^2*{d}^2/{M:,} = {fla:,.0f}  [A]")
    emit(f"    ratio     = standard/flash     = {std/fla:,.1f}x fewer accesses (A, this example only)")
    emit("    NOTE: this example only illustrates the formula's SHAPE. It is NOT the")
    emit("    paper's measured HBM traffic and NOT a prediction of the 9.16x above;")
    emit("    the paper's 4.4 vs 40.3 GB figures are measured, these are arithmetic.")
    emit("")
    emit("  (A) Why d^2 << M matters (T example):")
    for dd in (64, 128):
        emit(f"    d={dd:4d}: d^2 = {dd**2:>7,}   M/d^2 = {M/(dd**2):>8,.1f}"
             f"   -> the M^-1 factor wins" )

    # ---------- 3. Table 2 checks
    head("3. Table 2 (page 8): speedups recomputed from training days  [P + A]")
    for name, ppl, days, claimed in TABLE2:
        emit(f"  {name:32s} ppl={ppl:5.1f}  {days:5.1f} days  claimed {claimed:.1f}x")
    emit("")
    base_small = TABLE2[0][2]
    base_med = TABLE2[3][2]
    for name, ppl, days, claimed in TABLE2:
        if name.endswith("Huggingface"):
            continue
        base = base_small if "small" in name else base_med
        derived = base / days
        flag = "OK" if abs(derived - claimed) <= 0.26 else "MISMATCH"
        emit(f"  {name:32s} derived = {base:.1f}/{days:.1f} = {derived:.2f}x  "
             f"vs claimed {claimed:.1f}x   [{flag}]")
    emit("")
    emit("  (A) Perplexity comparison - the small quality gap the model must not hide:")
    s_small = [r for r in TABLE2 if "small" in r[0]]
    s_med = [r for r in TABLE2 if "medium" in r[0]]
    emit(f"    GPT-2 small : all three implementations report ppl = "
         f"{sorted(set(r[1] for r in s_small))}  -> identical")
    emit(f"    GPT-2 medium: Huggingface={s_med[0][1]}, Megatron-LM={s_med[1][1]}, "
         f"FlashAttention={s_med[2][1]}")
    emit(f"      FlashAttention vs Huggingface  = {s_med[2][1]-s_med[0][1]:+.1f} ppl "
         f"(FlashAttention is {'worse' if s_med[2][1]>s_med[0][1] else 'better'})")
    emit(f"      FlashAttention vs Megatron-LM  = {s_med[2][1]-s_med[1][1]:+.1f} ppl "
         f"(identical to Megatron-LM)")
    emit("    => 'the same perplexity' is exactly true for GPT-2 small, but for")
    emit("       GPT-2 medium FlashAttention's ppl is 0.1 HIGHER than HuggingFace's.")

    # ---------- 4. Block-sparse proportionality
    head("4. Block-sparse speedup vs sparsity  [T: figure axes are read from page 6]")
    emit("  Figure 2 (right) plots Fwd+Bwd runtime against % Non-Zero Blocks;")
    emit("  the paper states the speedup is 'proportional to the sparsity' [P: p.6 l.30].")
    emit("")
    emit("  (T) Teaching example: assume dense FlashAttention takes 100 units at 100% blocks.")
    emit("      If the sparse variant keeps only f fraction of blocks and the speedup")
    emit("      were exactly proportional to sparsity, runtime would scale as f.")
    for f in (1.0, 0.8, 0.6, 0.5, 0.4, 0.2):
        emit(f"      non-zero blocks {f*100:5.1f}%  ->  predicted runtime {100*f:6.1f} units  [T]")
    emit("      These are TEACHING numbers. The real figure is a measured plot and the")
    emit("      paper only claims proportionality, not an exact closed form.")
    emit("      Also from the paper (P: p.6 l.58-60): past block size 256 the runtime")
    emit("      stops improving (arithmetic bottleneck), and larger blocks stop")
    emit("      fitting in SRAM. So 'bigger sparse blocks = faster' is NOT unbounded.")

    emit()
    emit("-- summary --")
    emit("  Paper values (P): Fig.2 left table, Table 2, Theorem 2 / Proposition 3, Fig.2 caption.")
    emit("  Arithmetic (A):    all ratios, speedup recomputation, ppl differences.")
    emit("  Teaching (T):      the N/d/M example and the block-sparse proportionality table.")
    emit("  NOT done:           no GPU run, no kernel run, no training, no NLI, no new experiment.")

    out = Path(__file__).resolve().parent / "offline-output.txt"
    out.write_text("\n".join(lines) + "\n", encoding="utf8")
    print()
    print("wrote", out)


if __name__ == "__main__":
    main()
