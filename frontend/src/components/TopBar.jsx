import ShareBadge from "./ShareBadge.jsx";

function today() {
  return new Date().toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

export default function TopBar({ shared }) {
  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-md bg-ink-primary text-[17px] font-bold text-white">
          F
        </div>
        <div className="text-xl font-bold tracking-tight">Forge</div>
      </div>
      <div className="flex items-center gap-3">
        {shared && <ShareBadge />}
        <div className="text-sm text-ink-secondary">{today()}</div>
      </div>
    </div>
  );
}
