import ProjectGrid from "./ProjectGrid.jsx";
import TopBar from "./TopBar.jsx";

export default function ProjectPicker({ projects, onOpen, shared }) {
  return (
    <div className="mx-auto max-w-[920px] p-7 pb-20">
      <TopBar shared={shared} />

      <div className="mb-5 mt-7">
        <div className="text-[22px] font-bold tracking-tight">Your projects</div>
        <div className="mt-1 text-sm text-ink-secondary">
          {projects.length} active · pick up where you left off
        </div>
      </div>

      <ProjectGrid projects={projects} onOpen={onOpen} />
    </div>
  );
}
