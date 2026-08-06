import ProjectCard from "./ProjectCard.jsx";

export default function ProjectGrid({ projects, onOpen }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      {projects.map((project) => (
        <ProjectCard key={project.id} project={project} onClick={() => onOpen(project.id)} />
      ))}

      <div className="flex flex-col items-center justify-center gap-2 rounded-lg border-[1.5px] border-dashed border-line-strong p-8 text-sm font-medium text-ink-muted">
        <div className="flex h-8 w-8 items-center justify-center rounded-full border-[1.5px] border-line-strong text-base">
          +
        </div>
        New project
      </div>
    </div>
  );
}
