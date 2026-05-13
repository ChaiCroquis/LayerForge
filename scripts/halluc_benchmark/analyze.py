"""Aggregate verdicts from the 3 conditions and produce metrics."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.halluc_benchmark.corpus import QUESTIONS, QUESTION_BY_ID


VERDICT_TYPES = ("CORRECT", "REFUSED_SAFE", "INCORRECT", "HALLUCINATED")


def _load(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_verdict(v: str) -> str:
    """Be lenient about case / whitespace in verdict strings."""
    return v.strip().upper().replace(" ", "_")


def main() -> int:
    out_dir = Path(__file__).resolve().parent / "out"
    conditions = ("full", "layerforge", "oracle")

    print("# Hallucination benchmark — final results\n")
    print("Corpus: 24 fictional passages across 4 themes (zelgaria/phlogiston/vimnar/estron)")
    print("Questions: 12 (9 answerable, 3 unanswerable)")
    print("Verdict source: independent LLM judge subagent (one per condition)\n")

    rows = []
    answerable_ids = {q.id for q in QUESTIONS if q.answerable}
    unanswerable_ids = {q.id for q in QUESTIONS if not q.answerable}

    per_condition: dict[str, list[dict]] = {}
    for cond in conditions:
        verdicts = _load(out_dir / f"verdicts_{cond}.json")
        per_condition[cond] = verdicts

        counts = Counter(_normalize_verdict(v["verdict"]) for v in verdicts)
        # Split by answerable / unanswerable for a sharper view.
        counts_answerable = Counter(
            _normalize_verdict(v["verdict"]) for v in verdicts if v["q"] in answerable_ids
        )
        counts_unanswerable = Counter(
            _normalize_verdict(v["verdict"]) for v in verdicts if v["q"] in unanswerable_ids
        )

        n = len(verdicts)
        correct = counts.get("CORRECT", 0)
        refused = counts.get("REFUSED_SAFE", 0)
        incorrect = counts.get("INCORRECT", 0)
        hallucinated = counts.get("HALLUCINATED", 0)

        rows.append({
            "condition": cond,
            "n": n,
            "correct": correct,
            "refused_safe": refused,
            "incorrect": incorrect,
            "hallucinated": hallucinated,
            "accuracy_pct": round(100 * (correct + refused) / n, 1),
            "hallucination_pct": round(100 * hallucinated / n, 1),
            "answerable_correct": counts_answerable.get("CORRECT", 0),
            "answerable_n": len(answerable_ids),
            "unanswerable_refused": counts_unanswerable.get("REFUSED_SAFE", 0),
            "unanswerable_n": len(unanswerable_ids),
        })

    # --- Summary table ---
    print("| condition  | n  | correct | refused | incorrect | halluc | safe-acc | halluc-rate |")
    print("|------------|---:|--------:|--------:|----------:|-------:|---------:|------------:|")
    for r in rows:
        print(
            f"| {r['condition']:<10} | {r['n']:>2} | "
            f"{r['correct']:>7} | {r['refused_safe']:>7} | "
            f"{r['incorrect']:>9} | {r['hallucinated']:>6} | "
            f"{r['accuracy_pct']:>7}% | {r['hallucination_pct']:>10}% |"
        )

    print("\n## Breakdown: answerable vs unanswerable\n")
    print("| condition  | answerable CORRECT | unanswerable REFUSED_SAFE |")
    print("|------------|-------------------:|--------------------------:|")
    for r in rows:
        print(
            f"| {r['condition']:<10} | "
            f"{r['answerable_correct']}/{r['answerable_n']} | "
            f"{r['unanswerable_refused']}/{r['unanswerable_n']} |"
        )

    # --- Per-question disagreement detection ---
    print("\n## Per-question verdict comparison (condition shown only on disagreement)\n")
    by_q: dict[str, dict[str, str]] = {}
    for cond, verdicts in per_condition.items():
        for v in verdicts:
            by_q.setdefault(v["q"], {})[cond] = _normalize_verdict(v["verdict"])

    any_disagreement = False
    for qid in (q.id for q in QUESTIONS):
        verdicts_for_q = by_q.get(qid, {})
        unique = set(verdicts_for_q.values())
        if len(unique) > 1:
            any_disagreement = True
            q = QUESTION_BY_ID[qid]
            kind = "answerable" if q.answerable else "UNANSWERABLE"
            print(f"  {qid} ({kind}): {dict(verdicts_for_q)}")
    if not any_disagreement:
        print("  (all 12 questions received identical verdicts across all 3 conditions)")

    # --- Hypothesis test ---
    print("\n## Hypothesis verdict\n")
    full_h = next(r["hallucinated"] for r in rows if r["condition"] == "full")
    lf_h = next(r["hallucinated"] for r in rows if r["condition"] == "layerforge")
    oracle_h = next(r["hallucinated"] for r in rows if r["condition"] == "oracle")
    delta = full_h - lf_h
    print(f"H1: LayerForge filter reduces hallucination vs full corpus baseline.")
    print(f"   full hallucinations:       {full_h}")
    print(f"   layerforge hallucinations: {lf_h}")
    print(f"   oracle hallucinations:     {oracle_h}")
    print(f"   Δ (full - layerforge) = {delta}")
    if delta > 0:
        print(f"   → H1 SUPPORTED (LayerForge reduced hallucinations by {delta})")
    elif delta == 0 and full_h == 0:
        print(f"   → H1 NULL RESULT — baseline already has zero hallucinations; "
              f"this corpus/model combination is too easy to discriminate filtering benefit.")
    elif delta == 0:
        print(f"   → H1 NULL RESULT — same hallucination rate ({full_h}) in both conditions.")
    else:
        print(f"   → H1 REJECTED — LayerForge actually INCREASED hallucinations by {-delta}.")

    # --- Persist combined result ---
    (out_dir / "results_summary.json").write_text(
        json.dumps({"per_condition": rows, "per_q": by_q}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nWrote {out_dir / 'results_summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
