"use client";

import { useRef, useState } from "react";

export type Chapter = { t: number; label: string };

function fmt(s: number) {
  const m = Math.floor(s / 60);
  return `${m}:${String(Math.floor(s % 60)).padStart(2, "0")}`;
}

export default function VideoChapters({
  src,
  poster,
  chapters,
}: {
  src: string;
  poster: string;
  chapters: Chapter[];
}) {
  const ref = useRef<HTMLVideoElement>(null);
  const [now, setNow] = useState(0);

  const active = chapters.reduce((acc, c, i) => (now >= c.t ? i : acc), 0);

  const jump = (t: number) => {
    const v = ref.current;
    if (!v) return;
    v.currentTime = t;
    v.play().catch(() => {});
  };

  return (
    <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
      <div className="overflow-hidden rounded-xl border border-border bg-black">
        <video
          ref={ref}
          controls
          preload="metadata"
          poster={poster}
          playsInline
          onTimeUpdate={(e) => setNow(e.currentTarget.currentTime)}
          className="aspect-video w-full"
        >
          <source src={src} type="video/mp4" />
          Your browser does not support HTML5 video.{" "}
          <a href={src}>Download the video</a>.
        </video>
      </div>
      <div className="rounded-xl border border-border bg-surface p-3">
        <p className="px-2 pb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
          Jump to section
        </p>
        <ol className="flex max-h-[340px] flex-col gap-0.5 overflow-y-auto lg:max-h-none">
          {chapters.map((c, i) => (
            <li key={c.t}>
              <button
                onClick={() => jump(c.t)}
                className={`flex w-full items-baseline gap-3 rounded-md px-2 py-1.5 text-left text-sm transition-colors ${
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
  );
}
