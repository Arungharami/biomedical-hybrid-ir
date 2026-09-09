import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import SearchDemoClient from "@/components/SearchDemoClient";

export const metadata: Metadata = { title: "Search Demo" };

export default function SearchPage() {
  return (
    <div>
      <PageHeader
        eyebrow="Research retrieval demonstration"
        title="Search Demo"
        description="See how BM25, MedCPT, Hybrid RRF, and the cross-encoder reranker rank the same real query differently."
      />

      <Card className="mb-6 border-accent/30 bg-accent-soft">
        <p className="text-sm font-medium text-text-primary">
          🔒 <strong>Precomputed experiment output</strong> — not a live model call.
        </p>
        <p className="mt-1 text-sm text-text-secondary leading-relaxed">
          Per Section 35 of the project spec, transformer models never run inside this Vercel
          deployment. Every ranking shown below was computed offline by the real pipeline
          (<code className="rounded bg-surface-2 px-1 py-0.5 font-mono text-xs">
            results/runs/*.json
          </code>
          ) against the real NFCorpus test split, then exported statically — never live inference,
          never fabricated.
        </p>
      </Card>

      <SearchDemoClient />
    </div>
  );
}
