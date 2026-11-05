"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import ThemeToggle from "./ThemeToggle";

const PRIMARY = [
  { href: "/", label: "Overview" },
  { href: "/course", label: "Course Project" },
  { href: "/results", label: "Results" },
  { href: "/roadmap", label: "Roadmap" },
  { href: "/paper", label: "Paper" },
];

const EXPLORE = [
  { href: "/dataset", label: "Dataset", desc: "NFCorpus stats & provenance" },
  { href: "/pipeline", label: "Pipeline", desc: "Full retrieval architecture" },
  { href: "/models", label: "Models", desc: "TF-IDF → cross-encoder" },
  { href: "/experiments", label: "Experiments", desc: "Run manifests" },
  { href: "/evaluation", label: "Evaluation", desc: "Metrics & significance" },
  { href: "/error-analysis", label: "Error Analysis", desc: "Query-level wins & losses" },
  { href: "/efficiency", label: "Efficiency", desc: "Latency & index size" },
  { href: "/search", label: "Search Demo", desc: "Precomputed rankings" },
  { href: "/reproducibility", label: "Reproducibility", desc: "Regenerate every number" },
  { href: "/about", label: "About", desc: "Project & author" },
];

export default function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [explore, setExplore] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const exploreActive = EXPLORE.some((l) => l.href === pathname);

  useEffect(() => {
    if (!explore) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setExplore(false);
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setExplore(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [explore]);

  const pill = (active: boolean) =>
    `whitespace-nowrap rounded-full px-3.5 py-1.5 transition-colors ${
      active
        ? "bg-accent-soft font-medium text-accent"
        : "text-text-secondary hover:bg-surface-2 hover:text-text-primary"
    }`;

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2.5 font-semibold tracking-tight">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#1d4ed8] to-[#07122b] text-xs font-bold text-white shadow-sm">
            IR
          </span>
          <span className="hidden leading-tight sm:block">
            <span className="block text-sm">Hybrid Biomedical IR</span>
            <span className="block text-[10px] font-medium uppercase tracking-[0.14em] text-text-muted">
              FAU · CAP 6776
            </span>
          </span>
        </Link>

        <nav className="hidden items-center gap-1 text-sm lg:flex">
          {PRIMARY.map((l) => (
            <Link key={l.href} href={l.href} className={pill(pathname === l.href)}>
              {l.label}
            </Link>
          ))}
          <div ref={ref} className="relative">
            <button
              onClick={() => setExplore((v) => !v)}
              aria-expanded={explore}
              aria-haspopup="true"
              className={`${pill(exploreActive)} flex items-center gap-1`}
            >
              Explore
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className={`transition-transform ${explore ? "rotate-180" : ""}`}>
                <path d="m6 9 6 6 6-6" />
              </svg>
            </button>
            {explore && (
              <div className="absolute right-0 top-full mt-2 grid w-[460px] grid-cols-2 gap-1 rounded-2xl border border-border bg-surface p-2 shadow-2xl shadow-black/15">
                {EXPLORE.map((l) => (
                  <Link
                    key={l.href}
                    href={l.href}
                    onClick={() => setExplore(false)}
                    className={`rounded-xl px-3 py-2 transition-colors ${
                      pathname === l.href ? "bg-accent-soft" : "hover:bg-surface-2"
                    }`}
                  >
                    <span className={`block text-sm font-medium ${pathname === l.href ? "text-accent" : "text-text-primary"}`}>
                      {l.label}
                    </span>
                    <span className="block text-xs text-text-muted">{l.desc}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </nav>

        <div className="flex items-center gap-2">
          <a
            href="https://github.com/Arungharami/biomedical-hybrid-ir"
            target="_blank"
            rel="noreferrer"
            className="hidden rounded-full border border-border px-3 py-1.5 text-sm font-medium text-text-primary hover:bg-surface-2 md:inline-block"
          >
            GitHub ↗
          </a>
          <ThemeToggle />
          <button
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-text-secondary lg:hidden"
            aria-label="Toggle menu"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {open ? <path d="M18 6 6 18M6 6l12 12" /> : <path d="M3 6h18M3 12h18M3 18h18" />}
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <nav className="max-h-[75vh] overflow-y-auto border-t border-border bg-surface px-4 py-3 lg:hidden">
          <div className="flex flex-col gap-0.5">
            {PRIMARY.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-2 text-sm ${
                  pathname === l.href ? "bg-accent-soft font-medium text-accent" : "text-text-primary hover:bg-surface-2"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </div>
          <p className="mt-3 px-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-text-muted">Explore</p>
          <div className="mt-1 grid grid-cols-2 gap-0.5">
            {EXPLORE.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className={`rounded-lg px-3 py-2 text-sm ${
                  pathname === l.href ? "bg-accent-soft font-medium text-accent" : "text-text-secondary hover:bg-surface-2"
                }`}
              >
                {l.label}
              </Link>
            ))}
          </div>
        </nav>
      )}
    </header>
  );
}
