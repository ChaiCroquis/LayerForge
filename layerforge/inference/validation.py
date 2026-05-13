"""Schema-side validation helpers (Phase 1 minimal)."""
from __future__ import annotations

from typing import Any


def is_dict_with_keys(obj: Any, required: list[str]) -> bool:
    return isinstance(obj, dict) and all(k in obj for k in required)
