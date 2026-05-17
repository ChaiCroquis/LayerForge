// LayerForge v9 Main Paper — slim body + English figures + appendix reference
// chai 指示「論文は英語で公開、v9 として 1 フォルダに関連 file まとめて」

const path = require('path');
const fs = require('fs');
const docxPath = path.join(process.env.APPDATA, 'npm', 'node_modules', 'docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat, ImageRun,
        HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak } = require(docxPath);

const border = { style: BorderStyle.SINGLE, size: 1, color: "888888" };
const borders = { top: border, bottom: border, left: border, right: border };

function H1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, bold: true, size: 32 })], spacing: { before: 360, after: 240 }}); }
function H2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, bold: true, size: 26 })], spacing: { before: 240, after: 180 }}); }
function Body(text) { return new Paragraph({ children: [new TextRun({ text, size: 22 })],
  spacing: { after: 120 }, alignment: AlignmentType.JUSTIFIED }); }
function Bullet(text) { return new Paragraph({ numbering: { reference: "bullets", level: 0 },
  children: [new TextRun({ text, size: 22 })], spacing: { after: 60 }}); }
function Caption(text) { return new Paragraph({ alignment: AlignmentType.CENTER,
  spacing: { before: 60, after: 240 },
  children: [new TextRun({ text, italics: true, size: 18, color: "555555" })] }); }

function makeTable(headers, rows, colWidths) {
  const headerRow = new TableRow({ tableHeader: true,
    children: headers.map((h, i) => new TableCell({ borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: h, bold: true, size: 20 })] })] })) });
  const dataRows = rows.map(r => new TableRow({
    children: r.map((c, i) => new TableCell({ borders,
      width: { size: colWidths[i], type: WidthType.DXA },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: String(c), size: 18 })] })] })) }));
  return new Table({ width: { size: colWidths.reduce((a,b)=>a+b), type: WidthType.DXA },
    columnWidths: colWidths, rows: [headerRow, ...dataRows] });
}

function embedImage(filePath, w, h, captionText) {
  const data = fs.readFileSync(filePath);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 60 },
      children: [new ImageRun({ type: "png", data, transformation: { width: w, height: h },
        altText: { title: captionText, description: captionText, name: path.basename(filePath) } })] }),
    Caption(captionText),
  ];
}

const FIG_DIR = path.join(__dirname, 'figures');
const children = [];

children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "LayerForge v9: Phase 2b Verification Update", bold: true, size: 40 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({ text: "Two-Layer Fidelity Structure and Hybrid Ensemble Path",
    italics: true, size: 26 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 },
  children: [new TextRun({ text: "chai  ·  2026-05-17", size: 22 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({
    text: "(Main paper. Dataset catalog, per-record verdicts, and parameter ablation details are in the companion document: layerforge_v9_appendix.pdf)",
    italics: true, size: 18, color: "555555" })] }));

children.push(H2("Abstract"));
children.push(Body(
  "LayerForge is a deterministic text-decomposition tool that extracts 4 plus or minus 1 hierarchical themes via " +
  "CPM community detection on sentence-transformer embeddings. The v8.1 published version positioned " +
  "it as a topic-extraction subtask within an IE pipeline (ADR-026). This v9 update reports Phase 2b: " +
  "46 verifications and 14 parameter ablations across 14 datasets (EN/JA, multi-turn dialogue, " +
  "multi-hop QA, news, long-form). We articulate (1) a two-layer fidelity structure: theme-level " +
  "semantic preservation passes across multiple metric families on two datasets (hotpotqa EN / " +
  "livedoor JA), and fact-level lexical preservation fails across multiple metric families on the " +
  "same two datasets, (2) a statistically significant Hybrid ensemble path (LayerForge plus K-means; " +
  "ensemble vs LayerForge alone: hotpotqa N=100 p=2.7e-05, livedoor N=27 p=5.1e-08; see Table 1 for " +
  "vs K-means comparisons), (3) baseline parameter values frozen under bounded ablation budget — no " +
  "parameter change reached the IMPROVEMENT-LARGE threshold (>0.30 delta) across 14 ablations under " +
  "tested N (5-30); this is a freeze decision, not an optimality claim (see Section 4.5), and " +
  "(4) explicit extrapolation boundaries per pattern coverage. The fact-level structural limitation " +
  "is articulated as a constitutive design property (ADR-026), with hybrid pipeline as the operational remedy."
));

