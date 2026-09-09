import type { Metadata } from "next";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import Card, { TableWrap } from "@/components/Card";
import { comparison } from "@/lib/data";

export const metadata: Metadata = { title: "Results" };

const BEST = {
  "P@10": "bge",
  "Recall@100": "medcpt",
  MAP: "bge",
  "MRR@10": "hybrid_rrf",
  "nDCG@10": "hybrid_reranked",
};

const MODEL_KEY_BY_LABEL: Record<string, string> = {
  "TF-IDF": "tfidf",
  BM25: "bm25",
  BGE: "bge",
  MedCPT: "medcpt",
  "BM25+MedCPT (RRF)": "hybrid_rrf",
  "Hybrid+Reranker (pool=50)": "hybrid_reranked",
};

export default function ResultsPage() {
  const cols = ["P@10", "Recall@100", "MAP", "MRR@10", "nDCG@10", "Latency (ms/query)"] as const;

  return (
    <div>
      <PageHeader
        eyebrow="Main comparison"
        title="Results"
        description="All six models, evaluated identically against the same real NFCorpus test split (n=323 queries) and the same qrels. No number below is estimated — every cell is generated from results/metrics/*.json."
      />

      <Card>
        <TableWrap>
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-surface-2 text-left">
              <tr>
                <th className="px-4 py-2.5 font-medium text-text-secondary">Model</th>
                {cols.map((c) => (
                  <th key={c} className="px-4 py-2.5 text-right font-medium text-text-secondary">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {comparison.main_results.map((row) => {
                const key = MODEL_KEY_BY_LABEL[row.model] ?? "";
                return (
                  <tr key={row.model} className="border-b border-border last:border-0">
                    <td className="px-4 py-2.5 font-medium text-text-primary">{row.model}</td>
                    {cols.map((c) => {
                      const isBest = BEST[c as keyof typeof BEST] === key;
                      return (
                        <td
                          key={c}
                          className={`tabular px-4 py-2.5 text-right ${
                            isBest ? "font-semibold text-accent" : "text-text-primary"
                          }`}
                        >
                          {row[c]}
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </TableWrap>
        <p className="mt-3 text-xs text-text-muted">
          Bold/accent = best value in that column. Reranked row&apos;s Recall@100/MAP are capped by
          its 50-document candidate pool — see the note below and{" "}
          <Link href="/evaluation" className="text-accent hover:underline">
            Evaluation
          </Link>{" "}
          for the full explanation and statistical significance tests.
        </p>
      </Card>

      <Card title="Reading the reranker row correctly" className="mt-6">
        <p className="text-sm text-text-secondary leading-relaxed">
          A cross-encoder can only reorder the candidates it is given. With a candidate pool of 50,
          the reranked run never contains more than 50 documents per query, so Recall@100 ==
          Recall@50 exactly by construction — confirmed mechanistically: at pool=100, Recall@100
          exactly matches hybrid RRF&apos;s own Recall@100 (reordering an unchanged 100-document set
          cannot change how many relevant documents it contains). This is a genuine methodological
          property, not a bug — see the pool-size ablation on{" "}
          <Link href="/efficiency" className="text-accent hover:underline">
            Efficiency
          </Link>
          .
        </p>
      </Card>

      <Card title="Progression across the study" className="mt-6">
        <div className="flex flex-wrap items-center gap-2 text-sm">
          {["BM25", "TF-IDF", "Hybrid RRF", "MedCPT", "BGE", "Hybrid+Reranker"].map((m, i, arr) => (
            <span key={m} className="flex items-center gap-2">
              <span className="rounded-md bg-surface-2 px-2.5 py-1 font-medium text-text-primary">
                {m}
              </span>
              {i < arr.length - 1 && <span className="text-text-muted">&lt;</span>}
            </span>
          ))}
        </div>
        <p className="mt-2 text-xs text-text-muted">Ordered by real nDCG@10, lowest to highest.</p>
      </Card>
    </div>
  );
}
