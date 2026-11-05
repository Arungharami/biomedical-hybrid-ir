import type { Metadata } from "next";
import Link from "next/link";
import SlideViewer, { type Deck } from "@/components/SlideViewer";
import VideoChapters, { type Chapter } from "@/components/VideoChapters";
import { MODEL_LABELS, MODEL_ORDER, efficiency, formatMetric, metrics } from "@/lib/data";

export const metadata: Metadata = {
  title: "Course Project",
  description:
    "CAP 6776 Information Retrieval course project at Florida Atlantic University — video presentation, slide decks, poster, and the full step-by-step build of a hybrid biomedical retrieval system.",
};

const REPO = "https://github.com/Arungharami/biomedical-hybrid-ir";

const DECKS: Deck[] = [
  {
    id: "fau",
    title: "Final presentation",
    subtitle:
      "Biomedical Hybrid Information Retrieval — the FAU class presentation: problem, research questions, architecture, results and error analysis.",
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

const CHAPTERS: Chapter[] = [
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
];

type Step = {
  n: number;
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
    n: 1,
    phase: "Define",
    title: "Frame the problem and research questions",
    what:
      "Lay users search in plain words (“canker sores”, “Fosamax”) while PubMed papers use clinical vocabulary (“recurrent aphthous ulcers”, “bisphosphonate”). Keyword search can return nothing at all.",
    how: [
      "RQ1 — Does dense retrieval beat BM25 on vocabulary mismatch?",
      "RQ2 — Does biomedical training (MedCPT) beat a general model (BGE)?",
      "RQ3 — Do fusion and cross-encoder reranking justify their extra cost?",
    ],
    output: "Research questions + evaluation protocol fixed before any experiment ran.",
    link: { href: "/paper", label: "Read the paper" },
  },
  {
    n: 2,
    phase: "Data",
    title: "Download and audit NFCorpus",
    what:
      "Pull BEIR/NFCorpus and its qrels straight from the Hugging Face Hub and verify every count rather than trusting documentation.",
    how: [
      "3,633 PubMed documents · 3,237 lay-language queries",
      "323 held-out test queries — the only source of reported metrics",
      "Graded relevance 0 / 1 / 2; 0 duplicates, 0 missing qrels, 0 split overlap",
    ],
    cmd: "python scripts/audit_dataset.py",
    output: "data/processed/dataset_stats.json",
    link: { href: "/dataset", label: "Dataset page" },
  },
  {
    n: 3,
    phase: "Lexical",
    title: "Build the classical baselines: TF-IDF and BM25",
    what:
      "Implement exact-term retrieval. BM25 is written from scratch with frozen textbook defaults so no test-set tuning can leak in.",
    how: [
      "TF-IDF: sublinear TF, L2 norm, cosine similarity",
      "BM25: k1 = 1.2, b = 0.75, Robertson/Sparck-Jones IDF, inverted index",
      "Each retrieves its top 100 candidates per query",
    ],
    cmd: "python scripts/run_tfidf.py && python scripts/run_bm25.py",
    output: "results/runs/ · results/metrics/ · results/manifests/",
  },
  {
    n: 4,
    phase: "Dense",
    title: "Add dense retrievers: BGE and MedCPT",
    what:
      "Encode queries and abstracts into vectors so meaning can match even when words don’t, and compare a general model with a biomedical one.",
    how: [
      "BAAI/bge-base-en-v1.5 — general-purpose, CLS pooling, normalized",
      "ncbi/MedCPT Query + Article encoders — trained on PubMed search logs",
      "768-d vectors, exact inner-product search with FAISS",
    ],
    cmd: "python scripts/run_bge.py && python scripts/run_medcpt.py",
    output: "FAISS indices + ranked runs for both dense models",
    link: { href: "/models", label: "Model details" },
  },
  {
    n: 5,
    phase: "Fuse",
    title: "Hybrid retrieval with Reciprocal Rank Fusion",
    what:
      "BM25 scores (≈5–15) and MedCPT inner products (≈55–65) live on incompatible scales, so the hybrid merges ranks, not scores.",
    how: [
      "RRF(d) = Σ 1 / (60 + rankᵢ(d)) over the BM25 and MedCPT lists",
      "k = 60 (standard) — agreement between retrievers beats a single first place",
      "Adds only ~2 ms over the individual retrievers",
    ],
    cmd: "python scripts/run_hybrid.py",
    output: "Hybrid BM25 + MedCPT run",
    link: { href: "/pipeline", label: "Pipeline diagram" },
  },
  {
    n: 6,
    phase: "Rerank",
    title: "Rerank the top 50 with the MedCPT cross-encoder",
    what:
      "A cross-encoder reads the query and the article together so every query word attends to every article word — far more accurate, far slower.",
    how: [
      "ncbi/MedCPT-Cross-Encoder on the top 50 RRF candidates",
      "50 full transformer passes per query",
      "Final top-10 list returned to the user",
    ],
    cmd: "python scripts/run_reranker.py",
    output: "Highest nDCG@10 of all six systems (0.373)",
  },
  {
    n: 7,
    phase: "Evaluate",
    title: "Evaluate all six systems the same way",
    what:
      "Score every run with TREC-standard pytrec_eval, cross-checked against hand-written metric implementations, then test significance.",
    how: [
      "P@10, Recall@100, MAP, MRR@10, nDCG@10 (+ more cutoffs)",
      "Paired bootstrap with 10,000 resamples on per-query scores",
      "Mean latency per query measured on an Apple M1 Pro",
    ],
    cmd: "python scripts/evaluate_all.py && python scripts/generate_figures.py",
    output: "Main results table, significance tests, 7 figures",
    link: { href: "/evaluation", label: "Statistical analysis" },
  },
  {
    n: 8,
    phase: "Diagnose",
    title: "Error analysis: who rescues whom?",
    what:
      "Go query by query to see where each method fails, instead of stopping at averages.",
    how: [
      "MedCPT finds a relevant doc in the top 10 where BM25 fails: 244 queries",
      "BM25 wins where MedCPT drifts (e.g. “salmon” → generic seafood): 52 queries",
      "Reranker moved 926 relevant docs up but 832 down — a near coin-flip",
    ],
    cmd: "python scripts/error_analysis.py",
    output: "results/error-analysis/",
    link: { href: "/error-analysis", label: "Error analysis" },
  },
  {
    n: 9,
    phase: "Ship",
    title: "Make it reproducible and public",
    what:
      "Package everything as a tested Python library, export results to this web portal, and record the presentation.",
    how: [
      "src/biomedical_ir library + thin CLI scripts + pytest suite in CI",
      "Every experiment logged with a manifest (config, versions, timing)",
      "Next.js research portal on Vercel, two slide decks, recorded talk",
    ],
    cmd: "python scripts/export_web_results.py",
    output: "This website + GitHub repository",
    link: { href: "/reproducibility", label: "Reproduce it" },
  },
];

const FINDINGS = [
  {
    k: "RQ1",
    q: "Dense vs. lexical",
    a: "Yes. Both BGE and MedCPT beat BM25 on all five primary metrics (p < 0.005). Dense retrieval is the big step.",
    tone: "good",
  },
  {
    k: "RQ2",
    q: "Biomedical vs. general",
    a: "No measurable gain. BGE and MedCPT are statistically tied (all p ≥ 0.12) on this corpus.",
    tone: "neutral",
  },
  {
    k: "RQ3",
    q: "Is fusion + reranking worth it?",
    a: "Best nDCG@10 (0.373), but the +0.011 gain over hybrid is not significant (p = 0.19) and costs ~1,946 ms vs 4.1 ms — about 480× slower.",
    tone: "warn",
  },
  {
    k: "Surprise",
    q: "Untuned TF-IDF beat BM25",
    a: "On short PubMed abstracts, TF-IDF edged out default BM25 on nDCG@10 (p = 0.03).",
    tone: "neutral",
  },
];

function Section({
  id,
  eyebrow,
  title,
  intro,
  children,
}: {
  id: string;
  eyebrow: string;
  title: string;
  intro?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-accent">{eyebrow}</p>
      <h2 className="text-2xl font-bold tracking-tight text-text-primary">{title}</h2>
      {intro && <p className="mt-2 max-w-3xl text-text-secondary leading-relaxed">{intro}</p>}
      <div className="mt-6">{children}</div>
    </section>
  );
}

const TOC = [
  ["video", "Video"],
  ["slides", "Slides"],
  ["poster", "Poster"],
  ["steps", "Step-by-step"],
  ["results", "Results"],
  ["findings", "Findings"],
  ["deliverables", "Deliverables"],
] as const;

export default function CoursePage() {
  const latency = Object.fromEntries(efficiency.map((e) => [e.model, e.latency_ms_per_query ?? undefined]));
  const rows = MODEL_ORDER.map((id) => ({ id, m: metrics[id]?.metrics }));
  const best = (key: string) =>
    Math.max(...rows.map((r) => (r.m ? (r.m as Record<string, number>)[key] ?? 0 : 0)));
  const COLS = ["P@10", "Recall@100", "MAP", "MRR@10", "nDCG@10"];

  return (
    <div className="flex flex-col gap-16">
      {/* HERO */}
      <section className="relative overflow-hidden rounded-2xl border border-border bg-surface">
        <div
          className="absolute inset-x-0 top-0 h-1.5"
          style={{ background: "linear-gradient(90deg,#003366 0%,#003366 60%,#cc0000 60%,#cc0000 100%)" }}
        />
        <div className="grid gap-8 p-6 sm:p-10 lg:grid-cols-[1.4fr_1fr] lg:items-center">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent">
              Florida Atlantic University · CAP 6776 Information Retrieval · Course Project
            </p>
            <h1 className="mt-3 text-3xl font-bold leading-tight tracking-tight text-text-primary sm:text-4xl">
              Biomedical Hybrid Information Retrieval
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-text-secondary">
              Combining lexical relevance (BM25), semantic understanding (MedCPT), Reciprocal Rank
              Fusion and cross-encoder reranking to find the science behind everyday health
              questions — evaluated honestly on the NFCorpus benchmark.
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a
                href="#video"
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
              >
                ▶ Watch the presentation
              </a>
              <a
                href="#slides"
                className="rounded-md border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2"
              >
                View slides
              </a>
              <a
                href={REPO}
                target="_blank"
                rel="noreferrer"
                className="rounded-md border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2"
              >
                Source code ↗
              </a>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <figure className="overflow-hidden rounded-xl border border-border bg-surface-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/course/people/arun.jpg"
                alt="Arun Kumar Gharami presenting at Florida Atlantic University"
                className="aspect-[4/5] w-full object-cover object-[50%_30%]"
              />
              <figcaption className="p-3">
                <p className="text-xs uppercase tracking-wider text-text-muted">Student · Presenter</p>
                <p className="mt-0.5 font-semibold text-text-primary">Arun Kumar Gharami</p>
              </figcaption>
            </figure>
            <figure className="overflow-hidden rounded-xl border border-border bg-surface-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/course/people/dingding.jpg"
                alt="Dingding Wang, course instructor"
                className="aspect-[4/5] w-full object-cover object-top"
              />
              <figcaption className="p-3">
                <p className="text-xs uppercase tracking-wider text-text-muted">Course Instructor</p>
                <p className="mt-0.5 font-semibold text-text-primary">Dingding Wang</p>
              </figcaption>
            </figure>
          </div>
        </div>

        <nav className="flex gap-1 overflow-x-auto border-t border-border bg-surface-2 px-4 py-2 text-sm sm:px-8">
          {TOC.map(([id, label]) => (
            <a
              key={id}
              href={`#${id}`}
              className="whitespace-nowrap rounded-md px-3 py-1.5 text-text-secondary hover:bg-surface hover:text-text-primary"
            >
              {label}
            </a>
          ))}
        </nav>
      </section>

      {/* AT A GLANCE */}
      <section className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[
          ["3,633", "PubMed documents"],
          ["323", "held-out test queries"],
          ["6", "retrieval systems compared"],
          ["0.373", "best nDCG@10 (hybrid + reranker)"],
        ].map(([v, l]) => (
          <div key={l} className="rounded-lg border border-border bg-surface p-4">
            <p className="text-2xl font-bold tabular text-text-primary">{v}</p>
            <p className="mt-1 text-sm text-text-secondary">{l}</p>
          </div>
        ))}
      </section>

      <Section
        id="video"
        eyebrow="01 · Video presentation"
        title="CAP 6776: Hybrid Search — recorded talk"
        intro="A 10-minute walkthrough of the whole project, from the vocabulary-mismatch problem to the final results and limitations. Use the chapter list to jump to any part."
      >
        <VideoChapters
          src="/course/CAP6776_Hybrid_Search.mp4"
          poster="/course/video-poster.jpg"
          chapters={CHAPTERS}
        />
        <p className="mt-3 text-sm text-text-muted">
          9 min 50 s · 720p ·{" "}
          <a href="/course/CAP6776_Hybrid_Search.mp4" download className="text-accent hover:underline">
            download MP4 (26 MB)
          </a>
        </p>
      </Section>

      <Section
        id="slides"
        eyebrow="02 · Slide decks"
        title="Presentation slides"
        intro="Both decks used for the course, viewable right here. Click a thumbnail, use the arrows, or focus the slide and press ← / →. Original PowerPoint files are available to download."
      >
        <SlideViewer decks={DECKS} />
      </Section>

      <Section
        id="poster"
        eyebrow="03 · Research poster"
        title="Project at a glance"
        intro="A one-page visual summary of the problem, dataset, methods, architecture, contributions and benchmark results."
      >
        <a
          href="/course/infographic.jpg"
          target="_blank"
          rel="noreferrer"
          className="block overflow-hidden rounded-xl border border-border bg-white transition hover:border-accent"
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/course/infographic.jpg"
            alt="Research poster: Biomedical Hybrid Information Retrieval — problem, dataset, retrieval methods, hybrid workflow, contributions, benchmark evaluation and key findings"
            loading="lazy"
            className="w-full"
          />
        </a>
        <p className="mt-2 text-sm text-text-muted">
          Click to open full size. The authoritative numbers are in the{" "}
          <a href="#results" className="text-accent hover:underline">results table</a> below.
        </p>
      </Section>

      <Section
        id="steps"
        eyebrow="04 · How it was built"
        title="Step-by-step: the complete work"
        intro="The project was built in nine stages. Each stage is a script in the repository that writes a versioned artifact, so every number on this site can be regenerated."
      >
        <ol className="relative flex flex-col gap-5 border-l-2 border-border pl-6 sm:pl-8">
          {STEPS.map((s) => (
            <li key={s.n} className="relative">
              <span className="absolute -left-[39px] top-4 flex h-8 w-8 items-center justify-center rounded-full border-2 border-accent bg-surface text-sm font-bold text-accent sm:-left-[47px]">
                {s.n}
              </span>
              <div className="rounded-xl border border-border bg-surface p-5">
                <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Step {s.n} · {s.phase}
                </p>
                <h3 className="mt-1 text-lg font-semibold text-text-primary">{s.title}</h3>
                <p className="mt-2 text-text-secondary leading-relaxed">{s.what}</p>
                <ul className="mt-3 flex flex-col gap-1.5 text-sm text-text-primary">
                  {s.how.map((h) => (
                    <li key={h} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                      <span>{h}</span>
                    </li>
                  ))}
                </ul>
                <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  {s.cmd ? (
                    <code className="overflow-x-auto whitespace-nowrap rounded-md bg-surface-2 px-3 py-1.5 font-mono text-xs text-text-primary">
                      $ {s.cmd}
                    </code>
                  ) : (
                    <span />
                  )}
                  {s.link && (
                    <Link href={s.link.href} className="shrink-0 text-sm text-accent hover:underline">
                      {s.link.label} →
                    </Link>
                  )}
                </div>
                <p className="mt-2 text-xs text-text-muted">
                  <span className="font-semibold">Output:</span> {s.output}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </Section>

      <Section
        id="results"
        eyebrow="05 · Results"
        title="Benchmark results on 323 test queries"
        intro="All six systems, same queries, same qrels, same metrics. Bold marks the best value in each column."
      >
        <div className="overflow-x-auto rounded-xl border border-border bg-surface">
          <table className="w-full min-w-[640px] text-sm">
            <thead className="border-b border-border bg-surface-2 text-left text-text-secondary">
              <tr>
                <th className="px-4 py-2.5 font-medium">Model</th>
                {COLS.map((c) => (
                  <th key={c} className="px-4 py-2.5 text-right font-medium">
                    {c}
                  </th>
                ))}
                <th className="px-4 py-2.5 text-right font-medium">Latency / query</th>
              </tr>
            </thead>
            <tbody>
              {rows.map(({ id, m }) => (
                <tr key={id} className="border-b border-border last:border-0">
                  <td className="px-4 py-2.5 font-medium text-text-primary">{MODEL_LABELS[id]}</td>
                  {COLS.map((c) => {
                    const v = m ? (m as Record<string, number>)[c] : undefined;
                    const isBest = v !== undefined && Math.abs(v - best(c)) < 1e-9;
                    return (
                      <td
                        key={c}
                        className={`px-4 py-2.5 text-right tabular ${
                          isBest ? "font-bold text-accent" : "text-text-primary"
                        }`}
                      >
                        {formatMetric(v, 3)}
                      </td>
                    );
                  })}
                  <td className="px-4 py-2.5 text-right tabular text-text-secondary">
                    {latency[id] !== undefined
                      ? `${Number(latency[id]).toLocaleString(undefined, { maximumFractionDigits: 1 })} ms`
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-sm text-text-muted">
          Reranker Recall@100 and MAP are capped because it only reorders a 50-document pool. Full
          tables, charts and significance tests are on the{" "}
          <Link href="/results" className="text-accent hover:underline">Results</Link> and{" "}
          <Link href="/evaluation" className="text-accent hover:underline">Evaluation</Link> pages.
        </p>
      </Section>

      <Section id="findings" eyebrow="06 · Findings" title="What the research questions showed">
        <div className="grid gap-4 md:grid-cols-2">
          {FINDINGS.map((f) => (
            <div key={f.k} className="rounded-xl border border-border bg-surface p-5">
              <div className="flex items-center gap-2">
                <span
                  className={`rounded px-2 py-0.5 text-xs font-bold ${
                    f.tone === "good"
                      ? "bg-good/15 text-good"
                      : f.tone === "warn"
                        ? "bg-warn/15 text-warn"
                        : "bg-surface-2 text-text-secondary"
                  }`}
                >
                  {f.k}
                </span>
                <h3 className="font-semibold text-text-primary">{f.q}</h3>
              </div>
              <p className="mt-2 text-text-secondary leading-relaxed">{f.a}</p>
            </div>
          ))}
        </div>
        <blockquote className="mt-6 rounded-xl border-l-4 border-accent bg-accent-soft p-5 text-lg leading-relaxed text-text-primary">
          Meaning-based retrieval closes the vocabulary gap between everyday questions and medical
          literature, while lexical precision stays a valuable fallback. Fusion and reranking must
          earn their computational cost.
        </blockquote>
      </Section>

      <Section
        id="deliverables"
        eyebrow="07 · Deliverables"
        title="Everything submitted for the course"
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { t: "Recorded presentation", d: "MP4 · 9 min 50 s", href: "/course/CAP6776_Hybrid_Search.mp4" },
            { t: "Final presentation deck", d: "PowerPoint · 15 slides", href: DECKS[0].pptx },
            { t: "Bridging the Search Gap deck", d: "PowerPoint · 13 slides", href: DECKS[1].pptx },
            { t: "Research poster", d: "Image · full resolution", href: "/course/infographic.jpg" },
            { t: "Research paper", d: "Abstract → conclusion, online", href: "/paper" },
            { t: "Source code & tests", d: "GitHub repository", href: REPO },
          ].map((x) => (
            <a
              key={x.t}
              href={x.href}
              {...(x.href.startsWith("http") ? { target: "_blank", rel: "noreferrer" } : {})}
              className="rounded-lg border border-border bg-surface p-4 transition-colors hover:border-accent hover:bg-surface-2"
            >
              <p className="font-medium text-text-primary">{x.t}</p>
              <p className="mt-1 text-sm text-text-secondary">{x.d}</p>
            </a>
          ))}
        </div>
        <div className="mt-6 rounded-xl border border-border bg-surface p-5 text-sm text-text-secondary">
          <p>
            <span className="font-semibold text-text-primary">Course:</span> CAP 6776 — Information
            Retrieval, Florida Atlantic University
          </p>
          <p className="mt-1">
            <span className="font-semibold text-text-primary">Student:</span> Arun Kumar Gharami ·{" "}
            <span className="font-semibold text-text-primary">Instructor:</span> Dingding Wang
          </p>
          <p className="mt-1">
            <span className="font-semibold text-text-primary">Dataset:</span> BEIR / NFCorpus ·{" "}
            <span className="font-semibold text-text-primary">Models:</span> TF-IDF, BM25,
            BAAI/bge-base-en-v1.5, ncbi/MedCPT (query, article, cross-encoder)
          </p>
        </div>
      </Section>
    </div>
  );
}
