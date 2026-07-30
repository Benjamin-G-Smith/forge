function currentStreak(log) {
  const dates = new Set(log.map((s) => s.date));
  let streak = 0;
  const cursor = new Date();

  while (dates.has(cursor.toISOString().slice(0, 10))) {
    streak += 1;
    cursor.setDate(cursor.getDate() - 1);
  }
  return streak;
}

function Card({ label, value }) {
  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4 text-center shadow-sm">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm text-gray-500">{label}</div>
    </div>
  );
}

export default function MetricsRow({ metrics, log }) {
  return (
    <section className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <Card label="Day streak" value={currentStreak(log)} />
      <Card label="Projects shipped" value={metrics.projects_shipped} />
      <Card label="Stages complete" value={`${metrics.stages_complete}/5`} />
      <Card label="Applications sent" value={metrics.applications_sent} />
    </section>
  );
}
