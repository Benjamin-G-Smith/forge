export default function RoadmapStepper({ steps }) {
  return (
    <div className="rounded-lg border border-line bg-surface p-6 shadow-sm">
      <div className="mb-5 text-[11.5px] font-bold uppercase tracking-wide text-ink-secondary">Roadmap</div>
      <div className="relative flex flex-wrap gap-y-4">
        <div className="absolute left-10 right-10 top-[14px] h-px bg-line" />
        {steps.map((step, i) => {
          const dotClass =
            step.state === "done"
              ? "bg-green-solid text-white"
              : step.state === "current"
                ? "bg-accent-blue-solid text-white"
                : "border-[1.5px] border-line-strong bg-surface text-ink-muted";
          const labelClass =
            step.state === "done"
              ? "text-ink-muted line-through font-normal"
              : step.state === "current"
                ? "text-accent-blue-solid font-medium"
                : "text-ink-primary font-medium";
          const dotContent = step.state === "done" ? "✓" : step.state === "current" ? "●" : i + 1;

          return (
            <div key={step.label} className="relative z-[1] flex-1 basis-1/3 text-center sm:basis-0">
              <div className={`mx-auto mb-2 flex h-7 w-7 items-center justify-center rounded-full text-[13px] font-semibold ${dotClass}`}>
                {dotContent}
              </div>
              <div className={`text-[12.5px] ${labelClass}`}>{step.label}</div>
              <div className="mt-0.5 text-[11px] text-ink-muted">{step.date}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
