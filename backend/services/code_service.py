import json
import re
import shutil
import subprocess
import uuid
from pathlib import Path

ALLOWED_PROJECT_SUFFIXES = {
    ".html",
    ".css",
    ".js",
    ".mjs",
    ".json",
    ".txt",
    ".md",
    ".svg",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".ico",
    ".woff",
    ".woff2",
    ".ttf",
    ".map",
    ".avif",
}
ALLOWED_SOURCE_SUFFIXES = ALLOWED_PROJECT_SUFFIXES | {".ts", ".tsx", ".jsx"}
MAX_PROJECT_FILES = 20
MAX_CHANGE_FILES = 10
MAX_FILE_BYTES = 300 * 1024
REQUIRED_NEXT_SOURCE_PATHS = {
    "package.json",
    "next.config.ts",
    "tsconfig.json",
    "next-env.d.ts",
    "app/layout.tsx",
    "app/page.tsx",
    "app/globals.css",
}
ALLOWED_PACKAGE_DEPENDENCIES = {
    "next",
    "react",
    "react-dom",
    "typescript",
    "@types/node",
    "@types/react",
    "@types/react-dom",
}
ALLOWED_PACKAGE_SCRIPTS = {"dev", "build", "start"}
SAFE_PACKAGE_VERSION_PATTERN = re.compile(
    r"^(latest|\^?\d+(?:\.\d+){0,2}(?:[-+][0-9A-Za-z.-]+)?|~\d+(?:\.\d+){0,2}(?:[-+][0-9A-Za-z.-]+)?)$"
)
BUILD_TIMEOUT_SECONDS = 180


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
    files = _normalize_file_entries(data.get("files"), MAX_PROJECT_FILES, "files", source=True)
    _validate_next_source_entries(files, required_prefix="模型返回的项目")
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
    return _normalize_file_entries(data.get("changes"), MAX_CHANGE_FILES, "changes", source=True)


def save_project(app_id: str, files: list[dict[str, str]], data_dir: str) -> Path:
    files = _require_valid_entries(files, MAX_PROJECT_FILES, source=True)
    _validate_next_source_entries(files, required_prefix="模型返回的项目")

    source_dir = _source_dir(app_id, data_dir)
    project_dir = _project_dir(app_id, data_dir)
    temp_source_dir = _temp_project_dir(source_dir)
    temp_project_dir = _temp_project_dir(project_dir)
    source_backup_dir = _backup_project_dir(source_dir)
    project_backup_dir = _backup_project_dir(project_dir)

    _write_project_files(temp_source_dir, files, source=True)
    try:
        out_dir = build_static_export(temp_source_dir)
        _prepare_static_export_dir(out_dir, temp_project_dir)
        return _replace_source_and_project(
            source_dir,
            temp_source_dir,
            source_backup_dir,
            project_dir,
            temp_project_dir,
            project_backup_dir,
        )
    except Exception:
        _remove_dir_if_exists(temp_source_dir)
        _remove_dir_if_exists(temp_project_dir)
        raise


