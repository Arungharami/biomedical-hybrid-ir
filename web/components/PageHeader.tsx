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
    <div className="mb-8 max-w-3xl">
      {eyebrow && (
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-accent">{eyebrow}</p>
      )}
      <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">{title}</h1>
      {description && <p className="mt-3 text-text-secondary leading-relaxed">{description}</p>}
    </div>
  );
}
