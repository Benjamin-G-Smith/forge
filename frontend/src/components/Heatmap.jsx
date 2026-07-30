const LEVEL_COLORS = ["#eeede7", "#bbdebb", "#5db85d", "#267326"];
const WEEKS = 26;
const DAYS = 7;

function buildGrid(log) {
  const levelByDate = new Map(log.map((s) => [s.date, s.level]));
  const today = new Date();
  const cells = [];

  for (let w = WEEKS - 1; w >= 0; w -= 1) {
    for (let d = 0; d < DAYS; d += 1) {
      const date = new Date(today);
      date.setDate(date.getDate() - (w * DAYS + (DAYS - 1 - d)));
      const key = date.toISOString().slice(0, 10);
      cells.push({
        date: key,
        level: levelByDate.get(key) || 0,
        isToday: key === today.toISOString().slice(0, 10),
        isFuture: date > today,
      });
    }
  }
  return cells;
}

export default function Heatmap({ log }) {
  const cells = buildGrid(log);

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Activity</h2>
      <div className="grid grid-flow-col grid-rows-7 gap-1">
        {cells.map((cell) => (
          <div
            key={cell.date}
            title={cell.date}
            className={`h-3 w-3 rounded-sm ${cell.isToday ? "ring-2 ring-blue-500" : ""} ${cell.isFuture ? "opacity-30" : ""}`}
            style={{ backgroundColor: LEVEL_COLORS[cell.level] }}
          />
        ))}
      </div>
    </section>
  );
}
