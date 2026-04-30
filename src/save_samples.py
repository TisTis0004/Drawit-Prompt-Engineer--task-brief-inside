"""
Post-batch helper: copies the best available sample output (gemini-2.5-flash drawing_1)
from data/models_outputs/{module}/ to outputs/{module}/sample_output.json.

Run after run_batch.py completes:
    python src/save_samples.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

PROJECT_ROOT = Path(__file__).resolve().parent.parent

PREFERRED_MODEL = "gemini-2.5-flash"
PREFERRED_DRAWING = "drawing_1"
FALLBACK_MODELS = ["gemma4_e4b", "qwen2.5vl_7b"]


def find_best_result(module: str) -> Path | None:
    out_dir = PROJECT_ROOT / "data" / "models_outputs" / f"module_{module}"
    if not out_dir.exists():
        return None
    safe_model = PREFERRED_MODEL.replace(":", "_").replace("/", "_").replace(".", "-")
    # Try preferred: gemini flash, drawing_1
    matches = sorted(
        [p for p in out_dir.glob(f"{safe_model}_{PREFERRED_DRAWING}_*.json") if "_raw" not in p.name],
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    if matches:
        return matches[0]
    # Fallback: any valid result for drawing_1
    for fb in FALLBACK_MODELS:
        matches = sorted(
            [p for p in out_dir.glob(f"{fb}_{PREFERRED_DRAWING}_*.json") if "_raw" not in p.name],
            key=lambda p: p.stat().st_mtime, reverse=True
        )
        if matches:
            return matches[0]
    # Last fallback: any valid result in the module dir
    all_results = sorted(
        [p for p in out_dir.glob("*.json") if "_raw" not in p.name],
        key=lambda p: p.stat().st_mtime, reverse=True
    )
    for p in all_results:
        try:
            d = json.loads(p.read_text())
            if "error" not in d and "overallMood" in d:
                return p
        except Exception:
            continue
    return None


def save_samples():
    for module in ["a", "b", "c", "d"]:
        dest = PROJECT_ROOT / "outputs" / f"module_{module}" / "sample_output.json"
        src = find_best_result(module)
        if src is None:
            print(f"[module_{module}] No valid result found — skipping")
            continue
        data = json.loads(src.read_text())
        # Strip internal _meta field before saving to outputs/
        data.pop("_meta", None)
        dest.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        mood = data.get("overallMood", "?")
        title = data.get("drawingTitle", "?")[:50]
        print(f"[module_{module}] Saved → outputs/module_{module}/sample_output.json  [{mood}] \"{title}\"")


if __name__ == "__main__":
    save_samples()
