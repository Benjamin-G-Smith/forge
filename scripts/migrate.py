"""One-time import from career-metrics.json into SQLite. Idempotent by date."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session, select  # noqa: E402

from api.db.database import engine, init_db  # noqa: E402
from api.models.models import Metrics, Milestone, Session as SessionModel  # noqa: E402

SOURCE_PATH = Path("/Users/bensmith/Documents/ember-vault/_system/career-metrics.json")


def migrate(source_path: Path = SOURCE_PATH) -> None:
    if not source_path.exists():
        print(f"No source file at {source_path}, nothing to migrate.")
        return

    data = json.loads(source_path.read_text())
    init_db()

    with Session(engine) as session:
        existing_dates = set(session.exec(select(SessionModel.date)).all())
        added = 0
        for entry in data.get("log", []):
            if entry["date"] in existing_dates:
                continue
            session.add(
                SessionModel(
                    date=entry["date"],
                    type=json.dumps(entry.get("type", [])),
                    notes=entry.get("notes"),
                    commits=entry.get("commits", 0),
                    level=entry.get("level", 1),
                    created_at=int(time.time() * 1000),
                )
            )
            added += 1

        raw_metrics = data.get("metrics", {})
        metrics = session.get(Metrics, 1) or Metrics(id=1)
        metrics.projects_shipped = raw_metrics.get("projects_shipped", metrics.projects_shipped)
        metrics.applications_sent = raw_metrics.get("applications_sent", metrics.applications_sent)
        metrics.stages_complete = raw_metrics.get("stages_complete", metrics.stages_complete)
        metrics.updated_at = int(time.time() * 1000)
        session.add(metrics)

        milestone_count = 0
        for key, completed in raw_metrics.get("milestones", {}).items():
            milestone = session.get(Milestone, key) or Milestone(key=key)
            milestone.completed = completed
            if completed and milestone.completed_at is None:
                milestone.completed_at = int(time.time() * 1000)
            session.add(milestone)
            milestone_count += 1

        session.commit()

    print(f"Migrated {added} new sessions, updated metrics, {milestone_count} milestones.")


if __name__ == "__main__":
    migrate()
