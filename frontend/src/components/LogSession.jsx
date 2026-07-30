import { useState } from "react";

const TYPES = ["python", "project", "research", "application", "learning", "other"];
const INTENSITY = [
  { level: 1, label: "Light (<30m)" },
  { level: 2, label: "Solid (1-2h)" },
  { level: 3, label: "Deep (2h+)" },
];

export default function LogSession({ onSubmit }) {
  const [types, setTypes] = useState([]);
  const [notes, setNotes] = useState("");
  const [level, setLevel] = useState(2);

  const toggleType = (t) =>
    setTypes((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      date: new Date().toISOString().slice(0, 10),
      type: types,
      notes,
      level,
    });
    setTypes([]);
    setNotes("");
    setLevel(2);
  };

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold">Log Session</h2>
      <form onSubmit={handleSubmit} className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {TYPES.map((t) => (
            <button
              type="button"
              key={t}
              onClick={() => toggleType(t)}
              className={`rounded-full border px-3 py-1 text-sm ${
                types.includes(t) ? "border-blue-600 bg-blue-50 text-blue-700" : "border-gray-300"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="What did you work on?"
          className="w-full rounded-md border border-gray-300 p-2"
          rows={3}
        />

        <div className="flex gap-2">
          {INTENSITY.map((i) => (
            <button
              type="button"
              key={i.level}
              onClick={() => setLevel(i.level)}
              className={`rounded-md border px-3 py-1 text-sm ${
                level === i.level ? "border-blue-600 bg-blue-50 text-blue-700" : "border-gray-300"
              }`}
            >
              {i.label}
            </button>
          ))}
        </div>

        <button type="submit" className="rounded-md bg-gray-900 px-4 py-2 text-white hover:bg-gray-700">
          Log session
        </button>
      </form>
    </section>
  );
}
