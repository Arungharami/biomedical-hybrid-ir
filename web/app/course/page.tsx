import type { Metadata } from "next";
import Link from "next/link";
import SlideViewer, { type Deck } from "@/components/SlideViewer";
import VideoStudio, { type Talk } from "@/components/VideoStudio";
import { AUTHOR } from "@/lib/author";
import { MODEL_LABELS, MODEL_ORDER, efficiency, formatMetric, metrics } from "@/lib/data";

export const metadata: Metadata = {
  title: "Course Project",
  description:
    "CAP 6776 Information Retrieval course project at Florida Atlantic University — two video presentations, slide decks, poster, and the full step-by-step build of a hybrid biomedical retrieval system.",
};

const REPO = "https://github.com/Arungharami/biomedical-hybrid-ir";

const TALKS: Talk[] = [
  {
    id: "talk",
    kicker: "Video 1 · Main presentation",
    title: "CAP 6776: Hybrid Search",
    duration: "9:50",
    size: "26 MB",
    style: "Structured six-part research talk",
    src: "/course/CAP6776_Hybrid_Search.mp4",
    poster: "/course/video-poster.jpg",
    summary:
      "The formal course presentation. It follows the structure of a research paper — problem, data, method, evaluation, results, limitations — and walks through every component of the hybrid pipeline with the real numbers from the 323 held-out test queries.",
    highlights: [
      "Six numbered parts that mirror the written report",
      "Why “canker sores” never matches “recurrent aphthous ulcers”",
      "BM25 vs. MedCPT, fused with Reciprocal Rank Fusion",
      "How the cross-encoder jointly attends to query and article",
      "P@10, nDCG@10, MRR@10 and latency for every model",
      "Limitations and the latency-vs-precision question",
    ],
    chapters: [
      { t: 0, label: "Introduction — CAP 6776: Hybrid Search" },
      { t: 37, label: "Agenda" },
      { t: 55, label: "1 · The biomedical search problem" },
      { t: 128, label: "2 · Data & core retrievers" },
      { t: 235, label: "3 · Fusion & reranking" },
      { t: 277, label: "Reciprocal Rank Fusion" },
      { t: 318, label: "Cross-encoder joint attention" },
      { t: 348, label: "4 · Evaluating the system" },
      { t: 392, label: "5 · Results & analysis" },
      { t: 505, label: "6 · Limitations & future work" },
    ],
  },
  {
    id: "explainer",
    kicker: "Video 2 · Illustrated explainer",
    title: "Biomedical Search",
    duration: "9:08",
    size: "41 MB",
    style: "Story-driven, hand-drawn visual walkthrough",
    src: "/course/Biomedical_Search_Explainer.mp4",
    poster: "/course/video2-poster.jpg",
    summary:
      "A companion explainer that tells the same study as a story. Starting from the question “how do you find answers with zero shared words?”, it builds up from keyword search to meaning-based search, shows why a hybrid is needed, and ends on the central trade-off: is a small gain in accuracy worth a 480× slower answer?",
    highlights: [
      "Opens with the zero-shared-words puzzle",
      "Visual intuition for BM25 and 768-d MedCPT vectors",
      "Precision vs. meaning: why neither is enough alone",
      "RRF fuses positions, not raw scores",
      "Semantic drift and the reranker “coin flip”",
      "1,946 ms on an M1 — the speed vs. accuracy verdict",
    ],
    chapters: [
      { t: 0, label: "Introduction — Biomedical Search" },
      { t: 58, label: "Finding answers with zero shared words" },
      { t: 87, label: "Lexical search (BM25)" },
      { t: 118, label: "Dense retrieval (MedCPT)" },
      { t: 151, label: "Precision vs. meaning" },
      { t: 180, label: "Can a hybrid system do both?" },
      { t: 207, label: "The pipeline: retrievers → RRF → cross-encoder" },
      { t: 236, label: "Fusing positions, not scores" },
      { t: 270, label: "The dataset: 3,237 lay queries" },
      { t: 296, label: "nDCG@10 results" },
      { t: 327, label: "Test-set verdicts" },
      { t: 366, label: "Semantic drift" },
      { t: 395, label: "The reranker’s near-even split" },
      { t: 426, label: "The cost of cross-encoding" },
      { t: 452, label: "1,946 ms per query" },
      { t: 473, label: "Speed vs. accuracy" },
      { t: 502, label: "Is the accuracy worth 480× the wait?" },
    ],
  },
];