children.push(H1("1. Introduction"));
children.push(Body(
  "LayerForge v8.1 produces 4 plus or minus 1 hierarchical themes from arbitrary input text via four components: " +
  "(i) sentence-transformer embeddings (paraphrase-multilingual-mpnet-base-v2), (ii) CPM-Louvain " +
  "community detection (Traag 2011, Blondel 2008), (iii) scale_finder with K=4 plus or minus 1 cognitive constraint " +
  "(Miller 1956, Cowan 2001), (iv) ctfidf-based representation extraction (Grootendorst 2022). " +
  "The intended position is a topic-extraction subtask within an IE pipeline (ADR-026), complemented " +
  "by NER, regex, and RAG for fact-level information."
));
children.push(Body(
  "This v9 update articulates what LayerForge can and cannot do, where structural limitations lie, " +
  "and which improvement paths are evidence-grounded. Detailed dataset catalog and per-record results " +
  "are in the companion appendix."
));
children.push(Body("What is new in v9 (relative to v8.1):"));
children.push(Bullet("Direct fact-level fidelity measurement (V-021 substring, V-022 ROUGE-L, V-023 attribute breakdown, V-024/024-bis downstream LLM accuracy) — v8.1 reported only theme-level evidence."));
children.push(Bullet("Two-layer fidelity formalization (Section 2) and the Pareto plot set (V-040) consolidating 38 evidence points into 5 visualizations."));
children.push(Bullet("Hybrid ensemble path (LayerForge + K-means) with cross-corpus statistical significance (V-042-tri N=100 hotpotqa, V-042-quad N=27 livedoor), establishing an evidence-grounded improvement direction without modifying v8.1 core."));
children.push(Bullet("Explicit extrapolation boundaries per pattern coverage, and a decoupled 'freeze under bounded ablation budget' framing for the 14-ablation result (Section 4.5)."));

children.push(H1("2. Theoretical Framework: Two-Layer Fidelity"));
children.push(Body(
  "We articulate fidelity as a two-layer structure rather than a single aggregate metric. Each layer " +
  "carries internally consistent but oppositely-signed evidence:"
));
children.push(Bullet(
  "Theme-level semantic: response cosine, BERTScore F1, topic coherence (UMass/NPMI). " +
  "Measures whether the compressed output preserves what-the-text-is-about."
));
children.push(Bullet(
  "Fact-level lexical: answer substring, ROUGE-L, attribute breakdown, downstream LLM accuracy. " +
  "Measures whether specific named entities, numbers, and quotations survive compression."
));
children.push(Body(
  "These layers are independent dimensions. LayerForge is structurally PASS at theme-level and " +
  "structurally FAIL at fact-level. The theme-level PASS is corroborated by multiple metric families " +
  "(response cosine, BERTScore F1, topic coherence UMass/NPMI) on two datasets (hotpotqa EN, livedoor JA). " +
  "The fact-level FAIL is corroborated by four metric families (answer substring, ROUGE-L, attribute " +
  "breakdown, downstream LLM accuracy) on the same two datasets. The fact-level FAIL is constitutive " +
  "(ADR-026 design), not a defect; the remedy is hybrid pipeline (LayerForge plus NER/regex/RAG), not " +
  "LayerForge internal modification. Figure 1 visualizes this positioning."
));
children.push(Body(
  "Disclaimer (metric multiplicity vs corpus multiplicity). The above evidence is metric-multiple but " +
  "corpus-dual. Distinct metric families applied to the same corpus are statistically correlated and do " +
  "not constitute independent observations in the sense of independent draws from disjoint populations. " +
  "Per-dataset hotpotqa records dominate the fact-level evidence count (see Appendix B); livedoor provides " +
  "the only out-of-corpus replication for both theme-level and fact-level. We therefore refrain from any " +
  "ordinal 'n-tuple evidence' labeling and emphasize that broader corpus coverage (V-102 cross-domain " +
  "extension, see Section 7) is required before generalization beyond the two-corpus span."
));
children.push(Body(
  "Constitutive vs boundary-layer interventions. The fact-level FAIL is constitutive at the LayerForge " +
  "core: it is a property of what LayerForge produces (theme-level representations via CPM-Louvain on " +
  "sentence embeddings, ctfidf representation). It is not removed by any modification at the consumer " +
  "boundary. The future-work items I-101 (probe API) and I-103 (output interpretation layer) are " +
  "explicitly boundary-layer interventions: they help downstream consumers detect when a query requires " +
  "fact-level routing (i.e., NER / regex / RAG rather than trusting LayerForge output as-is), but they " +
  "do not change the internal constitutive property. The operational implication ('fact-level use cases " +
  "require the hybrid pipeline') therefore remains unchanged by I-101 / I-103."
));

