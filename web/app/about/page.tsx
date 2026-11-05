import type { Metadata } from "next";
import PageHeader from "@/components/PageHeader";
import Card from "@/components/Card";
import { AUTHOR, INSTRUCTOR } from "@/lib/author";

export const metadata: Metadata = { title: "About" };

export default function AboutPage() {
  return (
    <div>
      <PageHeader eyebrow="CAP 6776 — Information Retrieval" title="About this project" />

      <section className="relative mb-6 overflow-hidden rounded-3xl bg-[#07122b] text-white">
        <div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(55% 90% at 0% 0%, rgba(37,99,235,.5) 0%, transparent 60%), radial-gradient(45% 80% at 100% 100%, rgba(204,0,0,.32) 0%, transparent 60%)",
          }}
        />
        <div className="relative grid gap-6 p-6 sm:grid-cols-[auto_1fr] sm:items-center sm:p-8">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={AUTHOR.photo}
            alt={AUTHOR.name}
            className="h-28 w-28 rounded-2xl border border-white/20 object-cover object-[50%_25%] shadow-xl shadow-black/30"
          />
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-sky-300">About the author</p>
            <h2 className="mt-1 text-2xl font-bold tracking-tight sm:text-3xl">{AUTHOR.name}</h2>
            <p className="mt-1 text-white/70">{AUTHOR.role}</p>
            <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/75">
              I designed, built and evaluated this hybrid biomedical retrieval system as my CAP 6776 Information
              Retrieval course project at Florida Atlantic University, under {INSTRUCTOR.name}. My website has more
              about my background and my other AI research and engineering work.
            </p>
            <div className="mt-5 flex flex-wrap gap-3">
              <a
                href={AUTHOR.website}
                target="_blank"
                rel="noopener"
                className="rounded-xl bg-white px-4 py-2 text-sm font-semibold text-[#07122b] transition hover:bg-sky-50"
              >
                Visit {AUTHOR.websiteLabel} ↗
              </a>
              <a
                href={AUTHOR.github}
                target="_blank"
                rel="noopener"
                className="rounded-xl border border-white/25 bg-white/10 px-4 py-2 text-sm font-semibold backdrop-blur transition hover:bg-white/20"
              >
                GitHub ↗
              </a>
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card title="Course project">
          <p className="text-sm text-text-secondary leading-relaxed">
            Built for CAP 6776 (Information Retrieval). The primary deliverable is a scientifically
            reproducible information retrieval experiment on NFCorpus — this website presents the
            experiment and its verified results; it is not the deliverable itself.
          </p>
        </Card>

        <Card title="Scientific-integrity statement">
          <p className="text-sm text-text-secondary leading-relaxed">
            This project reports only genuine experimental output. No metric, dataset count,
            citation, or statistical result is fabricated. Pending experiments are labeled
            &quot;pending&quot;, never filled with plausible-looking numbers; failed runs are
            labeled &quot;failed&quot; with their error preserved. Every retrieval model choice
            (pooling, normalization, instruction prefixes, input formats) was verified against the
            official Hugging Face model card before use, not assumed.
          </p>
        </Card>

        <Card title="Architecture">
          <p className="text-sm text-text-secondary leading-relaxed">
            Hugging Face → Google Colab / local Python experiments → verified JSON/CSV artifacts →
            GitHub → Next.js → Vercel. Large models and embeddings stay in Colab/local
            environments — this website reads only compact exported results and never runs a
            transformer model itself.
          </p>
        </Card>

        <Card title="Technology">
          <ul className="space-y-1.5 text-sm text-text-secondary">
            <li>Research pipeline: Python 3.11, PyTorch, Transformers, sentence-transformers, FAISS, pytrec_eval</li>
            <li>Research portal: Next.js (App Router), TypeScript, Tailwind CSS</li>
            <li>Deployment: Vercel</li>
          </ul>
        </Card>
      </div>

      <Card title="Citation" className="mt-6">
        <pre className="overflow-x-auto rounded-md bg-surface-2 p-4 text-xs text-text-primary">
          <code>{`@misc{gharami2026hybridir,
  title  = {Hybrid Biomedical Information Retrieval with Lexical, Dense,
            and Cross-Encoder Reranking: A Reproducible Study on NFCorpus},
  author = {Gharami, Arun Kumar},
  year   = {2026},
  note   = {CAP 6776 -- Information Retrieval, Florida Atlantic University},
  url    = {https://biomedical-hybrid-ir.vercel.app},
  howpublished = {\\url{https://github.com/Arungharami/biomedical-hybrid-ir}}
}`}</code>
        </pre>
      </Card>
    </div>
  );
}
