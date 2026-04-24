import re
from pathlib import Path


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
