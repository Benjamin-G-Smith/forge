export default function MorningBrief({ brief, onRegenerate }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Morning Brief</h2>
        {onRegenerate && (
          <button
            onClick={onRegenerate}
            className="rounded-md bg-gray-900 px-3 py-1 text-sm text-white hover:bg-gray-700"
          >
            Regenerate
          </button>
        )}
      </div>

      {brief ? (
        <div className="mt-3 space-y-3">
          <p className="text-gray-700">{brief.summary}</p>
          <p className="font-medium text-gray-900">Today: {brief.focus}</p>
          <ul className="space-y-1">
            {brief.research.map((r) => (
              <li key={r.url} className="text-sm">
                <a href={r.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                  {r.title}
                </a>
                <span className="ml-2 text-gray-400">{r.reason}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-3 text-gray-400">No brief generated yet.</p>
      )}
    </section>
  );
}
