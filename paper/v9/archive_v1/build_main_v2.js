// LayerForge v9 Main Paper (v2) — slim body + figures + appendix reference
// chai 指示「理論 + 図中心、細かい検証は別資料 or 章立て、詰め込みすぎ NG」

const path = require('path');
const fs = require('fs');
const docxPath = path.join(process.env.APPDATA, 'npm', 'node_modules', 'docx');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, PageOrientation, LevelFormat, ImageRun,
        TabStopType, TabStopPosition, HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak } = require(docxPath);

const border = { style: BorderStyle.SINGLE, size: 1, color: "888888" };
const borders = { top: border, bottom: border, left: border, right: border };

function H1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, bold: true, size: 32 })], spacing: { before: 360, after: 240 }}); }
function H2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, bold: true, size: 26 })], spacing: { before: 240, after: 180 }}); }
function H3(text) { return new Paragraph({ heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, bold: true, size: 24 })], spacing: { before: 180, after: 120 }}); }
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

function embedImage(filePath, widthPx, heightPx, captionText) {
  const data = fs.readFileSync(filePath);
  return [
    new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 240, after: 60 },
      children: [new ImageRun({ type: "png", data,
        transformation: { width: widthPx, height: heightPx },
        altText: { title: captionText, description: captionText, name: path.basename(filePath) } })] }),
    Caption(captionText),
  ];
}

const IMG_DIR = path.join(__dirname, '..', 'docs', 'images');
const children = [];

// === Title ===
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 240 },
  children: [new TextRun({ text: "LayerForge v9: Phase 2b Verification Update", bold: true, size: 40 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({ text: "Two-Layer Fidelity Structure and Hybrid Ensemble Path",
    italics: true, size: 26 })] }));
children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 480 },
  children: [new TextRun({ text: "chai  ·  2026-05-17", size: 22 })] }));

children.push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 360 },
  children: [new TextRun({
    text: "(Main paper — slim body with figures. Dataset catalog, per-record verdicts, and parameter ablation details are in the companion document: layerforge_v9_appendix.pdf)",
    italics: true, size: 18, color: "555555" })] }));

// === Abstract ===
children.push(H2("Abstract"));
children.push(Body(
  "LayerForge is a deterministic text-decomposition tool that extracts 4±1 hierarchical themes via " +
  "CPM community detection on sentence-transformer embeddings. The v8.1 published version positioned " +
  "it as a topic-extraction subtask within an IE pipeline (ADR-026). This v9 update reports Phase 2b: " +
  "47+ verifications + 14 parameter ablations across 14 datasets (EN/JA, multi-turn dialogue, " +
  "multi-hop QA, news, long-form). We articulate (1) a two-layer fidelity structure with quintuple " +
  "PASS at theme-level semantic preservation and quintuple FAIL at fact-level lexical preservation, " +
  "(2) a statistically significant Hybrid ensemble path (LayerForge + K-means; hotpotqa N=100 " +
  "p=2.7e-05, livedoor N=27 p=5.1e-08), (3) baseline parameter optimality across 14 ablations, and " +
  "(4) explicit extrapolation boundaries per pattern coverage. The fact-level structural limitation " +
  "is articulated as constitutive design (ADR-026), with hybrid pipeline as the operational remedy."
));

// === 1. Introduction ===
children.push(H1("1. Introduction"));
children.push(Body(
  "LayerForge v8.1 produces 4±1 hierarchical themes from arbitrary input text via four components: " +
  "(i) sentence-transformer embeddings (paraphrase-multilingual-mpnet-base-v2), (ii) CPM-Louvain " +
  "community detection (Traag 2011, Blondel 2008), (iii) scale_finder with K=4±1 cognitive constraint " +
  "(Miller 1956, Cowan 2001), (iv) ctfidf-based representation extraction (Grootendorst 2022). " +
  "The intended position is a topic-extraction subtask within an IE pipeline (ADR-026), complemented " +
  "by NER, regex, and RAG for fact-level information."
));
children.push(Body(
  "This v9 update articulates what LayerForge can and cannot do, where structural limitations lie, " +
  "and which improvement paths are evidence-grounded. Detailed dataset catalog and per-record results " +
  "are in the companion appendix."
));

// === 2. Theoretical Framework ===
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
  "These layers are independent dimensions. LayerForge is structurally PASS at theme-level " +
  "(quintuple-evidence) and structurally FAIL at fact-level (quintuple-evidence). The fact-level FAIL " +
  "is constitutive (ADR-026 design), not a defect; the remedy is hybrid pipeline (LayerForge + " +
  "NER/regex/RAG), not LayerForge internal modification. Figure 1 visualizes this positioning."
));

// Figure 1: Two-layer fidelity structure (Plot 3)
const fig1 = embedImage(path.join(IMG_DIR, 'v040_plot3_theme_vs_fact.png'), 480, 336,
  "Figure 1. Two-layer fidelity structure (V-040 Plot 3). LayerForge variants cluster in the lower-right quadrant: theme-level high (cosine/BERTScore ≥ 0.8) but fact-level low (substring ≤ 0.1). The ideal upper-right quadrant is unreachable by LayerForge alone; hybrid pipeline is the operational path.");
