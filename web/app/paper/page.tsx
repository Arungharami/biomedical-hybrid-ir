import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";

export const metadata: Metadata = { title: "Paper" };

const REPO = "https://github.com/Arungharami/biomedical-hybrid-ir/blob/main/paper";

const SECTIONS = [
  { file: "abstract.md", label: "Abstract" },
  { file: "introduction.md", label: "1. Introduction" },
  { file: "related-work.md", label: "2. Related Work" },
  { file: "methodology.md", label: "3–5. Research Questions, Hypotheses & Methodology" },
  { file: "experimental-setup.md", label: "6–7. Experimental Setup & Evaluation Metrics" },
  { file: "results.md", label: "8–10. Results, Statistical Analysis & Error Analysis" },
  { file: "discussion.md", label: "12. Discussion" },
  { file: "limitations.md", label: "13–14. Limitations & Threats to Validity" },
  { file: "conclusion.md", label: "16. Conclusion" },
  { file: "references.bib", label: "References (BibTeX)" },
];

export default function PaperPage() {
  return (
    <div>
      <PageHeader
        eyebrow="CAP 6776 — Information Retrieval"
        title="Hybrid Biomedical Information Retrieval with Lexical, Dense, and Cross-Encoder Reranking: A Reproducible Study on NFCorpus"
      />

      <Card title="Abstract" className="mb-6">
        <p className="text-sm leading-relaxed text-text-secondary">
          Biomedical information retrieval sits between two demands that are often in tension:
          exact lexical precision (drug names, gene symbols, precise terminology) and semantic
          understanding of paraphrased, layperson queries against expert-authored literature. We
          present a reproducible study on NFCorpus (3,633 documents, 323 test queries, verified
          against the live Hugging Face Hub) comparing six retrieval systems along the progression
          classical lexical retrieval (TF-IDF, BM25) → general-purpose dense retrieval (BGE) →
          biomedical-domain dense retrieval (MedCPT) → hybrid lexical-semantic fusion (Reciprocal
          Rank Fusion) → biomedical cross-encoder reranking, under one evaluation protocol, one
          qrels set, and paired query-level significance testing.
        </p>
        <p className="mt-3 text-sm leading-relaxed text-text-secondary">
          Contrary to a common textbook expectation, TF-IDF significantly outperforms BM25 on this
          corpus. Both dense retrievers significantly and substantially outperform BM25 on every
          primary metric (p&lt;0.005 each) — the study&apos;s most robust finding — but
          biomedical-domain training (MedCPT) does not significantly outperform a strong
          general-purpose embedding model (BGE). Cross-encoder reranking achieves the highest
          nDCG@10 of all six systems at a real, substantial latency cost, but that specific
          improvement is not statistically significant. Query-level error analysis surfaces
          concrete mechanisms behind these aggregate numbers.
        </p>
        <a
          href={`${REPO}/abstract.md`}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-block text-sm text-accent hover:underline"
        >
          Read the full abstract on GitHub ↗
        </a>
      </Card>

      <Card title="Full paper sections">
        <p className="mb-4 text-sm text-text-secondary">
          Every section is complete and written only from real, completed results — no placeholder
          language remains. Full text is in the repository (rendered here would duplicate content
          that&apos;s already maintained as the single source of truth):
        </p>
        <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
          {SECTIONS.map((s) => (
            <li key={s.file}>
              <a
                href={`${REPO}/${s.file}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm text-text-primary transition-colors hover:border-accent hover:bg-surface-2"
              >
                {s.label}
                <span className="text-text-muted">↗</span>
              </a>
            </li>
          ))}
        </ul>
      </Card>
    </div>
  );
}
