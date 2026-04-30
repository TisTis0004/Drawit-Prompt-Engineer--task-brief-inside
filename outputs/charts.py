"""
Generate analysis charts for the Drawit prompt engineering task.
Outputs: outputs/charts/token_comparison.png
         outputs/charts/mood_classification.png
         outputs/charts/score_divergence.png
         outputs/charts/happiness_confidence.png
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

PROJECT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT / "outputs" / "charts"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Colours ──────────────────────────────────────────────────────────────────
C_BASELINE = "#4A4A8A"
C_GEMINI   = "#4285F4"
C_GEMMA    = "#34A853"
C_QWEN     = "#FBBC05"
C_V1       = "#E8734A"
C_V3       = "#5BA85D"
C_ARABIC   = "#9B59B6"
BG         = "#F8F9FA"


# ── 1. TOKEN COMPARISON ───────────────────────────────────────────────────────
def chart_tokens():
    labels  = ["v1_original\n(Module A)", "v3_optimized\n(Module B)", "v4_arabic\n(Module C, ref)"]
    tokens  = [1374, 940, 1487]
    colours = [C_V1, C_V3, C_ARABIC]

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    bars = ax.bar(labels, tokens, color=colours, width=0.5, zorder=3, edgecolor="white", linewidth=1.2)

    # Reduction arrow between v1 and v3
    ax.annotate(
        "", xy=(1, 940), xytext=(0, 1374),
        arrowprops=dict(arrowstyle="->", color="#E74C3C", lw=2.0),
        xycoords=("data", "data"),
    )
    ax.text(0.5, 1160, "−31.6%\n(434 tokens)", ha="center", va="center",
            fontsize=11, color="#E74C3C", fontweight="bold")

    # Value labels on bars
    for bar, val in zip(bars, tokens):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 15,
                f"{val:,}", ha="center", va="bottom", fontsize=12, fontweight="bold")

    # Target line
    ax.axhline(1374 * 0.70, color="#E74C3C", linestyle="--", linewidth=1.2, alpha=0.5, zorder=2)
    ax.text(2.42, 1374 * 0.70 + 15, "30% target (962)", fontsize=9,
            color="#E74C3C", alpha=0.8, ha="right")

    ax.set_ylim(0, 1700)
    ax.set_ylabel("Tokens (cl100k_base)", fontsize=12)
    ax.set_title("Prompt Token Count — Module A vs Module B", fontsize=14, fontweight="bold", pad=14)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "token_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ token_comparison.png")


# ── 2. MOOD CLASSIFICATION GRID ───────────────────────────────────────────────
MOOD_NUM = {"concerning": 0, "neutral": 1, "positive": 2}
MOOD_LABELS = ["concerning", "neutral", "positive"]
MOOD_COLOURS = ["#E74C3C", "#F39C12", "#2ECC71"]

def _mood_int(val):
    v = str(val).lower().strip()
    # non-standard qwen values → None
    return MOOD_NUM.get(v)


def chart_mood():
    drawings_display = ["Drawing 1\n(baseline: concerning)", "Drawing 2\n(baseline: concerning)",
                        "Drawing 3\n(baseline: neutral)", "Drawing 4\n(baseline: neutral)",
                        "Drawing 5\n(baseline: positive)"]
    drawing_ids = ["drawing_1", "drawing_2", "drawing_3", "drawing_4_paper", "drawing_5"]
    baselines   = [0, 0, 1, 1, 2]

    # Load module_a results for the 3 models
    out_dir = PROJECT / "data" / "models_outputs" / "module_a"
    models  = ["gemini-2.5-flash", "gemma4:e4b", "qwen2.5vl:7b"]
    safe    = {m: m.replace(":", "_").replace("/", "_") for m in models}

    results = {m: [] for m in models}
    for did in drawing_ids:
        for m in models:
            matches = sorted(
                [p for p in out_dir.glob(f"{safe[m]}_{did}_*.json") if "_raw" not in p.name],
                key=lambda p: p.stat().st_mtime, reverse=True,
            )
            if matches:
                d = json.loads(matches[0].read_text())
                results[m].append(_mood_int(d.get("overallMood", "")))
            else:
                results[m].append(None)

    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    x      = np.arange(len(drawing_ids))
    width  = 0.18
    labels = ["Baseline", "Gemini 2.5 Flash", "Gemma4:e4b", "Qwen2.5vl:7b"]
    colors = [C_BASELINE, C_GEMINI, C_GEMMA, C_QWEN]
    all_vals = [baselines] + [results[m] for m in models]

    for i, (vals, label, colour) in enumerate(zip(all_vals, labels, colors)):
        offsets = x + (i - 1.5) * width
        for j, (v, ox) in enumerate(zip(vals, offsets)):
            if v is None:
                ax.bar(ox, 0.3, bottom=0, color="#CCCCCC", width=width * 0.85, alpha=0.5, zorder=3)
                ax.text(ox, 0.15, "?", ha="center", va="center", fontsize=9, color="#888")
            else:
                ax.bar(ox, 1, bottom=v, color=colour, width=width * 0.85, alpha=0.85, zorder=3, edgecolor="white")
                ax.text(ox, v + 0.5, MOOD_LABELS[v][0].upper(), ha="center", va="center",
                        fontsize=8, fontweight="bold", color="white")

    # Y axis — mood bands
    for level, mc, ml in zip([0, 1, 2], MOOD_COLOURS, MOOD_LABELS):
        ax.axhspan(level, level + 1, color=mc, alpha=0.07, zorder=0)

    ax.set_xticks(x)
    ax.set_xticklabels(drawings_display, fontsize=9)
    ax.set_yticks([0.5, 1.5, 2.5])
    ax.set_yticklabels(["Concerning", "Neutral", "Positive"], fontsize=11)
    ax.set_ylim(0, 3)
    ax.set_title("Overall Mood Classification — Baseline vs All Models (Module A)", fontsize=13, fontweight="bold", pad=14)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.yaxis.grid(False)

    patches = [mpatches.Patch(color=c, label=l) for c, l in zip(colors, labels)]
    ax.legend(handles=patches, loc="upper right", fontsize=9, framealpha=0.7)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "mood_classification.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ mood_classification.png")


# ── 3. SCORE DIVERGENCE — drawing_1 (most divergent) ─────────────────────────
def chart_score_divergence():
    # Comparison table data for drawing_1 numeric fields
    fields = [
        "happiness", "confidence", "creativity", "socialBonds",
        "extroversion", "emotionalStability", "conscientiousness", "openness", "agreeableness",
        "colorDiversity", "emotionalColorChoices", "ageAppropriateColorUse",
    ]
    field_labels = [
        "Happiness", "Confidence", "Creativity", "Social Bonds",
        "Extroversion", "Emo. Stability", "Conscientious.", "Openness", "Agreeableness",
        "Color Diversity", "Color Emotion", "Color Age-App.",
    ]

    # From comparison_table.csv and direct file reads
    baseline = [0.4, 0.6, 0.7, 0.3,   0.3, 0.6, 0.8, 0.6, 0.6,   0.5, 0.4, 0.8]
    gemini   = [0.5, 0.7, 0.8, 0.3,   0.3, 0.7, 0.8, 0.7, 0.7,   0.8, 0.6, 0.9]
    gemma    = [0.5, 0.6, 0.5, 0.3,   0.4, 0.6, 0.5, 0.6, 0.5,   0.7, 0.6, 0.7]
    qwen     = [0.4, 0.3, 0.6, 0.5,   0.2, 0.3, 0.5, 0.4, 0.6,   0.4, 0.6, 0.8]

    x     = np.arange(len(fields))
    width = 0.2

    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)

    for i, (vals, label, colour) in enumerate(zip(
        [baseline, gemini, gemma, qwen],
        ["Baseline", "Gemini 2.5 Flash", "Gemma4:e4b", "Qwen2.5vl:7b"],
        [C_BASELINE, C_GEMINI, C_GEMMA, C_QWEN],
    )):
        ax.bar(x + (i - 1.5) * width, vals, width * 0.88, label=label, color=colour, zorder=3, edgecolor="white")

    # Section separators
    for sep in [3.5, 8.5]:
        ax.axvline(sep, color="#CCCCCC", linewidth=1.2, linestyle="--", zorder=2)

    ax.text(1.5, 1.03, "Emotional Indicators", ha="center", fontsize=9, color="#666", transform=ax.get_xaxis_transform())
    ax.text(6.0, 1.03, "Personality Traits", ha="center", fontsize=9, color="#666", transform=ax.get_xaxis_transform())
    ax.text(10.5, 1.03, "Color Metrics", ha="center", fontsize=9, color="#666", transform=ax.get_xaxis_transform())

    ax.set_xticks(x)
    ax.set_xticklabels(field_labels, rotation=35, ha="right", fontsize=9)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Score [0.0 – 1.0]", fontsize=11)
    ax.set_title("Score Divergence — Drawing 1 (Baseline: concerning) — Module A", fontsize=13, fontweight="bold", pad=14)
    ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="upper right", fontsize=9, framealpha=0.8)

    fig.tight_layout()
    fig.savefig(OUT_DIR / "score_divergence.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ score_divergence.png")


# ── 4. HAPPINESS + CONFIDENCE ACROSS ALL DRAWINGS ────────────────────────────
def chart_happiness_confidence():
    drawings_short = ["D1\n(concern.)", "D2\n(concern.)", "D3\n(neutral)", "D4\n(neutral)", "D5\n(positive)"]
    drawing_ids    = ["drawing_1", "drawing_2", "drawing_3", "drawing_4_paper", "drawing_5"]

    base_happiness   = [0.4, 0.6, 0.7, 0.7, 0.9]
    base_confidence  = [0.6, 0.4, 0.6, 0.6, 0.8]

    out_dir = PROJECT / "data" / "models_outputs" / "module_a"
    models  = ["gemini-2.5-flash", "gemma4:e4b", "qwen2.5vl:7b"]
    safe    = {m: m.replace(":", "_").replace("/", "_") for m in models}

    model_scores = {}
    for m in models:
        h_vals, c_vals = [], []
        for did in drawing_ids:
            matches = sorted(
                [p for p in out_dir.glob(f"{safe[m]}_{did}_*.json") if "_raw" not in p.name],
                key=lambda p: p.stat().st_mtime, reverse=True,
            )
            if matches:
                d = json.loads(matches[0].read_text())
                ei = d.get("emotionalIndicators", {})
                h_vals.append(ei.get("happiness"))
                c_vals.append(ei.get("confidence"))
            else:
                h_vals.append(None)
                c_vals.append(None)
        model_scores[m] = (h_vals, c_vals)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    fig.patch.set_facecolor(BG)

    for ax, metric_idx, title in [
        (ax1, 0, "Happiness Score"),
        (ax2, 1, "Confidence Score"),
    ]:
        ax.set_facecolor(BG)
        x = np.arange(len(drawing_ids))

        base_vals = base_happiness if metric_idx == 0 else base_confidence
        ax.plot(x, base_vals, "o--", color=C_BASELINE, linewidth=2.2, markersize=8,
                label="Baseline", zorder=4)

        for m, colour in zip(models, [C_GEMINI, C_GEMMA, C_QWEN]):
            vals = model_scores[m][metric_idx]
            clean_x = [xi for xi, v in zip(x, vals) if v is not None]
            clean_v = [v for v in vals if v is not None]
            ax.plot(clean_x, clean_v, "o-", color=colour, linewidth=1.8, markersize=7,
                    alpha=0.85, label=m, zorder=3)

        ax.set_xticks(x)
        ax.set_xticklabels(drawings_short, fontsize=10)
        ax.set_ylim(0, 1.05)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.yaxis.grid(True, linestyle="--", alpha=0.4, zorder=0)
        ax.set_axisbelow(True)
        ax.spines[["top", "right"]].set_visible(False)

    ax1.set_ylabel("Score [0.0 – 1.0]", fontsize=11)
    ax1.legend(fontsize=9, loc="lower right", framealpha=0.8)

    fig.suptitle("Happiness & Confidence — Baseline vs Models Across All Drawings (Module A)",
                 fontsize=13, fontweight="bold", y=1.02)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "happiness_confidence.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("  ✓ happiness_confidence.png")


if __name__ == "__main__":
    print("Generating charts...")
    chart_tokens()
    chart_mood()
    chart_score_divergence()
    chart_happiness_confidence()
    print(f"\nAll charts saved → {OUT_DIR}")