embedImage(path.join(FIG_DIR, 'v040_plot3_theme_vs_fact_en.png'), 480, 336,
  "Figure 1. Two-layer fidelity structure (V-040 Plot 3). LayerForge variants cluster in the lower-right quadrant: theme-level high (cosine/BERTScore >= 0.8) but fact-level low (substring <= 0.1). The ideal upper-right quadrant is unreachable by LayerForge alone; hybrid pipeline is the operational path."
).forEach(p => children.push(p));

children.push(H1("3. Method"));
children.push(Body(
  "All verifications follow ADR-022 Section 3: pre-register Sections 1-5 (claim, dataset, method, pre-commit " +
  "interpretations) with immutability, then execute and append Sections 6-8 (run record, outcome, impact). " +
  "This prevents post-hoc threshold drift. Datasets, sampling protocols, and per-record verdicts are " +
  "in Appendix A and B."
));
children.push(Body(
  "Self-preference bias disclosure: LLM-as-judge evaluations used Claude Code subagent (Sonnet/Opus) " +
  "as evaluator on Claude-compressed context. This bias affects only the LLM-judged subset of " +
  "verifications and not the metric-only subset; the differentiated scope (which verifications are " +
  "bias-affected vs bias-independent) and the cross-confirmation status are articulated in " +
  "Section 6 Limitations."
));

children.push(H1("4. Key Results"));

children.push(H2("4.1 Reduction Landscape (14 Datasets)"));
children.push(Body(
  "Reduction across 14 datasets confirms language-independent ceiling (Aozora 99.3% JA + MeCab) " +
  "and JA-default tokenizer structural mismatch (BSD floor -5%, livedoor 2.5%). See Appendix A " +
  "for dataset catalog. Figure 2 visualizes the reduction landscape colored by language and " +
  "tokenization."
));
embedImage(path.join(FIG_DIR, 'v040_plot4_reduction_landscape_en.png'), 540, 315,
  "Figure 2. Reduction landscape across 14 datasets (V-040 Plot 4). Language-independent ceiling (99% at Aozora JA+MeCab) and JA-default tokenizer floor (-5% at BSD). EN: 77-99%, JA+MeCab: 57-99%, JA-default: structural mismatch."
).forEach(p => children.push(p));

children.push(H2("4.2 Theme-level Fidelity (Pareto Frontier)"));
children.push(Body(
  "On the reduction-by-theme-fidelity plane, F4 hybrid format (V-007/V-025) occupies the Pareto " +
  "frontier with reduction around 0.85 and BERTScore F1 >= 0.83 (Figure 3). The trade-off between " +
  "reduction and theme-level fidelity is summarized by the visual heuristic fidelity ≈ 0.94 × " +
  "(1 − reduction × 0.15), obtained as a two-point interpolation between the V-007 and V-025 Pareto " +
  "endpoints (V-040 Pareto analysis). This is a heuristic approximation for reader orientation, not a " +
  "regression fit; no R² or confidence interval is reported, and the expression should not be used for " +
  "extrapolation outside the measured reduction range (approximately 0.77-0.99). Detailed verdicts and N " +
  "for each point are in Appendix B."
));
embedImage(path.join(FIG_DIR, 'v040_plot1_reduction_vs_theme_fidelity_en.png'), 540, 378,
  "Figure 3. Reduction vs theme-level fidelity Pareto frontier (V-040 Plot 1). F4 hybrid format (V-007/V-025) is current Pareto-optimal at reduction around 0.85, BERTScore F1 0.83-0.94. ADR-022 Claim 2 threshold (0.80) marked in red."
).forEach(p => children.push(p));

