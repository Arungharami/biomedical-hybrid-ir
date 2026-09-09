"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import ThemeToggle from "./ThemeToggle";

const LINKS = [
  { href: "/", label: "Overview" },
  { href: "/dataset", label: "Dataset" },
  { href: "/pipeline", label: "Pipeline" },
  { href: "/models", label: "Models" },
  { href: "/experiments", label: "Experiments" },
  { href: "/results", label: "Results" },
  { href: "/evaluation", label: "Evaluation" },
  { href: "/error-analysis", label: "Error Analysis" },
  { href: "/efficiency", label: "Efficiency" },
  { href: "/search", label: "Search Demo" },
  { href: "/paper", label: "Paper" },
  { href: "/reproducibility", label: "Reproducibility" },
  { href: "/about", label: "About" },
];

export default function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/90 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <span className="flex h-7 w-7 items-center justify-center rounded-md bg-accent text-xs font-bold text-white">
            IR
          </span>
          <span className="hidden text-sm sm:inline">Hybrid Biomedical IR</span>
        </Link>

        <nav className="hidden flex-1 items-center justify-center gap-1 overflow-x-auto text-sm lg:flex">
          {LINKS.map((link) => {
            const active = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`whitespace-nowrap rounded-md px-2.5 py-1.5 transition-colors ${
                  active
                    ? "bg-accent-soft text-accent font-medium"
                    : "text-text-secondary hover:bg-surface-2 hover:text-text-primary"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2">
          <ThemeToggle />
          <button
            className="flex h-8 w-8 items-center justify-center rounded-md border border-border text-text-secondary lg:hidden"
            aria-label="Toggle menu"
            onClick={() => setOpen((v) => !v)}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {open ? <path d="M18 6 6 18M6 6l12 12" /> : <path d="M3 6h18M3 12h18M3 18h18" />}
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <nav className="border-t border-border bg-surface px-4 py-2 lg:hidden">
          <div className="flex flex-col gap-0.5">
            {LINKS.map((link) => {
              const active = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  onClick={() => setOpen(false)}
                  className={`rounded-md px-3 py-2 text-sm ${
                    active
                      ? "bg-accent-soft text-accent font-medium"
                      : "text-text-secondary hover:bg-surface-2"
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </nav>
      )}
    </header>
  );
}
