export default function SourceNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="mt-3 rounded-md border border-border bg-surface-2 px-3 py-2 text-xs text-text-muted">
      <span className="font-medium text-text-secondary">Source: </span>
      {children}
    </p>
  );
}
