export const MILESTONE_ORDER = [
  "stage1_shipped",
  "building_in_public",
  "eval_harness_coded",
  "first_post_published",
  "ten_apps_sent",
  "pss_public_url",
  "second_project_shipped",
];

export const MILESTONE_LABELS = {
  stage1_shipped: "Stage 1 shipped",
  building_in_public: "Building in public",
  eval_harness_coded: "Eval harness coded",
  first_post_published: "First post published",
  ten_apps_sent: "10 applications sent",
  pss_public_url: "PSS Data public URL",
  second_project_shipped: "Second project shipped",
};

export function nextIncompleteMilestone(milestones) {
  const byKey = new Map(milestones.map((m) => [m.key, m]));
  for (const key of MILESTONE_ORDER) {
    const milestone = byKey.get(key);
    if (milestone && !milestone.completed) {
      return { key, label: MILESTONE_LABELS[key] || key };
    }
  }
  return null;
}
