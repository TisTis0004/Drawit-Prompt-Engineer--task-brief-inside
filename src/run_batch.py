"""
Batch runner — executes all module × model × drawing combinations.

Modules:
  a  →  v1_original   (cross-model replication)
  b  →  v3_optimized  (token-optimized prompt)
  c  →  v4_arabic     (Arabic localization)

Models tested:
  gemini-2.5-flash    (frontier cost-efficient)
  gemma4:e4b          (Ollama vision, open-source)
  qwen2.5vl:7b        (Ollama VL, open-source)
  ministral-3:8b      (Ollama text-only — included to document failure mode)

Usage:
  python src/run_batch.py
  python src/run_batch.py --modules a,b --models gemini-2.5-flash,gemma4:e4b
  python src/run_batch.py --skip-existing
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from helpers import load_prompt, save_result, setup_logger, list_drawings, get_drawing_path
from model_client import get_client
from models import validate_output
from evaluator import compare_outputs, generate_comparison_table, load_baseline

PROJECT_ROOT = Path(__file__).resolve().parent.parent

MODULE_PROMPT_MAP = {
    "a": "v1_original",
    "b": "v3_optimized",
    "c": "v4_arabic",
}

DEFAULT_MODULES = ["a", "b", "c"]
DEFAULT_MODELS = ["gemini-2.5-flash", "gemma4:e4b", "qwen2.5vl:7b", "ministral-3:8b"]

GEMINI_RATE_LIMIT_DELAY = 4  # seconds between Gemini calls (free tier: 15 RPM)


def result_exists(module: str, model: str, drawing_id: str) -> bool:
    """Check if a result already exists for this combination."""
    safe_model = model.replace(":", "_").replace("/", "_")
    out_dir = PROJECT_ROOT / "data" / "models_outputs" / f"module_{module}"
    pattern = f"{safe_model}_{drawing_id}_*.json"
    matches = [p for p in out_dir.glob(pattern) if "_raw" not in p.name]
    # Only count as existing if the file contains a valid (non-error) result
    for p in matches:
        try:
            d = json.loads(p.read_text())
            if "error" not in d and "overallMood" in d:
                return True
        except Exception:
            continue
    return False


def load_latest_result(module: str, model: str, drawing_id: str) -> dict | None:
    """Load the most recent saved result for this combination."""
    safe_model = model.replace(":", "_").replace("/", "_")
    out_dir = PROJECT_ROOT / "data" / "models_outputs" / f"module_{module}"
    pattern = f"{safe_model}_{drawing_id}_*.json"
    matches = sorted(
        [p for p in out_dir.glob(pattern) if "_raw" not in p.name],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not matches:
        return None
    with open(matches[0]) as f:
        return json.load(f)


def run_one(module: str, model: str, drawing_id: str, prompt_version: str, logger) -> dict | None:
    """Run a single inference, validate, save, and return result dict."""
    try:
        system_prompt = load_prompt(prompt_version)
    except FileNotFoundError as e:
        logger.error(f"Prompt not found ({prompt_version}): {e}")
        return None

    try:
        image_path = str(get_drawing_path(drawing_id))
    except FileNotFoundError as e:
        logger.error(str(e))
        return None

    try:
        client = get_client(model)
        raw = client.analyze(system_prompt, image_path)
    except Exception as e:
        logger.error(f"[{module}|{model}|{drawing_id}] Inference failed: {e}")
        err = {"error": str(e), "model": model, "drawing": drawing_id,
               "_meta": {"module": module, "model": model, "drawing_id": drawing_id,
                         "prompt_version": prompt_version, "validation_errors": [str(e)]}}
        save_result(err, module, model, drawing_id)
        return None

    validated, errors = validate_output(raw)
    if errors:
        logger.warning(f"[{module}|{model}|{drawing_id}] Validation issues: {errors}")
    else:
        logger.info(f"[{module}|{model}|{drawing_id}] OK — mood={_quick_mood(raw)}")

    if validated:
        from datetime import datetime, timezone
        result = validated.model_dump()
        result["createdAt"] = datetime.now(timezone.utc).isoformat()
    else:
        try:
            import re
            cleaned = re.sub(r"^```(?:json)?\s*\n?", "", raw.strip(), flags=re.IGNORECASE)
            cleaned = re.sub(r"\n?```\s*$", "", cleaned).strip()
            result = json.loads(cleaned)
        except Exception:
            result = {"raw_response": raw, "validation_errors": errors}

    result["_meta"] = {
        "module": module, "model": model, "drawing_id": drawing_id,
        "prompt_version": prompt_version, "validation_errors": errors,
    }
    save_result(result, module, model, drawing_id, raw=raw)
    return result


def _quick_mood(raw: str) -> str:
    import re
    m = re.search(r'"overallMood"\s*:\s*"([^"]+)"', raw)
    return m.group(1) if m else "?"


def build_module_a_table(all_results: dict[str, dict[str, dict]], logger):
    """Generate and save Module A comparison table across all models × drawings."""
    table_dir = PROJECT_ROOT / "evals" / "module_a"
    table_dir.mkdir(parents=True, exist_ok=True)
    csv_path = table_dir / "comparison_table.csv"

    chunks = []
    for drawing_id, outputs_by_model in sorted(all_results.items()):
        baseline = load_baseline(drawing_id, str(PROJECT_ROOT / "data" / "baseline_outputs"))
        if baseline is None:
            continue
        # Filter out results that errored
        clean_outputs = {m: r for m, r in outputs_by_model.items() if "error" not in r}
        if not clean_outputs:
            continue
        chunks.append(generate_comparison_table(drawing_id, baseline, clean_outputs))

    if not chunks:
        logger.warning("No valid outputs to build comparison table from.")
        return

    header = chunks[0].split("\n")[0]
    rows = [header]
    for chunk in chunks:
        rows.extend(chunk.split("\n")[1:])
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("\n".join(rows))
    logger.info(f"Comparison table saved → {csv_path}")


def run_batch(modules: list[str], models: list[str], skip_existing: bool, logger):
    drawings = list_drawings()
    logger.info(f"Starting batch: modules={modules} models={models} drawings={drawings}")

    # results[module][drawing_id][model] = result_dict
    results: dict[str, dict[str, dict[str, dict]]] = {m: {} for m in modules}
    stats = {"ok": 0, "skipped": 0, "failed": 0}

    for module in modules:
        prompt_version = MODULE_PROMPT_MAP[module]
        logger.info(f"\n{'='*60}\nMODULE {module.upper()} — prompt: {prompt_version}\n{'='*60}")

        for drawing_id in drawings:
            results[module][drawing_id] = {}
            for model in models:
                if skip_existing and result_exists(module, model, drawing_id):
                    logger.info(f"  [SKIP] {module}|{model}|{drawing_id} — already exists")
                    existing = load_latest_result(module, model, drawing_id)
                    if existing:
                        results[module][drawing_id][model] = existing
                    stats["skipped"] += 1
                    continue

                result = run_one(module, model, drawing_id, prompt_version, logger)

                if result:
                    results[module][drawing_id][model] = result
                    stats["ok"] += 1
                else:
                    stats["failed"] += 1

                # Rate-limit Gemini calls
                if model.startswith("gemini-"):
                    time.sleep(GEMINI_RATE_LIMIT_DELAY)

        # Post-module: generate comparison table for Module A
        if module == "a":
            build_module_a_table(results["a"], logger)

    # Final summary
    logger.info(f"\nBatch complete: {stats['ok']} OK, {stats['skipped']} skipped, {stats['failed']} failed")
    _print_summary(results, models, drawings)

    return results


def _print_summary(results, models, drawings):
    print(f"\n{'='*70}")
    print(f"{'MODULE':<8} {'DRAWING':<18} {'MODEL':<22} {'MOOD':<20} STATUS")
    print(f"{'='*70}")
    for module in sorted(results.keys()):
        for drawing_id in drawings:
            for model in models:
                r = results.get(module, {}).get(drawing_id, {}).get(model)
                if r is None:
                    print(f"{module:<8} {drawing_id:<18} {model:<22} {'—':<20} MISSING")
                elif "error" in r:
                    err_short = str(r["error"])[:40]
                    print(f"{module:<8} {drawing_id:<18} {model:<22} {'ERROR':<20} {err_short}")
                else:
                    mood = r.get("overallMood", "?")
                    errs = len(r.get("_meta", {}).get("validation_errors", []))
                    status = "OK" if errs == 0 else f"WARN({errs})"
                    print(f"{module:<8} {drawing_id:<18} {model:<22} {mood:<20} {status}")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Run all Drawit inference combinations.")
    parser.add_argument("--modules", default=",".join(DEFAULT_MODULES),
                        help=f"Comma-separated modules to run (default: {','.join(DEFAULT_MODULES)})")
    parser.add_argument("--models", default=",".join(DEFAULT_MODELS),
                        help="Comma-separated model names to use")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip combinations where a result file already exists")
    args = parser.parse_args()

    logger = setup_logger("drawit.batch")
    modules = [m.strip() for m in args.modules.split(",")]
    models = [m.strip() for m in args.models.split(",")]

    run_batch(modules, models, args.skip_existing, logger)


if __name__ == "__main__":
    main()
