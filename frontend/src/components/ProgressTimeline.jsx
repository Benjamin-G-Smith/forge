export default function ProgressTimeline({ items }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-6 shadow-sm">
      <div className="mb-4 text-[11.5px] font-bold uppercase tracking-wide text-ink-secondary">
        Recent progress
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-ink-muted">Nothing logged yet.</p>
      ) : (
        <div className="flex flex-col gap-3.5">
          {items.map((text, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className="mt-px flex h-[19px] w-[19px] shrink-0 items-center justify-center rounded-full bg-green-solid text-[11px] text-white">
                ✓
              </div>
              <div className="text-[13.5px] leading-relaxed text-ink-primary">{text}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
