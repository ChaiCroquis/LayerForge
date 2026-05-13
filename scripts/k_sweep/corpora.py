"""Synthetic corpora with parameterizable theme count for K-sweep robustness.

Each corpus has N themes × M passages-per-theme = N*M passages. Each passage
describes a uniquely-named fictional entity with 4 properties. Disjoint
vocabularies across themes ensure clean clusterability.

For K-sweep robustness check: vary N (theme count) and see whether the
optimal K (peak Q) tracks N.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Passage:
    id: str
    theme: str
    text: str


# Theme generators — each theme has unique entity-name pattern + property templates.
THEME_GENERATORS = {
    "alpha": {
        "pattern": "Alphacite-{}",
        "props": [
            ("mass_kg",      lambda r: r.choice(range(10, 500, 7))),
            ("orbit_days",   lambda r: r.choice(range(50, 2000, 13))),
            ("discovered",   lambda r: r.choice(range(1850, 1990))),
            ("density",      lambda r: round(r.uniform(2.1, 8.7), 2)),
        ],
        "text": lambda name, p: (
            f"{name} is a celestial object with mass {p['mass_kg']} kg and "
            f"orbit period {p['orbit_days']} days. Discovered in {p['discovered']}, "
            f"its density is {p['density']} g/cm^3."
        ),
    },
    "beta": {
        "pattern": "Betoxin-{}",
        "props": [
            ("ph",           lambda r: round(r.uniform(1.0, 13.5), 2)),
            ("ld50_mg",      lambda r: r.choice(range(5, 500, 11))),
            ("first_use",    lambda r: r.choice(range(1600, 1900))),
            ("color",        lambda r: r.choice(["amber", "violet", "ochre", "indigo", "crimson", "teal"])),
        ],
        "text": lambda name, p: (
            f"{name} is an alkaloid with pH {p['ph']} and LD50 of {p['ld50_mg']} mg/kg. "
            f"First documented in {p['first_use']}, the {p['color']} crystals exhibit "
            f"reversible polymerization at room temperature."
        ),
    },
    "gamma": {
        "pattern": "Gammite-{}",
        "props": [
            ("wing_span_cm", lambda r: r.choice(range(8, 70, 3))),
            ("clutch",       lambda r: r.choice(range(1, 14))),
            ("habitat",      lambda r: r.choice(["taiga", "savanna", "tundra", "wetland", "alpine", "estuary"])),
            ("call_hz",      lambda r: r.choice(range(80, 3000, 47))),
        ],
        "text": lambda name, p: (
            f"{name} is a passerine bird with wingspan {p['wing_span_cm']} cm. "
            f"It lays clutches of {p['clutch']} eggs in {p['habitat']} habitats. "
            f"The territorial call ranges around {p['call_hz']} Hz."
        ),
    },
    "delta": {
        "pattern": "Deltacode-{}",
        "props": [
            ("loc",          lambda r: r.choice(range(50, 50000, 73))),
            ("license",      lambda r: r.choice(["MIT", "Apache-2.0", "BSD-3", "GPL-3", "MPL-2", "LGPL"])),
            ("release_year", lambda r: r.choice(range(1990, 2025))),
            ("contributors", lambda r: r.choice(range(1, 500))),
        ],
        "text": lambda name, p: (
            f"{name} is an open-source library of {p['loc']} lines under {p['license']} "
            f"license, first released in {p['release_year']} with {p['contributors']} "
            f"distinct contributors over its lifetime."
        ),
    },
    "epsilon": {
        "pattern": "Epsilon-{}-Sonata",
        "props": [
            ("tempo_bpm",    lambda r: r.choice(range(40, 220, 9))),
            ("movements",    lambda r: r.choice([3, 4, 5])),
            ("key",          lambda r: r.choice(["C major", "A minor", "F# minor", "Bb major", "Eb major", "D minor"])),
            ("year",         lambda r: r.choice(range(1750, 1920))),
        ],
        "text": lambda name, p: (
            f"{name} is a classical sonata composed in {p['year']} in {p['key']}, "
            f"comprising {p['movements']} movements at tempo {p['tempo_bpm']} BPM. "
            f"The autograph manuscript is held in the Hofbibliothek."
        ),
    },
    "zeta": {
        "pattern": "Zetafish-{}",
        "props": [
            ("length_cm",    lambda r: round(r.uniform(3.0, 240.0), 1)),
            ("depth_m",      lambda r: r.choice(range(5, 1500, 17))),
            ("scales",       lambda r: r.choice(["ctenoid", "cycloid", "ganoid", "placoid"])),
            ("temperature",  lambda r: round(r.uniform(2.0, 28.0), 1)),
        ],
        "text": lambda name, p: (
            f"{name} is a marine fish growing to {p['length_cm']} cm. "
            f"Adults inhabit {p['depth_m']} m depths with {p['scales']} scale type, "
            f"preferring waters of {p['temperature']} degrees Celsius."
        ),
    },
    "eta": {
        "pattern": "Etacrop-{}",
        "props": [
            ("yield_t_ha",   lambda r: round(r.uniform(0.5, 12.0), 2)),
            ("water_mm",     lambda r: r.choice(range(200, 2000, 37))),
            ("cycle_days",   lambda r: r.choice(range(60, 360))),
            ("region",       lambda r: r.choice(["Mediterranean", "Subtropical", "Boreal", "Equatorial", "Alpine", "Steppe"])),
        ],
        "text": lambda name, p: (
            f"{name} is a domesticated cereal yielding {p['yield_t_ha']} tons per hectare. "
            f"It requires {p['water_mm']} mm annual rainfall and matures in {p['cycle_days']} days, "
            f"primarily cultivated in {p['region']} climates."
        ),
    },
}

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
         "XI", "XII", "XIII", "XIV", "XV", "XVI"]


def make_corpus(n_themes: int, per_theme: int = 6, seed: int = 20260512) -> tuple[Passage, ...]:
    """Generate a corpus with n_themes themes × per_theme passages each."""
    if n_themes > len(THEME_GENERATORS):
        raise ValueError(f"only {len(THEME_GENERATORS)} themes defined")
    if per_theme > len(ROMAN):
        raise ValueError(f"only {len(ROMAN)} per-theme slots defined")

    rng = random.Random(seed)
    chosen = list(THEME_GENERATORS.items())[:n_themes]
    passages: list[Passage] = []
    for theme_name, spec in chosen:
        for roman in ROMAN[:per_theme]:
            name = spec["pattern"].format(roman)
            props = {p_name: p_fn(rng) for p_name, p_fn in spec["props"]}
            text = spec["text"](name, props)
            pid = f"{theme_name[0]}-{roman}"
            passages.append(Passage(id=pid, theme=theme_name, text=text))
    return tuple(passages)
