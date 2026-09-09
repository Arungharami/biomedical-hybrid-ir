import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div>
      <PageHeader eyebrow="CAP 6776 — Information Retrieval" title="About this project" />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Course project">
          <p className="text-sm text-text-secondary leading-relaxed">
            Built for CAP 6776 (Information Retrieval). The primary deliverable is a scientifically
            reproducible information retrieval experiment on NFCorpus — this website presents the
            experiment and its verified results; it is not the deliverable itself.
          </p>
        </Card>

        <Card title="Scientific-integrity statement">
          <p className="text-sm text-text-secondary leading-relaxed">
            This project reports only genuine experimental output. No metric, dataset count,
            citation, or statistical result is fabricated. Pending experiments are labeled
            &quot;pending&quot;, never filled with plausible-looking numbers; failed runs are
            labeled &quot;failed&quot; with their error preserved. Every retrieval model choice
            (pooling, normalization, instruction prefixes, input formats) was verified against the
            official Hugging Face model card before use, not assumed.
          </p>
        </Card>

        <Card title="Architecture">
          <p className="text-sm text-text-secondary leading-relaxed">
            Hugging Face → Google Colab / local Python experiments → verified JSON/CSV artifacts →
            GitHub → Next.js → Vercel. Large models and embeddings stay in Colab/local
            environments — this website reads only compact exported results and never runs a
            transformer model itself.
          </p>
        </Card>

        <Card title="Technology">
          <ul className="space-y-1.5 text-sm text-text-secondary">
            <li>Research pipeline: Python 3.11, PyTorch, Transformers, sentence-transformers, FAISS, pytrec_eval</li>
            <li>Research portal: Next.js (App Router), TypeScript, Tailwind CSS</li>
            <li>Deployment: Vercel</li>
          </ul>
        </Card>
      </div>

      <Card title="Citation" className="mt-6">
        <pre className="overflow-x-auto rounded-md bg-surface-2 p-4 text-xs text-text-primary">
          <code>{`@misc{gharami2026hybridir,
  title  = {Hybrid Biomedical Information Retrieval with Lexical, Dense,
            and Cross-Encoder Reranking: A Reproducible Study on NFCorpus},
  author = {Gharami, Arun},
  year   = {2026},
  note   = {CAP 6776 -- Information Retrieval},
  url    = {https://github.com/Arungharami/biomedical-hybrid-ir}
}`}</code>
        </pre>
      </Card>
    </div>
  );
}
