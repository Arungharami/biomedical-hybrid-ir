import Link from "next/link";

const COLS = [
  {
    h: "Project",
    links: [
      { href: "/course", label: "Course Project" },
      { href: "/roadmap", label: "Research Roadmap" },
      { href: "/paper", label: "Paper" },
      { href: "/results", label: "Results" },
    ],
  },
  {
    h: "Study",
    links: [
      { href: "/dataset", label: "Dataset" },
      { href: "/pipeline", label: "Pipeline" },
      { href: "/evaluation", label: "Evaluation" },
      { href: "/error-analysis", label: "Error Analysis" },
    ],
  },
  {
    h: "Resources",
    links: [
      { href: "/reproducibility", label: "Reproducibility" },
      { href: "/search", label: "Search Demo" },
      { href: "https://github.com/Arungharami/biomedical-hybrid-ir", label: "GitHub ↗" },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="mt-20 border-t border-border bg-surface">
      <div className="mx-auto max-w-7xl px-4 py-12 sm:px-6">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(3,1fr)]">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#1d4ed8] to-[#07122b] text-xs font-bold text-white">
                IR
              </span>
              <span className="font-semibold text-text-primary">Hybrid Biomedical IR</span>
            </div>
            <p className="mt-3 max-w-sm text-sm leading-relaxed text-text-secondary">
              Lexical, dense and cross-encoder retrieval for everyday health questions — a reproducible study on
              NFCorpus.
            </p>
            <div className="mt-4 text-sm text-text-secondary">
              <p>
                <span className="text-text-muted">Student</span> · Arun Kumar Gharami
              </p>
              <p>
                <span className="text-text-muted">Instructor</span> · Dingding Wang
              </p>
              <p>
                <span className="text-text-muted">Course</span> · CAP 6776 Information Retrieval, Florida Atlantic
                University
              </p>
            </div>
          </div>
          {COLS.map((c) => (
            <div key={c.h}>
              <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-text-muted">{c.h}</p>
              <ul className="mt-3 flex flex-col gap-2 text-sm">
                {c.links.map((l) =>
                  l.href.startsWith("http") ? (
                    <li key={l.href}>
                      <a href={l.href} target="_blank" rel="noreferrer" className="text-text-secondary hover:text-accent">
                        {l.label}
                      </a>
                    </li>
                  ) : (
                    <li key={l.href}>
                      <Link href={l.href} className="text-text-secondary hover:text-accent">
                        {l.label}
                      </Link>
                    </li>
                  )
                )}
              </ul>
            </div>
          ))}
        </div>
        <p className="mt-10 border-t border-border pt-6 text-xs leading-relaxed text-text-muted">
          Scientific-integrity statement: this site reports only genuine experimental output. No metric, dataset count,
          citation or statistical result is fabricated. Planned experiments are labelled as pending until they run.
        </p>
      </div>
    </footer>
  );
}
