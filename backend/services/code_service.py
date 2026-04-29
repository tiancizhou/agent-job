import json
import re
import shutil
import uuid
from pathlib import Path

ALLOWED_PROJECT_SUFFIXES = {".html", ".css", ".js", ".json", ".txt", ".md", ".svg"}
MAX_PROJECT_FILES = 20
MAX_CHANGE_FILES = 10
MAX_FILE_BYTES = 300 * 1024


class ProjectValidationError(ValueError):
    pass


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
    try:
        return parse_project_json_or_raise(text)
    except ProjectValidationError:
        return None


def parse_project_json_or_raise(text: str) -> list[dict[str, str]]:
    data = _parse_json_object(text)
    if not isinstance(data, dict):
        raise ProjectValidationError("模型返回的项目不是有效 JSON，请重新生成。")
    files = _normalize_file_entries(data.get("files"), MAX_PROJECT_FILES, "files")
    paths = {file["path"] for file in files}
    required_paths = {"index.html", "css/style.css", "js/app.js"}
    missing_paths = sorted(required_paths - paths)
    if missing_paths:
        raise ProjectValidationError(f"模型返回的项目缺少必要文件：{', '.join(missing_paths)}。")
    return files


def parse_changes_json(text: str) -> list[dict[str, str]] | None:
    try:
        return parse_changes_json_or_raise(text)
    except ProjectValidationError:
        return None


def parse_changes_json_or_raise(text: str) -> list[dict[str, str]]:
    data = _parse_json_object(text)
    if not isinstance(data, dict):
        raise ProjectValidationError("模型返回的修改不是有效 JSON，请重新生成。")
    return _normalize_file_entries(data.get("changes"), MAX_CHANGE_FILES, "changes")


def save_project(app_id: str, files: list[dict[str, str]], data_dir: str) -> Path:
    files = _require_valid_entries(files, MAX_PROJECT_FILES)
    if not any(file["path"] == "index.html" for file in files):
        raise ProjectValidationError("模型返回的项目缺少必要文件：index.html。")

    project_dir = _project_dir(app_id, data_dir)
    temp_dir = _temp_project_dir(project_dir)
    backup_dir = _backup_project_dir(project_dir)
    _write_project_files(temp_dir, files)
    return _replace_project_dir(project_dir, temp_dir, backup_dir)


def save_changes(app_id: str, changes: list[dict[str, str]], data_dir: str) -> Path:
    changes = _require_valid_entries(changes, MAX_CHANGE_FILES)
    project_dir = _project_dir(app_id, data_dir)
    if not project_dir.exists() or not (project_dir / "index.html").is_file():
        raise ProjectValidationError("当前应用没有可修改的项目文件，请先重新生成应用。")

    temp_dir = _temp_project_dir(project_dir)
    backup_dir = _backup_project_dir(project_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    shutil.copytree(project_dir, temp_dir)
    try:
        for change in changes:
            target = resolve_project_file(temp_dir, change["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change["content"], encoding="utf-8")
        _validate_project_dir(temp_dir)
        return _replace_project_dir(project_dir, temp_dir, backup_dir)
    except Exception:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        raise


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


def _temp_project_dir(project_dir: Path) -> Path:
    return project_dir.with_name(f".{project_dir.name}.tmp-{uuid.uuid4().hex}")


def _backup_project_dir(project_dir: Path) -> Path:
    return project_dir.with_name(f".{project_dir.name}.bak-{uuid.uuid4().hex}")


def _write_project_files(project_dir: Path, files: list[dict[str, str]]) -> None:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        for file in files:
            target = resolve_project_file(project_dir, file["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(file["content"], encoding="utf-8")
    except Exception:
        if project_dir.exists():
            shutil.rmtree(project_dir)
        raise


def _validate_project_dir(project_dir: Path) -> None:
    if not (project_dir / "index.html").is_file():
        raise ProjectValidationError("修改后的项目缺少必要文件：index.html。")
    file_count = 0
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(project_dir).as_posix()
        if not is_safe_project_path(relative_path):
            raise ProjectValidationError(f"修改后的项目包含不安全或不支持的文件路径：{relative_path}。")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ProjectValidationError(f"修改后的项目文件超过大小上限：{relative_path}。")
        file_count += 1
        if file_count > MAX_PROJECT_FILES:
            raise ProjectValidationError(f"修改后的项目文件数量超过上限 {MAX_PROJECT_FILES} 个。")


def _replace_project_dir(project_dir: Path, temp_dir: Path, backup_dir: Path) -> Path:
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    moved_existing_project = False
    try:
        if project_dir.exists():
            project_dir.rename(backup_dir)
            moved_existing_project = True
        temp_dir.rename(project_dir)
    except Exception:
        if moved_existing_project and project_dir.exists():
            shutil.rmtree(project_dir)
        if moved_existing_project and backup_dir.exists() and not project_dir.exists():
            backup_dir.rename(project_dir)
        raise
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
    return project_dir


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


def _normalize_file_entries(value: object, max_files: int, field_name: str = "files") -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ProjectValidationError(f"模型返回的 `{field_name}` 必须是文件数组。")
    if len(value) == 0:
        raise ProjectValidationError("模型没有返回任何项目文件。")
    if len(value) > max_files:
        raise ProjectValidationError(f"模型返回的文件数量超过上限 {max_files} 个。")

    files: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ProjectValidationError("模型返回的文件条目格式不正确。")
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ProjectValidationError("模型返回的文件条目必须包含字符串 path 和 content。")
        if not is_safe_project_path(path):
            raise ProjectValidationError(f"模型返回了不安全或不支持的文件路径：{path}。")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ProjectValidationError(f"模型返回的文件超过大小上限：{path}。")
        files.append({"path": path, "content": content})
    return files


def _require_valid_entries(files: list[dict[str, str]], max_files: int) -> list[dict[str, str]]:
    return _normalize_file_entries(files, max_files)
