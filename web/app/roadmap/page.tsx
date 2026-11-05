import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Research Roadmap",
  description:
    "From course project to research paper: how instructor feedback maps to a multi-benchmark, validated, statistically rigorous study of lexical–dense fusion for biomedical retrieval.",
};

const REPO = "https://github.com/Arungharami/biomedical-hybrid-ir";
const BLOB = `${REPO}/blob/main`;

type Item = {
  n: string;
  ask: string;
  why: string;
  built: string[];
  design: { k: string; v: string }[];
  files: { label: string; href: string }[];
  next: string;
};

const ITEMS: Item[] = [
  {
    n: "1",
    ask: "Experiments on more benchmark datasets",
    why: "One collection of 323 test queries makes small effects hard to detect and limits how far the conclusions generalize.",
    built: [
      "Pinned Hugging Face loaders for NFCorpus, SciFact and TREC-COVID",
      "Strict validation: duplicate IDs, dangling qrels, empty text, split overlap, dev/test query-text overlap",
      "Dataset and qrels commit SHAs saved with every run",
    ],
    design: [
      { k: "NFCorpus", v: "Official validation split as dev" },
      { k: "SciFact", v: "Official test; 20% of train query IDs held out as dev (seed 42)" },
      { k: "TREC-COVID", v: "Test only — settings transferred frozen from another benchmark" },
    ],
    files: [
      { label: "research_data.py", href: `${BLOB}/src/biomedical_ir/research_data.py` },
    ],
    next: "Run NFCorpus and SciFact, then transfer frozen settings to TREC-COVID.",
  },
  {
    n: "2",
    ask: "Validation study on tuning hyperparameters",
    why: "The course study used textbook defaults (k1 = 1.2, b = 0.75, RRF k = 60) to avoid test leakage — tuning them on a dev split is the principled next step.",
    built: [
      "Grid search on dev, selection written to disk before any test metric is computed",
      "Deterministic tie-breaking; no transformer fine-tuning",
      "Optional common rerank-pool selection across all candidate sources",
    ],
    design: [
      { k: "BM25", v: "k1 ∈ {0.6, 1.2, 1.8} × b ∈ {0.25, 0.5, 0.75}" },
      { k: "RRF", v: "k ∈ {10, 30, 60, 100}" },
      { k: "Weighted fusion", v: "lexical α ∈ {0, .25, .5, .75, 1}" },
      { k: "Rerank pool", v: "{20, 50, 100}, chosen by mean dev nDCG@10" },
    ],
    files: [
      { label: "research_pipeline.py", href: `${BLOB}/src/biomedical_ir/research_pipeline.py` },
      { label: "configs/research.json", href: `${BLOB}/configs/research.json` },
    ],
    next: "Produce selection.json per benchmark and report how far tuned settings move from the defaults.",
  },
  {
    n: "3",
    ask: "All fusion methods vs. single methods — when does fusion help?",
    why: "The course result showed fusion helping on some queries and hurting on others. The paper question is under which conditions lexical–dense fusion actually improves retrieval.",
    built: [
      "Single systems: TF-IDF, BM25, BGE, MedCPT",
      "Fusion pairs: BM25+BGE and BM25+MedCPT",
      "Two fusion rules: RRF and per-query min-max weighted fusion",
      "Predefined strata: query length (≤8 / >8 tokens) and lexical–dense top-10 overlap (Jaccard ≤.2 / >.2)",
    ],
    design: [
      { k: "Candidates", v: "Top 100 per retriever; fusion sees up to 200, returns 100" },
      { k: "Contrasts", v: "Each of 4 fusion systems vs. BM25 and vs. its dense ingredient — 8 (15 with reranking)" },
      { k: "Cost", v: "Stage timings and peak memory recorded per system" },
    ],
    files: [
      { label: "research_fusion.py", href: `${BLOB}/src/biomedical_ir/research_fusion.py` },
    ],
    next: "Characterize wins and losses by stratum to explain when fusion helps.",
  },
  {
    n: "4",
    ask: "Evaluation rigor: multiple-testing correction and confidence intervals",
    why: "Many pairwise comparisons inflate false positives, and p-values alone don’t show effect size or uncertainty.",
    built: [
      "95% paired percentile bootstrap intervals for each system and each improvement",
      "Two-sided paired Monte Carlo sign-randomization tests (10,000 resamples, seed 42)",
      "Holm correction per dataset, plus study-wide Holm across benchmarks",
      "Supporting metrics kept descriptive — no uncorrected significance claims",
    ],
    design: [
      { k: "Primary metric", v: "nDCG@10 (pytrec_eval)" },
      { k: "Supporting", v: "P@10, Recall@100, MAP@100, MRR@10" },
      { k: "Correction", v: "Holm–Bonferroni, per dataset and study-wide" },
    ],
    files: [
      { label: "research_stats.py", href: `${BLOB}/src/biomedical_ir/research_stats.py` },
      { label: "summarize_research.py", href: `${BLOB}/scripts/summarize_research.py` },
    ],
    next: "Report adjusted p-values and intervals for every planned contrast.",
  },
];

