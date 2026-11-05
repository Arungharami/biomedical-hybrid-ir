import Link from "next/link";
import StatusBadge from "@/components/StatusBadge";
import { AUTHOR } from "@/lib/author";
import { comparison, dataset, formatMetric, metrics, researchStatus } from "@/lib/data";

const EXPLORE = [
  { href: "/dataset", label: "Dataset", desc: "NFCorpus schema, stats, provenance", icon: "▦" },
  { href: "/pipeline", label: "Pipeline", desc: "The full retrieval architecture", icon: "⇉" },
  { href: "/models", label: "Models", desc: "TF-IDF, BM25, BGE, MedCPT, RRF, cross-encoder", icon: "◈" },
  { href: "/experiments", label: "Experiments", desc: "Real manifests for every run", icon: "⚗" },
  { href: "/evaluation", label: "Evaluation", desc: "MAP, MRR, nDCG, P, R, significance", icon: "∑" },
  { href: "/error-analysis", label: "Error Analysis", desc: "Query-level wins and losses", icon: "⚑" },
  { href: "/efficiency", label: "Efficiency", desc: "Latency and index-size trade-offs", icon: "⏱" },
  { href: "/search", label: "Search Demo", desc: "Precomputed retrieval examples", icon: "⌕" },
];

const ROADMAP = [
  "More benchmark datasets",
  "Hyperparameter validation study",
  "Fusion vs. single methods",
  "Multiple-testing correction & CIs",
];

function Stage({ title, sub, tone = "base" }: { title: string; sub: string; tone?: "base" | "hot" | "end" }) {
  const cls =
    tone === "hot"
      ? "border-[#ff6b6b]/60 bg-[#cc0000]/20"
      : tone === "end"
        ? "border-sky-300/50 bg-sky-400/20"
        : "border-white/15 bg-white/10";
  return (
    <div className={`rounded-xl border px-3 py-2.5 backdrop-blur ${cls}`}>
      <p className="text-sm font-semibold leading-tight">{title}</p>
      <p className="mt-0.5 text-[11px] text-white/60">{sub}</p>
    </div>
  );
}

