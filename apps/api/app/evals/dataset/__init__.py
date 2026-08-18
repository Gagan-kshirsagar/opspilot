"""Golden dataset loader for OpsPilot evaluation harness."""

from __future__ import annotations

import json
from pathlib import Path

from app.evals.models import EvalCase, EvalCategory


def load_eval_cases(category: EvalCategory | str | None = None) -> list[EvalCase]:
    """Load evaluation cases from JSON dataset, optionally filtered by category."""
    json_path = Path(__file__).resolve().parent / "eval_cases.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Evaluation dataset not found at: {json_path}")

    with open(json_path, encoding="utf-8") as f:
        raw_data = json.load(f)

    cases = [EvalCase.model_validate(item) for item in raw_data]

    if category:
        cat_str = (
            category.value if isinstance(category, EvalCategory) else str(category)
        )
        cases = [c for c in cases if c.category.value == cat_str]

    return cases
