"use client";

import { useRef, useState } from "react";

export type Chapter = { t: number; label: string };

export type Talk = {
  id: string;
  kicker: string;
  title: string;
  duration: string;
  size: string;
  style: string;
  src: string;
  poster: string;
  summary: string;
  highlights: string[];
  chapters: Chapter[];
};

function fmt(s: number) {
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}

export default function VideoStudio({ talks }: { talks: Talk[] }) {
  const [idx, setIdx] = useState(0);
  const [now, setNow] = useState(0);
  const ref = useRef<HTMLVideoElement>(null);
  const talk = talks[idx];
  const active = talk.chapters.reduce((acc, c, i) => (now >= c.t ? i : acc), 0);

  const pick = (i: number) => {
    if (i === idx) return;
    ref.current?.pause();
    setNow(0);
    setIdx(i);
  };

  const jump = (t: number) => {
    const v = ref.current;
    if (!v) return;
    v.currentTime = t;
    v.play().catch(() => {});
  };

  return (
    <div className="flex flex-col gap-5">
      {/* Talk selector */}
      <div className="grid gap-3 sm:grid-cols-2" role="tablist" aria-label="Choose a video">
        {talks.map((t, i) => {
          const on = i === idx;
          return (
            <button
              key={t.id}
              role="tab"
              aria-selected={on}
              onClick={() => pick(i)}
              className={`group flex items-center gap-4 rounded-2xl border p-3 text-left transition-all ${
                on
                  ? "border-accent bg-accent-soft shadow-[0_0_0_3px_var(--accent-soft)]"
                  : "border-border bg-surface hover:border-accent/60"
              }`}
            >
              <span className="relative shrink-0 overflow-hidden rounded-lg">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={t.poster} alt="" className="h-16 w-28 object-cover sm:h-[72px] sm:w-32" />
                <span className="absolute inset-0 flex items-center justify-center bg-black/25 text-white">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-black/55 text-xs backdrop-blur">
                    ▶
                  </span>
                </span>
                <span className="absolute bottom-1 right-1 rounded bg-black/70 px-1 text-[10px] font-medium text-white tabular">
                  {t.duration}
                </span>
              </span>
              <span className="min-w-0">
                <span className={`block text-[11px] font-semibold uppercase tracking-wider ${on ? "text-accent" : "text-text-muted"}`}>
                  {t.kicker}
                </span>
                <span className="mt-0.5 block font-semibold leading-snug text-text-primary">{t.title}</span>
                <span className="mt-0.5 block text-xs text-text-secondary">{t.style}</span>
              </span>
            </button>
          );
        })}
      </div>

      {/* Player + chapters */}
      <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
        <div className="overflow-hidden rounded-2xl border border-border bg-black shadow-xl shadow-black/10">
          <video
            key={talk.id}
            ref={ref}
            controls
            preload="metadata"
            poster={talk.poster}
            playsInline
            onTimeUpdate={(e) => setNow(e.currentTarget.currentTime)}
            className="aspect-video w-full"
          >
            <source src={talk.src} type="video/mp4" />
            Your browser does not support HTML5 video. <a href={talk.src}>Download the video</a>.
          </video>
        </div>
        <div className="flex flex-col rounded-2xl border border-border bg-surface p-3">
          <p className="flex items-center justify-between px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
            <span>Chapters</span>
            <span className="tabular">{talk.chapters.length}</span>
          </p>
          <ol className="flex max-h-[300px] flex-col gap-0.5 overflow-y-auto lg:max-h-[420px]">
            {talk.chapters.map((c, i) => (
              <li key={c.t}>
                <button
                  onClick={() => jump(c.t)}
                  className={`flex w-full items-baseline gap-3 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ${
                    i === active
                      ? "bg-accent-soft font-medium text-accent"
                      : "text-text-secondary hover:bg-surface-2 hover:text-text-primary"
                  }`}
                >
                  <span className="w-9 shrink-0 font-mono text-xs tabular">{fmt(c.t)}</span>
                  <span>{c.label}</span>
                </button>
              </li>
            ))}
          </ol>
        </div>
      </div>

      {/* Details */}
      <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
        <div className="rounded-2xl border border-border bg-surface p-5 sm:p-6">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-accent">About this video</p>
          <h3 className="mt-1 text-xl font-semibold text-text-primary">{talk.title}</h3>
          <p className="mt-2 leading-relaxed text-text-secondary">{talk.summary}</p>
          <ul className="mt-4 grid gap-2 sm:grid-cols-2">
            {talk.highlights.map((h) => (
              <li key={h} className="flex gap-2.5 rounded-xl bg-surface-2 px-3 py-2.5 text-sm text-text-primary">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-accent" />
                <span>{h}</span>
              </li>
            ))}
          </ul>
        </div>
        <dl className="grid grid-cols-2 gap-3 self-start rounded-2xl border border-border bg-surface p-5 lg:grid-cols-1">
          {[
            ["Length", talk.duration],
            ["Format", "MP4 · 720p · narrated"],
            ["Presenter", "Arun Kumar Gharami"],
            ["Course", "CAP 6776 · FAU"],
          ].map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs text-text-muted">{k}</dt>
              <dd className="font-medium text-text-primary">{v}</dd>
            </div>
          ))}
          <a
            href={talk.src}
            download
            className="col-span-2 mt-1 rounded-lg bg-accent px-3 py-2 text-center text-sm font-medium text-white hover:opacity-90 lg:col-span-1"
          >
            Download MP4 ({talk.size})
          </a>
        </dl>
      </div>
    </div>
  );
}
