import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";

export const metadata: Metadata = { title: "Pipeline" };

const STAGES = [
  { n: 1, name: "Dataset ingestion", module: "biomedical_ir/data.py", script: "scripts/download_data.py" },
  { n: 2, name: "Dataset validation", module: "biomedical_ir/validation.py", script: "scripts/audit_dataset.py" },
  { n: 3, name: "TF-IDF (M1)", module: "biomedical_ir/tfidf.py", script: "scripts/run_tfidf.py" },
  { n: 4, name: "BM25 (M2)", module: "biomedical_ir/bm25.py", script: "scripts/run_bm25.py" },
  { n: 5, name: "General dense retrieval (M3, BGE)", module: "biomedical_ir/dense.py", script: "scripts/run_bge.py" },
  { n: 6, name: "Biomedical dense retrieval (M4, MedCPT)", module: "biomedical_ir/medcpt.py", script: "scripts/run_medcpt.py" },
  { n: 7, name: "Hybrid RRF (M5)", module: "biomedical_ir/fusion.py", script: "scripts/run_hybrid.py" },
  { n: 8, name: "Cross-encoder reranking (M6)", module: "biomedical_ir/reranker.py", script: "scripts/run_reranker.py" },
  { n: 9, name: "Evaluation + statistics", module: "biomedical_ir/{evaluation,statistics,efficiency}.py", script: "scripts/evaluate_all.py" },
  { n: 10, name: "Error analysis", module: "biomedical_ir/error_analysis.py", script: "scripts/error_analysis.py" },
  { n: 11, name: "Figures / tables", module: "—", script: "scripts/generate_figures.py" },
  { n: 12, name: "Web export", module: "—", script: "scripts/export_web_results.py" },
];

function Box({ children, wide = false }: { children: React.ReactNode; wide?: boolean }) {
  return (
    <div
      className={`rounded-lg border border-border bg-surface px-4 py-3 text-center text-sm font-medium text-text-primary ${wide ? "w-full max-w-md" : "w-fit"}`}
    >
      {children}
    </div>
  );
}

function Arrow({ vertical = true }: { vertical?: boolean }) {
  return (
    <div className={`text-text-muted ${vertical ? "" : "px-1"}`} aria-hidden>
      {vertical ? "↓" : "→"}
    </div>
  );
}

export default function PipelinePage() {
  return (
    <div>
      <PageHeader
        eyebrow="Architecture"
        title="Retrieval Pipeline"
        description="NFCorpus → validation → lexical + dense retrieval → RRF fusion → cross-encoder reranking → evaluation → statistical analysis → research portal."
      />

      <Card title="Full pipeline">
        <div className="flex flex-col items-center gap-2 py-4">
          <Box wide>NFCorpus (BeIR/nfcorpus + BeIR/nfcorpus-qrels)</Box>
          <Arrow />
          <Box wide>Data Validation</Box>
          <Arrow />
          <div className="flex flex-col items-center gap-2 sm:flex-row sm:gap-6">
            <Box>Lexical IR — TF-IDF / BM25</Box>
            <span className="text-text-muted">+</span>
            <Box>Dense IR — BGE / MedCPT</Box>
          </div>
          <Arrow />
          <Box wide>RRF Fusion (BM25 + MedCPT, rank-based)</Box>
          <Arrow />
          <Box wide>MedCPT Cross-Encoder Reranking</Box>
          <Arrow />
          <Box wide>Ranked Documents</Box>
          <Arrow />
          <div className="flex flex-col items-center gap-2 sm:flex-row sm:gap-6">
            <Box>Qrels (test split)</Box>
            <span className="text-text-muted">→</span>
            <Box>Evaluation (pytrec_eval)</Box>
          </div>
          <Arrow />
          <Box wide>MAP / MRR / nDCG / Precision / Recall</Box>
          <Arrow />
          <Box wide>Statistical Analysis (paired bootstrap)</Box>
          <Arrow />
          <Box wide>Research Results (this portal)</Box>
        </div>
      </Card>

      <Card title="Stage → module → script" className="mt-6">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-text-secondary">
              <tr>
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">Stage</th>
                <th className="px-3 py-2 font-medium">Module</th>
                <th className="px-3 py-2 font-medium">Script</th>
              </tr>
            </thead>
            <tbody>
              {STAGES.map((s) => (
                <tr key={s.n} className="border-b border-border last:border-0">
                  <td className="px-3 py-2 text-text-muted">{s.n}</td>
                  <td className="px-3 py-2 text-text-primary">{s.name}</td>
                  <td className="px-3 py-2 font-mono text-xs text-text-secondary">{s.module}</td>
                  <td className="px-3 py-2 font-mono text-xs text-accent">{s.script}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Why RRF operates on rank, not raw score">
          <p className="text-sm text-text-secondary leading-relaxed">
            BM25 scores are unbounded and MedCPT similarities are raw (unnormalized) dot products —
            not on a comparable scale. Summing them directly would implicitly and arbitrarily weight
            whichever retriever happens to produce larger-magnitude scores, not whichever is more
            accurate. Reciprocal Rank Fusion instead combines <strong>rank positions</strong>, which
            are already on a common scale by construction.
          </p>
        </Card>
        <Card title="Why Vercel never runs the models">
          <p className="text-sm text-text-secondary leading-relaxed">
            BGE, MedCPT, and the MedCPT cross-encoder are never invoked inside a Vercel serverless
            function. All embeddings/rankings are computed offline (locally or in Colab), evaluated,
            and exported as compact JSON artifacts. This portal only reads those artifacts — the{" "}
            <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">/search</code>{" "}
            page is explicitly labeled as showing precomputed experiment output, never a live model
            call.
          </p>
        </Card>
      </div>
    </div>
  );
}
