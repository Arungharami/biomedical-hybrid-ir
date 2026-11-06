"use client";

import { useEffect, useRef } from "react";

/*
 * Reader comments for /paper, stored as a GitHub Discussion on the repo via
 * giscus (https://giscus.app). Readers sign in with GitHub to post.
 *
 * To activate: enable Discussions on the repo, install the giscus GitHub App
 * on it, then set NEXT_PUBLIC_GISCUS_CATEGORY_ID in Vercel (giscus.app shows
 * the value). Until then the box falls back to "open a GitHub issue".
 */

const REPO = "Arungharami/biomedical-hybrid-ir";
const REPO_ID = "R_kgDOUTumvQ";
const CATEGORY = process.env.NEXT_PUBLIC_GISCUS_CATEGORY ?? "General";
const CATEGORY_ID = process.env.NEXT_PUBLIC_GISCUS_CATEGORY_ID ?? "";

function currentTheme() {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export default function PaperComments({ fallbackIssueUrl }: { fallbackIssueUrl: string }) {
  const host = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = host.current;
    if (!el || !CATEGORY_ID || el.querySelector("script, iframe")) return;
    const s = document.createElement("script");
    s.src = "https://giscus.app/client.js";
    s.async = true;
    s.crossOrigin = "anonymous";
    Object.entries({
      "data-repo": REPO,
      "data-repo-id": REPO_ID,
      "data-category": CATEGORY,
      "data-category-id": CATEGORY_ID,
      "data-mapping": "specific",
      "data-term": "Paper: Hybrid Biomedical Retrieval on NFCorpus",
      "data-strict": "1",
      "data-reactions-enabled": "1",
      "data-emit-metadata": "0",
      "data-input-position": "top",
      "data-theme": currentTheme(),
      "data-lang": "en",
      "data-loading": "lazy",
    }).forEach(([k, v]) => s.setAttribute(k, v));
    el.appendChild(s);

    // Keep giscus in step with the site's light/dark toggle.
    const observer = new MutationObserver(() => {
      const frame = el.querySelector<HTMLIFrameElement>("iframe.giscus-frame");
      frame?.contentWindow?.postMessage({ giscus: { setConfig: { theme: currentTheme() } } }, "https://giscus.app");
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => observer.disconnect();
  }, []);

  if (!CATEGORY_ID) {
    return (
      <div className="rounded-xl border border-dashed border-border bg-surface-2 p-5 text-sm text-text-secondary">
        <p>
          Comments on this page open shortly. Until then, every section heading has a{" "}
          <span className="font-medium text-text-primary">Comment</span> link, or you can{" "}
          <a href={fallbackIssueUrl} target="_blank" rel="noreferrer" className="font-medium text-accent hover:underline">
            leave general feedback on GitHub ↗
          </a>
          .
        </p>
      </div>
    );
  }
  return <div ref={host} className="giscus min-h-24" />;
}
