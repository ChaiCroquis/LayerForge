"""Fictional 4-theme corpus + 12-question ground-truth set.

Every entity, date, ratio, and proper noun is invented to eliminate
training-data leakage. Each passage contains specific verifiable facts;
each answerable question maps to exactly one source passage.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Passage:
    id: str
    theme: str
    text: str


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    answerable: bool
    source_passage_id: str | None  # None for unanswerable questions
    ground_truth: str  # canonical answer or "(not in corpus)"


# -----------------------------------------------------------------------------
# 24 passages — 4 themes × 6 passages each. All names/numbers fictional.
# -----------------------------------------------------------------------------

PASSAGES: tuple[Passage, ...] = (
    # ============== Theme A: Zelgaria (fictional medieval kingdom) =============
    Passage(
        id="a1", theme="zelgaria",
        text=(
            "The Zelgar Dynasty was founded by King Thanir in 1187 AD. "
            "Thanir was crowned in the city of Velmoor after defeating the "
            "Korash tribes at the Battle of Hollow Crag."
        ),
    ),
    Passage(
        id="a2", theme="zelgaria",
        text=(
            "Queen Mirelda, second monarch of the Zelgar Dynasty, ruled from "
            "1213 to 1241. She established the Royal Council of Twelve, which "
            "advised on matters of taxation and grain distribution."
        ),
    ),
    Passage(
        id="a3", theme="zelgaria",
        text=(
            "The Zelgar Dynasty's third capital, Brennhold, was constructed "
            "entirely from gray basalt quarried from the Druvic Mountains. "
            "Construction took 47 years and was completed in 1289."
        ),
    ),
    Passage(
        id="a4", theme="zelgaria",
        text=(
            "The Zelgar currency, the silver thavn, was minted in three "
            "denominations: 1, 5, and 25 thavn. The 25-thavn coin bore the "
            "dynasty's emblem, a falcon clutching three arrows."
        ),
    ),
    Passage(
        id="a5", theme="zelgaria",
        text=(
            "Zelgar military doctrine emphasized cavalry over infantry. The "
            "elite Iron Lances regiment consisted of 800 mounted knights, each "
            "equipped with a 14-foot lance forged in the city of Korith."
        ),
    ),
    Passage(
        id="a6", theme="zelgaria",
        text=(
            "The Zelgar Dynasty collapsed in 1374 after the Long Winter, a "
            "6-year period of crop failures that reduced the kingdom's "
            "population from 2.1 million to roughly 1.3 million."
        ),
    ),

    # ============= Theme B: Phlogiston chemistry (fictional alchemy) ===========
    Passage(
        id="b1", theme="phlogiston",
        text=(
            "Phlogiston, discovered by alchemist Bertrand Lascelles in 1672, "
            "is a colorless gas that emits blue luminescence at exactly 437 "
            "nanometers when heated above 312 degrees Celsius."
        ),
    ),
    Passage(
        id="b2", theme="phlogiston",
        text=(
            "The Trifold Calcination Method, developed by Madame Verennes in "
            "1731, produces phlogiston by combining sulfur, mercury salt, and "
            "a rare mineral called argillite at a 3:2:1 ratio."
        ),
    ),
    Passage(
        id="b3", theme="phlogiston",
        text=(
            "Phlogiston compounds bond preferentially with bismuth and "
            "tellurium. The most stable phlogiston-bismuth compound, known as "
            "luminoxide-VII, melts at 894 degrees Celsius."
        ),
    ),
    Passage(
        id="b4", theme="phlogiston",
        text=(
            "When phlogiston is exposed to ultraviolet light below 300 nm "
            "wavelength, it decomposes into two products: argentic vapor and a "
            "solid residue called caustic ash."
        ),
    ),
    Passage(
        id="b5", theme="phlogiston",
        text=(
            "Industrial phlogiston extraction reached commercial scale in 1849 "
            "with the construction of the Liege Phlogiston Works in Belgium, "
            "which produced 12 tons annually at peak operation."
        ),
    ),
    Passage(
        id="b6", theme="phlogiston",
        text=(
            "Phlogiston is highly reactive with the alloy known as "
            "Vandermeer's Bronze (78% copper, 18% tin, 4% lead), forming a "
            "green precipitate within 3 seconds of contact at room temperature."
        ),
    ),

    # ============== Theme C: Vimnar creatures (fictional biology) =============
    Passage(
        id="c1", theme="vimnar",
        text=(
            "The Crested Vimnar (Vimnarus cristatus) is a nocturnal mammal "
            "native to the Khorvac Highlands. It weighs 4-6 kg and possesses "
            "a bioluminescent crest along its spine that glows yellow-green "
            "during mating season."
        ),
    ),
    Passage(
        id="c2", theme="vimnar",
        text=(
            "Vimnar species share a unique respiratory adaptation: a tertiary "
            "lung lobe called the 'silvar', which extracts oxygen from soil "
            "moisture, allowing them to survive in dust storms lasting up to "
            "14 days."
        ),
    ),
    Passage(
        id="c3", theme="vimnar",
        text=(
            "The Pygmy Vimnar (Vimnarus minor), the smallest of the genus, "
            "measures only 12-15 cm in length and reproduces by laying "
            "gel-coated eggs in clusters of 8-13."
        ),
    ),
    Passage(
        id="c4", theme="vimnar",
        text=(
            "Vimnars communicate through a combination of subsonic vibrations "
            "(12-18 Hz range) and chemical pheromones secreted from glands "
            "behind the front legs. They have no vocal cords."
        ),
    ),
    Passage(
        id="c5", theme="vimnar",
        text=(
            "The Greater Banded Vimnar (Vimnarus fasciatus) is the only known "
            "carnivorous vimnar. It hunts in packs of 4-6 individuals and "
            "preys primarily on the Korith Marmot, which it consumes whole."
        ),
    ),
    Passage(
        id="c6", theme="vimnar",
        text=(
            "Vimnar fossils have been recovered from sites dating back 2.7 "
            "million years. The earliest specimens, classified as Vimnarus "
            "primordialis, were approximately 3 meters long—much larger than "
            "modern descendants."
        ),
    ),

    # ============= Theme D: Estron music (fictional music theory) =============
    Passage(
        id="d1", theme="estron",
        text=(
            "Estron music is built on a 14-tone scale, dividing the octave "
            "into intervals of 85.7 cents each. This contrasts with Western "
            "12-tone equal temperament's 100-cent semitones."
        ),
    ),
    Passage(
        id="d2", theme="estron",
        text=(
            "The Three Foundational Modes of Estron music are: Velar (bright, "
            "used for daytime ceremonies), Sundric (somber, funeral music), "
            "and Holvar (energetic, festival contexts). Each mode uses a "
            "different 7-note subset of the 14-tone scale."
        ),
    ),
    Passage(
        id="d3", theme="estron",
        text=(
            "The dulvanthar, the primary Estron stringed instrument, has 23 "
            "strings arranged in three courses: 9 melody strings, 11 drone "
            "strings, and 3 percussion strings struck with a hammer."
        ),
    ),
    Passage(
        id="d4", theme="estron",
        text=(
            "Estron compositions traditionally follow a five-phase structure: "
            "opening (rishon), development (varion), inversion (kelvar), "
            "resolution (turash), and silence (vor)—each phase corresponds to "
            "one element."
        ),
    ),
    Passage(
        id="d5", theme="estron",
        text=(
            "The Codex Estronus, compiled around 1500 AD by an unknown scribe, "
            "catalogues 1,247 traditional compositions across 89 distinct "
            "sub-styles."
        ),
    ),
    Passage(
        id="d6", theme="estron",
        text=(
            "Master Vilnar of Estron, born 1421, is credited with introducing "
            "the doubled-octave technique, in which the same melody is played "
            "simultaneously two octaves apart on the dulvanthar."
        ),
    ),
)


# -----------------------------------------------------------------------------
# 12 questions: 9 answerable (each maps to one source passage) + 3 unanswerable.
# -----------------------------------------------------------------------------

QUESTIONS: tuple[Question, ...] = (
    Question(
        id="q01", answerable=True, source_passage_id="a6",
        text="In what year did the Zelgar Dynasty collapse, and what caused it?",
        ground_truth="1374, due to the Long Winter (a 6-year period of crop failures).",
    ),
    Question(
        id="q02", answerable=True, source_passage_id="a4",
        text="How many denominations of the silver thavn existed, and what were they?",
        ground_truth="Three denominations: 1, 5, and 25 thavn.",
    ),
    Question(
        id="q03", answerable=True, source_passage_id="b1",
        text="At what wavelength does phlogiston luminesce, and above what temperature?",
        ground_truth="437 nanometers, above 312 degrees Celsius.",
    ),
    Question(
        id="q04", answerable=True, source_passage_id="b6",
        text="What is the composition of Vandermeer's Bronze?",
        ground_truth="78% copper, 18% tin, 4% lead.",
    ),
    Question(
        id="q05", answerable=True, source_passage_id="c4",
        text="How do vimnars communicate with each other?",
        ground_truth="Subsonic vibrations (12-18 Hz) and chemical pheromones secreted from glands behind the front legs.",
    ),
    Question(
        id="q06", answerable=True, source_passage_id="c5",
        text="Which vimnar species is carnivorous, and what does it primarily hunt?",
        ground_truth="The Greater Banded Vimnar (Vimnarus fasciatus); it hunts the Korith Marmot.",
    ),
    Question(
        id="q07", answerable=True, source_passage_id="d3",
        text="How many strings does the dulvanthar have, and how are they arranged?",
        ground_truth="23 strings: 9 melody, 11 drone, 3 percussion.",
    ),
    Question(
        id="q08", answerable=True, source_passage_id="d6",
        text="Who was Master Vilnar of Estron, and what technique is he credited with?",
        ground_truth="Born 1421; credited with the doubled-octave technique on the dulvanthar.",
    ),
    Question(
        id="q09", answerable=True, source_passage_id="a1",
        text="Who fought at the Battle of Hollow Crag, and what was the outcome?",
        ground_truth="King Thanir defeated the Korash tribes, after which he was crowned in Velmoor.",
    ),
    # ----- 3 unanswerable: facts NOT in any passage -----
    Question(
        id="q10", answerable=False, source_passage_id=None,
        text="What is the typical lifespan of a Crested Vimnar?",
        ground_truth="(not in corpus — vimnar passages mention weight and luminescence but not lifespan)",
    ),
    Question(
        id="q11", answerable=False, source_passage_id=None,
        text="What is the melting point of caustic ash?",
        ground_truth="(not in corpus — caustic ash is named as a phlogiston decomposition product but no melting point given)",
    ),
    Question(
        id="q12", answerable=False, source_passage_id=None,
        text="When was the Codex Zelgar written?",
        ground_truth="(not in corpus — the Codex Estronus exists in theme D, the Zelgar Dynasty in theme A, but no 'Codex Zelgar')",
    ),
)


# Lookup helpers ---------------------------------------------------------------

PASSAGE_BY_ID: dict[str, Passage] = {p.id: p for p in PASSAGES}
PASSAGES_BY_THEME: dict[str, tuple[Passage, ...]] = {
    theme: tuple(p for p in PASSAGES if p.theme == theme)
    for theme in {p.theme for p in PASSAGES}
}
QUESTION_BY_ID: dict[str, Question] = {q.id: q for q in QUESTIONS}


def all_passage_texts() -> list[str]:
    return [p.text for p in PASSAGES]


def all_passage_ids() -> list[str]:
    return [p.id for p in PASSAGES]
