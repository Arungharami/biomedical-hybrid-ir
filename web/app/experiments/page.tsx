import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import StatusBadge from "@/components/StatusBadge";
import { experiments } from "@/lib/data";

export const metadata: Metadata = { title: "Experiments" };

export default function ExperimentsPage() {
  const sorted = [...experiments].sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  return (
    <div>
      <PageHeader
        eyebrow="Experiment registry"
        title="Experiments"
        description="Every experiment run for this study writes a manifest recording its exact configuration, environment, and runtime — so results can be traced back to a reproducible run, never a guess."
      />

      <div className="flex flex-col gap-4">
        {sorted.map((exp) => (
          <Card key={exp.experiment_id}>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <p className="font-mono text-sm font-semibold text-text-primary">{exp.experiment_id}</p>
                <p className="mt-1 text-sm text-text-secondary">{exp.model}</p>
              </div>
              <StatusBadge status={exp.status} />
            </div>
            <dl className="mt-4 grid grid-cols-2 gap-x-6 gap-y-2 text-xs sm:grid-cols-4">
              <div>
                <dt className="text-text-muted">Split</dt>
                <dd className="font-medium text-text-primary">{exp.split}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Device</dt>
                <dd className="font-medium text-text-primary">{exp.device}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Seed</dt>
                <dd className="tabular font-medium text-text-primary">{exp.seed}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Runtime</dt>
                <dd className="tabular font-medium text-text-primary">
                  {exp.runtime_seconds.toFixed(2)}s
                </dd>
              </div>
              <div>
                <dt className="text-text-muted">Python</dt>
                <dd className="font-medium text-text-primary">{exp.python_version}</dd>
              </div>
              <div>
                <dt className="text-text-muted">Git commit</dt>
                <dd className="font-mono font-medium text-text-primary">
                  {exp.git_commit.slice(0, 10)}
                </dd>
              </div>
              <div>
                <dt className="text-text-muted">Timestamp (UTC)</dt>
                <dd className="font-medium text-text-primary">
                  {new Date(exp.timestamp).toISOString().replace("T", " ").slice(0, 19)}
                </dd>
              </div>
              <div>
                <dt className="text-text-muted">Dataset</dt>
                <dd className="font-medium text-text-primary">{exp.dataset}</dd>
              </div>
            </dl>
            {exp.error && (
              <p className="mt-3 rounded-md border border-bad/30 bg-bad/10 px-3 py-2 text-xs text-bad">
                Error preserved: {exp.error}
              </p>
            )}
          </Card>
        ))}
      </div>

      <Card title="Manifest schema" className="mt-6">
        <p className="text-sm text-text-secondary leading-relaxed">
          Every manifest is validated against a required schema (
          <code className="rounded bg-surface-2 px-1.5 py-0.5 font-mono text-xs">
            src/biomedical_ir/manifests.py
          </code>
          ) before being written: experiment_id, timestamp, git_commit, dataset, split, model,
          parameters, seed, device, python_version, library_versions, runtime_seconds, and status
          (pending / running / complete / failed — a failed run must preserve its error, never be
          silently replaced with a guessed value).
        </p>
      </Card>
    </div>
  );
}
