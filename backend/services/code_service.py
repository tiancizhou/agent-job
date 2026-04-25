import json
import re
import shutil
from pathlib import Path

ALLOWED_PROJECT_SUFFIXES = {".html", ".css", ".js", ".json", ".txt", ".md", ".svg"}
MAX_PROJECT_FILES = 20
MAX_CHANGE_FILES = 10
MAX_FILE_BYTES = 300 * 1024


def extract_html(text: str) -> str | None:
    """
    Extract HTML content from LLM reply text.

    1. Try to find a ```html ... ``` fenced code block — return its content.
    2. If not found but text contains <html or <!DOCTYPE — return the full text.
    3. Otherwise return None.
    """
    pattern = r"```html\s*([\s\S]*?)```"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    if "<html" in text.lower() or "<!doctype" in text.lower():
        return text.strip()

    return None


def save_html(app_id: str, html: str, data_dir: str) -> Path:
    """
    Write HTML to {data_dir}/apps/{app_id}/index.html, creating dirs as needed.
    Returns the path.
    """
    app_dir = Path(data_dir) / "apps" / app_id
    app_dir.mkdir(parents=True, exist_ok=True)
    html_path = app_dir / "index.html"
    html_path.write_text(html, encoding="utf-8")
    return html_path


def parse_project_json(text: str) -> list[dict[str, str]] | None:
    data = _parse_json_object(text)
    if not isinstance(data, dict):
        return None
    files = _normalize_file_entries(data.get("files"), MAX_PROJECT_FILES)
    if files is None:
        return None
    if not any(file["path"] == "index.html" for file in files):
        return None
    return files


def parse_changes_json(text: str) -> list[dict[str, str]] | None:
    data = _parse_json_object(text)
    if not isinstance(data, dict):
        return None
    return _normalize_file_entries(data.get("changes"), MAX_CHANGE_FILES)


def save_project(app_id: str, files: list[dict[str, str]], data_dir: str) -> Path:
    files = _require_valid_entries(files, MAX_PROJECT_FILES)
    if not any(file["path"] == "index.html" for file in files):
        raise ValueError("project must include index.html")

    project_dir = _project_dir(app_id, data_dir)
    if project_dir.exists():
        shutil.rmtree(project_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        target = resolve_project_file(project_dir, file["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(file["content"], encoding="utf-8")

    return project_dir


def save_changes(app_id: str, changes: list[dict[str, str]], data_dir: str) -> Path:
    changes = _require_valid_entries(changes, MAX_CHANGE_FILES)
    project_dir = _project_dir(app_id, data_dir)
    project_dir.mkdir(parents=True, exist_ok=True)

    for change in changes:
        target = resolve_project_file(project_dir, change["path"])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(change["content"], encoding="utf-8")

    return project_dir


def read_project_files(app_id: str, data_dir: str) -> list[dict[str, str]]:
    project_dir = _project_dir(app_id, data_dir)
    if not project_dir.exists():
        return []

    files: list[dict[str, str]] = []
    for path in sorted(project_dir.rglob("*")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(project_dir).as_posix()
        if not is_safe_project_path(relative_path):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        files.append({"path": relative_path, "content": path.read_text(encoding="utf-8")})
        if len(files) >= MAX_PROJECT_FILES:
            break
    return files


def is_safe_project_path(path: str) -> bool:
    if not isinstance(path, str):
        return False
    if not path or path.endswith("/") or path.endswith("\\"):
        return False
    if "\\" in path or path.startswith("/"):
        return False
    if re.match(r"^[A-Za-z]:", path):
        return False

    candidate = Path(path)
    if candidate.is_absolute():
        return False
    if any(part in {"", ".", ".."} for part in candidate.parts):
        return False
    return candidate.suffix.lower() in ALLOWED_PROJECT_SUFFIXES


def resolve_project_file(project_dir: Path, path: str) -> Path:
    if not is_safe_project_path(path):
        raise ValueError("unsafe project path")
    root = project_dir.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("project path escapes project directory")
    return target


def project_dir_for(app_id: str, data_dir: str) -> Path:
    return _project_dir(app_id, data_dir)


def _project_dir(app_id: str, data_dir: str) -> Path:
    return Path(data_dir) / "apps" / app_id / "project"


def _parse_json_object(text: str) -> object | None:
    for candidate in _json_candidates(text):
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def _json_candidates(text: str) -> list[str]:
    candidates = [match.group(1).strip() for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", text, re.IGNORECASE)]
    stripped = text.strip()
    if stripped:
        candidates.append(stripped)
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidates.append(stripped[start:end + 1])
    return candidates


def _normalize_file_entries(value: object, max_files: int) -> list[dict[str, str]] | None:
    if not isinstance(value, list) or len(value) == 0 or len(value) > max_files:
        return None

    files: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            return None
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            return None
        if not is_safe_project_path(path):
            return None
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            return None
        files.append({"path": path, "content": content})
    return files


def _require_valid_entries(files: list[dict[str, str]], max_files: int) -> list[dict[str, str]]:
    normalized = _normalize_file_entries(files, max_files)
    if normalized is None:
        raise ValueError("invalid project files")
    return normalized
