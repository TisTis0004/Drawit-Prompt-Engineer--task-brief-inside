"""
Compares model outputs against the baseline and each other.
Highlights divergences by type: structural, semantic, tonal.
"""

import csv
import io
import json


NUMERIC_FIELDS = {
    "emotionalIndicators.happiness",
    "emotionalIndicators.confidence",
    "emotionalIndicators.creativity",
    "emotionalIndicators.socialBonds",
    "personalityTraits.extroversion",
    "personalityTraits.emotionalStability",
    "personalityTraits.conscientiousness",
    "personalityTraits.openness",
    "personalityTraits.agreeableness",
    "colorUsage.colorDiversity",
    "colorUsage.emotionalColorChoices",
    "colorUsage.ageAppropriateColorUse",
}

TONAL_FIELDS = {"concerns", "recommendations", "keyInsights"}
SEMANTIC_FIELDS = {"overallMood", "drawingTitle"}


def _get(d: dict, dotted_key: str):
    """Safely retrieve a value from a nested dict using dot notation."""
    keys = dotted_key.split(".")
    for k in keys:
        if not isinstance(d, dict):
            return None
        d = d.get(k)
    return d


def _divergence_type(field: str) -> str:
    top = field.split(".")[0]
    if top in TONAL_FIELDS:
        return "tonal"
    if top in SEMANTIC_FIELDS:
        return "semantic"
    if field in NUMERIC_FIELDS:
        return "numeric"
    return "structural"


def compare_outputs(baseline: dict, model_output: dict) -> dict:
    """
    Field-by-field comparison between baseline and a single model output.
    Returns a dict of {field: {baseline, model, divergence_type, delta}}.
    """
    results = {}

    for field in NUMERIC_FIELDS:
        b_val = _get(baseline, field)
        m_val = _get(model_output, field)
        if b_val is None and m_val is None:
            continue
        delta = round(abs((m_val or 0) - (b_val or 0)), 3)
        results[field] = {
            "baseline": b_val,
            "model": m_val,
            "divergence_type": "numeric",
            "delta": delta,
            "flag": delta > 0.2,
        }

    for field in SEMANTIC_FIELDS:
        b_val = _get(baseline, field)
        m_val = _get(model_output, field)
        results[field] = {
            "baseline": b_val,
            "model": m_val,
            "divergence_type": "semantic",
            "delta": None,
            "flag": b_val != m_val,
        }

    # Check structural completeness
    required_top_keys = {
        "drawingTitle", "overallMood", "colorUsage", "emotionalIndicators",
        "personalityTraits", "keyInsights", "recommendations", "concerns", "createdAt",
    }
    missing = required_top_keys - set(model_output.keys())
    if missing:
        results["_structural"] = {
            "baseline": list(required_top_keys),
            "model": list(model_output.keys()),
            "divergence_type": "structural",
            "delta": None,
            "flag": True,
            "missing_fields": list(missing),
        }

    # Count tonal differences in concerns
    b_concerns = baseline.get("concerns", [])
    m_concerns = model_output.get("concerns", [])
    results["concerns.count"] = {
        "baseline": len(b_concerns),
        "model": len(m_concerns),
        "divergence_type": "tonal",
        "delta": abs(len(b_concerns) - len(m_concerns)),
        "flag": len(b_concerns) != len(m_concerns),
    }
    results["keyInsights.count"] = {
        "baseline": len(baseline.get("keyInsights", [])),
        "model": len(model_output.get("keyInsights", [])),
        "divergence_type": "tonal",
        "delta": None,
        "flag": False,
    }

    return results


def generate_comparison_table(
    drawing_id: str,
    baseline: dict,
    outputs: dict[str, dict],
) -> str:
    """
    Build a CSV comparison table.
    outputs = {"gemini-2.5-pro": {...}, "gemini-2.5-flash": {...}, ...}
    Returns CSV string.
    """
    model_names = list(outputs.keys())
    buf = io.StringIO()
    writer = csv.writer(buf)

    header = ["drawing_id", "field", "baseline"] + model_names + ["divergence_type", "flagged"]
    writer.writerow(header)

    all_fields = list(NUMERIC_FIELDS) + list(SEMANTIC_FIELDS) + ["concerns.count", "keyInsights.count"]

    for field in all_fields:
        dtype = _divergence_type(field)
        b_val = _get(baseline, field) if "." in field and field not in {"concerns.count", "keyInsights.count"} else None

        if field == "concerns.count":
            b_val = len(baseline.get("concerns", []))
        elif field == "keyInsights.count":
            b_val = len(baseline.get("keyInsights", []))
        elif "." in field:
            b_val = _get(baseline, field)
        else:
            b_val = baseline.get(field)

        model_vals = []
        flagged = False
        for name in model_names:
            out = outputs[name]
            if field == "concerns.count":
                mv = len(out.get("concerns", []))
            elif field == "keyInsights.count":
                mv = len(out.get("keyInsights", []))
            elif "." in field:
                mv = _get(out, field)
            else:
                mv = out.get(field)
            model_vals.append(mv)
            if mv != b_val:
                flagged = True

        writer.writerow([drawing_id, field, b_val] + model_vals + [dtype, "YES" if flagged else ""])

    return buf.getvalue()


def load_baseline(drawing_id: str, baseline_dir: str) -> dict | None:
    """Load baseline JSON for a drawing, returns None if not found."""
    import os
    path = os.path.join(baseline_dir, f"{drawing_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)
