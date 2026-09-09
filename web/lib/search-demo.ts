import searchDemoRaw from "@/data/search-demo.json";

export interface SearchDemoResult {
  doc_id: string;
  score: number;
  title: string;
  snippet: string;
  relevant: boolean;
}

export interface SearchDemoEntry {
  query_id: string;
  query: string;
  results: Record<string, SearchDemoResult[]>;
}

export const searchDemo = searchDemoRaw as unknown as SearchDemoEntry[];