children.push(H2("4.3 Hybrid Ensemble Path (Statistical Significance)"));
children.push(Body(
  "V-036 observed K-means baseline tok_recall 2x superior to LayerForge alone on hotpotqa N=5. " +
  "We pursued Path 2 (LayerForge plus K-means ensemble) as the v8.1-integrity-preserving improvement " +
  "direction. N progression confirms statistical significance and cross-corpus consistency:"
));
const tblEns = makeTable(
  ["V-ID", "Dataset", "N", "Ens vs LF (p)", "Ens vs K-means (p)", "comp_mean LF", "comp_mean Ens"],
  [
    ["V-042", "hotpotqa", "5", "+0.067 (n.s.)", "+0.000 (n.s.)", "174.6", "264.0"],
    ["V-042-bis", "hotpotqa", "30", "+0.098", "+0.042", "188.5", "272.6"],
    ["V-042-tri", "hotpotqa", "100", "+0.113 (2.7e-05)", "+0.033 (2.4e-03)", "n/a*", "n/a*"],
    ["V-042-quad", "livedoor (JA)", "27", "+0.140 (5.1e-08)", "+0.260 (1.3e-10)", "n/a*", "n/a*"],
  ],
  [1100, 1700, 650, 1850, 2100, 1000, 1000]
);
children.push(tblEns);
children.push(Caption(
  "Table 1. Hybrid ensemble N progression and cross-corpus statistical significance, with " +
  "decomposition output cost (comp_mean, characters per query). Both datasets confirm ensemble > " +
  "both baselines (paired t-test); ensemble incurs a consistent positive comp_mean overhead vs " +
  "LayerForge alone on the rows where it was measured. (*) V-042-tri / V-042-quad did not dump " +
  "summary.*.comp_mean in the raw JSON (the tri/quad evaluators recorded only tok_recall fields); " +
  "the +44.6% overhead pattern measured at N=30 (V-042-bis) is taken as the representative " +
  "estimate. Raw values from v042*_results.json."
));
children.push(Body(
  "Computational overhead (cost-adjusted view). Table 1 reports both significance (p-values) and " +
  "decomposition output cost (comp_mean, characters per query) for the rows where the latter is " +
  "available. Ensemble incurs a consistent positive comp_mean overhead on both measured rows " +
  "(V-042 hotpotqa N=5: 264.0 vs 174.6, +51.2%; V-042-bis hotpotqa N=30: 272.6 vs 188.5, +44.6%), " +
  "before accounting for the additional K-means clustering step. The paired-t improvements must " +
  "therefore be read against this overhead. The ensemble path is a per-deployment trade-off " +
  "decision (recall gain vs output / latency cost), not a universal recommendation; formal " +
  "downstream-LLM-token cost measurement, and back-filling comp_mean for V-042-tri / V-042-quad, " +
  "are filed as E-101 in the future-work roadmap."
));

children.push(H2("4.4 Cost vs Accuracy Sweet Spot"));
children.push(Body(
  "Figure 4 plots per-query input-token cost (log scale) versus downstream LLM accuracy on V-029-a (N=5 " +
  "hotpotqa pilot). Full context averages 4.4k tokens/query at 60% accuracy (3/5; exact-binomial 95% CI " +
  "[14.7%, 94.7%]); F4-hybrid alone averages 0.7k tokens/query at 0% accuracy (0/5; 95% CI [0%, 52.2%]). " +
  "The two CIs overlap substantially, so this figure is reported as a pilot-scale indication rather than " +
  "a significance claim. The hypothesized operational region (F4-hybrid + RAG retrieval at approximately " +
  "1-10k tokens/query and 30-70% accuracy) is drawn as a shaded uncertainty band; per-query verification " +
  "of this region requires V-030 (Pending). Raw per-sample token counts are in v029a_cost_latency_results.json."
));
embedImage(path.join(FIG_DIR, 'v040_plot5_cost_vs_accuracy_en.png'), 540, 378,
  "Figure 4. Per-query input-token cost (log scale) vs downstream LLM accuracy, V-029-a hotpotqa N=5 pilot (V-040 Plot 5). Full baseline averages 4.4k tokens/query, accuracy 3/5 (60%, 95% CI [14.7%, 94.7%]). F4-hybrid alone averages 0.7k tokens/query, accuracy 0/5 (0%, 95% CI [0%, 52.2%]); CIs overlap. Shaded band: hypothesized F4-hybrid + RAG operational region, unverified, awaits V-030. N=5 pilot — axis values are indicative, not significance claims."
).forEach(p => children.push(p));

