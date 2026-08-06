import { accentOf } from "../accents.js";

export default function StatusPill({ status, accent }) {
  const a = accentOf(accent);
  return (
    <span className={`whitespace-nowrap rounded-full px-3 py-1 text-[11.5px] font-semibold ${a.bg} ${a.text}`}>
      {status}
    </span>
  );
}