def save_changes(app_id: str, changes: list[dict[str, str]], data_dir: str) -> Path:
    changes = _require_valid_entries(changes, MAX_CHANGE_FILES, source=True)
    source_dir = _source_dir(app_id, data_dir)
    project_dir = _project_dir(app_id, data_dir)
    if not source_dir.exists() or not (source_dir / "app" / "page.tsx").is_file():
        raise ProjectValidationError("当前应用没有可修改的源项目文件，请先重新生成应用。")

    temp_source_dir = _temp_project_dir(source_dir)
    temp_project_dir = _temp_project_dir(project_dir)
    source_backup_dir = _backup_project_dir(source_dir)
    project_backup_dir = _backup_project_dir(project_dir)
    _remove_dir_if_exists(temp_source_dir)
    shutil.copytree(source_dir, temp_source_dir)
    try:
        for change in changes:
            target = resolve_source_file(temp_source_dir, change["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(change["content"], encoding="utf-8")
        _validate_source_dir(temp_source_dir)
        out_dir = build_static_export(temp_source_dir)
        _prepare_static_export_dir(out_dir, temp_project_dir)
        return _replace_source_and_project(
            source_dir,
            temp_source_dir,
            source_backup_dir,
            project_dir,
            temp_project_dir,
            project_backup_dir,
        )
    except Exception:
        _remove_dir_if_exists(temp_source_dir)
        _remove_dir_if_exists(temp_project_dir)
        raise


def build_static_export(source_dir: Path) -> Path:
    try:
        _run_build_command([_npm_command(), "install"], source_dir)
        _run_build_command([_npm_command(), "run", "build"], source_dir)
    except (OSError, subprocess.SubprocessError) as exc:
        detail = str(exc)
        if isinstance(exc, subprocess.CalledProcessError):
            output = "\n".join(part for part in [exc.stdout, exc.stderr] if part)
            detail = output.strip() or detail
        raise ProjectValidationError(f"Next.js 项目构建失败，请检查生成的源码：{_short_error(detail)}。") from exc

    out_dir = source_dir / "out"
    if not out_dir.exists() or not (out_dir / "index.html").is_file():
        raise ProjectValidationError("Next.js 项目构建未生成可预览的 out/index.html。")
    return out_dir


def read_project_files(app_id: str, data_dir: str) -> list[dict[str, str]]:
    return read_source_files(app_id, data_dir)


def read_source_files(app_id: str, data_dir: str) -> list[dict[str, str]]:
    source_dir = _source_dir(app_id, data_dir)
    if not source_dir.exists():
        return []

    files: list[dict[str, str]] = []
    for path in sorted(source_dir.rglob("*")):
        if not path.is_file() or "node_modules" in path.parts or path.name == ".next":
            continue
        relative_path = path.relative_to(source_dir).as_posix()
        if relative_path.startswith(".next/") or relative_path.startswith("out/"):
            continue
        if not is_safe_source_path(relative_path):
            continue
        if path.stat().st_size > MAX_FILE_BYTES:
            continue
        files.append({"path": relative_path, "content": path.read_text(encoding="utf-8")})
        if len(files) >= MAX_PROJECT_FILES:
            break
    return files


def is_safe_project_path(path: str) -> bool:
    return _is_safe_path(path, ALLOWED_PROJECT_SUFFIXES, reject_next_runtime=False)


def is_safe_source_path(path: str) -> bool:
    return _is_safe_path(path, ALLOWED_SOURCE_SUFFIXES, reject_next_runtime=True)


def resolve_project_file(project_dir: Path, path: str) -> Path:
    if not is_safe_project_path(path):
        raise ValueError("unsafe project path")
    return _resolve_safe_file(project_dir, path)


def resolve_source_file(source_dir: Path, path: str) -> Path:
    if not is_safe_source_path(path):
        raise ValueError("unsafe source path")
    return _resolve_safe_file(source_dir, path)


def project_dir_for(app_id: str, data_dir: str) -> Path:
    return _project_dir(app_id, data_dir)


def source_dir_for(app_id: str, data_dir: str) -> Path:
    return _source_dir(app_id, data_dir)


def _project_dir(app_id: str, data_dir: str) -> Path:
    return Path(data_dir) / "apps" / app_id / "project"


def _source_dir(app_id: str, data_dir: str) -> Path:
    return Path(data_dir) / "apps" / app_id / "source"


def _temp_project_dir(project_dir: Path) -> Path:
    return project_dir.with_name(f".{project_dir.name}.tmp-{uuid.uuid4().hex}")


def _backup_project_dir(project_dir: Path) -> Path:
    return project_dir.with_name(f".{project_dir.name}.bak-{uuid.uuid4().hex}")


def _write_project_files(project_dir: Path, files: list[dict[str, str]], source: bool = False) -> None:
    if project_dir.exists():
        shutil.rmtree(project_dir)
    try:
        project_dir.mkdir(parents=True, exist_ok=True)
        for file in files:
            target = resolve_source_file(project_dir, file["path"]) if source else resolve_project_file(project_dir, file["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(file["content"], encoding="utf-8")
    except Exception:
        _remove_dir_if_exists(project_dir)
        raise


def _validate_source_dir(source_dir: Path) -> None:
    file_count = 0
    seen_paths: set[str] = set()
    for path in source_dir.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(source_dir).as_posix()
        if relative_path.startswith("node_modules/") or relative_path.startswith(".next/") or relative_path.startswith("out/"):
            continue
        if not is_safe_source_path(relative_path):
            raise ProjectValidationError(f"修改后的项目包含不安全、不支持或被禁止的文件路径：{relative_path}。")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ProjectValidationError(f"修改后的项目文件超过大小上限：{relative_path}。")
        seen_paths.add(relative_path)
        file_count += 1
        if file_count > MAX_PROJECT_FILES:
            raise ProjectValidationError(f"修改后的项目文件数量超过上限 {MAX_PROJECT_FILES} 个。")

    missing_paths = sorted(REQUIRED_NEXT_SOURCE_PATHS - seen_paths)
    if missing_paths:
        raise ProjectValidationError(f"修改后的项目缺少必要文件：{', '.join(missing_paths)}。")
    _validate_package_json((source_dir / "package.json").read_text(encoding="utf-8"), "修改后的项目")
    _validate_next_config((source_dir / "next.config.ts").read_text(encoding="utf-8"), "修改后的项目")


def _prepare_static_export_dir(out_dir: Path, temp_project_dir: Path) -> None:
    _remove_dir_if_exists(temp_project_dir)
    shutil.copytree(out_dir, temp_project_dir)
    _rewrite_static_export_asset_paths(temp_project_dir)
    _validate_static_export_dir(temp_project_dir)


def _rewrite_static_export_asset_paths(project_dir: Path) -> None:
    """
    Next static export can emit root-relative /_next/... asset URLs.
    Generated apps are hosted under /generated/{app_id}/project/, so rewrite those
    URLs to paths relative to each published file before validation/replacement.
    """
    text_suffixes = {".html", ".css", ".js", ".mjs", ".map"}
    for path in project_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path.suffix.lower() in {".js", ".mjs"}:
            next_prefix = "_next/"
        else:
            relative_parent = path.parent.relative_to(project_dir).as_posix()
            depth = 0 if relative_parent == "." else len(Path(relative_parent).parts)
            next_prefix = "../" * depth + "_next/"
        rewritten = content.replace("\"/_next/", f"\"{next_prefix}").replace("'/_next/", f"'{next_prefix}")
        rewritten = rewritten.replace("url(/_next/", f"url({next_prefix}")
        rewritten = rewritten.replace("url('/_next/", f"url('{next_prefix}").replace('url("/_next/', f'url("{next_prefix}')
        if rewritten != content:
            path.write_text(rewritten, encoding="utf-8")


def _validate_static_export_dir(project_dir: Path) -> None:
    if not (project_dir / "index.html").is_file():
        raise ProjectValidationError("构建产物缺少预览入口 index.html。")
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(project_dir).as_posix()
        if not is_safe_project_path(relative_path):
            raise ProjectValidationError(f"构建产物包含不安全或不支持的文件路径：{relative_path}。")
        if path.stat().st_size > MAX_FILE_BYTES:
            raise ProjectValidationError(f"构建产物文件超过大小上限：{relative_path}。")


def _replace_source_and_project(
    source_dir: Path,
    temp_source_dir: Path,
    source_backup_dir: Path,
    project_dir: Path,
    temp_project_dir: Path,
    project_backup_dir: Path,
) -> Path:
    source_dir.parent.mkdir(parents=True, exist_ok=True)
    project_dir.parent.mkdir(parents=True, exist_ok=True)
    _remove_dir_if_exists(source_backup_dir)
    _remove_dir_if_exists(project_backup_dir)
    moved_source = False
    moved_project = False
    placed_source = False
    placed_project = False
    try:
        if source_dir.exists():
            source_dir.rename(source_backup_dir)
            moved_source = True
        if project_dir.exists():
            project_dir.rename(project_backup_dir)
            moved_project = True
        temp_source_dir.rename(source_dir)
        placed_source = True
        temp_project_dir.rename(project_dir)
        placed_project = True
    except Exception:
        if placed_source and source_dir.exists():
            shutil.rmtree(source_dir)
        if placed_project and project_dir.exists():
            shutil.rmtree(project_dir)
        if moved_source and source_backup_dir.exists() and not source_dir.exists():
            source_backup_dir.rename(source_dir)
        if moved_project and project_backup_dir.exists() and not project_dir.exists():
            project_backup_dir.rename(project_dir)
        raise
    finally:
        _remove_dir_if_exists(temp_source_dir)
        _remove_dir_if_exists(temp_project_dir)
        _remove_dir_if_exists(source_backup_dir)
        _remove_dir_if_exists(project_backup_dir)
    return project_dir


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
        _remove_dir_if_exists(temp_dir)
        _remove_dir_if_exists(backup_dir)
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


def _normalize_file_entries(value: object, max_files: int, field_name: str = "files", source: bool = False) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise ProjectValidationError(f"模型返回的 `{field_name}` 必须是文件数组。")
    if len(value) == 0:
        raise ProjectValidationError("模型没有返回任何项目文件。")
    if len(value) > max_files:
        raise ProjectValidationError(f"模型返回的文件数量超过上限 {max_files} 个。")

    files: list[dict[str, str]] = []
    seen_paths: set[str] = set()
    for item in value:
        if not isinstance(item, dict):
            raise ProjectValidationError("模型返回的文件条目格式不正确。")
        path = item.get("path")
        content = item.get("content")
        if not isinstance(path, str) or not isinstance(content, str):
            raise ProjectValidationError("模型返回的文件条目必须包含字符串 path 和 content。")
        is_safe = is_safe_source_path(path) if source else is_safe_project_path(path)
        if not is_safe:
            raise ProjectValidationError(f"模型返回了不安全、不支持或被禁止的文件路径：{path}。")
        if path in seen_paths:
            raise ProjectValidationError(f"模型返回了重复文件路径：{path}。")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ProjectValidationError(f"模型返回的文件超过大小上限：{path}。")
        seen_paths.add(path)
        files.append({"path": path, "content": content})
    return files


def _require_valid_entries(files: list[dict[str, str]], max_files: int, source: bool = False) -> list[dict[str, str]]:
    return _normalize_file_entries(files, max_files, source=source)


def _validate_next_source_entries(files: list[dict[str, str]], required_prefix: str) -> None:
    paths = {file["path"] for file in files}
    missing_paths = sorted(REQUIRED_NEXT_SOURCE_PATHS - paths)
    if missing_paths:
        raise ProjectValidationError(f"{required_prefix}缺少必要文件：{', '.join(missing_paths)}。")
    contents = {file["path"]: file["content"] for file in files}
    _validate_package_json(contents["package.json"], required_prefix)
    _validate_next_config(contents["next.config.ts"], required_prefix)


def _validate_package_json(content: str, required_prefix: str) -> None:
    try:
        package_data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ProjectValidationError(f"{required_prefix}的 package.json 不是有效 JSON。") from exc
    if not isinstance(package_data, dict):
        raise ProjectValidationError(f"{required_prefix}的 package.json 格式不正确。")

    scripts = package_data.get("scripts") or {}
    if not isinstance(scripts, dict):
        raise ProjectValidationError(f"{required_prefix}的 package.json scripts 格式不正确。")
    unsupported_scripts = sorted(set(scripts) - ALLOWED_PACKAGE_SCRIPTS)
    if unsupported_scripts:
        raise ProjectValidationError(f"{required_prefix}的 package.json 包含不支持的脚本：{', '.join(unsupported_scripts)}。")
    if scripts.get("build") != "next build":
        raise ProjectValidationError(f"{required_prefix}的 package.json 必须包含 build 脚本：next build。")

    dependencies: set[str] = set()
    for field_name in ["dependencies", "devDependencies"]:
        value = package_data.get(field_name) or {}
        if not isinstance(value, dict):
            raise ProjectValidationError(f"{required_prefix}的 package.json {field_name} 格式不正确。")
        for name, version in value.items():
            if not isinstance(name, str) or not isinstance(version, str):
                raise ProjectValidationError(f"{required_prefix}的 package.json {field_name} 依赖格式不正确。")
            if not SAFE_PACKAGE_VERSION_PATTERN.match(version):
                raise ProjectValidationError(f"{required_prefix}的 package.json 依赖版本不安全或不支持：{name}。")
            dependencies.add(name)
    missing = sorted({"next", "react", "react-dom"} - dependencies)
    if missing:
        raise ProjectValidationError(f"{required_prefix}的 package.json 缺少必要依赖：{', '.join(missing)}。")
    unsupported = sorted(dependencies - ALLOWED_PACKAGE_DEPENDENCIES)
    if unsupported:
        raise ProjectValidationError(f"{required_prefix}的 package.json 包含 MVP 暂不支持的依赖：{', '.join(unsupported)}。")


def _validate_next_config(content: str, required_prefix: str) -> None:
    normalized = re.sub(r"\s+", "", content).replace('"', "'")
    if "output:'export'" not in normalized:
        raise ProjectValidationError(f"{required_prefix}的 next.config.ts 必须启用 output: 'export'。")
    if "assetPrefix:'./'" not in normalized:
        raise ProjectValidationError(f"{required_prefix}的 next.config.ts 必须配置 assetPrefix: './'。")
    if not re.search(r"images:\{[^}]*unoptimized:true", normalized):
        raise ProjectValidationError(f"{required_prefix}的 next.config.ts 必须配置 images.unoptimized = true。")


def _is_safe_path(path: str, allowed_suffixes: set[str], reject_next_runtime: bool) -> bool:
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
    parts = candidate.parts
    if any(part in {"", ".", ".."} for part in parts):
        return False
    if reject_next_runtime and _is_forbidden_next_runtime_path(path, parts):
        return False
    return candidate.suffix.lower() in allowed_suffixes


def _is_forbidden_next_runtime_path(path: str, parts: tuple[str, ...]) -> bool:
    lowered_parts = tuple(part.lower() for part in parts)
    lowered_path = path.lower()
    if lowered_path in {"middleware.ts", "middleware.tsx", "middleware.js", "middleware.jsx"}:
        return True
    if lowered_path.startswith("app/api/") or lowered_path.startswith("pages/api/"):
        return True
    if any(part in {"route.ts", "route.tsx", "route.js", "route.jsx"} for part in lowered_parts):
        return True
    return False


def _resolve_safe_file(root_dir: Path, path: str) -> Path:
    root = root_dir.resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root):
        raise ValueError("project path escapes project directory")
    return target


def _run_build_command(command: list[str], source_dir: Path) -> None:
    subprocess.run(
        command,
        cwd=source_dir,
        check=True,
        text=True,
        capture_output=True,
        timeout=BUILD_TIMEOUT_SECONDS,
    )


def _npm_command() -> str:
    return "npm.cmd" if shutil.which("npm.cmd") else "npm"


def _short_error(detail: str) -> str:
    compact = re.sub(r"\s+", " ", detail).strip()
    if len(compact) > 500:
        return compact[:500] + "..."
    return compact or "未知错误"


def _remove_dir_if_exists(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
