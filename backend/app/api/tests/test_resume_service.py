import os
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

sample_pdf = os.path.join(os.path.dirname(__file__), os.path.join("assets", "sample.pdf"))

transport = ASGITransport(app=app)

@pytest.mark.asyncio
async def test_resume_upload_integration():
    assert os.path.exists(sample_pdf), f"{sample_pdf} not found"
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        with open(sample_pdf, "rb") as f:
            response = await ac.post(
                "/resume_upload",
                files={"file": ("sample.pdf", f, "application/pdf")}
            )

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == 200
    assert "data" in json_data
    assert "resume_id" in json_data["data"]
    assert "summary" in json_data["data"]
    assert isinstance(json_data["data"]["summary"], str)
    assert len(json_data["data"]["summary"]) > 0