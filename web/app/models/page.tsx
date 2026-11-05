import type { Metadata } from "next";
import Link from "next/link";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import { formatMetric, MODEL_LABELS, models, metrics } from "@/lib/data";

export const metadata: Metadata = { title: "Models" };

const SHOWN = ["P@10", "Recall@100", "MAP", "MRR@10", "nDCG@10"] as const;

export default function ModelsPage() {
  return (
    <div>
      <PageHeader
        eyebrow="M1 – M6"
        title="Models"
        description="Every model's pooling, normalization, and input-format choices are verified against the official Hugging Face model card before use — never assumed."
      />

      <div className="flex flex-col gap-4">
        {models.map((m) => {
          const modelMetrics = metrics[m.id]?.metrics as Record<string, number> | undefined;
          return (
            <Card key={m.id}>
              <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wide text-accent">{m.family}</p>
                  <h2 className="mt-1 text-lg font-semibold text-text-primary">{m.name}</h2>
                  {m.huggingface && (
                    <p className="mt-1 font-mono text-xs text-text-secondary">{m.huggingface}</p>
                  )}
                  <p className="mt-2 max-w-2xl text-sm text-text-secondary leading-relaxed">
                    {m.description}
                  </p>
                  <p className="mt-2 font-mono text-xs text-text-muted">{m.config}</p>
                </div>
                {modelMetrics && (
                  <dl className="grid shrink-0 grid-cols-3 gap-x-4 gap-y-2 text-sm sm:grid-cols-2">
                    {SHOWN.map((k) => (
                      <div key={k}>
                        <dt className="text-xs text-text-muted">{k}</dt>
                        <dd className="tabular font-medium text-text-primary">
                          {formatMetric(modelMetrics[k])}
                        </dd>
                      </div>
                    ))}
                  </dl>
                )}
              </div>
              {!modelMetrics && (
                <p className="mt-3 text-sm text-text-muted">
                  No metrics exported for {MODEL_LABELS[m.id] ?? m.name}.
                </p>
              )}
            </Card>
          );
        })}
      </div>

      <p className="mt-6 text-sm text-text-secondary">
        Compare all models side by side on the{" "}
        <Link href="/results" className="text-accent hover:underline">
          Results
        </Link>{" "}
        page.
      </p>
    </div>
  );
}
