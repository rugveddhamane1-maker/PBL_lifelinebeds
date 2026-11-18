from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Hospital(Base):
    __tablename__ = "hospitals"

    id = Column(Integer, primary_key=True, index=True)
    hospital_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(200), index=True, nullable=False)
    type = Column(String(50), default="Government / Multi-Speciality") # Government, Private, Charitable
    address = Column(String(300), nullable=False)
    city = Column(String(100), index=True, nullable=False)
    locality = Column(String(100), index=True, nullable=False)
    pincode = Column(String(20), index=True, nullable=False)
    contact_emergency = Column(String(50), nullable=False)
    contact_reception = Column(String(50), nullable=True)
    ambulance_available = Column(Boolean, default=True)
    oxygen_plant_active = Column(Boolean, default=True)
    blood_bank_available = Column(Boolean, default=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_emergency_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    beds = relationship("BedCategory", back_populates="hospital", cascade="all, delete-orphan")
    audit_logs = relationship("BedAuditLog", back_populates="hospital", cascade="all, delete-orphan")
    staff_members = relationship("Staff", back_populates="hospital")

class BedCategory(Base):
    __tablename__ = "bed_categories"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    bed_type = Column(String(50), nullable=False, index=True) # ICU, NICU, VENTILATOR, GENERAL, OXYGEN
    total_beds = Column(Integer, default=0, nullable=False)
    available_beds = Column(Integer, default=0, nullable=False)
    occupied_beds = Column(Integer, default=0, nullable=False)
    last_updated = Column(DateTime, default=utc_now, onupdate=utc_now)

    hospital = relationship("Hospital", back_populates="beds")

    __table_args__ = (
        Index("idx_hosp_bedtype", "hospital_id", "bed_type", unique=True),
    )

class BedAuditLog(Base):
    __tablename__ = "bed_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    bed_type = Column(String(50), nullable=False)
    change_type = Column(String(20), nullable=False) # "INCREMENT", "DECREMENT", "SET"
    previous_count = Column(Integer, nullable=False)
    new_count = Column(Integer, nullable=False)
    updated_by = Column(String(100), default="Staff Nurse / Ward Incharge")
    timestamp = Column(DateTime, default=utc_now)

    hospital = relationship("Hospital", back_populates="audit_logs")

class Staff(Base):
    __tablename__ = "staff_accounts"

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("hospitals.id"), nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(150), nullable=False)
    pin_code = Column(String(20), nullable=False) # e.g. "1234"
    role = Column(String(50), default="Nurse / Ward Staff")
    is_active = Column(Boolean, default=True)

    hospital = relationship("Hospital", back_populates="staff_members")
