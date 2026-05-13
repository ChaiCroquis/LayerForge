"""LayerForge constants — single source of truth for axiomatic values.

All values are referenced in docs/03_extracted_formulas.md by the same names.
"""
from __future__ import annotations

# === F3.1 Cowan's 4±1 ===
LAYER_COUNT_MIN: int = 3
LAYER_COUNT_MAX: int = 5
LAYER_COUNT_OPTIMAL: int = 4

# === F3.4 Recursion depth limit ===
MAX_RECURSION_DEPTH: int = 4

# === F2.9 SCA hyperparameter defaults (paper §C.1 Trump dataset) ===
SCA_DEFAULT_MU: float = 0.95
SCA_DEFAULT_ALPHA: float = 0.20
SCA_DEFAULT_THETA: float = 0.5
SCA_DEFAULT_MIN_CLUSTER_SIZE: int = 100
SCA_DEFAULT_MIN_SAMPLES: int = 50
SCA_DEFAULT_MAX_ITER: int = 10
SCA_DEFAULT_NC_S: int = 2
SCA_DEFAULT_NC_THRESHOLD: int = 5
SCA_DEFAULT_RN_THRESHOLD: float = 0.01

# === F2.7 Purity thresholds ===
PURITY_THRESHOLD_GOOD: float = 0.7
PURITY_THRESHOLD_ACCEPTABLE: float = 0.5

# === F4.7 Modularity thresholds ===
MODULARITY_THRESHOLD_GOOD: float = 0.7
MODULARITY_THRESHOLD_ACCEPTABLE: float = 0.3

# === F1.4 Binary search ===
SCALE_SEARCH_MAX_ITER: int = 50
SCALE_SEARCH_TOLERANCE: float = 1e-6

# === Determinism ===
DETERMINISTIC_SEED: int = 42

# === Inference layer ===
MAX_RETRIES: int = 3

# === F2.8 LayerForge extension: giant generic cluster detection ===
GIANT_CLUSTER_RATIO_THRESHOLD: float = 0.3

# === SCA reference-impl defaults (mainlp/semantic_components) ===
SCA_EPS_COMPONENT: float = 0.01  # min centroid norm to keep a component
SCA_UMAP_N_NEIGHBORS: int = 20
SCA_UMAP_N_EPOCHS: int = 200
SCA_UMAP_MIN_DIST: float = 0.0
SCA_UMAP_N_COMPONENTS: int = 5
