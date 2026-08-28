from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.types import JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    contact_data = Column(JSON, nullable=False)
    business_info = Column(Text, nullable=True)
    budget = Column(String(50), nullable=True)
    preferred_contact = Column(String(50), nullable=True)
    comments = Column(Text, nullable=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    referer = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True)
    page_load_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)