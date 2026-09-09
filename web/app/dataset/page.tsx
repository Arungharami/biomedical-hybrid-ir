import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import StatCard from "@/components/StatCard";
import SourceNote from "@/components/SourceNote";
import { dataset } from "@/lib/data";

export const metadata: Metadata = { title: "Dataset" };

type WordStats = { min: number; max: number; mean: number; median: number; n: number };

export default function DatasetPage() {
  const corpus = dataset.corpus_detail as unknown as {
    num_documents: number;
    documents_with_nonempty_title: number;
    title_word_count: WordStats;
    body_word_count: WordStats;
    approx_vocabulary_size: number;
  };
  const provenance = dataset.provenance as Record<string, unknown>;
  const validation = dataset.validation;

  return (
    <div>
      <PageHeader
        eyebrow="NFCorpus"
        title="Dataset"
        description="Biomedical/nutrition IR collection: layperson health queries paired with graded relevance judgments against PubMed-indexed scientific articles."
      />

      <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard label="Corpus" value={dataset.corpus_size.toLocaleString()} sublabel="documents" />
        <StatCard label="Queries (total)" value={dataset.query_count.toLocaleString()} />
        <StatCard label="Train qrels" value={String(dataset.qrel_counts.train)} sublabel="queries" />
        <StatCard label="Test qrels" value={String(dataset.qrel_counts.test)} sublabel="queries" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Splits and their role">
          <ul className="space-y-3 text-sm">
            {Object.entries(dataset.splits).map(([split, info]) => (
              <li key={split} className="flex items-start justify-between gap-4">
                <span className="font-mono text-xs font-medium text-text-primary">{split}</span>
                <span className="text-right text-text-secondary">{(info as { role: string }).role}</span>
              </li>
            ))}
          </ul>
          <SourceNote>
            The qrels HF split is literally named &quot;validation&quot;, mapped internally to
            &quot;dev&quot;. See docs/dataset.md.
          </SourceNote>
        </Card>

        <Card title="Validation (automatic)">
          <div className="mb-3 flex items-center gap-2">
            <span
              className={`inline-flex h-2.5 w-2.5 rounded-full ${validation.ok ? "bg-good" : "bg-bad"}`}
            />
            <span className="text-sm font-medium text-text-primary">
              {validation.ok ? "All checks passed" : "Validation errors found"}
            </span>
          </div>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            {Object.entries(validation.stats).map(([k, v]) => {
              if (typeof v === "object") return null;
              return (
                <div key={k} className="flex justify-between border-b border-border py-1">
                  <dt className="text-text-secondary">{k.replace(/_/g, " ")}</dt>
                  <dd className="tabular font-medium text-text-primary">{String(v)}</dd>
                </div>
              );
            })}
          </dl>
          <SourceNote>data/processed/dataset_stats.json (scripts/audit_dataset.py)</SourceNote>
        </Card>

        <Card title="Corpus statistics">
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between">
              <dt className="text-text-secondary">Documents</dt>
              <dd className="tabular font-medium">{corpus.num_documents.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-text-secondary">Approx. vocabulary size</dt>
              <dd className="tabular font-medium">{corpus.approx_vocabulary_size.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-text-secondary">Title word count (mean / median)</dt>
              <dd className="tabular font-medium">
                {corpus.title_word_count.mean} / {corpus.title_word_count.median}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-text-secondary">Body word count (mean / median)</dt>
              <dd className="tabular font-medium">
                {corpus.body_word_count.mean} / {corpus.body_word_count.median}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-text-secondary">Body word count (min–max)</dt>
              <dd className="tabular font-medium">
                {corpus.body_word_count.min}–{corpus.body_word_count.max}
              </dd>
            </div>
          </dl>
          <SourceNote>data/processed/corpus_stats.json</SourceNote>
        </Card>

        <Card title="Provenance">
          <dl className="space-y-2 text-sm">
            {Object.entries(provenance)
              .filter(([k]) => !["duplicate_corpus_ids", "duplicate_query_ids"].includes(k))
              .map(([k, v]) => (
                <div key={k} className="flex justify-between gap-4">
                  <dt className="text-text-secondary">{k.replace(/_/g, " ")}</dt>
                  <dd className="max-w-[60%] break-words text-right font-medium text-text-primary">
                    {typeof v === "object" ? JSON.stringify(v) : String(v)}
                  </dd>
                </div>
              ))}
          </dl>
          <SourceNote>
            Verified directly against the live Hugging Face Hub — BeIR/nfcorpus (corpus, queries) +
            BeIR/nfcorpus-qrels.
          </SourceNote>
        </Card>
      </div>

      <Card title="Document composition" className="mt-6">
        <p className="text-sm text-text-secondary leading-relaxed">
          When both fields exist, a document is composed as{" "}
          <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-xs">
            {"{title} [SEP] {text}"}
          </code>{" "}
          for TF-IDF/BM25/BGE. MedCPT&apos;s article encoder instead consumes documents as a
          structured{" "}
          <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-xs">[title, text]</code>{" "}
          pair — the format its tokenizer call expects, verified against the official model card.
        </p>
      </Card>
    </div>
  );
}
