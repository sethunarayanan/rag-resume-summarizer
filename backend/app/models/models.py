from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

class ResumeMeta(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    file_name: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    content_text: Optional[str] = None
    chroma_ids: Optional[List[str]] = Field(default_factory=list)
    summary: Optional[str] = None
    interview_questions: Optional[List[str]] = Field(default_factory=list)
    status: str = "pending" # pending | processing | complete

class ResumeChunk(BaseModel):
    pass