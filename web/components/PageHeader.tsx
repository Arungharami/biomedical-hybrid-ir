export default function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <div className="relative mb-10 overflow-hidden rounded-3xl border border-border bg-surface px-6 py-8 sm:px-10 sm:py-10">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-70"
        style={{
          background:
            "radial-gradient(50% 120% at 100% 0%, var(--accent-soft) 0%, transparent 70%), radial-gradient(30% 80% at 0% 100%, rgba(204,0,0,.06) 0%, transparent 70%)",
        }}
      />
      <div aria-hidden className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-[#003366] via-accent to-[#cc0000]" />
      <div className="relative max-w-3xl">
        {eyebrow && (
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-accent">{eyebrow}</p>
        )}
        <h1 className="text-3xl font-bold tracking-tight text-text-primary sm:text-4xl">{title}</h1>
        {description && <p className="mt-3 text-lg leading-relaxed text-text-secondary">{description}</p>}
      </div>
    </div>
  );
}
