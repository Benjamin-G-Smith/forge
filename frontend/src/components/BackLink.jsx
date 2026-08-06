export default function BackLink({ onClick }) {
  return (
    <button
      onClick={onClick}
      className="mb-4 mt-2 inline-flex items-center gap-1.5 text-[13.5px] font-medium text-ink-secondary transition-colors hover:text-ink-primary"
    >
      ← All projects
    </button>
  );
}
