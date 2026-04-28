import json
import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import (
    App,
    AppDataCreateRequest,
    AppDataRecord,
    AppDataRecordResponse,
    AppDataUpdateRequest,
    now_utc,
)

router = APIRouter()
COLLECTION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
MAX_PAYLOAD_BYTES = 64 * 1024


def can_access_generated_app(app: App | None) -> bool:
    return bool(
        app
        and (
            app.status == "active"
            or (app.status in {"editing", "edit_failed"} and app.version > 0)
        )
    )


def ensure_generated_app(app_id: str, db: Session) -> App:
    app = db.query(App).filter(App.id == app_id).first()
    if not can_access_generated_app(app):
        raise HTTPException(status_code=404, detail="App not found")
    return app


def validate_collection(collection: str) -> str:
    if not COLLECTION_PATTERN.fullmatch(collection):
        raise HTTPException(status_code=400, detail="Invalid collection name")
    return collection


def encode_payload(data: dict) -> str:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if len(payload.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Payload too large")
    return payload


def decode_payload(payload: str) -> dict:
    data = json.loads(payload)
    return data if isinstance(data, dict) else {}


def record_response(record: AppDataRecord) -> AppDataRecordResponse:
    return AppDataRecordResponse(
        id=record.id,
        app_id=record.app_id,
        collection=record.collection,
        data=decode_payload(record.payload),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def get_record(app_id: str, collection: str, record_id: str, db: Session) -> AppDataRecord:
    record = (
        db.query(AppDataRecord)
        .filter(
            AppDataRecord.app_id == app_id,
            AppDataRecord.collection == collection,
            AppDataRecord.id == record_id,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record



@router.get("/generated/{app_id}/data/{collection}", response_model=list[AppDataRecordResponse])
def list_app_data_records(
    app_id: str,
    collection: str,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    ensure_generated_app(app_id, db)
    collection = validate_collection(collection)
    records = (
        db.query(AppDataRecord)
        .filter(AppDataRecord.app_id == app_id, AppDataRecord.collection == collection)
        .order_by(AppDataRecord.created_at.desc(), AppDataRecord.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [record_response(record) for record in records]


@router.post("/generated/{app_id}/data/{collection}", response_model=AppDataRecordResponse, status_code=201)
def create_app_data_record(
    app_id: str,
    collection: str,
    body: AppDataCreateRequest,
    db: Session = Depends(get_db),
):
    ensure_generated_app(app_id, db)
    collection = validate_collection(collection)
    record = AppDataRecord(
        id=str(uuid.uuid4()),
        app_id=app_id,
        collection=collection,
        payload=encode_payload(body.data),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record_response(record)


@router.get("/generated/{app_id}/data/{collection}/{record_id}", response_model=AppDataRecordResponse)
def read_app_data_record(
    app_id: str,
    collection: str,
    record_id: str,
    db: Session = Depends(get_db),
):
    ensure_generated_app(app_id, db)
    collection = validate_collection(collection)
    return record_response(get_record(app_id, collection, record_id, db))


@router.put("/generated/{app_id}/data/{collection}/{record_id}", response_model=AppDataRecordResponse)
def update_app_data_record(
    app_id: str,
    collection: str,
    record_id: str,
    body: AppDataUpdateRequest,
    db: Session = Depends(get_db),
):
    ensure_generated_app(app_id, db)
    collection = validate_collection(collection)
    record = get_record(app_id, collection, record_id, db)
    record.payload = encode_payload(body.data)
    record.updated_at = now_utc()
    db.commit()
    db.refresh(record)
    return record_response(record)


@router.delete("/generated/{app_id}/data/{collection}/{record_id}")
def delete_app_data_record(
    app_id: str,
    collection: str,
    record_id: str,
    db: Session = Depends(get_db),
):
    ensure_generated_app(app_id, db)
    collection = validate_collection(collection)
    record = get_record(app_id, collection, record_id, db)
    db.delete(record)
    db.commit()
    return {"ok": True}
