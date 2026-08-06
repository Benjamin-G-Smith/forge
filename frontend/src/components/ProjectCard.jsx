import { accentOf, relativeTime } from "../accents.js";
import StatusPill from "./StatusPill.jsx";

export default function ProjectCard({ project, onClick }) {
  const a = accentOf(project.accent);
  const stat = project.stats[0];

  return (
    <div
      onClick={onClick}
      className="cursor-pointer rounded-lg border border-line bg-surface p-6 shadow-sm transition-all hover:-translate-y-px hover:border-line-strong"
    >
      <div className="mb-3.5 flex items-start justify-between">
        <div className={`flex h-[38px] w-[38px] items-center justify-center rounded-md text-lg ${a.bg} ${a.text}`}>
          {project.icon}
        </div>
        <StatusPill status={project.status} accent={project.accent} />
      </div>

      <div className="mb-1 text-[17px] font-semibold tracking-tight">{project.name}</div>
      <div className="mb-4 text-[13px] leading-normal text-ink-muted">{project.subtitle}</div>

      {project.stage_progress ? (
        <div className="mb-4 flex gap-1.5">
          {Array.from({ length: project.stage_progress.total }).map((_, i) => (
            <div
              key={i}
              className={`h-2 w-2 rounded-full ${
                i < project.stage_progress.complete
                  ? "bg-green-solid"
                  : i === project.stage_progress.complete
                    ? a.solid
                    : "bg-line-strong"
              }`}
            />
          ))}
        </div>
      ) : (
        <div className="mb-4 text-[13px] text-ink-secondary">{project.focus_meta}</div>
      )}

      <div className="flex items-center justify-between border-t border-line pt-3.5 text-xs text-ink-muted">
        <span>{relativeTime(project.last_active)}</span>
        {stat && (
          <span className="font-medium text-ink-primary">
            {stat[1]} {stat[0]} →
          </span>
        )}
      </div>
    </div>
  );
}
