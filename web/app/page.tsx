import Link from "next/link";
import Card from "@/components/Card";
import StatCard from "@/components/StatCard";
import StatusBadge from "@/components/StatusBadge";
import { comparison, dataset, formatMetric, researchStatus } from "@/lib/data";

const PIPELINE = [
  "NFCorpus",
  "Validation",
  "TF-IDF / BM25",
  "BGE / MedCPT",
  "RRF Fusion",
  "Cross-Encoder",
  "Evaluation",
];

const SECTIONS = [
  { href: "/dataset", label: "Dataset", desc: "NFCorpus schema, stats, provenance" },
  { href: "/pipeline", label: "Pipeline", desc: "The full retrieval architecture" },
  { href: "/models", label: "Models", desc: "TF-IDF, BM25, BGE, MedCPT, RRF, Cross-Encoder" },
  { href: "/experiments", label: "Experiments", desc: "Real manifests for every run" },
  { href: "/results", label: "Results", desc: "Main comparison table" },
  { href: "/evaluation", label: "Evaluation", desc: "MAP, MRR, nDCG, P, R, significance" },
  { href: "/error-analysis", label: "Error Analysis", desc: "Query-level win/loss examples" },
  { href: "/efficiency", label: "Efficiency", desc: "Latency, index size trade-offs" },
  { href: "/search", label: "Search Demo", desc: "Precomputed retrieval examples" },
  { href: "/paper", label: "Paper", desc: "Abstract, methodology, full results" },
];

export default function Home() {
  const bm25vsBge = comparison.statistical_tests.comparisons.find(
    (c) => c.model_a === "BM25" && c.model_b === "BGE" && c.metric === "nDCG@10"
  );

  return (
    <div className="flex flex-col gap-14">
      <section>
        <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-accent">
          CAP 6776 — Information Retrieval
        </p>
        <h1 className="max-w-3xl text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">
          Hybrid Biomedical Information Retrieval with Lexical, Dense, and Cross-Encoder Reranking
        </h1>
        <p className="mt-4 max-w-2xl text-lg text-text-secondary leading-relaxed">
          A reproducible study on NFCorpus comparing six retrieval systems — TF-IDF, BM25, BGE,
          MedCPT, a BM25+MedCPT hybrid, and biomedical cross-encoder reranking — under one
          evaluation protocol and real paired statistical significance testing.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/results"
            className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:opacity-90"
          >
            View real results
          </Link>
          <Link
            href="/paper"
            className="rounded-md border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2"
          >
            Read the paper
          </Link>
          <a
            href="https://github.com/Arungharami/biomedical-hybrid-ir"
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-border px-4 py-2 text-sm font-medium text-text-primary hover:bg-surface-2"
          >
            GitHub ↗
          </a>
        </div>
      </section>

      <section>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatCard label="Corpus" value={dataset.corpus_size.toLocaleString()} sublabel="documents" />
          <StatCard label="Test queries" value={String(dataset.qrel_counts.test)} sublabel="with qrels" />
          <StatCard label="Models compared" value="6" sublabel="lexical → dense → hybrid → reranked" />
          <StatCard
            label="Best nDCG@10"
            value={formatMetric(0.3731)}
            sublabel="Hybrid + Cross-Encoder"
            accent
          />
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Pipeline</h2>
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-border bg-surface p-4">
          {PIPELINE.map((step, i) => (
            <span key={step} className="flex items-center gap-2">
              <span className="rounded-md bg-surface-2 px-3 py-1.5 text-sm font-medium text-text-primary">
                {step}
              </span>
              {i < PIPELINE.length - 1 && <span className="text-text-muted">→</span>}
            </span>
          ))}
        </div>
        <p className="mt-2 text-sm text-text-secondary">
          See <Link href="/pipeline" className="text-accent hover:underline">Pipeline</Link> for the
          full architecture diagram and design rationale.
        </p>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Headline finding</h2>
        <Card>
          <p className="text-text-primary leading-relaxed">
            Both dense retrievers (BGE, MedCPT) significantly outperform BM25 on every primary
            metric
            {bm25vsBge && (
              <> (e.g. nDCG@10: p={formatMetric(bm25vsBge.p_value, 4)})</>
            )}
            {" "}— the most robust finding across all statistical tests run. Biomedical-domain
            training (MedCPT) did <strong>not</strong> significantly outperform a general-purpose
            embedding model (BGE), and cross-encoder reranking&apos;s best raw nDCG@10 number in
            the study is not statistically significant relative to hybrid RRF.
          </p>
          <Link href="/evaluation" className="mt-3 inline-block text-sm text-accent hover:underline">
            See the full statistical analysis →
          </Link>
        </Card>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Explore</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {SECTIONS.map((s) => (
            <Link
              key={s.href}
              href={s.href}
              className="rounded-lg border border-border bg-surface p-4 transition-colors hover:border-accent hover:bg-surface-2"
            >
              <p className="font-medium text-text-primary">{s.label}</p>
              <p className="mt-1 text-sm text-text-secondary">{s.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-4 text-lg font-semibold text-text-primary">Experiment status</h2>
        <div className="overflow-x-auto rounded-lg border border-border bg-surface">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-text-secondary">
              <tr>
                <th className="px-4 py-2 font-medium">Milestone</th>
                <th className="px-4 py-2 font-medium">Description</th>
                <th className="px-4 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {researchStatus.map((r) => (
                <tr key={r.milestone} className="border-b border-border last:border-0">
                  <td className="px-4 py-2 font-mono text-xs text-text-secondary">{r.milestone}</td>
                  <td className="px-4 py-2 text-text-primary">{r.description}</td>
                  <td className="px-4 py-2">
                    <StatusBadge status={r.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