fig1.forEach(p => children.push(p));

// === 3. Method ===
children.push(H1("3. Method"));
children.push(Body(
  "All verifications follow ADR-022 §3: pre-register §1-§5 (claim, dataset, method, pre-commit " +
  "interpretations) with immutability, then execute and append §6-§8 (run record, outcome, impact). " +
  "This prevents post-hoc threshold drift. Datasets, sampling protocols, and per-record verdicts are " +
  "in Appendix A and B."
));
children.push(Body(
  "Self-preference bias disclosure: LLM-as-judge evaluations used Claude Code subagent (Sonnet/Opus) " +
  "as evaluator on Claude-compressed context. Formal Anthropic API + Haiku 4.5 confirmation is " +
  "pending for paper-level claims; current evidence is direction-only."
));

// === 4. Key Results ===
children.push(H1("4. Key Results"));

children.push(H2("4.1 Reduction Landscape (14 Datasets)"));
children.push(Body(
  "Reduction across 14 datasets confirms language-independent ceiling (Aozora 99.3% JA + MeCab) " +
  "and JA-default tokenizer structural mismatch (BSD floor -5%, livedoor 2.5%). See Appendix A " +
  "for dataset catalog. Figure 2 visualizes the reduction landscape colored by language × " +
  "tokenization."
));
const fig2 = embedImage(path.join(IMG_DIR, 'v040_plot4_reduction_landscape.png'), 540, 315,
  "Figure 2. Reduction landscape across 14 datasets (V-040 Plot 4). Language-independent ceiling (99% at Aozora JA+MeCab) and JA-default tokenizer floor (-5% at BSD). EN: 77-99%, JA+MeCab: 57-99%, JA-default: structural mismatch.");
fig2.forEach(p => children.push(p));

children.push(H2("4.2 Theme-level Fidelity (Pareto Frontier)"));
children.push(Body(
  "On the reduction × theme-fidelity plane, F4 hybrid format (V-007/V-025) occupies the Pareto " +
  "frontier with reduction ~0.85 and BERTScore F1 ≥ 0.83 (Figure 3). The trade-off curve is " +
  "approximately fidelity ≈ 0.94 × (1 - reduction × 0.15). Detailed verdicts and N for each point " +
  "are in Appendix B."
));
const fig3 = embedImage(path.join(IMG_DIR, 'v040_plot1_reduction_vs_theme_fidelity.png'), 540, 378,
  "Figure 3. Reduction × theme-level fidelity Pareto frontier (V-040 Plot 1). F4 hybrid format (V-007/V-025) is current Pareto-optimal at reduction ~0.85, BERTScore F1 0.83-0.94. ADR-022 §1 threshold (0.80) marked in red.");
fig3.forEach(p => children.push(p));

children.push(H2("4.3 Hybrid Ensemble Path (Statistical Significance)"));
children.push(Body(
  "V-036 observed K-means baseline tok_recall 2x superior to LayerForge alone on hotpotqa N=5. " +
  "We pursued Path 2 (LayerForge + K-means ensemble) as the v8.1-integrity-preserving improvement " +
  "direction. N progression confirms statistical significance and cross-corpus consistency:"
));
const tblEns = makeTable(
  ["V-ID", "Dataset", "N", "Ens vs LF (p)", "Ens vs K-means (p)"],
  [
    ["V-042", "hotpotqa", "5", "+0.067 (n.s.)", "+0.000 (n.s.)"],
    ["V-042-bis", "hotpotqa", "30", "+0.098", "+0.042"],
    ["V-042-tri", "hotpotqa", "100", "+0.113 (2.7e-05)", "+0.033 (2.4e-03)"],
    ["V-042-quad", "livedoor (JA)", "27", "+0.140 (5.1e-08)", "+0.260 (1.3e-10)"],
  ],
  [1400, 2200, 800, 2300, 2660]
);
children.push(tblEns);
children.push(Caption("Table 1. Hybrid ensemble N progression and cross-corpus statistical significance. Both datasets confirm ensemble > both baselines (paired t-test)."));

children.push(H2("4.4 Cost vs Accuracy Sweet Spot"));
children.push(Body(
  "Figure 4 plots input-token cost (log scale) vs downstream LLM accuracy. Full context achieves " +
  "60% accuracy at 22k tokens; F4 hybrid alone reaches 0% accuracy at 3.5k tokens. The hypothesized " +
  "operational sweet spot is F4 hybrid + RAG retrieval at ~8k tokens × 50% accuracy " +
  "(implementation pending; V-030 future verification trigger)."
));
const fig4 = embedImage(path.join(IMG_DIR, 'v040_plot5_cost_vs_accuracy.png'), 540, 378,
  "Figure 4. Cost (input tokens, log scale) × downstream LLM accuracy (V-040 Plot 5). Full baseline 22k tokens at 60% accuracy. F4 hybrid alone is cost-efficient but accuracy 0%. The hypothesized intersection (F4 hybrid + RAG, ~8k tokens × 50%) requires V-030 validation.");
