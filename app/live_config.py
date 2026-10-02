from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"


def load_local_env() -> None:
    """Load the ignored local .env without adding another runtime dependency."""
    if not ENV_PATH.is_file():
        return
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip().startswith("AI_SCROLL_"):
            os.environ[key.strip()] = value.strip()


def live_model_status() -> dict[str, str | bool]:
    load_local_env()
    return {
        "configured": bool(os.getenv("AI_SCROLL_API_KEY", "").strip()),
        "base_url": os.getenv("AI_SCROLL_BASE_URL", "https://openrouter.ai/api/v1").strip(),
        "model": os.getenv("AI_SCROLL_MODEL", "openai/gpt-5-mini").strip(),
    }


def save_live_model_config(api_key: str, base_url: str, model: str) -> None:
    values = {
        "AI_SCROLL_API_KEY": api_key.strip(),
        "AI_SCROLL_BASE_URL": base_url.strip(),
        "AI_SCROLL_MODEL": model.strip(),
        "AI_SCROLL_INPUT_PRICE_PER_MILLION": "0.25",
        "AI_SCROLL_OUTPUT_PRICE_PER_MILLION": "2.00",
    }
    if not all((values["AI_SCROLL_API_KEY"], values["AI_SCROLL_BASE_URL"], values["AI_SCROLL_MODEL"])):
        raise ValueError("API key, base URL and model are required.")
    ENV_PATH.write_text(
        "# Local Live model configuration. This file is ignored by Git.\n"
        + "\n".join(f"{key}={value}" for key, value in values.items())
        + "\n",
        encoding="utf-8",
    )
    os.environ.update(values)
