export default function StatChip({ label, value }) {
  return (
    <div className="rounded-md border border-line bg-surface px-4 py-2.5 text-xs text-ink-secondary">
      {label}: <b className="font-semibold text-ink-primary">{value}</b>
    </div>
  );
}
