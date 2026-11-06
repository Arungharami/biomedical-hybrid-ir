"use client";

import { useEffect, useState } from "react";
import type { TocEntry } from "@/lib/paper";

/** Sticky contents list with scroll-spy, plus a thin reading-progress bar. */
export default function PaperToc({ toc }: { toc: TocEntry[] }) {
  const [active, setActive] = useState<string>(toc[0]?.id ?? "");
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    const onScroll = () => {
      const article = document.getElementById("paper-article");
      if (!article) return;
      const rect = article.getBoundingClientRect();
      const total = rect.height - window.innerHeight;
      setProgress(total > 0 ? Math.min(1, Math.max(0, -rect.top / total)) : 0);
      let current = toc[0]?.id ?? "";
      for (const t of toc) {
        const h = document.getElementById(t.id);
        if (h && h.getBoundingClientRect().top < 120) current = t.id;
      }
      setActive(current);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, [toc]);

  return (
    <>
      <div className="fixed inset-x-0 top-0 z-50 h-0.5 bg-transparent" aria-hidden>
        <div className="h-full bg-accent transition-[width] duration-150" style={{ width: `${progress * 100}%` }} />
      </div>
      <nav aria-label="Contents" className="text-sm">
        <p className="mb-3 text-[11px] font-semibold uppercase tracking-[0.18em] text-text-muted">Contents</p>
        <ol className="space-y-1 border-l border-border">
          {toc.map((t) => (
            <li key={t.id}>
              <a
                href={`#${t.id}`}
                className={`-ml-px block border-l-2 py-0.5 leading-snug transition-colors ${t.depth === 3 ? "pl-6 text-[13px]" : "pl-3"} ${
                  active === t.id
                    ? "border-accent font-medium text-accent"
                    : "border-transparent text-text-secondary hover:text-text-primary"
                }`}
              >
                {t.text}
              </a>
            </li>
          ))}
          <li>
            <a href="#comments" className="-ml-px block border-l-2 border-transparent py-0.5 pl-3 text-text-secondary hover:text-text-primary">
              Comments
            </a>
          </li>
        </ol>
      </nav>
    </>
  );
}