const DECKS: Deck[] = [
  {
    id: "fau",
    title: "Final presentation",
    subtitle:
      "Biomedical Hybrid Information Retrieval — the FAU class deck: problem, research questions, architecture, results and error analysis.",
    folder: "/course/slides/fau",
    count: 15,
    pptx: "/course/downloads/Biomedical_Hybrid_IR_FAU.pptx",
    pdf: "/course/downloads/Biomedical_Hybrid_IR_FAU.pdf",
  },
  {
    id: "gap",
    title: "Bridging the Search Gap",
    subtitle:
      "Finding the science behind everyday health questions — an illustrated companion deck explaining the same study visually.",
    folder: "/course/slides/gap",
    count: 13,
    pptx: "/course/downloads/Bridging_the_Biomedical_Search_Gap.pptx",
    pdf: "/course/downloads/Bridging_the_Biomedical_Search_Gap.pdf",
  },
];

type Step = {
  phase: string;
  title: string;
  what: string;
  how: string[];
  cmd?: string;
  output: string;
  link?: { href: string; label: string };
};

const STEPS: Step[] = [
  {
    phase: "Define",
    title: "Frame the problem",
    what: "Lay users say “canker sores”; papers say “recurrent aphthous ulcers”. Keyword search can return nothing.",
    how: ["RQ1 · Dense vs. BM25", "RQ2 · MedCPT vs. BGE", "RQ3 · Is fusion + reranking worth it?"],
    output: "Research questions and protocol fixed up front",
    link: { href: "/paper", label: "Paper" },
  },
  {
    phase: "Data",
    title: "Audit NFCorpus",
    what: "Pull BEIR/NFCorpus from Hugging Face and verify every count instead of trusting docs.",
    how: ["3,633 docs · 3,237 queries", "323 held-out test queries", "Graded relevance 0/1/2, zero leakage"],
    cmd: "python scripts/audit_dataset.py",
    output: "data/processed/dataset_stats.json",
    link: { href: "/dataset", label: "Dataset" },
  },
  {
    phase: "Lexical",
    title: "TF-IDF & BM25 baselines",
    what: "Exact-term retrieval; BM25 written from scratch with frozen textbook defaults.",
    how: ["k1 = 1.2, b = 0.75", "Inverted index", "Top 100 per query"],
    cmd: "python scripts/run_bm25.py",
    output: "Ranked runs + metrics + manifests",
  },
  {
    phase: "Dense",
    title: "BGE & MedCPT encoders",
    what: "Turn queries and abstracts into 768-d vectors so meaning matches even when words don’t.",
    how: ["BAAI/bge-base-en-v1.5", "ncbi/MedCPT query + article", "FAISS exact search"],
    cmd: "python scripts/run_medcpt.py",
    output: "Dense indices + runs",
    link: { href: "/models", label: "Models" },
  },
  {
    phase: "Fuse",
    title: "Reciprocal Rank Fusion",
    what: "BM25 (≈5–15) and MedCPT (≈55–65) scores don’t compare, so merge ranks instead.",
    how: ["RRF(d) = Σ 1 / (60 + rank)", "Agreement beats a lone #1", "+2 ms over retrievers"],
    cmd: "python scripts/run_hybrid.py",
    output: "Hybrid BM25 + MedCPT run",
    link: { href: "/pipeline", label: "Pipeline" },
  },
  {
    phase: "Rerank",
    title: "MedCPT cross-encoder",
    what: "Read query and article together — every word attends to every word — on the top 50.",
    how: ["50 transformer passes/query", "Best nDCG@10: 0.373", "≈1,946 ms per query"],
    cmd: "python scripts/run_reranker.py",
    output: "Final top-10 lists",
  },
  {
    phase: "Evaluate",
    title: "Same protocol for all six",
    what: "TREC-standard pytrec_eval, cross-checked by hand-written metrics, plus significance tests.",
    how: ["P@10 · R@100 · MAP · MRR · nDCG", "10,000 paired bootstrap resamples", "Latency on Apple M1 Pro"],
    cmd: "python scripts/evaluate_all.py",
    output: "Results table, tests, 7 figures",
    link: { href: "/evaluation", label: "Evaluation" },
  },
  {
    phase: "Diagnose",
    title: "Query-level error analysis",
    what: "Look past averages to see where each method wins and fails.",
    how: ["MedCPT rescues BM25: 244 queries", "BM25 rescues MedCPT: 52", "Reranker: 926 up vs. 832 down"],
    cmd: "python scripts/error_analysis.py",
    output: "results/error-analysis/",
    link: { href: "/error-analysis", label: "Errors" },
  },
  {
    phase: "Ship",
    title: "Reproducible & public",
    what: "Tested Python library, manifests for every run, this portal, two decks and two videos.",
    how: ["src/biomedical_ir + CI tests", "One manifest per experiment", "Live on Vercel"],
    cmd: "python scripts/export_web_results.py",
    output: "This website + GitHub repo",
    link: { href: "/reproducibility", label: "Reproduce" },
  },
];

