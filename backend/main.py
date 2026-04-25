import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config import settings
from database import get_db, initialize_database
from models import App, User
from routers import admin, apps, auth, chat, styles
from services import code_service
from services.auth_service import get_current_user

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

initialize_database()

app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
app.include_router(apps.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(styles.router, prefix="/api")

# Serve generated apps at /apps/{app_id}/
data_dir = settings.DATA_DIR
os.makedirs(f"{data_dir}/apps", exist_ok=True)


@app.get("/generated/{app_id}/project/{file_path:path}")
def serve_generated_project_file(
    app_id: str,
    file_path: str,
    db: Session = Depends(get_db),
):
    generated_app = db.query(App).filter(App.id == app_id).first()
    if not _can_serve_generated_files(generated_app):
        raise HTTPException(status_code=404, detail="App not found")

    project_dir = code_service.project_dir_for(app_id, data_dir)
    try:
        target = code_service.resolve_project_file(project_dir, file_path)
    except ValueError:
        raise HTTPException(status_code=404, detail="App file not found")
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="App file not found")
    return FileResponse(target, headers={"Cache-Control": "no-store"})


@app.get("/apps/{app_id}/")
def serve_generated_app(
    app_id: str,
    db: Session = Depends(get_db),
):
    generated_app = db.query(App).filter(App.id == app_id).first()
    if not _can_serve_generated_files(generated_app):
        raise HTTPException(status_code=404, detail="App not found")
    index_path = os.path.join(data_dir, "apps", app_id, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(status_code=404, detail="App file not found")
    return FileResponse(index_path, headers={"Cache-Control": "no-store"})


def _can_serve_generated_files(generated_app: App | None) -> bool:
    return bool(
        generated_app
        and (
            generated_app.status == "active"
            or (generated_app.status in {"editing", "edit_failed"} and generated_app.version > 0)
        )
    )


# Serve frontend build at / (if static/ exists)
static_dir = "static"
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")
