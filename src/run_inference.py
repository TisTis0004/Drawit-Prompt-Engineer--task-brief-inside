"""
Main entry point for running Drawit drawing analysis inference.

Usage (run from project root):
    python src/run_inference.py --module a --model gemini-2.5-flash --drawing drawing_1
    python src/run_inference.py --module a --model gemini-2.5-pro --drawing all
    python src/run_inference.py --module b --model gemma4:e4b --drawing drawing_3
    python src/run_inference.py --module c --model gemini-2.5-flash --drawing drawing_1

Module → prompt version mapping:
    a  →  v1_original   (baseline prompt, cross-model replication)
    b  →  v3_optimized  (30%+ reduced prompt, token optimization)
    c  →  v4_arabic     (Arabic localization)
    d  →  v1_original   (edge case stress-testing with original prompt)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

# Ensure src/ is on the path when run from project root
sys.path.insert(0, str(Path(__file__).resolve().parent))

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
    "d": "v1_original",
}


def run_single(module: str, model: str, drawing_id: str, prompt_version: str, logger) -> dict | None:
    """
    Run inference for one drawing, validate output, save results, compare to baseline.
    Returns parsed dict on success, None on failure.
    """
    logger.info(f"Running module={module} model={model} drawing={drawing_id} prompt={prompt_version}")

    # Load prompt
    try:
        system_prompt = load_prompt(prompt_version)
    except FileNotFoundError as e:
        logger.error(f"Prompt not found: {e}")
        return None

    # Get image path
    try:
        image_path = str(get_drawing_path(drawing_id))
    except FileNotFoundError as e:
        logger.error(str(e))
        return None

    # Run inference
    try:
        client = get_client(model)
        raw_response = client.analyze(system_prompt, image_path)
    except Exception as e:
        logger.error(f"Inference failed: {e}")
        save_result({"error": str(e), "model": model, "drawing": drawing_id}, module, model, drawing_id)
        return None

    # Validate schema
    validated, errors = validate_output(raw_response)

    if errors:
        logger.warning(f"Schema validation issues for {drawing_id}: {errors}")
    else:
        logger.info(f"Schema valid for {drawing_id}")

    # Build result dict
    if validated:
        result = validated.model_dump()
        result["createdAt"] = datetime.now(timezone.utc).isoformat()
    else:
        # Save raw even if invalid so nothing is lost
        try:
            import json as _json
            result = _json.loads(raw_response.strip().lstrip("```json").rstrip("```").strip())
        except Exception:
            result = {"raw_response": raw_response, "validation_errors": errors}

    result["_meta"] = {
        "module": module,
        "model": model,
        "drawing_id": drawing_id,
        "prompt_version": prompt_version,
        "validation_errors": errors,
    }

    saved_path = save_result(result, module, model, drawing_id, raw=raw_response)
    logger.info(f"Saved to {saved_path}")

    # Compare to baseline if available
    baseline = load_baseline(drawing_id, str(PROJECT_ROOT / "data" / "baseline_outputs"))
    if baseline:
        diff = compare_outputs(baseline, result)
        flagged = {k: v for k, v in diff.items() if v.get("flag")}
        if flagged:
            logger.warning(f"Divergences from baseline ({len(flagged)} fields): {list(flagged.keys())}")
        else:
            logger.info("No significant divergences from baseline.")
    else:
        logger.debug(f"No baseline found for {drawing_id}")

    return result


def run_module_a_table(model_outputs: dict[str, dict[str, dict]], logger):
    """
    After running Module A across multiple models and drawings,
    generate and save a comparison table per drawing.
    model_outputs = {drawing_id: {model_name: result_dict}}
    """
    table_dir = PROJECT_ROOT / "evals" / "module_a"
    table_dir.mkdir(parents=True, exist_ok=True)
    csv_path = table_dir / "comparison_table.csv"

    all_rows = []
    for drawing_id, outputs_by_model in model_outputs.items():
        baseline = load_baseline(drawing_id, str(PROJECT_ROOT / "data" / "baseline_outputs"))
        if baseline is None:
            logger.warning(f"No baseline for {drawing_id}, skipping from table")
            continue
        csv_chunk = generate_comparison_table(drawing_id, baseline, outputs_by_model)
        all_rows.append(csv_chunk)

    if all_rows:
        # Keep header from first chunk only
        first = all_rows[0]
        rest = ["\n".join(chunk.split("\n")[1:]) for chunk in all_rows[1:]]
        combined = first + "\n".join(rest)
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(combined)
        logger.info(f"Comparison table saved to {csv_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Run Drawit drawing analysis inference.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--module", "-m",
        required=True,
        choices=["a", "b", "c", "d"],
        help="Which module to run (determines prompt version)",
    )
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Model name: gemini-2.5-pro | gemini-2.5-flash | gemma4:e4b | ministral-3:8b | qwen3.5:latest",
    )
    parser.add_argument(
        "--drawing",
        default="drawing_1",
        help="Drawing stem name (e.g. drawing_1) or 'all' to run all 5 drawings",
    )
    parser.add_argument(
        "--prompt-version",
        default=None,
        help="Override the prompt version folder (e.g. v2_refined). Defaults to module mapping.",
    )
    parser.add_argument(
        "--compare-table",
        action="store_true",
        help="(Module A) After running, also generate a comparison table against baseline",
    )

    args = parser.parse_args()
    logger = setup_logger("drawit")

    prompt_version = args.prompt_version or MODULE_PROMPT_MAP[args.module]

    drawings = list_drawings() if args.drawing == "all" else [args.drawing]
    logger.info(f"Drawings to process: {drawings}")

    results_by_drawing: dict[str, dict] = {}
    for drawing_id in drawings:
        result = run_single(args.module, args.model, drawing_id, prompt_version, logger)
        if result:
            results_by_drawing[drawing_id] = result

    logger.info(f"Completed {len(results_by_drawing)}/{len(drawings)} drawings successfully.")

    # Generate comparison table for module A
    if args.module == "a" and args.compare_table and results_by_drawing:
        run_module_a_table({d: {args.model: r} for d, r in results_by_drawing.items()}, logger)

    # Print summary to stdout
    print(f"\n{'='*60}")
    print(f"Module {args.module.upper()} | Model: {args.model} | Prompt: {prompt_version}")
    print(f"Results: {len(results_by_drawing)}/{len(drawings)} drawings")
    for drawing_id, result in results_by_drawing.items():
        mood = result.get("overallMood", "unknown")
        title = result.get("drawingTitle", "—")
        errs = result.get("_meta", {}).get("validation_errors", [])
        status = "OK" if not errs else f"WARN ({len(errs)} schema issues)"
        print(f"  {drawing_id}: [{mood}] \"{title}\" — {status}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
