import type { Metadata } from "next";
import Image from "next/image";
import PageHeader from "@/components/PageHeader";
import Card, { TableWrap } from "@/components/Card";
import SourceNote from "@/components/SourceNote";
import { efficiency, formatLatency, formatMetric, MODEL_LABELS, metrics } from "@/lib/data";

export const metadata: Metadata = { title: "Efficiency" };

export default function EfficiencyPage() {
  const ablation = metrics.reranker_pool_ablation as unknown as {
    pool_sizes_tested: number[];
    default_pool: number;
    results_by_pool: Record<
      string,
      { candidate_pool: number; metrics: Record<string, number>; reranking_latency_ms_per_query: number }
    >;
  };

  return (
    <div>
      <PageHeader
        eyebrow="M7 · Section 19"
        title="Efficiency"
        description="Latency, index size, and the effectiveness/efficiency trade-off, measured on Apple M1 Pro (MPS) — not representative of GPU-optimized production latency, but real measurements on the hardware actually used."
      />

      <Card>
        <TableWrap>
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-surface-2 text-left">
              <tr>
                <th className="px-3 py-2 font-medium text-text-secondary">Model</th>
                <th className="px-3 py-2 font-medium text-text-secondary">Device</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">Embedding dim</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">Index size</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">Latency</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">nDCG@10</th>
              </tr>
            </thead>
            <tbody>
              {efficiency.map((r) => (
                <tr key={r.model} className="border-b border-border last:border-0">
                  <td className="px-3 py-2 font-medium text-text-primary">
                    {MODEL_LABELS[r.model] ?? r.model}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">{r.device}</td>
                  <td className="tabular px-3 py-2 text-right text-text-primary">
                    {r.embedding_dim ?? "—"}
                  </td>
                  <td className="tabular px-3 py-2 text-right text-text-primary">
                    {r.index_size_bytes ? `${(r.index_size_bytes / 1024).toFixed(1)} KB` : "—"}
                  </td>
                  <td className="tabular px-3 py-2 text-right text-text-primary">
                    {formatLatency(r.latency_ms_per_query)}
                  </td>
                  <td className="tabular px-3 py-2 text-right text-text-primary">
                    {formatMetric(r["nDCG@10"])}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
        <SourceNote>results/tables/efficiency.json — src/biomedical_ir/efficiency.py</SourceNote>
      </Card>

      <Card title="nDCG@10 vs. latency" className="mt-6">
        <Image
          src="/figures/figure9_ndcg_vs_latency.png"
          alt="Scatter plot of nDCG@10 versus query latency (log scale) for all six models"
          width={960}
          height={660}
          className="mx-auto h-auto w-full max-w-2xl rounded-md border border-border"
        />
        <p className="mt-2 text-xs text-text-muted">
          Cross-encoder reranking sits roughly three orders of magnitude further right than any
          other system for a nDCG@10 gain that is numerically real but not statistically
          significant (see Evaluation).
        </p>
      </Card>

      {ablation && (
        <Card title="Reranker candidate-pool ablation (A6)" className="mt-6">
          <TableWrap>
            <table className="w-full text-sm">
              <thead className="border-b border-border bg-surface-2 text-left">
                <tr>
                  <th className="px-3 py-2 font-medium text-text-secondary">Pool</th>
                  <th className="px-3 py-2 text-right font-medium text-text-secondary">P@10</th>
                  <th className="px-3 py-2 text-right font-medium text-text-secondary">Recall@100</th>
                  <th className="px-3 py-2 text-right font-medium text-text-secondary">MAP</th>
                  <th className="px-3 py-2 text-right font-medium text-text-secondary">nDCG@10</th>
                  <th className="px-3 py-2 text-right font-medium text-text-secondary">Latency</th>
                </tr>
              </thead>
              <tbody>
                {ablation.pool_sizes_tested.map((pool) => {
                  const r = ablation.results_by_pool[String(pool)];
                  const isDefault = pool === ablation.default_pool;
                  return (
                    <tr key={pool} className="border-b border-border last:border-0">
                      <td className="px-3 py-2 font-medium text-text-primary">
                        {pool} {isDefault && <span className="text-accent">(default)</span>}
                      </td>
                      <td className="tabular px-3 py-2 text-right">{formatMetric(r.metrics["P@10"])}</td>
                      <td className="tabular px-3 py-2 text-right">
                        {formatMetric(r.metrics["Recall@100"])}
                      </td>
                      <td className="tabular px-3 py-2 text-right">{formatMetric(r.metrics["MAP"])}</td>
                      <td className="tabular px-3 py-2 text-right">
                        {formatMetric(r.metrics["nDCG@10"])}
                      </td>
                      <td className="tabular px-3 py-2 text-right">
                        {formatLatency(r.reranking_latency_ms_per_query)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </TableWrap>
          <p className="mt-3 text-sm text-text-secondary leading-relaxed">
            Recall@k for k exceeding the pool size equals Recall@pool exactly — a reranker cannot
            recover documents outside its candidate pool. Effectiveness vs. pool size is
            non-monotonic for nDCG@10 (peaks at 50, not 100).
          </p>
        </Card>
      )}
    </div>
  );
}
