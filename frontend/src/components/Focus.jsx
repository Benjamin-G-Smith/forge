import { nextIncompleteMilestone } from "../milestones.js";

export default function Focus({ brief, milestones }) {
  const next = nextIncompleteMilestone(milestones);

  return (
    <section className="grid gap-4 sm:grid-cols-2">
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-5">
        <div className="text-xs font-semibold uppercase tracking-wide text-blue-600">
          Today's focus
        </div>
        <p className="mt-2 text-lg font-medium text-gray-900">
          {brief?.focus || "Log a session to get a focus recommendation."}
        </p>
      </div>

      <div className="rounded-xl border border-amber-200 bg-amber-50 p-5">
        <div className="text-xs font-semibold uppercase tracking-wide text-amber-600">
          Next milestone
        </div>
        <p className="mt-2 text-lg font-medium text-gray-900">
          {next ? next.label : "All milestones complete 🎉"}
        </p>
      </div>
    </section>
  );
}
