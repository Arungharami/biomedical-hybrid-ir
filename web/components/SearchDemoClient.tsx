"use client";

import { useState } from "react";
import { searchDemo } from "@/lib/search-demo";
import { MODEL_LABELS } from "@/lib/data";

const DEMO_MODELS = ["bm25", "medcpt", "hybrid_rrf", "hybrid_reranked"] as const;

export default function SearchDemoClient() {
  const [queryId, setQueryId] = useState(searchDemo[0]?.query_id ?? "");
  const entry = searchDemo.find((e) => e.query_id === queryId) ?? searchDemo[0];

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <label htmlFor="query-select" className="text-sm font-medium text-text-primary">
          Query:
        </label>
        <select
          id="query-select"
          value={queryId}
          onChange={(e) => setQueryId(e.target.value)}
          className="rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-primary"
        >
          {searchDemo.map((e) => (
            <option key={e.query_id} value={e.query_id}>
              {e.query_id} — &quot;{e.query}&quot;
            </option>
          ))}
        </select>
      </div>

      {entry && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          {DEMO_MODELS.map((model) => {
            const results = entry.results[model] ?? [];
            return (
              <div key={model} className="rounded-lg border border-border bg-surface p-4">
                <h3 className="mb-3 text-sm font-semibold text-text-primary">
                  {MODEL_LABELS[model] ?? model}
                </h3>
                {results.length === 0 ? (
                  <p className="text-sm text-text-muted">
                    No documents retrieved for this query (real behavior — see Error Analysis).
                  </p>
                ) : (
                  <ol className="flex flex-col gap-2">
                    {results.map((r, i) => (
                      <li
                        key={r.doc_id}
                        className={`rounded-md border px-3 py-2 text-sm ${
                          r.relevant
                            ? "border-good/30 bg-good/5"
                            : "border-border bg-surface-2"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-medium text-text-primary">
                            {i + 1}. {r.title || r.doc_id}
                          </span>
                          {r.relevant && (
                            <span className="shrink-0 rounded bg-good/15 px-1.5 py-0.5 text-[10px] font-medium text-good">
                              relevant
                            </span>
                          )}
                        </div>
                        <p className="mt-1 text-xs text-text-muted">{r.snippet}…</p>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