children.push(H2("4.5 Parameter Ablation Summary"));
children.push(Body(
  "14 ablations did not find any parameter change yielding >0.30 delta improvement under the tested N " +
  "(5-30). This is an empirical statement about the ablation search budget, not a claim of global " +
  "optimality: three parameters remain pending-refinement candidates (SNIPPET_CHARS PARTIAL-IMPROVEMENT " +
  "240/480, CPM gamma dataset-dependent best, ASCII tokenizer pattern core-spec future), and at least " +
  "one ablation exhibited N-sensitive direction reversal (V-032-bis: mpnet > MiniLM-L6 at N=30 reverses " +
  "the N=5 direction). Baseline snapshot v1 is therefore preserved unchanged as a freeze decision under " +
  "bounded ablation budget, not as an optimality assertion. Small-N ablation results should be read as " +
  "direction-only. Notable individual findings: V-027 (digit preservation NEGATIVE leads to core-spec " +
  "modification trigger), V-032-bis (the N=5→N=30 reversal motivating careful-strategy Rule 3). Full " +
  "ablation table is in Appendix C."
));

children.push(H1("5. Discussion"));

children.push(H2("5.1 Cross-corpus Direction Reversal"));
children.push(Body(
  "V-042-tri (hotpotqa) shows K-means superior to LayerForge alone (+0.080). V-042-quad (livedoor) " +
  "shows LayerForge superior to K-means (+0.121, direction reversed). Both datasets confirm ensemble " +
  "superior to both baselines. As an empirical finding we report the reversal as dataset-dependent " +
  "baseline behavior; we did not pre-register a hypothesis predicting this direction. A post-hoc " +
  "interpretation — 'K-means frequency tokens may favor multi-hop QA, LayerForge theme tokens may favor " +
  "JA news' — is offered only as a candidate explanation pending V-103 (direction-reversal root cause, " +
  "see Appendix E) and should not be read as a confirmed cause. The ensemble's headline property — " +
  "absorbing both regimes regardless of which baseline dominates — does not depend on resolving the " +
  "cause attribution."
));

children.push(H2("5.2 Why the Two-Layer Structure Matters"));
children.push(Body(
  "Single aggregate fidelity metrics (e.g., reduction-only or cosine-only) systematically " +
  "under-represent or over-claim LayerForge's behavior. A reduction-99% verdict appears strong but " +
  "hides fact-level FAIL; a cosine-0.94 verdict appears strong but applies only at theme-level. " +
  "The two-layer structure makes both true claims simultaneously articulable and prevents " +
  "consumer-side misuse (e.g., expecting fact-extraction from LayerForge output)."
));

children.push(H2("5.3 Driver-level vs Core-spec Modifications"));
children.push(Body(
  "Driver-level parameter sweeps (TOP_MEMBERS, SNIPPET_CHARS, tokenizer matching) preserve v8.1 " +
  "integrity. Core-spec modifications (ctfidf to tf hybrid, embedding swap, K=4 plus or minus 1 relaxation, " +
  "scale_finder change) require v8.1 integrity reconsideration and paper update synchronization. " +
  "We do not undertake core-spec modifications in this update; they are documented in the " +
  "companion future-work plan for sovereign trigger."
));

