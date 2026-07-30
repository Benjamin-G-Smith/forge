import os
from sqlmodel import SQLModel, Session, create_engine

DB_PATH = os.environ.get("DB_PATH", "career.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:
    from api.models import models  # noqa: F401  (register tables on metadata)

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        if session.get(models.Metrics, 1) is None:
            session.add(models.Metrics(id=1))
            session.commit()


def get_session():
    with Session(engine) as session:
        yield session
