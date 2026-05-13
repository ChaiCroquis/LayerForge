"""Hallucination-reduction benchmark for LayerForge (ADR-012 verification).

Tests the hypothesis: passing only the LayerForge-filtered layer to the AI
reduces hallucination vs passing the full corpus.

Corpus is entirely fictional to eliminate training-data leakage — every
named entity, year, ratio, and chemical formula is invented.
"""
