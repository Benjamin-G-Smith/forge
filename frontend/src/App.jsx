import { useEffect, useState } from "react";

import { api, isSharedView } from "./api.js";
import ProjectDetail from "./components/ProjectDetail.jsx";
import ProjectPicker from "./components/ProjectPicker.jsx";

function idFromLocation() {
  return new URLSearchParams(window.location.search).get("id");
}

export default function App() {
  const [projects, setProjects] = useState(null);
  const [project, setProject] = useState(null);
  const [selectedId, setSelectedId] = useState(idFromLocation);
  const [error, setError] = useState(null);
  const shared = isSharedView();

  const loadProjects = () => {
    api.getProjects().then(setProjects).catch((err) => setError(err.message));
  };
  const loadProject = (id) => {
    api.getProject(id).then(setProject).catch((err) => setError(err.message));
  };

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedId) loadProject(selectedId);
  }, [selectedId]);

  useEffect(() => {
    const onPopState = () => setSelectedId(idFromLocation());
    window.addEventListener("popstate", onPopState);
    return () => window.removeEventListener("popstate", onPopState);
  }, []);

  const openProject = (id) => {
    window.history.pushState({}, "", `?id=${id}`);
    setSelectedId(id);
  };

  const backToPicker = () => {
    window.history.pushState({}, "", window.location.pathname);
    setProject(null);
    setSelectedId(null);
    loadProjects();
  };

  const reloadCurrent = () => {
    loadProjects();
    if (selectedId) loadProject(selectedId);
  };

  if (error) return <div className="p-8 text-red-600">Failed to load: {error}</div>;

  if (selectedId) {
    if (!project) return <div className="p-8 text-ink-secondary">Loading…</div>;
    return (
      <ProjectDetail
        project={project}
        shared={shared}
        onBack={backToPicker}
        onRefresh={shared ? null : () => api.refreshProject(selectedId).then(reloadCurrent)}
        onApply={
          shared ? null : () => api.applyProjectSnapshot(selectedId, project.snapshot_id).then(reloadCurrent)
        }
        onComplete={shared ? null : (index) => api.completeUpNextItem(selectedId, index).then(reloadCurrent)}
        onToggleMilestone={
          shared ? null : (key, completed) => api.toggleMilestone(key, completed).then(reloadCurrent)
        }
        onLogSession={shared ? null : (payload) => api.logSession(payload).then(reloadCurrent)}
        onRegenerateBrief={shared ? null : () => api.generateBrief().then(reloadCurrent)}
      />
    );
  }

  if (!projects) return <div className="p-8 text-ink-secondary">Loading…</div>;
  return <ProjectPicker projects={projects} onOpen={openProject} shared={shared} />;
}
