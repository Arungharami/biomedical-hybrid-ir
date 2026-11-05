"use client";

import { useCallback, useEffect, useRef, useState } from "react";

export type Deck = {
  id: string;
  title: string;
  subtitle: string;
  folder: string; // e.g. /course/slides/fau
  count: number;
  pptx: string;
  pdf: string;
};

function pad(n: number) {
  return String(n).padStart(2, "0");
}

export default function SlideViewer({ decks }: { decks: Deck[] }) {
  const [deckIdx, setDeckIdx] = useState(0);
  const [slide, setSlide] = useState(1);
  const frameRef = useRef<HTMLDivElement>(null);
  const thumbsRef = useRef<HTMLDivElement>(null);
  const deck = decks[deckIdx];

  const go = useCallback(
    (n: number) => setSlide(Math.min(deck.count, Math.max(1, n))),
    [deck.count]
  );

  useEffect(() => {
    // Scroll only the thumbnail strip — never the page.
    const strip = thumbsRef.current;
    const el = strip?.querySelector<HTMLElement>(`[data-slide="${slide}"]`);
    if (!strip || !el) return;
    const left = el.offsetLeft - strip.clientWidth / 2 + el.clientWidth / 2;
    strip.scrollTo({ left: Math.max(0, left), behavior: "smooth" });
  }, [slide, deckIdx]);

  const onKey = (e: React.KeyboardEvent) => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      go(slide + 1);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      go(slide - 1);
    }
  };

  const fullscreen = () => {
    const el = frameRef.current;
    if (!el) return;
    if (document.fullscreenElement) document.exitFullscreen();
    else el.requestFullscreen?.();
  };

  return (
    <div className="rounded-xl border border-border bg-surface p-3 sm:p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-1 rounded-lg bg-surface-2 p-1" role="tablist">
          {decks.map((d, i) => (
            <button
              key={d.id}
              role="tab"
              aria-selected={i === deckIdx}
              onClick={() => {
                setDeckIdx(i);
                setSlide(1);
              }}
              className={`rounded-md px-3 py-1.5 text-sm transition-colors ${
                i === deckIdx
                  ? "bg-surface font-medium text-text-primary shadow-sm"
                  : "text-text-secondary hover:text-text-primary"
              }`}
            >
              {d.title}
              <span className="ml-1.5 text-xs text-text-muted">{d.count}</span>
            </button>
          ))}
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <a
            href={deck.pptx}
            download
            className="rounded-md border border-border px-3 py-1.5 font-medium text-text-primary hover:bg-surface-2"
          >
            Download .pptx
          </a>
          <a
            href={deck.pdf}
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-border px-3 py-1.5 font-medium text-text-primary hover:bg-surface-2"
          >
            Open PDF ↗
          </a>
        </div>
      </div>

      <p className="mb-3 text-sm text-text-secondary">{deck.subtitle}</p>

      <div
        ref={frameRef}
        tabIndex={0}
        onKeyDown={onKey}
        className="group relative overflow-hidden rounded-lg border border-border bg-black outline-none focus-visible:ring-2 focus-visible:ring-accent"
        aria-label={`${deck.title}, slide ${slide} of ${deck.count}. Use arrow keys to navigate.`}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`${deck.folder}/${pad(slide)}.jpg`}
          alt={`${deck.title} — slide ${slide}`}
          className="mx-auto aspect-video h-auto w-full object-contain"
        />
        <button
          onClick={() => go(slide - 1)}
          disabled={slide === 1}
          aria-label="Previous slide"
          className="absolute left-2 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/55 text-white opacity-80 transition hover:bg-black/75 disabled:opacity-0"
        >
          ‹
        </button>
        <button
          onClick={() => go(slide + 1)}
          disabled={slide === deck.count}
          aria-label="Next slide"
          className="absolute right-2 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-full bg-black/55 text-white opacity-80 transition hover:bg-black/75 disabled:opacity-0"
        >
          ›
        </button>
        <div className="absolute bottom-2 right-2 flex items-center gap-2">
          <span className="rounded bg-black/60 px-2 py-0.5 text-xs text-white tabular">
            {slide} / {deck.count}
          </span>
          <button
            onClick={fullscreen}
            aria-label="Toggle fullscreen"
            className="rounded bg-black/60 px-2 py-0.5 text-xs text-white hover:bg-black/80"
          >
            ⛶ Fullscreen
          </button>
        </div>
      </div>

      <div ref={thumbsRef} className="relative mt-3 flex gap-2 overflow-x-auto pb-1">
        {Array.from({ length: deck.count }, (_, i) => i + 1).map((n) => (
          <button
            key={n}
            data-slide={n}
            onClick={() => setSlide(n)}
            aria-label={`Go to slide ${n}`}
            className={`relative shrink-0 overflow-hidden rounded-md border-2 transition ${
              n === slide ? "border-accent" : "border-transparent opacity-70 hover:opacity-100"
            }`}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={`${deck.folder}/${pad(n)}.jpg`}
              alt=""
              loading="lazy"
              className="h-14 w-24 object-cover sm:h-16 sm:w-28"
            />
            <span className="absolute bottom-0.5 left-0.5 rounded bg-black/60 px-1 text-[10px] text-white">
              {n}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
