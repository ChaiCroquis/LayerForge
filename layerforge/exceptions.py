"""LayerForge exception hierarchy (docs/05 §例外設計)."""
from __future__ import annotations


class LayerForgeError(Exception):
    """Base class for all LayerForge exceptions."""


class NoValidScaleError(LayerForgeError):
    """4±1 に収まる scale 係数が見つからない (F3.3, F1.4)."""

    def __init__(self, message: str, similarity_stats: dict | None = None) -> None:
        super().__init__(message)
        self.similarity_stats = similarity_stats or {}


class SeparationQualityError(LayerForgeError):
    """Modularity Q が threshold を下回る (F4.8)."""

    def __init__(self, modularity: float, threshold: float) -> None:
        super().__init__(
            f"Modularity {modularity:.3f} < threshold {threshold:.3f}"
        )
        self.modularity = modularity
        self.threshold = threshold


class SchemaViolation(LayerForgeError):
    """推論層出力が schema に違反."""


class LLMError(LayerForgeError):
    """LLM API 呼び出し失敗."""


class ValidationError(LayerForgeError):
    """出力検証失敗."""
