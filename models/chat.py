from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatSessionDocument(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessageDocument(BaseModel):
    session_id: str
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    classifications: List[str] = Field(default_factory=list)
    agents_used: List[str] = Field(default_factory=list)
    pdf_url: Optional[str] = None