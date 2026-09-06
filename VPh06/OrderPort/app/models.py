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
    business_niche = Column(String(255), nullable=True)
    company_size = Column(String(50), nullable=True)
    task_volume = Column(String(50), nullable=True)
    role = Column(String(100), nullable=True)
    budget = Column(String(50), nullable=True)
    preferred_contact = Column(String(50), nullable=True)
    comments = Column(Text, nullable=True)
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    referer = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True)
    page_load_time = Column(Float, nullable=True)
    service_id = Column(Integer, ForeignKey("admin_settings.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Изменено: uselist=True, так как у одного лида может быть много метрик
    behavior_metrics = relationship("BehaviorMetrics", uselist=True, back_populates="lead")


class AdminSettings(Base):
    __tablename__ = "admin_settings"

    id = Column(Integer, primary_key=True, index=True)
    services = Column(String(255), nullable=False)
    budget_range = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class BehaviorMetrics(Base):
    __tablename__ = "behavior_metrics"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False, index=True)  # убрали unique=True
    page_load_time = Column(Float, nullable=True)
    session_duration = Column(Float, nullable=True)
    clicks = Column(Integer, nullable=True)
    scroll_depth = Column(Integer, nullable=True)
    other_metrics = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())

    lead = relationship("Lead", back_populates="behavior_metrics")


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())