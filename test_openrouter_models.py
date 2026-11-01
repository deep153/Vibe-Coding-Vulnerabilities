"""Verify OpenRouter connectivity and SARD model slugs."""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from sard_config import (
    AUTO_REVIEWER_MODEL_ID,
    CODING_MODELS,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
)

load_dotenv()


def main() -> int:
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY not set")
        return 1

    client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
    targets = [m["model_id"] for m in CODING_MODELS] + [AUTO_REVIEWER_MODEL_ID]

    print("OpenRouter connectivity check\n")
    ok = 0
    for model_id in targets:
        try:
            resp = client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": "Reply with OK only."}],
                max_tokens=8,
                temperature=0,
            )
            text = (resp.choices[0].message.content or "").strip()
            print(f"  OK  {model_id} -> {text[:40]!r}")
            ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  FAIL {model_id} -> {exc}")

    print(f"\n{ok}/{len(targets)} models reachable")
    return 0 if ok == len(targets) else 2


if __name__ == "__main__":
    sys.exit(main())