fig4.forEach(p => children.push(p));

children.push(H2("4.5 Parameter Ablation Summary"));
children.push(Body(
  "14 ablations confirm baseline parameter values are at or near improvement-LARGE threshold " +
  "(no parameter shows >0.30 delta improvement). Baseline snapshot v1 is preserved unchanged. " +
  "Notable findings: V-027 (digit preservation NEGATIVE → core-spec modification trigger), " +
  "V-032-bis (mpnet > MiniLM-L6 in N=30 reverses N=5 direction, illustrating careful-strategy " +
  "Rule §3 importance). Full ablation table is in Appendix C."
));

// === 5. Discussion ===
children.push(H1("5. Discussion"));

children.push(H2("5.1 Cross-corpus Direction Reversal"));
children.push(Body(
  "V-042-tri (hotpotqa) shows K-means superior to LayerForge alone (+0.080). V-042-quad (livedoor) " +
  "shows LayerForge superior to K-means (+0.121, direction reversed). Both datasets confirm ensemble " +
  "superior to both baselines. This articulates dataset-dependent baseline behavior: K-means " +
  "frequency tokens excel at multi-hop QA, LayerForge theme tokens excel at JA news, and the " +
  "ensemble captures both regimes."
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
  "integrity. Core-spec modifications (ctfidf → tf hybrid, embedding swap, K=4±1 relaxation, " +
  "scale_finder change) require v8.1 integrity reconsideration and paper update synchronization. " +
  "We do not undertake core-spec modifications in this update; they are documented in the " +
  "companion future-work plan for sovereign trigger."
));

// === 6. Limitations ===
children.push(H1("6. Limitations"));
children.push(Bullet("Sample sizes N=5-100; formal population-scale not achieved."));
children.push(Bullet("Self-preference bias: subagent fallback (Claude evaluating Claude). Formal Anthropic API + Haiku 4.5 confirmation pending."));
children.push(Bullet("Coverage bias: EN long-form dominated by hotpotqa (16/16 verifications), JA mid-form dominated by livedoor."));
children.push(Bullet("Fact-level FAIL is constitutive (ADR-026 design), remediated by hybrid pipeline (bucket B), not by LayerForge modification."));
children.push(Bullet("Path 1 (core-spec ctfidf → tf hybrid) is unevaluated; requires v8.1 integrity reconsideration."));

// === 7. Future Work ===
children.push(H1("7. Future Work"));
children.push(Body(
  "We articulate 15 future work items across 4 axes. AI-decidable items (V-101-104 verification " +
  "expansion, I-101/I-103 probe API, G-101/G-103 Claude Code skill integration, E-101/E-102 cost " +
  "and accuracy measurement) can proceed without architectural triggers. Sovereign-trigger items " +
  "(I-102 routing logic, I-104 v8.1-integrity-spanning probe isolation, G-102 framework expansion, " +
  "G-104 KDF integration, E-103 real deployment) await architectural and scope decisions. Full " +
  "roadmap is in the companion appendix."
));

// === 8. Conclusion ===
children.push(H1("8. Conclusion"));
children.push(Body(
  "LayerForge v9 confirms a two-layer fidelity structure: theme-level semantic preservation is " +
  "structurally PASS (quintuple-evidence), fact-level lexical preservation is structurally FAIL " +
  "(quintuple-evidence). The Hybrid ensemble path is statistically significantly superior to both " +
  "baselines on two datasets (hotpotqa p<2.7e-05, livedoor p<5.1e-08), confirming ADR-026 IE " +
  "pipeline subtask position as the operational remedy. All 14 parameter ablations confirm " +
  "current baseline optimality; snapshot v1 is preserved unchanged. Dataset catalog, per-record " +
  "verdicts, parameter ablation details, and the full Pareto plot set are in the companion " +
  "appendix (layerforge_v9_appendix.pdf)."
));

// === Refs ===
children.push(H1("References"));
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
  "LayerForge v9 Appendix (2026). docs/verification_index.md v6 (commit a2e91a8).",
  "LayerForge v9 Appendix (2026). docs/parameter_baseline.md v8 (commit 8d792fe).",
  "LayerForge v9 Appendix (2026). docs/capability_matrix.md (commit bce1e81).",
  "LayerForge v9 Appendix (2026). docs/future_plan.md (commit c462618).",
  "LayerForge v9 Appendix (2026). docs/06_decision_log.md ADR-013 through ADR-026.",
];
refs.forEach((r, i) => children.push(new Paragraph({
  children: [new TextRun({ text: `[${i+1}] ${r}`, size: 20 })],
  spacing: { after: 80 }, indent: { left: 360, hanging: 360 }})));

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
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 120 }, outlineLevel: 2 } },
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
