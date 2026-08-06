export default function UpNextChecklist({ items, onComplete }) {
  if (items.length === 0) {
    return (
      <div className="rounded-lg border border-line bg-surface p-6 shadow-sm">
        <div className="mb-1 text-[11.5px] font-bold uppercase tracking-wide text-ink-secondary">Up next</div>
        <p className="text-sm text-ink-muted">Nothing queued — refresh from the vault to sync.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-line bg-surface p-6 shadow-sm">
      <div className="mb-4 text-[11.5px] font-bold uppercase tracking-wide text-ink-secondary">Up next</div>
      <div className="flex flex-col gap-4">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-3">
            <button
              onClick={() => onComplete && onComplete(i)}
              disabled={!onComplete}
              title={onComplete ? "Mark done" : undefined}
              className="mt-0.5 h-[19px] w-[19px] shrink-0 rounded-full border-2 border-line-strong transition-colors hover:border-accent-blue-solid disabled:hover:border-line-strong"
            />
            <div>
              <div className="text-sm font-medium leading-normal text-ink-primary">{item.title}</div>
              {item.detail && <div className="mt-0.5 text-xs leading-normal text-ink-muted">{item.detail}</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
