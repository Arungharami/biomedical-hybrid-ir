export default function Footer() {
  return (
    <footer className="mt-16 border-t border-border bg-surface">
      <div className="mx-auto max-w-7xl px-4 py-8 text-sm text-text-secondary sm:px-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="font-medium text-text-primary">
              Hybrid Biomedical Information Retrieval with Lexical, Dense, and Cross-Encoder Reranking
            </p>
            <p className="mt-1 max-w-xl">
              CAP 6776 — Information Retrieval. A reproducible study on NFCorpus. All results on
              this site are genuine experimental output — see{" "}
              <a href="/reproducibility" className="text-accent hover:underline">
                reproducibility
              </a>{" "}
              for how to regenerate them.
            </p>
          </div>
          <div className="flex flex-col gap-1">
            <a
              href="https://github.com/Arungharami/biomedical-hybrid-ir"
              target="_blank"
              rel="noreferrer"
              className="text-accent hover:underline"
            >
              GitHub repository ↗
            </a>
            <a href="/paper" className="text-accent hover:underline">
              Read the paper ↗
            </a>
          </div>
        </div>
        <p className="mt-6 text-xs text-text-muted">
          Scientific-integrity statement: this project reports only genuine experimental output.
          No metric, dataset count, citation, or statistical result is fabricated.
        </p>
      </div>
    </footer>
  );
}