export default function Home() {
  const bm25vsBge = comparison.statistical_tests.comparisons.find(
    (c) => c.model_a === "BM25" && c.model_b === "BGE" && c.metric === "nDCG@10"
  );
  const best = metrics.hybrid_reranked?.metrics["nDCG@10"];
  const bm25 = metrics.bm25?.metrics["nDCG@10"];
  const done = researchStatus.filter((r) => r.status === "complete").length;

  return (
    <div className="flex flex-col gap-20">
      {/* HERO */}
      <section className="relative -mx-4 -mt-8 overflow-hidden text-white sm:mx-0 sm:mt-0 sm:rounded-3xl">
        <div className="absolute inset-0 bg-[#07122b]" />
        <div
          className="absolute inset-0"
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
        <div className="relative grid gap-10 px-5 py-12 sm:px-10 sm:py-16 lg:grid-cols-[1.25fr_1fr] lg:items-center">
          <div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
                CAP 6776 · Information Retrieval
              </span>
              <span className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-xs font-medium backdrop-blur">
                Florida Atlantic University
              </span>
            </div>
            <h1 className="mt-5 text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-[3.6rem]">
              Finding the science behind{" "}
              <span className="bg-gradient-to-r from-sky-300 via-blue-200 to-white bg-clip-text text-transparent">
                everyday health questions
              </span>
            </h1>
            <p className="mt-5 max-w-xl text-lg leading-relaxed text-white/75">
              A reproducible study of six retrieval systems on NFCorpus — from TF-IDF and BM25 to BGE, MedCPT, hybrid
              Reciprocal Rank Fusion and biomedical cross-encoder reranking — with paired significance testing.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link
                href="/course"
                className="rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-[#07122b] shadow-lg shadow-black/20 transition hover:bg-sky-50"
              >
                ▶ Course presentation
              </Link>
              <Link
                href="/results"
                className="rounded-xl border border-white/25 bg-white/10 px-5 py-2.5 text-sm font-semibold backdrop-blur transition hover:bg-white/20"
              >
                View results
              </Link>
              <Link
                href="/roadmap"
                className="rounded-xl border border-white/25 bg-white/10 px-5 py-2.5 text-sm font-semibold backdrop-blur transition hover:bg-white/20"
              >
                Research roadmap
              </Link>
            </div>
            <a
              href={AUTHOR.website}
              target="_blank"
              rel="noopener"
              className="group mt-7 inline-flex items-center gap-3 rounded-full border border-white/15 bg-white/5 py-1.5 pl-1.5 pr-4 backdrop-blur transition hover:bg-white/10"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={AUTHOR.photo} alt="" className="h-8 w-8 rounded-full object-cover object-[50%_25%]" />
              <span className="text-sm leading-tight">
                <span className="block text-white/60">Built by</span>
                <span className="block font-semibold">
                  {AUTHOR.name} <span className="font-normal text-sky-300 group-hover:underline">· {AUTHOR.websiteLabel} ↗</span>
                </span>
              </span>
            </a>
          </div>

          {/* Pipeline visual */}
          <div className="rounded-2xl border border-white/15 bg-white/5 p-4 shadow-2xl shadow-black/30 backdrop-blur sm:p-5">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-white/50">Hybrid pipeline</p>
            <div className="mt-3 flex flex-col gap-2">
              <Stage title="“canker sores”" sub="plain-language question" />
              <div className="grid grid-cols-2 gap-2">
                <Stage title="BM25" sub="exact words · top 100" />
                <Stage title="MedCPT" sub="768-d meaning · top 100" />
              </div>
              <Stage title="Reciprocal Rank Fusion" sub="Σ 1 / (60 + rank)" />
              <Stage title="MedCPT cross-encoder" sub="re-reads the top 50" tone="hot" />
              <Stage title="“recurrent aphthous ulcers…”" sub="top-10 PubMed articles" tone="end" />
            </div>
          </div>
        </div>

        <div className="relative grid grid-cols-2 border-t border-white/10 bg-black/20 backdrop-blur sm:grid-cols-4">
          {[
            [dataset.corpus_size.toLocaleString(), "PubMed documents"],
            [String(dataset.qrel_counts.test), "held-out test queries"],
            ["6", "retrieval systems"],
            [formatMetric(best, 3), "best nDCG@10"],
          ].map(([v, l], i) => (
            <div
              key={l}
              className={`border-white/10 px-5 py-5 sm:px-8 ${i % 2 ? "border-l" : ""} ${i >= 2 ? "border-t sm:border-t-0" : ""} ${i === 2 ? "sm:border-l" : ""}`}
            >
              <p className="text-2xl font-bold tabular sm:text-3xl">{v}</p>
              <p className="mt-0.5 text-xs text-white/60 sm:text-sm">{l}</p>
            </div>
          ))}
        </div>
      </section>

      {/* COURSE FEATURE */}
      <section className="grid gap-5 lg:grid-cols-[1.3fr_1fr]">
        <Link
          href="/course"
          className="group relative overflow-hidden rounded-3xl border border-border bg-surface p-6 transition hover:border-accent/60 hover:shadow-xl hover:shadow-black/5 sm:p-8"
        >
          <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">Course project</p>
          <h2 className="mt-2 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
            Two videos, two slide decks, one complete story
          </h2>
          <p className="mt-3 max-w-xl leading-relaxed text-text-secondary">
            Watch the recorded presentation and the illustrated explainer, flip through both decks, and follow all nine
            build stages from problem to live portal.
          </p>
          <div className="mt-6 flex items-center gap-4">
            <div className="flex -space-x-3">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/course/people/arun.jpg" alt="Arun Kumar Gharami" className="h-12 w-12 rounded-full border-2 border-surface object-cover object-[50%_25%]" />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/course/people/dingding.jpg" alt="Dingding Wang" className="h-12 w-12 rounded-full border-2 border-surface object-cover object-top" />
            </div>
            <div className="text-sm">
              <p className="font-medium text-text-primary">Arun Kumar Gharami</p>
              <p className="text-text-muted">Instructor: Dingding Wang</p>
            </div>
            <span className="ml-auto hidden rounded-full bg-accent px-4 py-2 text-sm font-medium text-white transition group-hover:opacity-90 sm:inline-block">
              Open →
            </span>
          </div>
        </Link>
        <div className="grid grid-cols-2 gap-3">
          {[
            { src: "/course/video-poster.jpg", t: "Main presentation", d: "9:50" },
            { src: "/course/video2-poster.jpg", t: "Illustrated explainer", d: "9:08" },
            { src: "/course/slides/fau/09.jpg", t: "Final deck", d: "15 slides" },
            { src: "/course/slides/gap/01.jpg", t: "Search Gap deck", d: "13 slides" },
          ].map((m) => (
            <Link key={m.t} href="/course" className="group overflow-hidden rounded-2xl border border-border bg-surface">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={m.src} alt="" loading="lazy" className="aspect-video w-full object-cover transition duration-500 group-hover:scale-105" />
              <div className="flex items-center justify-between gap-2 px-3 py-2">
                <span className="truncate text-xs font-medium text-text-primary">{m.t}</span>
                <span className="shrink-0 text-[11px] text-text-muted tabular">{m.d}</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* FINDINGS */}
      <section>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">Headline findings</p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">What the study found</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          <div className="rounded-2xl border border-border bg-surface p-6">
            <p className="text-3xl font-black text-good tabular">
              {bm25vsBge
                ? bm25vsBge.p_value < 0.0001
                  ? "p < 0.0001"
                  : `p = ${formatMetric(bm25vsBge.p_value, 4)}`
                : "p < 0.005"}
            </p>
            <p className="mt-2 font-semibold text-text-primary">Dense beats lexical</p>
            <p className="mt-1 text-sm leading-relaxed text-text-secondary">
              Both BGE and MedCPT significantly outperform BM25 on every primary metric — the study’s most robust result.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-surface p-6">
            <p className="text-3xl font-black text-text-primary tabular">≈</p>
            <p className="mt-2 font-semibold text-text-primary">General ≈ biomedical</p>
            <p className="mt-1 text-sm leading-relaxed text-text-secondary">
              Domain-trained MedCPT did not significantly outperform the general-purpose BGE embedding model.
            </p>
          </div>
          <div className="rounded-2xl border border-border bg-surface p-6">
            <p className="text-3xl font-black text-warn tabular">480×</p>
            <p className="mt-2 font-semibold text-text-primary">Reranking is costly</p>
            <p className="mt-1 text-sm leading-relaxed text-text-secondary">
              Best nDCG@10 ({formatMetric(best, 3)} vs. BM25 {formatMetric(bm25, 3)}), but not significant over hybrid
              RRF and far slower per query.
            </p>
          </div>
        </div>
        <Link href="/evaluation" className="mt-4 inline-block text-sm font-medium text-accent hover:underline">
          Full statistical analysis →
        </Link>
      </section>

      {/* ROADMAP TEASER */}
      <section className="relative overflow-hidden rounded-3xl bg-[#07122b] p-6 text-white sm:p-10">
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(50% 90% at 0% 0%, rgba(37,99,235,.5) 0%, transparent 60%), radial-gradient(40% 80% at 100% 100%, rgba(204,0,0,.35) 0%, transparent 60%)",
          }}
        />
        <div className="relative grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">Next: research paper</p>
            <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
              When does lexical–dense fusion improve biomedical retrieval?
            </h2>
            <p className="mt-3 leading-relaxed text-white/70">
              Following the instructor’s feedback, the code for a multi-benchmark, validated and statistically corrected
              study is built. The experiments are next.
            </p>
            <Link
              href="/roadmap"
              className="mt-6 inline-block rounded-xl bg-white px-5 py-2.5 text-sm font-semibold text-[#07122b] transition hover:bg-sky-50"
            >
              See the roadmap →
            </Link>
          </div>
          <ol className="grid gap-2 sm:grid-cols-2">
            {ROADMAP.map((r, i) => (
              <li key={r} className="rounded-2xl border border-white/15 bg-white/10 p-4 backdrop-blur">
                <span className="text-xs font-bold text-sky-300 tabular">0{i + 1}</span>
                <p className="mt-1 font-semibold leading-snug">{r}</p>
                <p className="mt-2 flex gap-1.5 text-[11px]">
                  <span className="rounded-full bg-emerald-400/20 px-2 py-0.5 text-emerald-200">code built</span>
                  <span className="rounded-full bg-amber-400/20 px-2 py-0.5 text-amber-200">runs pending</span>
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* EXPLORE */}
      <section>
        <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">Explore the study</p>
        <h2 className="mt-1 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">Every part, in detail</h2>
        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {EXPLORE.map((s) => (
            <Link
              key={s.href}
              href={s.href}
              className="group rounded-2xl border border-border bg-surface p-5 transition hover:-translate-y-0.5 hover:border-accent/60 hover:shadow-lg hover:shadow-black/5"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-soft text-lg text-accent">
                {s.icon}
              </span>
              <p className="mt-3 font-semibold text-text-primary">{s.label}</p>
              <p className="mt-1 text-sm text-text-secondary">{s.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* MILESTONES */}
      <section>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">Progress</p>
            <h2 className="mt-1 text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">Milestones</h2>
          </div>
          <p className="text-sm text-text-secondary tabular">
            {done} of {researchStatus.length} complete
          </p>
        </div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-surface-2">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent to-sky-400"
            style={{ width: `${(done / researchStatus.length) * 100}%` }}
          />
        </div>
        <ol className="mt-6 grid gap-2 md:grid-cols-2">
          {researchStatus.map((r) => (
            <li
              key={r.milestone}
              className="flex items-center gap-3 rounded-xl border border-border bg-surface px-4 py-3"
            >
              <span className="w-9 shrink-0 font-mono text-xs text-text-muted">{r.milestone}</span>
              <span className="flex-1 text-sm text-text-primary">{r.description}</span>
              <StatusBadge status={r.status} />
            </li>
          ))}
        </ol>
      </section>
    </div>
  );
}
