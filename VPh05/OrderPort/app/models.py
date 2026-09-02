from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
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
    service_id = Column(Integer, ForeignKey("admin_settings.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())   # <-- изменено
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())   # <-- изменено

    behavior_metrics = relationship("BehaviorMetrics", uselist=False, back_populates="lead")


class AdminSettings(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    services = Column(String(255), nullable=False)
    budget_range = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())   # <-- изменено
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())   # <-- изменено


class BehaviorMetrics(Base):
    __tablename__ = "behavior_metrics"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), unique=True, nullable=False, index=True)
    page_load_time = Column(Float, nullable=True)
    session_duration = Column(Float, nullable=True)
    clicks = Column(Integer, nullable=True)
    scroll_depth = Column(Integer, nullable=True)
    other_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())   # <-- изменено

    lead = relationship("Lead", back_populates="behavior_metrics")