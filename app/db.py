from contextlib import contextmanager
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./ucp_demo.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


@contextmanager
def get_session():
    with Session(engine) as session:
        yield session
