from pathlib import Path
from urllib.parse import unquote, urlparse

from alembic import command
from alembic.config import Config

from config import settings


def sqlite_path_from_url(database_url: str) -> Path | None:
    parsed = urlparse(database_url)
    if not parsed.scheme.startswith("sqlite"):
        return None
    if parsed.path in {"", "/:memory:"}:
        return None
    if parsed.netloc:
        return Path(unquote(f"//{parsed.netloc}{parsed.path}"))
    path = unquote(parsed.path)
    if len(path) >= 3 and path[0] == "/" and path[2] == ":":
        path = path[1:]
    return Path(path)


def database_exists(database_url: str) -> bool:
    sqlite_path = sqlite_path_from_url(database_url)
    if sqlite_path is None:
        return False
    return sqlite_path.exists()


def upgrade_database() -> None:
    alembic_cfg = Config(str(Path(__file__).resolve().parent / "alembic.ini"))
    command.upgrade(alembic_cfg, "head")


def main() -> None:
    upgrade_database()


if __name__ == "__main__":
    main()
