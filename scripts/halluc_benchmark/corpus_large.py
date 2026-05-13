"""Large fictional corpus generator for the hallucination benchmark.

100 passages across 4 themes (25 each), each describing a uniquely-named
fictional entity with 4 properties. Entities share naming patterns within
a theme (e.g., luminoxide-I, luminoxide-II, ...) so the AI must disambiguate
specific instances — this is the cross-contamination test the small corpus
lacks.

Questions ask about specific (entity, property) pairs from random passages,
forcing the AI to locate the exact passage rather than approximate.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from scripts.halluc_benchmark.corpus import Passage, Question


# Deterministic seed for reproducibility.
_RNG = random.Random(20260512)


# Roman numerals for entity suffixes (cross-contamination by similar names).
ROMAN = [
    "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X",
    "XI", "XII", "XIII", "XIV", "XV", "XVI", "XVII", "XVIII", "XIX", "XX",
    "XXI", "XXII", "XXIII", "XXIV", "XXV",
]

# Each theme has its own naming pattern + property templates.
THEME_SPECS = {
    "zelgaria": {
        "entity_pattern": "King-{}-Zelgar",  # 25 fictional kings
        "props": [
            ("reign_start", lambda r: r.choice(range(1100, 1500))),
            ("reign_end", lambda r: r.choice(range(1100, 1500))),  # may be < start, fine for fictional
            ("capital", lambda r: r.choice(
                ["Velmoor", "Brennhold", "Korith", "Druvic-Hall", "Hollowcrest", "Iron-Reach",
                 "Thavn-Tower", "Falcon-Keep", "Mirelda-Hold", "Long-Winter-Vale"])),
            ("army_size", lambda r: r.choice(range(400, 2400, 100))),
        ],
        "prop_text": lambda name, props: (
            f"{name}, ruler of the Zelgar Dynasty, reigned from "
            f"{props['reign_start']} to {props['reign_end']}. The seat of "
            f"government during the reign was {props['capital']}, and the "
            f"royal army numbered {props['army_size']} mounted knights."
        ),
    },
    "phlogiston": {
        "entity_pattern": "luminoxide-{}",
        "props": [
            ("melt_celsius", lambda r: r.choice(range(200, 1200, 13))),
            ("wavelength_nm", lambda r: r.choice(range(380, 700, 7))),
            ("discovered_year", lambda r: r.choice(range(1600, 1900))),
            ("density", lambda r: round(r.uniform(1.2, 9.8), 2)),
        ],
        "prop_text": lambda name, props: (
            f"The phlogiston compound {name} melts at {props['melt_celsius']} "
            f"degrees Celsius and emits luminescence at {props['wavelength_nm']} "
            f"nanometers. It was first synthesized in {props['discovered_year']} "
            f"and has a density of {props['density']} g/cm^3."
        ),
    },
    "vimnar": {
        "entity_pattern": "Vimnarus-{}",
        "props": [
            ("weight_kg", lambda r: round(r.uniform(0.3, 50.0), 1)),
            ("habitat", lambda r: r.choice(
                ["Khorvac Highlands", "Druvic Wetlands", "Silvar Coast",
                 "Korith Forest", "Velmoor Plateau", "Long Winter Tundra",
                 "Brennhold Marsh", "Hollowcrest Steppe"])),
            ("offspring_per_clutch", lambda r: r.choice(range(1, 16))),
            ("nocturnal", lambda r: r.choice([True, False])),
        ],
        "prop_text": lambda name, props: (
            f"{name} is a {'nocturnal' if props['nocturnal'] else 'diurnal'} "
            f"vimnar species native to the {props['habitat']}. Adults weigh "
            f"{props['weight_kg']} kg and lay clusters of "
            f"{props['offspring_per_clutch']} eggs per breeding season."
        ),
    },
    "estron": {
        "entity_pattern": "Codex-{}-Estronus",
        "props": [
            ("composition_count", lambda r: r.choice(range(50, 2000, 17))),
            ("substyle_count", lambda r: r.choice(range(3, 100))),
            ("compiled_year", lambda r: r.choice(range(1300, 1700))),
            ("string_count", lambda r: r.choice(range(7, 37))),
        ],
        "prop_text": lambda name, props: (
            f"The {name} catalogues {props['composition_count']} traditional "
            f"compositions across {props['substyle_count']} sub-styles. It was "
            f"compiled around {props['compiled_year']} AD and prescribes a "
            f"dulvanthar with {props['string_count']} strings."
        ),
    },
}


def _generate_corpus():
    passages = []
    facts = {}  # (theme, entity, prop) -> value, for question generation
    for theme, spec in THEME_SPECS.items():
        for roman in ROMAN:
            entity = spec["entity_pattern"].format(roman)
            props = {p_name: p_fn(_RNG) for p_name, p_fn in spec["props"]}
            text = spec["prop_text"](entity, props)
            pid = f"{theme[0]}-{roman}"
            passages.append(Passage(id=pid, theme=theme, text=text))
            for p_name, p_val in props.items():
                facts[(theme, entity, p_name)] = (p_val, pid)
    return tuple(passages), facts


PASSAGES_LARGE, _FACTS = _generate_corpus()


def _question_for_fact(qid: str, theme: str, entity: str, prop: str) -> Question:
    val, source_pid = _FACTS[(theme, entity, prop)]
    spec = THEME_SPECS[theme]
    text_map = {
        "zelgaria": {
            "reign_start": f"In what year did {entity} begin his/her reign?",
            "reign_end":   f"In what year did the reign of {entity} end?",
            "capital":     f"What was the capital during the reign of {entity}?",
            "army_size":   f"How many mounted knights did {entity}'s army number?",
        },
        "phlogiston": {
            "melt_celsius":    f"At what temperature (degrees Celsius) does {entity} melt?",
            "wavelength_nm":   f"At what wavelength (nanometers) does {entity} emit luminescence?",
            "discovered_year": f"In what year was {entity} first synthesized?",
            "density":         f"What is the density (g/cm^3) of {entity}?",
        },
        "vimnar": {
            "weight_kg":             f"What is the adult weight (kg) of {entity}?",
            "habitat":               f"What is the native habitat of {entity}?",
            "offspring_per_clutch":  f"How many eggs does {entity} lay per breeding season?",
            "nocturnal":             f"Is {entity} nocturnal or diurnal?",
        },
        "estron": {
            "composition_count": f"How many compositions does {entity} catalogue?",
            "substyle_count":    f"Across how many sub-styles is {entity} organized?",
            "compiled_year":     f"Around what year was {entity} compiled?",
            "string_count":      f"How many strings does {entity} prescribe for the dulvanthar?",
        },
    }
    return Question(
        id=qid,
        text=text_map[theme][prop],
        answerable=True,
        source_passage_id=source_pid,
        ground_truth=str(val),
    )


def _build_questions() -> tuple[Question, ...]:
    """Construct 12 questions: 9 answerable + 3 unanswerable.

    Answerable questions are picked deterministically from random
    (theme, entity, prop) triples — one per entity-property combination
    to cover all 4 themes and varied properties.
    """
    # 9 answerable: ~2 per theme + 1 extra
    # Pick entities deterministically: middle-of-pack roman numerals reduce
    # the chance the AI guesses from name patterns.
    targets = [
        ("zelgaria",  "King-XII-Zelgar",      "reign_end"),
        ("zelgaria",  "King-VIII-Zelgar",     "army_size"),
        ("zelgaria",  "King-XX-Zelgar",       "capital"),
        ("phlogiston","luminoxide-XV",        "melt_celsius"),
        ("phlogiston","luminoxide-VII",       "density"),
        ("vimnar",    "Vimnarus-IX",          "weight_kg"),
        ("vimnar",    "Vimnarus-XXIII",       "habitat"),
        ("estron",    "Codex-IV-Estronus",    "composition_count"),
        ("estron",    "Codex-XVIII-Estronus", "string_count"),
    ]
    answerable = [
        _question_for_fact(f"q{i+1:02d}", theme, entity, prop)
        for i, (theme, entity, prop) in enumerate(targets)
    ]
    unanswerable = (
        Question(
            id="q10", answerable=False, source_passage_id=None,
            text="What is the favorite color of King-XII-Zelgar?",
            ground_truth="(not in corpus — color is never a Zelgar passage property)",
        ),
        Question(
            id="q11", answerable=False, source_passage_id=None,
            text="What is the boiling point of luminoxide-LV?",
            ground_truth="(not in corpus — luminoxide names only go up to XXV, and boiling point isn't a property)",
        ),
        Question(
            id="q12", answerable=False, source_passage_id=None,
            text="How many strings does Codex-XXVII-Estronus prescribe?",
            ground_truth="(not in corpus — Codex names only go up to XXV; this entity does not exist)",
        ),
    )
    return tuple(answerable) + unanswerable


QUESTIONS_LARGE: tuple[Question, ...] = _build_questions()


PASSAGE_BY_ID_LARGE: dict[str, Passage] = {p.id: p for p in PASSAGES_LARGE}
QUESTION_BY_ID_LARGE: dict[str, Question] = {q.id: q for q in QUESTIONS_LARGE}
