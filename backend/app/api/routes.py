from fastapi import APIRouter, UploadFile, File, WebSocket, WebSocketDisconnect
from app.services.resume_service import process_resume_file, process_resume_file_bulk, send_resume_progress
from typing import Dict, List

router = APIRouter()

active_connections: Dict[str, List[WebSocket]] = {}

@router.post("/resume_upload")
async def resume_upload(file: UploadFile = File(...)):
    return await process_resume_file(file)

@router.post("/resume_upload_bulk")
async def resume_upload_bulk():
    return await process_resume_file_bulk()

@router.websocket("/ws/resume/{resume_id}")
async def resume_ws(websocket: WebSocket, resume_id: str):
    await websocket.accept()
    if resume_id not in active_connections:
        active_connections[resume_id] = []
    active_connections[resume_id].append(websocket)
    await send_resume_progress(websocket, resume_id, active_connections)