import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";

export const metadata: Metadata = { title: "Reproducibility" };

const NOTEBOOKS = [
  { name: "00_environment_setup.ipynb", status: "Verified (executed)" },
  { name: "01_nfcorpus_dataset_audit.ipynb", status: "Verified (M1)" },
  { name: "02_tfidf_baseline.ipynb", status: "Verified (executed)" },
  { name: "03_bm25_baseline.ipynb", status: "Verified (executed)" },
  { name: "04_bge_dense_retrieval.ipynb", status: "Complete (~2 min runtime)" },
  { name: "05_medcpt_dense_retrieval.ipynb", status: "Complete (~3 min runtime)" },
  { name: "06_hybrid_rrf.ipynb", status: "Verified (executed)" },
  { name: "07_cross_encoder_reranking.ipynb", status: "Complete (~40 min for all pools)" },
  { name: "08_evaluation.ipynb", status: "Verified (executed)" },
  { name: "09_statistical_analysis.ipynb", status: "Verified (executed)" },
  { name: "10_error_analysis.ipynb", status: "Verified (executed)" },
  { name: "11_export_research_results.ipynb", status: "Verified (executed)" },
  { name: "Biomedical_Hybrid_IR_Full_Pipeline.ipynb", status: "Complete (master notebook)" },
];

export default function ReproducibilityPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Section 24 of the project spec"
        title="Reproducibility"
        description="Exact instructions to regenerate every number on this site from scratch."
      />

      <Card title="One-command reproduction">
        <pre className="overflow-x-auto rounded-md bg-surface-2 p-4 text-sm text-text-primary">
          <code>{`git clone https://github.com/Arungharami/biomedical-hybrid-ir
cd biomedical-hybrid-ir
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

python scripts/reproduce.py --config configs/default.yaml`}</code>
        </pre>
        <p className="mt-3 text-sm text-text-secondary leading-relaxed">
          Runs, in order: dataset audit → TF-IDF → BM25 → BGE → MedCPT → hybrid RRF → cross-encoder
          reranking → statistical/efficiency analysis → error analysis → web export. Each step is{" "}
          <strong>skipped</strong> if its expected output artifact already exists — pass{" "}
          <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">--force</code> to
          recompute everything, or{" "}
          <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">--from &lt;step&gt;</code>{" "}
          to resume after a failure.
        </p>
      </Card>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Environment">
          <ul className="space-y-1.5 text-sm text-text-secondary">
            <li>Python 3.11 (PyTorch/FAISS wheels lag behind newer CPython releases)</li>
            <li>seed = 42 throughout</li>
            <li>
              Library versions recorded per-run in every{" "}
              <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">
                results/manifests/*.json
              </code>{" "}
              — never hand-maintained, so they can&apos;t drift out of sync
            </li>
          </ul>
        </Card>
        <Card title="Device handling">
          <p className="text-sm text-text-secondary leading-relaxed">
            Prefers CUDA (Colab / cloud GPUs), then Apple MPS (used for local development on this
            project&apos;s M1 Pro), then CPU. Configurable via{" "}
            <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">
              configs/default.yaml → device.preference
            </code>
            .
          </p>
        </Card>
      </div>

      <Card title="Colab notebooks" className="mt-6">
        <p className="mb-4 text-sm text-text-secondary">
          13 notebooks total. 8 were executed end-to-end in a real Jupyter kernel during
          development — not just validated as well-formed JSON.
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="border-b border-border text-left text-text-secondary">
              <tr>
                <th className="px-3 py-2 font-medium">Notebook</th>
                <th className="px-3 py-2 font-medium">Status</th>
              </tr>
            </thead>
            <tbody>
              {NOTEBOOKS.map((n) => (
                <tr key={n.name} className="border-b border-border last:border-0">
                  <td className="px-3 py-2 font-mono text-xs text-text-primary">{n.name}</td>
                  <td className="px-3 py-2 text-text-secondary">{n.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="Testing" className="mt-6">
        <p className="text-sm text-text-secondary leading-relaxed">
          <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">pytest -q</code> — 209
          tests, all passing (unit tests for TF-IDF/BM25/RRF/metrics/statistics/error-analysis, plus
          notebook and figure validity checks). CI (
          <code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">
            .github/workflows/python-ci.yml
          </code>
          ) runs install → lint → test on every push, using CPU-only PyTorch and no network calls
          — it intentionally does not download NFCorpus or any transformer model.
        </p>
      </Card>
    </div>
  );
}
