// Loads the static JSON artifacts exported by scripts/export_web_results.py.
// These are real research results -- this module never invents a value.

import datasetRaw from "@/data/dataset.json";
import modelsRaw from "@/data/models.json";
import experimentsRaw from "@/data/experiments.json";
import metricsRaw from "@/data/metrics.json";
import comparisonRaw from "@/data/comparison.json";
import errorAnalysisRaw from "@/data/error-analysis.json";
import efficiencyRaw from "@/data/efficiency.json";
import researchStatusRaw from "@/data/research-status.json";

import type {
  ComparisonData,
  DatasetData,
  EfficiencyRow,
  ErrorAnalysisData,
  ExperimentManifest,
  MetricsData,
  ModelMeta,
  ResearchStatusEntry,
} from "./types";

export const dataset = datasetRaw as unknown as DatasetData;
export const models = modelsRaw as unknown as ModelMeta[];
export const experiments = experimentsRaw as unknown as ExperimentManifest[];
export const metrics = metricsRaw as unknown as MetricsData;
export const comparison = comparisonRaw as unknown as ComparisonData;
export const errorAnalysis = errorAnalysisRaw as unknown as ErrorAnalysisData;
export const efficiency = efficiencyRaw as unknown as EfficiencyRow[];
export const researchStatus = researchStatusRaw as unknown as ResearchStatusEntry[];

export const MODEL_ORDER = [
  "tfidf",
  "bm25",
  "bge",
  "medcpt",
  "hybrid_rrf",
  "hybrid_reranked",
] as const;

export const MODEL_LABELS: Record<string, string> = {
  tfidf: "TF-IDF",
  bm25: "BM25",
  bge: "BGE",
  medcpt: "MedCPT",
  hybrid_rrf: "Hybrid RRF",
  hybrid_reranked: "Hybrid + Reranker",
};

export const SERIES_COLORS: Record<string, string> = {
  tfidf: "var(--series-1)",
  bm25: "var(--series-2)",
  bge: "var(--series-3)",
  medcpt: "var(--series-4)",
  hybrid_rrf: "var(--series-5)",
  hybrid_reranked: "var(--series-6)",
};

export function modelById(id: string): ModelMeta | undefined {
  return models.find((m) => m.id === id);
}

export function manifestByModelId(id: string): ExperimentManifest | undefined {
  const key = id.replace(/_/g, "-");
  return experiments.find(
    (e) => e.experiment_id === `exp-${key}-001` || e.experiment_id.includes(key)
  );
}

export function formatMetric(value: number | null | undefined, digits = 4): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toFixed(digits);
}

export function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return "—";
  if (ms >= 1000) return `${(ms / 1000).toFixed(2)} s`;
  return `${ms.toFixed(2)} ms`;
}
