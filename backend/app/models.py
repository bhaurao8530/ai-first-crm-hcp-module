from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class HCP(Base):
    """A Healthcare Professional (doctor) that a field rep visits."""
    __tablename__ = "hcps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    specialty = Column(String(120))
    hospital = Column(String(200))
    email = Column(String(120))
    phone = Column(String(30))
    segment = Column(String(50), default="B")  # A/B/C tiering
    created_at = Column(DateTime, default=datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """A single logged interaction (visit/call/email) with an HCP."""
    __tablename__ = "interactions"

    id = Column(Integer, primary_key=True, index=True)
    hcp_id = Column(Integer, ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(50), default="Visit")  # Visit / Call / Email / Conference
    channel = Column(String(50), default="In-person")
    date = Column(DateTime, default=datetime.utcnow)

    raw_notes = Column(Text)          # what the rep typed/said, verbatim
    summary = Column(Text)            # LLM-generated summary
    topics_discussed = Column(Text)   # comma separated / JSON string
    products_discussed = Column(Text)
    sentiment = Column(String(20))    # Positive / Neutral / Negative
    samples_dropped = Column(String(200))
    follow_up_action = Column(Text)
    follow_up_date = Column(DateTime, nullable=True)
    compliance_flag = Column(String(20), default="OK")  # OK / REVIEW
    compliance_reason = Column(Text, nullable=True)

    created_via = Column(String(20), default="form")  # "form" or "chat"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hcp = relationship("HCP", back_populates="interactions")