children.push(H1("6. Limitations"));
children.push(Bullet("Sample sizes N=5-100; formal population-scale not achieved."));
children.push(Bullet("Self-preference bias (scope-specific): downstream-LLM-judged verifications V-024 (F3 refusal), V-024-bis (F4-hybrid accuracy), and V-025 (BERTScore via Claude-rendered evaluation) route through a Claude subagent acting as judge on Claude-compressed context and are therefore subject to LLM-as-judge self-preference bias (Anthropic acknowledged limitation). The V-042 family (paired t-test on tok_recall, including V-042-tri hotpotqa p=2.7e-05 and V-042-quad livedoor p=5.1e-08) computes its primary metric without an LLM judge and is therefore structurally independent of this bias. Formal Anthropic API plus Haiku 4.5 cross-confirmation remains pending for the LLM-judged subset."));
children.push(Bullet("Coverage bias: EN long-form is dominated by hotpotqa (16/16 pure-hotpotqa-dataset rows in Appendix B Table B2; an additional 2 parameter-sweep rows V-024-tri/V-024-quad operate on hotpotqa data, and 2 mixed-corpus rows V-020/V-026 include hotpotqa alongside ShareGPT). JA mid-form is dominated by livedoor (V-022, V-029-b, V-029-d, V-042-quad, plus V-027/V-037/V-033 cross-corpus replication). Generalization beyond this two-corpus span requires V-102 (see Section 7) and is bounded by the metric-vs-corpus multiplicity caveat in the Section 2 disclaimer."));
children.push(Bullet("Fact-level FAIL is constitutive (ADR-026 design), remediated by hybrid pipeline (bucket B), not by LayerForge modification."));
children.push(Bullet("Path 1 (core-spec ctfidf to tf hybrid) is unevaluated; requires v8.1 integrity reconsideration."));
children.push(Bullet("Ensemble cost overhead unquantified at the downstream-LLM-token level: V-042-bis shows +44.6% decomposition output volume for the ensemble vs LayerForge alone, but per-deployment cost / latency impact on the consuming LLM is unmeasured (E-101 pending)."));
children.push(Bullet("K=4±1 cognitive constraint robustness is only partially verified outside the constraint range. The only experiments probing ground-truth K outside K=4±1 are V-008 (polbooks, ground-truth K=3, LayerForge K=6 over-segmentation, ARI 0.6140 AMBIGUOUS) and V-009 (football, ground-truth K=12, K-FAIL with ARI 0.8549). These are graph-community benchmarks rather than text decomposition, and they indicate that the K=4±1 constraint produces partial agreement with out-of-range ground truth but is not validated for arbitrary K. Text decomposition with substantially different intrinsic K remains an extrapolation boundary."));

children.push(H1("7. Future Work"));
children.push(Body(
  "We articulate 15 future work items across 4 axes. Following the Section 2 constitutive vs " +
  "boundary-layer distinction: I-101 (probe API) and I-103 (output interpretation layer) are " +
  "boundary-layer interventions that do not modify the LayerForge core; V-101-104, G-101/G-103, and " +
  "E-101/E-102 are observational / packaging items. None of these touch the v8.1 core spec. I-102 " +
  "(routing logic) and I-104 (probe driver isolation), G-102/G-104 (framework / cross-tool " +
  "integration), and E-103 (real deployment) are sovereign-trigger items because they either span " +
  "v8.1 integrity or scope-expand beyond the personal-OS setting. AI-decidable items can proceed " +
  "without architectural triggers; sovereign-trigger items await architectural and scope decisions. " +
  "Full roadmap is in the companion appendix."
));

children.push(H1("8. Conclusion"));
children.push(Body(
  "LayerForge v9 confirms a two-layer fidelity structure: theme-level semantic preservation is " +
  "structurally PASS across multiple metric families on two datasets, and fact-level lexical " +
  "preservation is structurally FAIL across multiple metric families on the same two datasets " +
  "(hotpotqa EN, livedoor JA; see Section 2 disclaimer for the metric-vs-corpus multiplicity " +
  "caveat). The Hybrid ensemble path is statistically significantly superior to both baselines on " +
  "two datasets (hotpotqa p<2.7e-05, livedoor p<5.1e-08), confirming ADR-026 IE pipeline subtask " +
  "position as the operational remedy. All 14 parameter ablations under tested N (5-30) produced " +
  "no parameter change above the IMPROVEMENT-LARGE threshold; baseline snapshot v1 is frozen under " +
  "bounded ablation budget (not an optimality claim). Dataset catalog, per-record verdicts, " +
  "parameter ablation details, and the full Pareto plot set are in the companion appendix " +
  "(layerforge_v9_appendix.pdf)."
));