const PLAN = [
  { s: "done", t: "Course study on NFCorpus", d: "Six systems, paired bootstrap, error analysis, live portal." },
  { s: "done", t: "Research infrastructure", d: "Loaders, tuning grids, fusion matrix, Holm + CIs; 26 offline tests passing." },
  { s: "next", t: "Run NFCorpus + SciFact", d: "Dev-tuned settings, all single and fusion systems, full statistics." },
  { s: "next", t: "Transfer to TREC-COVID", d: "Frozen settings, no test-set tuning." },
  { s: "next", t: "Aggregate & analyze", d: "Study-wide Holm, stratified fusion gains, failure cases." },
  { s: "next", t: "Related work & paper revision", d: "Position the contribution against prior fusion literature, update tables and figures with verified outputs only." },
];

export default function RoadmapPage() {
  return (
    <div className="flex flex-col gap-16">
      {/* Hero */}
      <section className="relative -mx-4 -mt-8 overflow-hidden text-white sm:mx-0 sm:mt-0 sm:rounded-3xl">
        <div className="absolute inset-0 bg-[#07122b]" />
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(55% 80% at 0% 0%, rgba(37,99,235,.5) 0%, transparent 60%), radial-gradient(45% 70% at 100% 100%, rgba(204,0,0,.35) 0%, transparent 60%)",
          }}
        />
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(255,255,255,.8) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.8) 1px, transparent 1px)",
            backgroundSize: "44px 44px",
          }}
        />
        <div className="relative px-5 py-12 sm:px-10 sm:py-16">
          <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
            Research Roadmap
          </span>
          <h1 className="mt-5 max-w-4xl text-3xl font-black leading-tight tracking-tight sm:text-5xl">
            From course project{" "}
            <span className="bg-gradient-to-r from-sky-300 to-white bg-clip-text text-transparent">to research paper</span>
          </h1>
          <p className="mt-5 max-w-2xl text-lg leading-relaxed text-white/75">
            Proposed title: <em className="text-white">When Does Lexical–Dense Fusion Improve Biomedical Retrieval? A
            Multi-Benchmark Study with Validated Hyperparameters and Statistical Evaluation.</em>
          </p>
          <div className="mt-8 grid max-w-3xl gap-3 sm:grid-cols-3">
            {[
              ["4 / 4", "feedback points with code in place"],
              ["3", "benchmarks: NFCorpus, SciFact, TREC-COVID"],
              ["0", "new results claimed yet"],
            ].map(([v, l]) => (
              <div key={l} className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
                <p className="text-2xl font-bold tabular">{v}</p>
                <p className="mt-0.5 text-sm text-white/65">{l}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feedback */}
      <section className="grid gap-6 lg:grid-cols-[1fr_1.2fr] lg:items-start">
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">Instructor feedback</p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
            Four directions for a research paper
          </h2>
          <p className="mt-3 leading-relaxed text-text-secondary">
            After reviewing the course project, Dingding Wang suggested four ways to develop it into a research paper.
            Each one is mapped below to what is already implemented in the repository and what still needs to run.
          </p>
          <div className="mt-5 flex items-start gap-3 rounded-2xl border border-good/30 bg-good/10 p-4">
            <span className="mt-0.5 text-good">✓</span>
            <p className="text-sm text-text-primary">
              <strong>Honest status:</strong> the experiment infrastructure is built and tested offline. The new
              multi-benchmark experiments have <strong>not been run yet</strong>, so this page reports design, not results.
              Existing NFCorpus results keep their original provenance.
            </p>
          </div>
        </div>
        <figure className="relative overflow-hidden rounded-2xl border border-border bg-surface p-6 sm:p-8">
          <span aria-hidden className="absolute -top-6 right-4 text-[120px] font-black leading-none text-accent/10">
            “
          </span>
          <blockquote className="relative text-lg leading-relaxed text-text-primary">
            This work is more than good enough for a course project. For turning it into a research paper, the following
            directions may be considered.
          </blockquote>
          <ol className="relative mt-4 flex flex-col gap-2 text-text-secondary">
            {ITEMS.map((it) => (
              <li key={it.n} className="flex gap-3">
                <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-accent-soft text-xs font-bold text-accent">
                  {it.n}
                </span>
                <span>{it.ask}</span>
              </li>
            ))}
          </ol>
          <figcaption className="relative mt-5 flex items-center gap-3 border-t border-border pt-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/course/people/dingding.jpg" alt="" className="h-10 w-10 rounded-full object-cover object-top" />
            <span>
              <span className="block text-sm font-semibold text-text-primary">Dingding Wang</span>
              <span className="block text-xs text-text-muted">Course Instructor · CAP 6776, Florida Atlantic University</span>
            </span>
          </figcaption>
        </figure>
      </section>

      {/* Mapping */}
      <section className="flex flex-col gap-5">
        {ITEMS.map((it) => (
          <article key={it.n} className="overflow-hidden rounded-2xl border border-border bg-surface">
            <div className="flex flex-col gap-3 border-b border-border bg-surface-2/60 p-5 sm:flex-row sm:items-center sm:justify-between sm:p-6">
              <div className="flex items-center gap-4">
                <span className="bg-gradient-to-br from-accent to-[#cc0000] bg-clip-text text-4xl font-black leading-none text-transparent tabular">
                  0{it.n}
                </span>
                <h3 className="text-lg font-semibold text-text-primary sm:text-xl">{it.ask}</h3>
              </div>
              <div className="flex shrink-0 gap-2 text-xs font-medium">
                <span className="rounded-full border border-good/30 bg-good/10 px-2.5 py-1 text-good">Code built</span>
                <span className="rounded-full border border-warn/30 bg-warn/10 px-2.5 py-1 text-warn">Runs pending</span>
              </div>
            </div>
            <div className="grid gap-6 p-5 sm:p-6 lg:grid-cols-[1fr_1fr]">
              <div>
                <p className="text-sm leading-relaxed text-text-secondary">
                  <span className="font-semibold text-text-primary">Why it matters. </span>
                  {it.why}
                </p>
                <p className="mt-4 text-[11px] font-semibold uppercase tracking-[0.16em] text-text-muted">Implemented</p>
                <ul className="mt-2 flex flex-col gap-1.5">
                  {it.built.map((b) => (
                    <li key={b} className="flex gap-2 text-sm text-text-primary">
                      <span className="text-good">✓</span>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex flex-wrap gap-2">
                  {it.files.map((f) => (
                    <a
                      key={f.label}
                      href={f.href}
                      target="_blank"
                      rel="noreferrer"
                      className="rounded-lg bg-[#07122b] px-2.5 py-1 font-mono text-[11px] text-sky-200 hover:bg-[#0c1d45]"
                    >
                      {f.label} ↗
                    </a>
                  ))}
                </div>
              </div>
              <div className="flex flex-col gap-4">
                <dl className="overflow-hidden rounded-xl border border-border">
                  {it.design.map((d, i) => (
                    <div key={d.k} className={`grid grid-cols-[120px_1fr] gap-3 px-4 py-2.5 text-sm ${i ? "border-t border-border" : ""}`}>
                      <dt className="font-medium text-text-primary">{d.k}</dt>
                      <dd className="text-text-secondary">{d.v}</dd>
                    </div>
                  ))}
                </dl>
                <p className="rounded-xl bg-accent-soft px-4 py-3 text-sm text-text-primary">
                  <span className="font-semibold text-accent">Next → </span>
                  {it.next}
                </p>
              </div>
            </div>
          </article>
        ))}
      </section>

      {/* Plan */}
      <section>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">Plan</p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">Path to submission</h2>
        <ol className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {PLAN.map((p, i) => (
            <li
              key={p.t}
              className={`rounded-2xl border p-5 ${
                p.s === "done" ? "border-good/30 bg-good/5" : "border-border bg-surface"
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-text-muted tabular">Stage {i + 1}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${
                    p.s === "done" ? "bg-good/15 text-good" : "bg-surface-2 text-text-muted"
                  }`}
                >
                  {p.s === "done" ? "Done" : "Up next"}
                </span>
              </div>
              <p className="mt-2 font-semibold text-text-primary">{p.t}</p>
              <p className="mt-1 text-sm leading-relaxed text-text-secondary">{p.d}</p>
            </li>
          ))}
        </ol>

        <div className="mt-6 rounded-2xl border border-border bg-surface p-5 sm:p-6">
          <p className="font-semibold text-text-primary">Run it yourself</p>
          <pre className="mt-3 overflow-x-auto rounded-xl bg-[#07122b] p-4 font-mono text-xs leading-relaxed text-sky-200">
{`python scripts/run_research.py --dataset nfcorpus --device cuda
python scripts/run_research.py --dataset scifact  --device cuda
python scripts/run_research.py --dataset trec-covid --device cuda \\
       --frozen-selection SOURCE/selection.json
python scripts/summarize_research.py NFCORPUS_RUN SCIFACT_RUN TREC_COVID_RUN`}
          </pre>
          <p className="mt-3 text-sm text-text-secondary">
            Full protocol in{" "}
            <a href={`${BLOB}/docs/research-extension.md`} target="_blank" rel="noreferrer" className="text-accent hover:underline">
              docs/research-extension.md
            </a>
            . A Kaggle notebook is included for GPU runs. See the current{" "}
            <Link href="/course" className="text-accent hover:underline">course project</Link> and{" "}
            <Link href="/results" className="text-accent hover:underline">NFCorpus results</Link>.
          </p>
        </div>
      </section>
    </div>
  );
}
