import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import SourceNote from "@/components/SourceNote";
import { errorAnalysis } from "@/lib/data";

export const metadata: Metadata = { title: "Error Analysis" };

const CATEGORY_TITLES: Record<string, string> = {
  bm25_wins_medcpt_loses: "BM25 wins / MedCPT loses",
  medcpt_wins_bm25_loses: "MedCPT wins / BM25 loses",
  hybrid_fixes_lexical_failure: "Hybrid fixes a lexical (BM25) failure",
  hybrid_fixes_semantic_failure: "Hybrid fixes a semantic (MedCPT) failure",
  reranker_improves_result: "Reranker improves the result",
  reranker_degrades_result: "Reranker degrades the result",
};

export default function ErrorAnalysisPage() {
  return (
    <div>
      <PageHeader
        eyebrow="M8"
        title="Error Analysis"
        description="Every (query, relevant document) pair from the real test qrels, classified by each model's real rank for that document. Concrete mechanisms behind the aggregate metrics."
      />

      <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {Object.entries(errorAnalysis.total_examples_found_per_category).map(([cat, count]) => (
          <div key={cat} className="rounded-lg border border-border bg-surface p-3 text-center">
            <p className="tabular text-xl font-bold text-text-primary">{count}</p>
            <p className="mt-1 text-xs text-text-secondary">{CATEGORY_TITLES[cat] ?? cat}</p>
          </div>
        ))}
      </div>

      <div className="flex flex-col gap-8">
        {Object.entries(errorAnalysis.categories).map(([cat, examples]) => (
          <section key={cat}>
            <h2 className="mb-3 text-base font-semibold text-text-primary">
              {CATEGORY_TITLES[cat] ?? cat}{" "}
              <span className="font-normal text-text-muted">
                ({errorAnalysis.total_examples_found_per_category[cat]} found, showing{" "}
                {examples.length})
              </span>
            </h2>
            <div className="flex flex-col gap-3">
              {examples.map((ex, i) => (
                <Card key={i}>
                  <div className="flex flex-wrap items-baseline justify-between gap-2">
                    <p className="font-mono text-xs text-text-muted">{ex.query_id}</p>
                    <p className="text-xs text-text-muted">relevance = {ex.relevance}</p>
                  </div>
                  <p className="mt-1 text-sm font-medium text-text-primary">&ldquo;{ex.query}&rdquo;</p>
                  <p className="mt-2 text-sm text-text-secondary">
                    <span className="font-medium text-text-primary">{ex.doc_title}</span> ({ex.doc_id}
                    )
                  </p>
                  <p className="mt-1 text-sm text-text-muted italic">{ex.doc_snippet}</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {Object.entries(ex.ranks).map(([model, rank]) => (
                      <span
                        key={model}
                        className="rounded-md bg-surface-2 px-2 py-1 font-mono text-xs text-text-secondary"
                      >
                        {model}={rank ?? "—"}
                      </span>
                    ))}
                  </div>
                </Card>
              ))}
              {examples.length === 0 && (
                <p className="text-sm text-text-muted">No examples found in this run.</p>
              )}
            </div>
          </section>
        ))}
      </div>

      <SourceNote>
        results/error-analysis/error_analysis.json — src/biomedical_ir/error_analysis.py. Rank
        thresholds: good ≤ {errorAnalysis.rank_thresholds.good_rank}, bad = not retrieved or &gt;{" "}
        {errorAnalysis.rank_thresholds.bad_rank}.
      </SourceNote>
    </div>
  );
}
