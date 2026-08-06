import { accentOf, relativeTime } from "../accents.js";
import BackLink from "./BackLink.jsx";
import FocusCard from "./FocusCard.jsx";
import Heatmap from "./Heatmap.jsx";
import LogSession from "./LogSession.jsx";
import MetricsRow from "./MetricsRow.jsx";
import Milestones from "./Milestones.jsx";
import MorningBrief from "./MorningBrief.jsx";
import ProgressTimeline from "./ProgressTimeline.jsx";
import RoadmapStepper from "./RoadmapStepper.jsx";
import StatChip from "./StatChip.jsx";
import StatusPill from "./StatusPill.jsx";
import TopBar from "./TopBar.jsx";
import UpNextChecklist from "./UpNextChecklist.jsx";

export default function ProjectDetail({
  project,
  shared,
  onBack,
  onRefresh,
  onApply,
  onComplete,
  onToggleMilestone,
  onLogSession,
  onRegenerateBrief,
}) {
  const a = accentOf(project.accent);

  return (
    <div className="mx-auto max-w-[920px] p-7 pb-20">
      <TopBar shared={shared} />
      <BackLink onClick={onBack} />

      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3.5">
          <div className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-md text-xl ${a.bg} ${a.text}`}>
            {project.icon}
          </div>
          <div>
            <div className="text-[22px] font-bold tracking-tight">{project.name}</div>
            <div className="mt-0.5 text-[13.5px] text-ink-secondary">{project.subtitle}</div>
          </div>
        </div>
        <StatusPill status={project.status} accent={project.accent} />
      </div>

      <div className="mb-4 flex flex-wrap gap-2.5">
        {project.stats.map(([label, value]) => (
          <StatChip key={label} label={label} value={value} />
        ))}
        <StatChip label="Last active" value={relativeTime(project.last_active) || "—"} />
        {onRefresh && (
          <button
            onClick={onRefresh}
            className="ml-auto rounded-md bg-ink-primary px-3 py-1.5 text-sm text-white hover:bg-ink-secondary"
          >
            Refresh from vault
          </button>
        )}
      </div>

      <FocusCard focus={project.focus} focusMeta={project.focus_meta} accent={project.accent} />

      <UpNextChecklist items={project.up_next} onComplete={shared ? null : onComplete} />

      <div className="mt-4 grid gap-4 sm:grid-cols-[1.4fr_1fr]">
        <ProgressTimeline items={project.progress} />
        {project.flagship && (
          <div className="flex flex-col gap-4">
            <MorningBrief brief={project.brief} onRegenerate={shared ? null : onRegenerateBrief} />
            <Heatmap log={project.log} />
          </div>
        )}
      </div>

      {project.flagship && (
        <>
          <div className="mt-4">
            <MetricsRow metrics={project.metrics} log={project.log} />
          </div>
          {!project.applied && project.proposed_stage !== null && (
            <div className="mt-4 rounded-lg border border-accent-coral-solid/30 bg-accent-coral-bg p-4">
              <p className="text-sm font-medium text-accent-coral-text">Proposed update (not yet applied)</p>
              <p className="mt-1 text-sm text-accent-coral-text">Proposed stage: {project.proposed_stage}</p>
              {onApply && (
                <button
                  onClick={onApply}
                  className="mt-2 rounded-md bg-accent-coral-solid px-3 py-1 text-sm text-white hover:opacity-90"
                >
                  Apply to tracked state
                </button>
              )}
            </div>
          )}
          <div className="mt-4">
            <RoadmapStepper steps={project.roadmap} />
          </div>
          <div className="mt-4">
            <Milestones
              milestones={project.milestones}
              readOnly={shared}
              onToggle={onToggleMilestone}
            />
          </div>
          {!shared && (
            <div className="mt-4">
              <LogSession onSubmit={onLogSession} />
            </div>
          )}
        </>
      )}
    </div>
  );
}
