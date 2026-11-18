from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Hospital, BedCategory
from app.schemas import AnalyticsSummary

router = APIRouter(prefix="/api/analytics", tags=["City Analytics"])

@router.get("/summary", response_model=AnalyticsSummary)
def get_analytics_summary(db: Session = Depends(get_db)):
    hospitals = db.query(Hospital).filter(Hospital.is_emergency_active == True).all()
    
    total_beds = 0
    total_avail = 0
    total_occ = 0

    category_stats = {
        "ICU": {"total": 0, "avail": 0},
        "NICU": {"total": 0, "avail": 0},
        "VENTILATOR": {"total": 0, "avail": 0},
        "GENERAL": {"total": 0, "avail": 0},
        "OXYGEN": {"total": 0, "avail": 0},
    }

    critical_hospitals = []

    for hosp in hospitals:
        hosp_icu_avail = None
        hosp_vent_avail = None
        
        for bed in hosp.beds:
            b_type = bed.bed_type.upper()
            total_beds += bed.total_beds
            total_avail += bed.available_beds
            total_occ += bed.occupied_beds

            if b_type in category_stats:
                category_stats[b_type]["total"] += bed.total_beds
                category_stats[b_type]["avail"] += bed.available_beds

            if b_type == "ICU":
                hosp_icu_avail = bed.available_beds
            elif b_type == "VENTILATOR":
                hosp_vent_avail = bed.available_beds

        # Flag critical shortage if ICU or Ventilator beds <= 2
        if (hosp_icu_avail is not None and hosp_icu_avail <= 2) or \
           (hosp_vent_avail is not None and hosp_vent_avail <= 1):
            critical_hospitals.append({
                "hospital_id": hosp.id,
                "name": hosp.name,
                "locality": hosp.locality,
                "icu_available": hosp_icu_avail if hosp_icu_avail is not None else 0,
                "ventilator_available": hosp_vent_avail if hosp_vent_avail is not None else 0,
                "emergency_phone": hosp.contact_emergency
            })

    occupancy_pct = round((total_occ / total_beds * 100), 1) if total_beds > 0 else 0.0

    return AnalyticsSummary(
        total_hospitals=len(hospitals),
        total_beds=total_beds,
        total_available_beds=total_avail,
        total_occupied_beds=total_occ,
        city_occupancy_percentage=occupancy_pct,
        icu_total=category_stats["ICU"]["total"],
        icu_available=category_stats["ICU"]["avail"],
        nicu_total=category_stats["NICU"]["total"],
        nicu_available=category_stats["NICU"]["avail"],
        ventilator_total=category_stats["VENTILATOR"]["total"],
        ventilator_available=category_stats["VENTILATOR"]["avail"],
        general_total=category_stats["GENERAL"]["total"],
        general_available=category_stats["GENERAL"]["avail"],
        oxygen_total=category_stats["OXYGEN"]["total"],
        oxygen_available=category_stats["OXYGEN"]["avail"],
        critical_shortage_hospitals=critical_hospitals
    )
