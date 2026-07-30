import { useEffect, useState } from "react";

import { api, isSharedView } from "./api.js";
import Heatmap from "./components/Heatmap.jsx";
import LogSession from "./components/LogSession.jsx";
import MetricsRow from "./components/MetricsRow.jsx";
import Milestones from "./components/Milestones.jsx";
import MorningBrief from "./components/MorningBrief.jsx";
import ShareBadge from "./components/ShareBadge.jsx";
import StageTrack from "./components/StageTrack.jsx";

export default function App() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState(null);
  const shared = isSharedView();

  const reload = () => {
    api.getDashboard().then(setDashboard).catch((err) => setError(err.message));
  };

  useEffect(reload, []);

  if (error) return <div className="p-8 text-red-600">Failed to load: {error}</div>;
  if (!dashboard) return <div className="p-8 text-gray-500">Loading…</div>;

  return (
    <div className="mx-auto max-w-4xl space-y-8 p-6">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Career Tracker</h1>
        {shared && <ShareBadge />}
      </header>

      <MorningBrief brief={dashboard.brief} onRegenerate={shared ? null : () => api.generateBrief().then(reload)} />
      <MetricsRow metrics={dashboard.metrics} log={dashboard.log} />
      <Heatmap log={dashboard.log} />
      <StageTrack stagesComplete={dashboard.metrics.stages_complete} />
      <Milestones milestones={dashboard.milestones} readOnly={shared} onToggle={(key, completed) => api.toggleMilestone(key, completed).then(reload)} />
      {!shared && <LogSession onSubmit={(payload) => api.logSession(payload).then(reload)} />}
    </div>
  );
}