children.push(H1("References"));
const repoNote = "Repository access note for [11]-[16]: References [11] (verification index subset) and [12] (raw JSON results) are publicly resolvable at the LayerForge core repository (https://github.com/ChaiCroquis/LayerForge). References [13]-[16] (full per-record verification narratives, parameter_baseline / capability_matrix / future_plan / decision_log) reside in a separate author-maintained repository (https://github.com/ChaiCroquis/LayerForge-dev) which is currently private during pre-publication review; peer reviewers may request read access from the corresponding author. A persistent archival deposit (Zenodo DOI) of the cited commits will be created for the camera-ready submission and will supersede the GitHub URLs below.";
const refs = [
  "Blei, D. M., Ng, A. Y., Jordan, M. I. (2003). Latent Dirichlet Allocation. JMLR.",
  "Blondel, V. D., et al. (2008). Fast unfolding of communities in large networks. J. Stat. Mech.",
  "Cowan, N. (2001). The magical number 4 in short-term memory. Behavioral and Brain Sciences.",
  "Grootendorst, M. (2022). BERTopic: Neural topic modeling with class-based TF-IDF.",
  "Lin, C.-Y. (2004). ROUGE: A Package for Automatic Evaluation of Summaries.",
  "Miller, G. A. (1956). The magical number seven, plus or minus two. Psychological Review.",
  "Reichardt, J., Bornholdt, S. (2006). Statistical mechanics of community detection. Phys. Rev. E.",
  "Reimers, N., Gurevych, I. (2019). Sentence-BERT. EMNLP-IJCNLP.",
  "Traag, V. A., Van Dooren, P., Nesterov, Y. (2011). Narrow scope for resolution-limit-free community detection. Phys. Rev. E.",
  "Zhang, T., et al. (2020). BERTScore: Evaluating Text Generation with BERT. ICLR.",
  "LayerForge v9 Supplementary (2026). docs/verifications_index_v9.md (public subset). Resolvable at https://github.com/ChaiCroquis/LayerForge/blob/main/docs/verifications_index_v9.md",
  "LayerForge v9 Supplementary (2026). verification_results/v9/ — raw JSON output (22 files) for V-021 through V-042-quad, sufficient for independent re-verification of all numeric claims (p-values, comp_mean, accuracy, etc.). Resolvable at https://github.com/ChaiCroquis/LayerForge/tree/main/verification_results/v9",
  "LayerForge v9 Supplementary (2026). docs/parameter_baseline.md v8, commit 8d792fe. https://github.com/ChaiCroquis/LayerForge-dev/blob/8d792fe/docs/parameter_baseline.md (private repository, see access note above)",
  "LayerForge v9 Supplementary (2026). docs/capability_matrix.md, commit bce1e81. https://github.com/ChaiCroquis/LayerForge-dev/blob/bce1e81/docs/capability_matrix.md (private repository, see access note above)",
  "LayerForge v9 Supplementary (2026). docs/future_plan.md, commit c462618. https://github.com/ChaiCroquis/LayerForge-dev/blob/c462618/docs/future_plan.md (private repository, see access note above)",
  "LayerForge v9 Supplementary (2026). docs/06_decision_log.md, ADR-013 through ADR-026. Repository root: https://github.com/ChaiCroquis/LayerForge-dev (private repository; DOI deposit pending).",
];
refs.forEach((r, i) => {
  children.push(new Paragraph({
    children: [new TextRun({ text: `[${i+1}] ${r}`, size: 20 })],
    spacing: { after: 80 }, indent: { left: 360, hanging: 360 }}));
  // Insert repository access note between [10] and [11].
  if (i + 1 === 10) {
    children.push(new Paragraph({
      children: [new TextRun({ text: repoNote, italics: true, size: 20, color: "555555" })],
      spacing: { before: 120, after: 120 }, alignment: AlignmentType.JUSTIFIED }));
  }
});

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 1 } },
    ]
  },
  numbering: { config: [{ reference: "bullets",
    levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: "LayerForge v9 Main — Page ", size: 18 }),
        new TextRun({ children: [PageNumber.CURRENT], size: 18 }),
      ] })] }) },
    children: children,
  }]
});

Packer.toBuffer(doc).then(buffer => {
  const outPath = path.join(__dirname, 'layerforge_v9_main.docx');
  fs.writeFileSync(outPath, buffer);
  console.log(`Wrote: ${outPath} (${buffer.length} bytes)`);
});
