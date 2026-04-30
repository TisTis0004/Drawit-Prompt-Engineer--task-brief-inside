"""
Helper functions: prompt loading, image encoding, result saving, logging setup.
"""

import base64
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_prompt(version: str = "v1_original") -> str:
    """
    Load system prompt and schema for a given prompt version folder.
    Falls back to the shared prompts/schema.json if no local schema.json exists.
    """
    prompt_dir = PROJECT_ROOT / "prompts" / version
    system_path = prompt_dir / "system.txt"
    local_schema = prompt_dir / "schema.json"
    global_schema = PROJECT_ROOT / "prompts" / "schema.json"

    with open(system_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    schema_path = local_schema if local_schema.exists() else global_schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()

    return system_prompt + "\n\nJSON Schema:\n" + schema


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def save_result(
    result: dict,
    module: str,
    model: str,
    drawing_id: str,
    raw: str | None = None,
) -> Path:
    """
    Save inference result JSON to data/models_outputs/{module}/.
    Also saves the raw string if provided (for debugging parse failures).
    Returns the path of the saved file.
    """
    safe_model = model.replace(":", "_").replace("/", "_")
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    out_dir = PROJECT_ROOT / "data" / "models_outputs" / f"module_{module}"
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = f"{safe_model}_{drawing_id}_{timestamp}"
    json_path = out_dir / f"{stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if raw is not None:
        raw_path = out_dir / f"{stem}_raw.txt"
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(raw)

    return json_path


def setup_logger(name: str) -> logging.Logger:
    """
    Returns a logger that writes to both console and logs/{date}.log.
    """
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


def list_drawings() -> list[str]:
    """Return drawing file stems (no extension), sorted."""
    drawings_dir = PROJECT_ROOT / "data" / "drawings"
    stems = sorted(
        p.stem for p in drawings_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png"}
    )
    return stems


def get_drawing_path(drawing_id: str) -> Path:
    drawings_dir = PROJECT_ROOT / "data" / "drawings"
    for ext in [".jpg", ".jpeg", ".png"]:
        p = drawings_dir / f"{drawing_id}{ext}"
        if p.exists():
            return p
    raise FileNotFoundError(f"No image found for drawing_id='{drawing_id}' in {drawings_dir}")
