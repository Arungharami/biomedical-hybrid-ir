import { readFileSync } from "node:fs";
import path from "node:path";
import katex from "katex";
import { Marked, type Tokens } from "marked";

/**
 * Turns content/paper.md into page segments at build time.
 *
 * - ```latex blocks are rendered to static HTML with KaTeX (no client JS).
 * - `<!-- figure:name -->` lines split the text; the page renders the named
 *   SVG figure (components/PaperFigures.tsx) between the HTML chunks.
 * - h2/h3 headings get stable ids, a table-of-contents entry and a
 *   "comment" link that opens a pre-filled GitHub issue for that section.
 */

export const REPO_URL = "https://github.com/Arungharami/biomedical-hybrid-ir";
export const SITE_URL = "https://biomedical-hybrid-ir.vercel.app";

export type TocEntry = { id: string; text: string; depth: 2 | 3 };
export type Segment = { kind: "html"; html: string } | { kind: "figure"; name: string };

const FIGURE_MARKER = /^<!--\s*figure:([a-z0-9-]+)\s*-->\s*$/gm;

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/<[^>]+>/g, "")
    .replace(/&[a-z#0-9]+;/g, "")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function plainText(html: string): string {
  return html
    .replace(/<[^>]+>/g, "")
    .replace(/&amp;/g, "&")
    .replace(/&#39;|&apos;/g, "'")
    .replace(/&quot;/g, '"');
}

export function issueUrl(section: string, anchor: string): string {
  const title = `Paper feedback: ${section}`;
  const body = [
    `**Section:** ${section}`,
    `**Link:** ${SITE_URL}/paper#${anchor}`,
    "",
    "<!-- Write your comment below. Quote the sentence you mean if it helps. -->",
    "",
  ].join("\n");
  return `${REPO_URL}/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}`;
}

function buildMarked(toc: TocEntry[]): Marked {
  const used = new Map<string, number>();
  const marked = new Marked({ gfm: true });
  marked.use({
    renderer: {
      code({ text, lang }: Tokens.Code) {
        if (lang === "latex") {
          const html = katex.renderToString(text, { displayMode: true, throwOnError: true, strict: "ignore" });
          return `<div class="paper-math" role="math">${html}</div>\n`;
        }
        return false; // default rendering for any other code block
      },
      heading({ tokens, depth }: Tokens.Heading) {
        const inner = this.parser.parseInline(tokens);
        const label = plainText(inner);
        const base = slugify(label) || "section";
        const n = used.get(base) ?? 0;
        used.set(base, n + 1);
        const id = n ? `${base}-${n}` : base;
        if (depth === 2 || depth === 3) toc.push({ id, text: label, depth });
        const comment =
          depth === 2 || depth === 3
            ? ` <a class="paper-comment-link" href="${issueUrl(label, id)}" target="_blank" rel="noreferrer" aria-label="Comment on ${label.replace(/"/g, "")}">Comment</a>`
            : "";
        return `<h${depth} id="${id}"><a class="paper-anchor" href="#${id}">${inner}</a>${comment}</h${depth}>\n`;
      },
    },
  });
  return marked;
}

function toHtml(marked: Marked, markdown: string): string {
  const html = marked.parse(markdown, { async: false }) as string;
  // Wide tables scroll inside their own box instead of the whole page.
  return html.replace(/<table>/g, '<div class="paper-table"><table>').replace(/<\/table>/g, "</table></div>");
}

export function loadPaper(): { segments: Segment[]; toc: TocEntry[]; words: number } {
  const source = readFileSync(path.join(process.cwd(), "content", "paper.md"), "utf8");
  const toc: TocEntry[] = [];
  const marked = buildMarked(toc);
  const segments: Segment[] = [];

  let last = 0;
  for (const match of source.matchAll(FIGURE_MARKER)) {
    const chunk = source.slice(last, match.index);
    if (chunk.trim()) segments.push({ kind: "html", html: toHtml(marked, chunk) });
    segments.push({ kind: "figure", name: match[1] });
    last = (match.index ?? 0) + match[0].length;
  }
  const tail = source.slice(last);
  if (tail.trim()) segments.push({ kind: "html", html: toHtml(marked, tail) });

  const words = source
    .replace(/```[\s\S]*?```/g, " ")
    .split(/\s+/)
    .filter(Boolean).length;
  return { segments, toc, words };
}
