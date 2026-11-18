from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

class BedCategoryBase(BaseModel):
    bed_type: str = Field(..., description="Type of bed: ICU, NICU, VENTILATOR, GENERAL, OXYGEN")
    total_beds: int = Field(ge=0, description="Total bed capacity")
    available_beds: int = Field(ge=0, description="Currently vacant beds available for emergency admission")
    occupied_beds: int = Field(ge=0, description="Currently occupied beds")

class BedCategoryOut(BedCategoryBase):
    id: int
    hospital_id: int
    last_updated: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class BedUpdateAction(BaseModel):
    bed_type: str = Field(..., description="Bed category to update")
    action: str = Field(..., description="'increment' to add available bed, 'decrement' to occupy, or 'set'")
    value: Optional[int] = Field(None, ge=0, description="Required only when action is 'set'")
    updated_by: Optional[str] = Field("Ward Staff", description="Name/Role of staff updating")

class HospitalBase(BaseModel):
    hospital_code: str
    name: str
    type: str = "Government / Multi-Speciality"
    address: str
    city: str
    locality: str
    pincode: str
    contact_emergency: str
    contact_reception: Optional[str] = None
    ambulance_available: bool = True
    oxygen_plant_active: bool = True
    blood_bank_available: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_emergency_active: bool = True

class HospitalOut(HospitalBase):
    id: int
    last_updated: Optional[datetime] = None
    beds: List[BedCategoryOut] = []
    model_config = ConfigDict(from_attributes=True)

class BedAuditLogOut(BaseModel):
    id: int
    hospital_id: int
    bed_type: str
    change_type: str
    previous_count: int
    new_count: int
    updated_by: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class StaffLoginRequest(BaseModel):
    hospital_id: int
    pin_code: str

class StaffLoginResponse(BaseModel):
    authenticated: bool
    hospital_id: int
    hospital_name: str
    staff_name: str
    role: str
    token: str

class AnalyticsSummary(BaseModel):
    total_hospitals: int
    total_beds: int
    total_available_beds: int
    total_occupied_beds: int
    city_occupancy_percentage: float
    icu_total: int
    icu_available: int
    nicu_total: int
    nicu_available: int
    ventilator_total: int
    ventilator_available: int
    general_total: int
    general_available: int
    oxygen_total: int
    oxygen_available: int
    critical_shortage_hospitals: List[dict] = []
