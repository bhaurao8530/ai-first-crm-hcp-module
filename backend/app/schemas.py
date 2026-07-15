from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    hospital: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = "B"


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    id: int
    class Config:
        from_attributes = True


class InteractionBase(BaseModel):
    hcp_id: int
    interaction_type: Optional[str] = "Visit"
    channel: Optional[str] = "In-person"
    raw_notes: Optional[str] = None
    topics_discussed: Optional[str] = None
    products_discussed: Optional[str] = None
    samples_dropped: Optional[str] = None
    follow_up_action: Optional[str] = None
    follow_up_date: Optional[datetime] = None


class InteractionCreate(InteractionBase):
    created_via: Optional[str] = "form"


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    channel: Optional[str] = None
    raw_notes: Optional[str] = None
    topics_discussed: Optional[str] = None
    products_discussed: Optional[str] = None
    samples_dropped: Optional[str] = None
    follow_up_action: Optional[str] = None
    follow_up_date: Optional[datetime] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None


class InteractionOut(InteractionBase):
    id: int
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    compliance_flag: Optional[str] = None
    compliance_reason: Optional[str] = None
    created_via: str
    date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    session_id: str
    message: str
    hcp_id: Optional[int] = None


class ChatResponse(BaseModel):
    reply: str
    tool_used: Optional[str] = None
    interaction: Optional[InteractionOut] = None
    state: Optional[dict] = None
