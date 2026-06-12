"""Generate the S3 results summary figure (6 panels) from recorded metrics.

Data is hard-coded from the experiment logs of 12-13 Jun 2026 (see
docs/รายงานงาน_13มิย2569_S3-HeadOnly-MultiSeed.md). Re-run after new
experiments by editing the tables below.

Usage:
    python src/plot_s3_results.py  [--out output/figures/s3_results.png]
"""

import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

C_CURV, C_RAND, C_REG = "#d62728", "#1f77b4", "#2ca02c"

# ── Full-scene budget sweep (seed 0, downscale 4) ────────────────────
BUDGETS = [5_000, 10_000, 15_000]
FULL = {
    "curv": {"PSNR": [15.384, 16.014, 15.920], "SSIM": [0.5262, 0.5563, 0.5681], "LPIPS": [0.6075, 0.6060, 0.5749]},
    "rand": {"PSNR": [14.944, 15.503, 15.748], "SSIM": [0.4952, 0.5243, 0.5516], "LPIPS": [0.6127, 0.5997, 0.5930]},
}

# ── Head-only @5k faces, 3 seeds ─────────────────────────────────────
HEAD = {
    "curv": {"PSNR": [22.355, 22.383, 22.386], "SSIM": [0.8048, 0.7989, 0.8024], "LPIPS": [0.2033, 0.2066, 0.1992]},
    "rand": {"PSNR": [22.276, 22.247, 22.399], "SSIM": [0.8022, 0.8015, 0.7943], "LPIPS": [0.2022, 0.2029, 0.2065]},
}

# ── Regularizer ablation (head-only curv @5k, seed 0) ────────────────
REG_L = [0.0, 0.01, 0.1]
REG = {"PSNR": [22.355, 22.066, 21.527], "SSIM": [0.8048, 0.7976, 0.7637], "LPIPS": [0.2033, 0.2037, 0.2342]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join("output", "figures", "s3_results.png"))
    args = ap.parse_args()
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    fig, axes = plt.subplots(2, 3, figsize=(17, 9.5))
    fig.suptitle("CG-Soup S2/S3 results — buddha scene, DiffSoup, 10k steps, downscale 4",
                 fontsize=13, y=0.99)

    # row 1: full-scene budget sweep
    for ax, metric, better in zip(axes[0], ["PSNR", "SSIM", "LPIPS"], ["higher", "higher", "lower"]):
        ax.plot(BUDGETS, FULL["curv"][metric], "o-", color=C_CURV, label="curvature (ours)")
        ax.plot(BUDGETS, FULL["rand"][metric], "s--", color=C_RAND, label="random (baseline)")
        ax.set_xticks(BUDGETS)
        ax.set_xticklabels(["5k", "10k", "15k"])
        ax.set_xlabel("triangle budget (max faces)")
        ax.set_ylabel(metric + (" (dB)" if metric == "PSNR" else ""))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=9)

    axes[0][0].set_title("(a) full-scene: PSNR vs budget  [higher = better]")
    axes[0][1].set_title("(b) full-scene: SSIM vs budget  [higher = better]")
    axes[0][2].set_title("(c) full-scene: LPIPS vs budget  [lower = better]")

    # (d) head-only vs full-scene jump @5k
    ax = axes[1][0]
    groups = ["PSNR (dB)", "SSIM ×20", "LPIPS ×20"]
    full5 = [FULL["curv"]["PSNR"][0], FULL["curv"]["SSIM"][0] * 20, FULL["curv"]["LPIPS"][0] * 20]
    head5 = [np.mean(HEAD["curv"]["PSNR"]), np.mean(HEAD["curv"]["SSIM"]) * 20, np.mean(HEAD["curv"]["LPIPS"]) * 20]
    x = np.arange(3)
    ax.bar(x - 0.18, full5, 0.36, color="#aaaaaa", label="full-scene")
    ax.bar(x + 0.18, head5, 0.36, color=C_CURV, label="head-only (masked)")
    for xi, (f, h) in enumerate(zip(full5, head5)):
        ax.text(xi - 0.18, f + 0.25, f"{f:.2f}", ha="center", fontsize=8)
        ax.text(xi + 0.18, h + 0.25, f"{h:.2f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_title("(d) head-only pipeline effect @5k faces (curvature)\nPSNR +7.0 dB, SSIM 0.53→0.80, LPIPS 0.61→0.20")
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3, axis="y")

    # (e) head-only multi-seed mean±SD
    ax = axes[1][1]
    for i, (k, color, lbl) in enumerate([("curv", C_CURV, "curvature (ours)"), ("rand", C_RAND, "random")]):
        vals = HEAD[k]["PSNR"]
        ax.bar(i, np.mean(vals), 0.6, yerr=np.std(vals, ddof=1), capsize=8, color=color, alpha=0.85, label=lbl)
        ax.scatter([i] * 3, vals, color="black", zorder=3, s=18)
        ax.text(i, np.mean(vals) + 0.12, f"{np.mean(vals):.3f}±{np.std(vals, ddof=1):.3f}", ha="center", fontsize=9)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["curvature", "random"])
    ax.set_ylim(21.9, 22.7)
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(e) head-only @5k: PSNR over 3 seeds (dots = runs)\ncurvature is ~5x more consistent (SD 0.017 vs 0.081)")
    ax.grid(alpha=0.3, axis="y")

    # (f) regularizer ablation
    ax = axes[1][2]
    x = np.arange(3)
    ax.bar(x, REG["PSNR"], 0.55, color=C_REG, alpha=0.85)
    for xi, (p, s) in enumerate(zip(REG["PSNR"], REG["SSIM"])):
        ax.text(xi, p + 0.05, f"{p:.2f}\nSSIM {s:.3f}", ha="center", fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels(["λ = 0", "λ = 0.01", "λ = 0.1"])
    ax.set_ylim(21.0, 22.8)
    ax.set_ylabel("PSNR (dB)")
    ax.set_title("(f) normal-consistency regularizer ablation\n(head-only curv @5k) — image metrics prefer λ = 0")
    ax.grid(alpha=0.3, axis="y")

    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(args.out, dpi=130)
    print("saved:", args.out)


if __name__ == "__main__":
    main()
