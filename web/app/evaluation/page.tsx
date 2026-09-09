import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card, { TableWrap } from "@/components/Card";
import SourceNote from "@/components/SourceNote";
import { comparison, formatMetric } from "@/lib/data";

export const metadata: Metadata = { title: "Evaluation" };

const HYPOTHESIS_VERDICTS = [
  {
    id: "H1",
    text: "BM25 will outperform TF-IDF",
    verdict: "REJECTED",
    tone: "bad" as const,
    detail: "TF-IDF significantly beats BM25 on P@10 (p=0.017), Recall@100 (p=0.010), nDCG@10 (p=0.030).",
  },
  {
    id: "H2",
    text: "MedCPT will outperform BGE (biomedical vs. general dense)",
    verdict: "NOT SUPPORTED",
    tone: "warn" as const,
    detail: "No significant difference on any of 5 metrics (all p≥0.12) — statistically indistinguishable.",
  },
  {
    id: "H3",
    text: "Hybrid RRF will outperform BM25 and MedCPT individually",
    verdict: "NOT SUPPORTED",
    tone: "warn" as const,
    detail: "MedCPT significantly beats Hybrid RRF on Recall@100 (p=0.040) — the opposite direction.",
  },
  {
    id: "H4",
    text: "Cross-encoder reranking improves nDCG@10, increases latency",
    verdict: "PARTIALLY SUPPORTED",
    tone: "warn" as const,
    detail:
      "Latency increase unambiguous. nDCG@10 gain is the best point estimate in the study but not significant (p=0.194). P@10 improves significantly (p=0.015).",
  },
];

const TONE_STYLES = {
  bad: "bg-bad/10 text-bad border-bad/30",
  warn: "bg-warn/10 text-warn border-warn/30",
  good: "bg-good/10 text-good border-good/30",
};

export default function EvaluationPage() {
  const { comparisons, method, n_resamples, seed } = comparison.statistical_tests;

  return (
    <div>
      <PageHeader
        eyebrow="M7"
        title="Evaluation & Statistical Analysis"
        description="Every model evaluated with the same qrels via pytrec_eval, cross-checked against from-scratch metric implementations. Significance: paired bootstrap at the query level."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card title="Metrics computed" className="lg:col-span-1">
          <ul className="space-y-1.5 text-sm text-text-secondary">
            <li>Precision@{"{1,5,10}"}</li>
            <li>Recall@{"{10,20,50,100}"}</li>
            <li>MRR, MRR@10</li>
            <li>MAP, MAP@100</li>
            <li>nDCG@{"{5,10,20}"}</li>
          </ul>
          <SourceNote>src/biomedical_ir/evaluation.py, cross-checked in tests/test_metrics.py</SourceNote>
        </Card>

        <Card title="Graded relevance handling" className="lg:col-span-2">
          <p className="text-sm text-text-secondary leading-relaxed">
            NFCorpus qrels are graded (0/1/2). Empirically confirmed (not assumed): binary-style
            measures treat any grade &gt;0 as relevant; nDCG uses <strong>linear</strong> gain
            (gain(rel)=rel), not exponential gain; a query with zero relevant documents scores 0.0
            for every measure.
          </p>
        </Card>
      </div>

      <h2 className="mb-4 mt-8 text-lg font-semibold text-text-primary">
        Statistical significance ({method}, n_resamples={n_resamples}, seed={seed})
      </h2>
      <Card>
        <TableWrap>
          <table className="w-full text-sm">
            <thead className="border-b border-border bg-surface-2 text-left">
              <tr>
                <th className="px-3 py-2 font-medium text-text-secondary">Comparison</th>
                <th className="px-3 py-2 font-medium text-text-secondary">Metric</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">Diff (A−B)</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">95% CI</th>
                <th className="px-3 py-2 text-right font-medium text-text-secondary">p</th>
                <th className="px-3 py-2 text-center font-medium text-text-secondary">Sig.</th>
              </tr>
            </thead>
            <tbody>
              {comparisons.map((c, i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  <td className="whitespace-nowrap px-3 py-2 text-text-primary">
                    {c.model_a} vs {c.model_b}
                  </td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">{c.metric}</td>
                  <td className="tabular px-3 py-2 text-right text-text-primary">
                    {c.mean_diff >= 0 ? "+" : ""}
                    {formatMetric(c.mean_diff)}
                  </td>
                  <td className="tabular px-3 py-2 text-right text-xs text-text-secondary">
                    [{formatMetric(c.ci_95_low)}, {formatMetric(c.ci_95_high)}]
                  </td>
                  <td className="tabular px-3 py-2 text-right text-text-primary">
                    {formatMetric(c.p_value)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {c["significant_at_alpha_0.05"] ? (
                      <span className="text-good">✓</span>
                    ) : (
                      <span className="text-text-muted">–</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableWrap>
        <SourceNote>
          results/tables/statistical_tests.json — src/biomedical_ir/statistics.py
          (paired_bootstrap_test)
        </SourceNote>
      </Card>

      <h2 className="mb-4 mt-8 text-lg font-semibold text-text-primary">Per-hypothesis verdicts</h2>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {HYPOTHESIS_VERDICTS.map((h) => (
          <Card key={h.id}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-text-muted">{h.id}</p>
                <p className="mt-0.5 text-sm font-medium text-text-primary">{h.text}</p>
              </div>
              <span
                className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${TONE_STYLES[h.tone]}`}
              >
                {h.verdict}
              </span>
            </div>
            <p className="mt-2 text-sm text-text-secondary leading-relaxed">{h.detail}</p>
          </Card>
        ))}
      </div>
      <p className="mt-4 text-xs text-text-muted">
        Note: &quot;not supported&quot; means no significant difference was found — this is not the
        same claim as &quot;proven equal&quot; (absence of evidence is not evidence of absence).
      </p>
    </div>
  );
}
