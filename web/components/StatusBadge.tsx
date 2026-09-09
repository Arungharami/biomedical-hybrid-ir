const STYLES: Record<string, string> = {
  complete: "bg-good/10 text-good border-good/30",
  in_progress: "bg-warn/10 text-warn border-warn/30",
  pending: "bg-surface-2 text-text-muted border-border",
  failed: "bg-bad/10 text-bad border-bad/30",
};

const ICONS: Record<string, string> = {
  complete: "✅",
  in_progress: "🟡",
  pending: "⚪",
  failed: "❌",
};

const LABELS: Record<string, string> = {
  complete: "Complete",
  in_progress: "In progress",
  pending: "Pending",
  failed: "Failed",
};

export default function StatusBadge({ status }: { status: string }) {
  const style = STYLES[status] ?? STYLES.pending;
  const icon = ICONS[status] ?? ICONS.pending;
  const label = LABELS[status] ?? status;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${style}`}
    >
      <span aria-hidden>{icon}</span>
      {label}
    </span>
  );
}
