import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import PageHeader from "@/components/PageHeader";
import PaperFigure from "@/components/PaperFigures";
import PaperToc from "@/components/PaperToc";
import PaperComments from "@/components/PaperComments";
import { REPO_URL, issueUrl, loadPaper } from "@/lib/paper";

const TITLE = "Hybrid Biomedical Retrieval on NFCorpus: Lexical, Dense, Fusion and Cross-Encoder Reranking";

export const metadata: Metadata = {
  title: "Paper",
  description:
    "Full paper: six retrieval systems on NFCorpus — TF-IDF, BM25, BGE, MedCPT, RRF fusion and cross-encoder reranking — with significance tests, figures and error analysis.",
};

export default function PaperPage() {
  const { segments, toc, words } = loadPaper();
  const minutes = Math.round(words / 230);

  return (
    <div>
      <PageHeader eyebrow="CAP 6776 — Information Retrieval · Final paper" title={TITLE} />

      <div className="mb-10 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-text-secondary">
        <span>
          <a href="https://arungharami.info" className="font-medium text-text-primary hover:text-accent">
            Arun Kumar Gharami
          </a>
        </span>
        <span>October 30, 2026</span>
        <span>{minutes} min read · 10 figures</span>
        <a href="#comments" className="text-accent hover:underline">Comments ↓</a>
        <a href={`${REPO_URL}/blob/main/web/content/paper.md`} target="_blank" rel="noreferrer" className="text-accent hover:underline">
          Source ↗
        </a>
      </div>

      <details className="mb-8 rounded-xl border border-border bg-surface px-4 py-3 text-sm lg:hidden">
        <summary className="cursor-pointer font-medium text-text-primary">Contents</summary>
        <ol className="mt-3 space-y-1.5">
          {toc.map((t) => (
            <li key={t.id} className={t.depth === 3 ? "pl-4" : ""}>
              <a href={`#${t.id}`} className="text-text-secondary hover:text-accent">{t.text}</a>
            </li>
          ))}
          <li>
            <a href="#comments" className="text-text-secondary hover:text-accent">Comments</a>
          </li>
        </ol>
      </details>

      <div className="grid grid-cols-1 gap-12 lg:grid-cols-[minmax(0,1fr)_15rem]">
        <article id="paper-article" className="paper min-w-0">
          {segments.map((s, i) =>
            s.kind === "html" ? (
              <div key={i} dangerouslySetInnerHTML={{ __html: s.html }} />
            ) : (
              <PaperFigure key={i} name={s.name} />
            ),
          )}

          <section id="comments" className="mt-16 scroll-mt-24 border-t border-border pt-10">
            <h2 className="!mt-0">Comments</h2>
            <p>
              Questions, corrections or ideas are welcome. Sign in with GitHub to comment below, or use the{" "}
              <span className="font-medium text-text-primary">Comment</span> link beside any heading to discuss one section.
            </p>
            <PaperComments fallbackIssueUrl={issueUrl("General", "comments")} />
          </section>
        </article>

        <aside className="hidden lg:block">
          <div className="sticky top-24 max-h-[calc(100vh-8rem)] overflow-y-auto pr-2">
            <PaperToc toc={toc} />
          </div>
        </aside>
      </div>
    </div>
  );
}
