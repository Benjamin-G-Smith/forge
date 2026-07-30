const STAGES = [
  { title: "Python + wrapper project", target: "Aug 2026" },
  { title: "Memory + state", target: "Sept 2026" },
  { title: "Ask PSS Data (text-to-SQL)", target: "Oct 2026" },
  { title: "Agents + MCP", target: "Nov 2026" },
  { title: "Ship to real users", target: "Dec 2026" },
];

export default function StageTrack({ stagesComplete }) {
  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Roadmap</h2>
      <div className="flex flex-col gap-2">
        {STAGES.map((stage, i) => {
          const done = i < stagesComplete;
          const active = i === stagesComplete;
          return (
            <div key={stage.title} className="flex items-center gap-3">
              <span
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs text-white ${
                  done ? "bg-green-600" : active ? "bg-blue-600" : "bg-gray-300"
                }`}
              >
                {i + 1}
              </span>
              <span className={done ? "text-gray-400 line-through" : "text-gray-900"}>{stage.title}</span>
              <span className="ml-auto text-xs text-gray-400">{stage.target}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
