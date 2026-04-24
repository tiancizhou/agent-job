from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./quickapp.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def initialize_database():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        columns = connection.execute(text("PRAGMA table_info(apps)")).fetchall()
        column_names = {column[1] for column in columns}
        if column_names and "progress" not in column_names:
            connection.execute(text("ALTER TABLE apps ADD COLUMN progress TEXT"))
        if column_names and "user_id" not in column_names:
            connection.execute(text("ALTER TABLE apps ADD COLUMN user_id TEXT"))
        if column_names and "style_id" not in column_names:
            connection.execute(text("ALTER TABLE apps ADD COLUMN style_id TEXT"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