const FINDINGS = [
  {
    k: "RQ1",
    q: "Dense beats lexical",
    a: "BGE and MedCPT both beat BM25 on all five primary metrics (p < 0.005). Dense retrieval is the big step.",
    tone: "good",
    big: "p < 0.005",
  },
  {
    k: "RQ2",
    q: "General ≈ biomedical",
    a: "BGE and MedCPT are statistically tied (all p ≥ 0.12). Domain training gave no measurable gain here.",
    tone: "neutral",
    big: "p ≥ 0.12",
  },
  {
    k: "RQ3",
    q: "Reranking is costly",
    a: "Best nDCG@10 (0.373), but +0.011 over hybrid is not significant (p = 0.19) and it is ~480× slower.",
    tone: "warn",
    big: "480×",
  },
  {
    k: "Surprise",
    q: "TF-IDF beat BM25",
    a: "On short PubMed abstracts, untuned TF-IDF edged out default BM25 on nDCG@10 (p = 0.03).",
    tone: "neutral",
    big: "p = 0.03",
  },
];

const TOC = [
  ["presentation", "Presentation"],
  ["slides", "Slides"],
  ["poster", "Poster"],
  ["steps", "How it was built"],
  ["results", "Results"],
  ["findings", "Findings"],
  ["feedback", "Feedback"],
  ["deliverables", "Deliverables"],
] as const;

function Section({
  id,
  n,
  eyebrow,
  title,
  intro,
  children,
}: {
  id: string;
  n: string;
  eyebrow: string;
  title: string;
  intro?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-32">
      <div className="mb-7 flex items-end gap-4">
        <span
          aria-hidden
          className="bg-gradient-to-br from-accent to-[#cc0000] bg-clip-text text-5xl font-black leading-none text-transparent tabular sm:text-6xl"
        >
          {n}
        </span>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">{eyebrow}</p>
          <h2 className="mt-1 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">{title}</h2>
        </div>
      </div>
      {intro && <p className="-mt-2 mb-7 max-w-3xl leading-relaxed text-text-secondary">{intro}</p>}
      {children}
    </section>
  );
}

