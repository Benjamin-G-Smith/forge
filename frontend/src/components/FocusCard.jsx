import { accentOf } from "../accents.js";

export default function FocusCard({ focus, focusMeta, accent }) {
  const a = accentOf(accent);
  return (
    <div className={`mb-4 rounded-lg p-6 ${a.bg}`}>
      <div className={`mb-2.5 text-[11.5px] font-bold uppercase tracking-wide ${a.text}`}>Current focus</div>
      <p className={`m-0 text-base leading-relaxed ${a.text}`}>{focus}</p>
      {focusMeta && (
        <div className={`mt-3 inline-block rounded-full bg-white/55 px-3 py-1 text-xs font-medium ${a.text}`}>
          {focusMeta}
        </div>
      )}
    </div>
  );
}
