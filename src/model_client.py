"""
Unified model client supporting Gemini (via OpenAI-compatible API) and Ollama (local).
Use get_client(model_name) to get the right client without knowing the backend.
"""

import base64
import io
import os
from abc import ABC, abstractmethod
from pathlib import Path

from openai import OpenAI


GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

# qwen2.5vl crashes with GGML assertion error on images larger than ~1280px (too many 28×28 patches).
# gemma4 and Gemini handle large images fine, so the cap is Ollama-only.
OLLAMA_MAX_IMAGE_PX = 1280

SUPPORTED_MODELS = {
    "gemini": ["gemini-2.5-flash"],
    # vision-capable: gemma4:e4b, qwen2.5vl:7b
    # text-only (no image support, will fail gracefully): ministral-3:8b
    "ollama": ["gemma4:e4b", "qwen2.5vl:7b", "ministral-3:8b"],
}


class ModelClient(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def analyze(self, system_prompt: str, image_path: str) -> str:
        """Run inference on a single drawing and return the raw response string."""
        pass

    def _encode_image(self, image_path: str, max_px: int | None = None) -> tuple[str, str]:
        """
        Returns (base64_string, mime_type).
        If max_px is set and the image exceeds it on either dimension, resize proportionally.
        """
        ext = Path(image_path).suffix.lower()
        mime = "image/png" if ext == ".png" else "image/jpeg"

        if max_px is None:
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8"), mime

        try:
            from PIL import Image as PILImage
            img = PILImage.open(image_path)
            w, h = img.size
            if w > max_px or h > max_px:
                scale = max_px / max(w, h)
                img = img.resize((int(w * scale), int(h * scale)), PILImage.LANCZOS)
            buf = io.BytesIO()
            fmt = "PNG" if ext == ".png" else "JPEG"
            img.save(buf, format=fmt, quality=90)
            return base64.b64encode(buf.getvalue()).decode("utf-8"), mime
        except ImportError:
            # Pillow not installed — send as-is and let the model handle it
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8"), mime

    def _build_messages(self, system_prompt: str, image_path: str, max_px: int | None = None) -> list[dict]:
        b64, mime = self._encode_image(image_path, max_px=max_px)
        return [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Analyze this child's drawing."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            },
        ]


class GeminiClient(ModelClient):
    def __init__(self, model_name: str, api_key: str):
        super().__init__(model_name)
        self._client = OpenAI(api_key=api_key, base_url=GEMINI_BASE_URL)

    def analyze(self, system_prompt: str, image_path: str) -> str:
        messages = self._build_messages(system_prompt, image_path)
        response = self._client.chat.completions.create(
            model=self.model_name, messages=messages
        )
        return response.choices[0].message.content


class OllamaClient(ModelClient):
    def __init__(self, model_name: str, base_url: str):
        super().__init__(model_name)
        self._client = OpenAI(api_key="ollama", base_url=base_url)

    def analyze(self, system_prompt: str, image_path: str) -> str:
        messages = self._build_messages(system_prompt, image_path, max_px=OLLAMA_MAX_IMAGE_PX)
        response = self._client.chat.completions.create(
            model=self.model_name, messages=messages
        )
        return response.choices[0].message.content


def get_client(model_name: str) -> ModelClient:
    """Factory: routes to GeminiClient or OllamaClient based on model name prefix."""
    if model_name.startswith("gemini-"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        return GeminiClient(model_name, api_key)
    else:
        base_url = os.getenv("OLLAMA_LOCAL_BASE_URL", "http://localhost:11434/v1")
        return OllamaClient(model_name, base_url)