export default function CoursePage() {
  const latency = Object.fromEntries(efficiency.map((e) => [e.model, e.latency_ms_per_query ?? undefined]));
  const rows = MODEL_ORDER.map((id) => ({ id, m: metrics[id]?.metrics as Record<string, number> | undefined }));
  const COLS = ["P@10", "Recall@100", "MAP", "MRR@10", "nDCG@10"];
  const best = (key: string) => Math.max(...rows.map((r) => r.m?.[key] ?? 0));
  const ndcgMax = best("nDCG@10");

  return (
    <div className="flex flex-col gap-20">
      {/* ───────────── HERO ───────────── */}
      <section className="relative -mx-4 -mt-8 overflow-hidden text-white sm:mx-0 sm:mt-0 sm:rounded-3xl">
        <div className="absolute inset-0 bg-[#07122b]" />
        <div
          className="absolute inset-0 opacity-90"
          style={{
            background:
              "radial-gradient(60% 80% at 10% 0%, rgba(37,99,235,.55) 0%, transparent 60%), radial-gradient(50% 70% at 100% 100%, rgba(204,0,0,.38) 0%, transparent 60%), radial-gradient(40% 50% at 70% 10%, rgba(56,189,248,.25) 0%, transparent 70%)",
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

        <div className="relative grid gap-10 px-5 py-10 sm:px-10 sm:py-14 lg:grid-cols-[1.35fr_1fr] lg:items-center">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
                Florida Atlantic University
              </span>
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
                CAP 6776 · Information Retrieval
              </span>
              <span className="rounded-full bg-[#cc0000] px-3 py-1 text-xs font-semibold">Course Project</span>
            </div>
            <h1 className="mt-5 text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              Biomedical Hybrid
              <br />
              <span className="bg-gradient-to-r from-sky-300 via-blue-200 to-white bg-clip-text text-transparent">
                Information Retrieval
              </span>
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-white/75">
              Finding the science behind everyday health questions — by combining BM25 keyword precision,
              MedCPT semantic meaning, Reciprocal Rank Fusion and cross-encoder reranking.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <a
                href="#presentation"
                className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-[#07122b] shadow-lg shadow-black/20 transition hover:bg-sky-50"
              >
                ▶ Watch presentations
              </a>
              <a
                href="#slides"
                className="rounded-xl border border-white/25 bg-white/10 px-5 py-2.5 text-sm font-semibold backdrop-blur transition hover:bg-white/20"
              >
                View slides
              </a>
              <a
                href={REPO}
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-white/25 bg-white/10 px-5 py-2.5 text-sm font-semibold backdrop-blur transition hover:bg-white/20"
              >
                GitHub ↗
              </a>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              {
                src: "/course/people/arun.jpg",
                alt: "Arun Kumar Gharami presenting at Florida Atlantic University",
                role: "Presented by",
                name: "Arun Kumar Gharami",
                pos: "object-[50%_30%]",
                lift: "",
                link: { href: AUTHOR.website, label: AUTHOR.websiteLabel },
              },
              {
                src: "/course/people/dingding.jpg",
                alt: "Dingding Wang, course instructor",
                role: "Course Instructor",
                name: "Dingding Wang",
                pos: "object-top",
                lift: "lg:translate-y-8",
                link: null,
              },
            ].map((p) => (
              <figure
                key={p.name}
                className={`overflow-hidden rounded-2xl border border-white/15 bg-white/10 p-2 shadow-2xl shadow-black/30 backdrop-blur ${p.lift}`}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={p.src} alt={p.alt} className={`aspect-[4/5] w-full rounded-xl object-cover ${p.pos}`} />
                <figcaption className="px-2 pb-1 pt-3">
                  <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-white/55">{p.role}</p>
                  <p className="mt-0.5 font-semibold leading-tight">{p.name}</p>
                  {p.link && (
                    <a
                      href={p.link.href}
                      target="_blank"
                      rel="noopener"
                      className="mt-1.5 inline-flex items-center gap-1 rounded-full bg-white/15 px-2.5 py-0.5 text-[11px] font-medium text-sky-200 transition hover:bg-white/25"
                    >
                      {p.link.label} ↗
                    </a>
                  )}
                </figcaption>
              </figure>
            ))}
          </div>
        </div>

        <div className="relative grid grid-cols-2 border-t border-white/10 bg-black/20 backdrop-blur sm:grid-cols-4">
          {[
            ["3,633", "PubMed documents"],
            ["323", "held-out test queries"],
            ["6", "retrieval systems"],
            [formatMetric(ndcgMax, 3), "best nDCG@10"],
          ].map(([v, l], i) => (
            <div
              key={l}
              className={`px-5 py-5 sm:px-8 ${i % 2 ? "border-l" : ""} ${i >= 2 ? "border-t sm:border-t-0" : ""} ${i === 2 ? "sm:border-l" : ""} border-white/10`}
            >
              <p className="text-2xl font-bold tabular sm:text-3xl">{v}</p>
              <p className="mt-0.5 text-xs text-white/60 sm:text-sm">{l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Sticky section bar */}
      <nav
        aria-label="On this page"
        className="sticky top-[57px] z-30 -mx-4 -my-12 flex gap-1 overflow-x-auto border-y border-border bg-background/85 px-4 py-2 text-sm backdrop-blur sm:mx-0 sm:rounded-full sm:border sm:px-2"
      >
        {TOC.map(([id, label]) => (
          <a
            key={id}
            href={`#${id}`}
            className="whitespace-nowrap rounded-full px-3.5 py-1.5 font-medium text-text-secondary transition-colors hover:bg-accent-soft hover:text-accent"
          >
            {label}
          </a>
        ))}
      </nav>

      {/* ───────────── PRESENTATION ───────────── */}
      <Section
        id="presentation"
        n="01"
        eyebrow="Video presentations"
        title="Watch the project"
        intro="Two narrated videos present the same study in two ways: a structured research talk and an illustrated story. Pick one, then use the chapters to jump to any part."
      >
        <VideoStudio talks={TALKS} />
      </Section>

      <Section
        id="slides"
        n="02"
        eyebrow="Slide decks"
        title="Presentation slides"
        intro="Both decks used for the course. Click a thumbnail, use the arrows or ← / → keys, or go fullscreen to present. The original PowerPoint files can be downloaded."
      >
        <SlideViewer decks={DECKS} />
      </Section>

      <Section
        id="poster"
        n="03"
        eyebrow="Research poster"
        title="The project on one page"
        intro="Problem, dataset, methods, architecture, contributions and results in a single visual summary."
      >
        <a
          href="/course/infographic.jpg"
          target="_blank"
          rel="noreferrer"
          className="group relative block overflow-hidden rounded-2xl border border-border bg-white shadow-xl shadow-black/5"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/course/infographic.jpg"
            alt="Research poster: Biomedical Hybrid Information Retrieval — problem, dataset, retrieval methods, hybrid workflow, contributions, benchmark evaluation and key findings"
            loading="lazy"
            className="w-full transition duration-500 group-hover:scale-[1.01]"
          />
          <span className="absolute bottom-3 right-3 rounded-full bg-black/70 px-3 py-1 text-xs font-medium text-white backdrop-blur">
            Open full size ↗
          </span>
        </a>
        <p className="mt-3 text-sm text-text-muted">
          Authoritative numbers are in the <a href="#results" className="text-accent hover:underline">results table</a>.
        </p>
      </Section>

      {/* ───────────── STEPS ───────────── */}
      <Section
        id="steps"
        n="04"
        eyebrow="Step by step"
        title="How the project was built"
        intro="Nine stages, each a script in the repository that writes a versioned artifact — so every number here can be regenerated."
      >
        <ol className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {STEPS.map((s, i) => (
            <li
              key={s.title}
              className="group relative flex flex-col overflow-hidden rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-0.5 hover:border-accent/60 hover:shadow-lg hover:shadow-black/5"
            >
              <span
                aria-hidden
                className="pointer-events-none absolute -right-2 -top-5 select-none text-[96px] font-black leading-none text-text-primary/[0.05] tabular"
              >
                {i + 1}
              </span>
              <div className="flex items-center gap-2">
                <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-accent to-[#2563eb] text-xs font-bold text-white tabular">
                  {i + 1}
                </span>
                <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-muted">{s.phase}</span>
              </div>
              <h3 className="mt-3 text-lg font-semibold text-text-primary">{s.title}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-text-secondary">{s.what}</p>
              <ul className="mt-3 flex flex-wrap gap-1.5">
                {s.how.map((h) => (
                  <li key={h} className="rounded-full bg-surface-2 px-2.5 py-1 text-xs text-text-primary">
                    {h}
                  </li>
                ))}
              </ul>
              <div className="mt-auto pt-4">
                {s.cmd && (
                  <code className="block overflow-x-auto whitespace-nowrap rounded-lg bg-[#07122b] px-3 py-2 font-mono text-[11px] text-sky-200">
                    $ {s.cmd}
                  </code>
                )}
                <div className="mt-2 flex items-center justify-between gap-2 text-xs">
                  <span className="text-text-muted">→ {s.output}</span>
                  {s.link && (
                    <Link href={s.link.href} className="shrink-0 font-medium text-accent hover:underline">
                      {s.link.label} →
                    </Link>
                  )}
                </div>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      {/* ───────────── RESULTS ───────────── */}
      <Section
        id="results"
        n="05"
        eyebrow="Results"
        title="Benchmark on 323 test queries"
        intro="Six systems, same queries, same relevance judgments, same metrics. Highlighted cells are the best in each column."
      >
        <div className="overflow-hidden rounded-2xl border border-border bg-surface">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead className="bg-surface-2 text-left text-xs uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="px-5 py-3 font-semibold">Model</th>
                  {COLS.map((c) => (
                    <th key={c} className="px-4 py-3 text-right font-semibold">
                      {c}
                    </th>
                  ))}
                  <th className="px-5 py-3 text-right font-semibold">Latency</th>
                </tr>
              </thead>
              <tbody>
                {rows.map(({ id, m }) => (
                  <tr key={id} className="border-t border-border">
                    <td className="px-5 py-3 font-medium text-text-primary">
                      {MODEL_LABELS[id]}
                      <div className="mt-1.5 h-1 w-28 overflow-hidden rounded-full bg-surface-2">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-accent to-sky-400"
                          style={{ width: `${((m?.["nDCG@10"] ?? 0) / ndcgMax) * 100}%` }}
                        />
                      </div>
                    </td>
                    {COLS.map((c) => {
                      const v = m?.[c];
                      const isBest = v !== undefined && Math.abs(v - best(c)) < 1e-9;
                      return (
                        <td key={c} className="px-4 py-3 text-right tabular">
                          <span
                            className={
                              isBest
                                ? "rounded-md bg-accent-soft px-1.5 py-0.5 font-bold text-accent"
                                : "text-text-primary"
                            }
                          >
                            {formatMetric(v, 3)}
                          </span>
                        </td>
                      );
                    })}
                    <td className="px-5 py-3 text-right tabular text-text-secondary">
                      {latency[id] !== undefined
                        ? `${Number(latency[id]).toLocaleString(undefined, { maximumFractionDigits: 1 })} ms`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
        <p className="mt-3 text-sm text-text-muted">
          Bar under each model = nDCG@10 relative to the best. Reranker Recall@100 and MAP are capped by its 50-document
          pool. Full analysis: <Link href="/results" className="text-accent hover:underline">Results</Link> ·{" "}
          <Link href="/evaluation" className="text-accent hover:underline">Evaluation</Link>.
        </p>
      </Section>

      {/* ───────────── FINDINGS ───────────── */}
      <Section id="findings" n="06" eyebrow="Findings" title="What the research questions showed">
        <div className="grid gap-4 md:grid-cols-2">
          {FINDINGS.map((f) => (
            <div
              key={f.k}
              className="relative overflow-hidden rounded-2xl border border-border bg-surface p-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span
                    className={`rounded-md px-2 py-0.5 text-xs font-bold ${
                      f.tone === "good"
                        ? "bg-good/15 text-good"
                        : f.tone === "warn"
                          ? "bg-warn/15 text-warn"
                          : "bg-surface-2 text-text-secondary"
                    }`}
                  >
                    {f.k}
                  </span>
                  <h3 className="mt-2 text-lg font-semibold text-text-primary">{f.q}</h3>
                </div>
                <span className="shrink-0 text-2xl font-black tracking-tight text-text-primary/80 tabular">{f.big}</span>
              </div>
              <p className="mt-2 leading-relaxed text-text-secondary">{f.a}</p>
            </div>
          ))}
        </div>
        <blockquote className="relative mt-6 overflow-hidden rounded-2xl bg-[#07122b] p-7 text-white sm:p-9">
          <div
            className="absolute inset-0 opacity-80"
            style={{
              background:
                "radial-gradient(50% 90% at 0% 0%, rgba(37,99,235,.5) 0%, transparent 60%), radial-gradient(40% 80% at 100% 100%, rgba(204,0,0,.35) 0%, transparent 60%)",
            }}
          />
          <p className="relative text-xl font-semibold leading-relaxed sm:text-2xl">
            “Meaning-based retrieval closes the vocabulary gap between everyday questions and medical literature.
            Fusion and reranking must earn their computational cost.”
          </p>
          <p className="relative mt-3 text-sm text-white/60">— Project conclusion</p>
        </blockquote>
      </Section>

      {/* ───────────── FEEDBACK ───────────── */}
      <Section
        id="feedback"
        n="07"
        eyebrow="Instructor feedback"
        title="From course project to research paper"
      >
        <div className="grid gap-5 lg:grid-cols-[1.1fr_1fr]">
          <figure className="relative overflow-hidden rounded-2xl border border-border bg-surface p-6 sm:p-8">
            <span aria-hidden className="absolute -top-6 right-4 text-[120px] font-black leading-none text-accent/10">
              “
            </span>
            <blockquote className="relative text-xl font-medium leading-relaxed text-text-primary">
              This work is more than good enough for a course project.
            </blockquote>
            <p className="relative mt-3 leading-relaxed text-text-secondary">
              To develop it into a research paper, the suggested directions are more benchmark datasets, a validation
              study on hyperparameter tuning, a full comparison of fusion and single methods to learn when lexical–dense
              fusion helps, and stronger evaluation rigor with multiple-testing correction and confidence intervals.
            </p>
            <figcaption className="relative mt-5 flex items-center gap-3 border-t border-border pt-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/course/people/dingding.jpg" alt="" className="h-10 w-10 rounded-full object-cover object-top" />
              <span>
                <span className="block text-sm font-semibold text-text-primary">Dingding Wang</span>
                <span className="block text-xs text-text-muted">Course Instructor</span>
              </span>
            </figcaption>
          </figure>
          <div className="flex flex-col gap-3">
            {[
              ["More benchmarks", "NFCorpus + SciFact + TREC-COVID loaders"],
              ["Hyperparameter validation", "BM25, RRF, weighted-fusion and rerank-pool grids on dev"],
              ["Fusion vs. single methods", "4 single systems × 2 fusion pairs × 2 fusion rules"],
              ["Evaluation rigor", "Bootstrap 95% CIs + Holm-corrected randomization tests"],
            ].map(([t, d], i) => (
              <div key={t} className="flex items-start gap-4 rounded-2xl border border-border bg-surface p-4">
                <span className="bg-gradient-to-br from-accent to-[#cc0000] bg-clip-text text-2xl font-black leading-none text-transparent tabular">
                  0{i + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-text-primary">{t}</p>
                  <p className="text-sm text-text-secondary">{d}</p>
                  <span className="mt-2 inline-block rounded-full border border-warn/30 bg-warn/10 px-2 py-0.5 text-[11px] font-medium text-warn sm:hidden">
                    Code built · runs pending
                  </span>
                </div>
                <span className="hidden shrink-0 rounded-full border border-warn/30 bg-warn/10 px-2 py-0.5 text-[11px] font-medium text-warn sm:inline-block">
                  Code built · runs pending
                </span>
              </div>
            ))}
            <Link
              href="/roadmap"
              className="mt-1 rounded-xl bg-accent px-4 py-2.5 text-center text-sm font-semibold text-white hover:opacity-90"
            >
              Open the full research roadmap →
            </Link>
          </div>
        </div>
      </Section>

      {/* ───────────── DELIVERABLES ───────────── */}
      <Section id="deliverables" n="08" eyebrow="Deliverables" title="Everything submitted">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { t: "Video 1 · Main presentation", d: "MP4 · 9:50", href: TALKS[0].src, icon: "▶" },
            { t: "Video 2 · Illustrated explainer", d: "MP4 · 9:08", href: TALKS[1].src, icon: "▶" },
            { t: "Final presentation deck", d: "PowerPoint · 15 slides", href: DECKS[0].pptx, icon: "▤" },
            { t: "Bridging the Search Gap deck", d: "PowerPoint · 13 slides", href: DECKS[1].pptx, icon: "▤" },
            { t: "Research poster", d: "Full-resolution image", href: "/course/infographic.jpg", icon: "◧" },
            { t: "Research paper", d: "Abstract → conclusion", href: "/paper", icon: "¶" },
            { t: "Source code & tests", d: "GitHub repository", href: REPO, icon: "{ }" },
            { t: "Live research portal", d: "Results, models, demo", href: "/", icon: "◎" },
          ].map((x) => (
            <a
              key={x.t}
              href={x.href}
              {...(x.href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
              className="group flex items-start gap-3 rounded-2xl border border-border bg-surface p-4 transition hover:-translate-y-0.5 hover:border-accent/60 hover:shadow-lg hover:shadow-black/5"
            >
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent-soft text-sm font-bold text-accent">
                {x.icon}
              </span>
              <span>
                <span className="block font-medium leading-snug text-text-primary">{x.t}</span>
                <span className="mt-0.5 block text-sm text-text-secondary">{x.d}</span>
              </span>
            </a>
          ))}
        </div>

        <div className="mt-6 grid gap-4 rounded-2xl border border-border bg-surface p-6 sm:grid-cols-3">
          {[
            ["Course", "CAP 6776 — Information Retrieval, Florida Atlantic University"],
            ["Student", "Arun Kumar Gharami", AUTHOR.website],
            ["Instructor", "Dingding Wang"],
            ["Dataset", "BEIR / NFCorpus"],
            ["Models", "TF-IDF, BM25, BGE-base, MedCPT (query, article, cross-encoder)"],
            ["Code", "github.com/Arungharami/biomedical-hybrid-ir", "https://github.com/Arungharami/biomedical-hybrid-ir"],
          ].map(([k, v, href]) => (
            <div key={k}>
              <p className="text-xs uppercase tracking-wider text-text-muted">{k}</p>
              {href ? (
                <a
                  href={href}
                  target="_blank"
                  rel="noopener"
                  className="mt-0.5 inline-block text-sm font-medium text-accent hover:underline"
                >
                  {v} ↗
                </a>
              ) : (
                <p className="mt-0.5 text-sm font-medium text-text-primary">{v}</p>
              )}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
