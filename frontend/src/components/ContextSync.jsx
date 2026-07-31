import { useState } from "react";

import { MILESTONE_ORDER, MILESTONE_LABELS } from "../milestones.js";

export default function ContextSync({ context, onRefresh, onApply }) {
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await onRefresh();
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Context Sync</h2>
        {onRefresh && (
          <button
            onClick={handleRefresh}
            disabled={loading}
            className="rounded-md bg-gray-900 px-3 py-1 text-sm text-white hover:bg-gray-700 disabled:opacity-50"
          >
            {loading ? "Syncing…" : "Refresh from vault"}
          </button>
        )}
      </div>

      {!context ? (
        <p className="mt-3 text-gray-400">Not synced yet.</p>
      ) : (
        <div className="mt-3 space-y-3">
          <p className="text-gray-700">{context.summary}</p>
          {context.next_action && (
            <p className="font-medium text-gray-900">Next: {context.next_action}</p>
          )}

          {!context.applied && (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
              <p className="text-sm font-medium text-amber-800">Proposed update (not yet applied)</p>
              {context.reasoning && (
                <p className="mt-1 text-sm text-amber-700">{context.reasoning}</p>
              )}
              <p className="mt-1 text-sm text-amber-700">Proposed stage: {context.proposed_stage}</p>
              <ul className="mt-1 space-y-0.5 text-sm text-amber-700">
                {MILESTONE_ORDER.map((key) => (
                  <li key={key}>
                    {context.proposed_milestones[key] ? "✓" : "○"} {MILESTONE_LABELS[key] || key}
                  </li>
                ))}
              </ul>
              {onApply && (
                <button
                  onClick={() => onApply(context.id)}
                  className="mt-2 rounded-md bg-amber-600 px-3 py-1 text-sm text-white hover:bg-amber-700"
                >
                  Apply to tracked state
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
