const LABELS = {
  stage1_shipped: "Stage 1 shipped",
  building_in_public: "Building in public",
  eval_harness_coded: "Eval harness coded",
  first_post_published: "First post published",
  ten_apps_sent: "10 applications sent",
  pss_public_url: "PSS Data public URL",
  second_project_shipped: "Second project shipped",
};

export default function Milestones({ milestones, readOnly, onToggle }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Milestones</h2>
      <ul className="space-y-2">
        {milestones.map((m) => (
          <li key={m.key} className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={m.completed}
              disabled={readOnly}
              onChange={(e) => onToggle(m.key, e.target.checked)}
            />
            <span className={m.completed ? "text-gray-400 line-through" : ""}>
              {LABELS[m.key] || m.key}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}
