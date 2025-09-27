# tests/test_resume_routes.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock
from app.main import app

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_resume_upload_pdf(monkeypatch):
    monkeypatch.setattr(
        "app.services.resume_service.process_resume_file",
        AsyncMock(return_value={"data": {}})
    )
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/resume_upload",
            files={"file": ("test.pdf", b"%PDF-1.4 fake PDF content", "application/pdf")}
        )
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_resume_upload_invalid_file(monkeypatch):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/resume_upload",
            files={"file": ("test.txt", b"not a pdf", "text/plain")}
        )
    assert response.json() == {
        "status": 400,
        "message": "Only pdfs allowed"
    }