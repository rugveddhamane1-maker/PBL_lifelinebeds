from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models import Hospital, BedCategory, BedAuditLog, Staff
from app.schemas import (
    HospitalOut, BedUpdateAction, StaffLoginRequest, StaffLoginResponse,
    BedAuditLogOut
)
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/api", tags=["Hospitals & Beds"])

@router.get("/hospitals", response_model=List[HospitalOut])
def get_hospitals(
    search: Optional[str] = Query(None, description="Search by name, address, locality or pincode"),
    bed_type: Optional[str] = Query(None, description="Filter hospitals having available beds in this category"),
    locality: Optional[str] = Query(None, description="Filter by locality"),
    emergency_only: bool = Query(True, description="Only show active emergency departments"),
    db: Session = Depends(get_db)
):
    query = db.query(Hospital)

    if emergency_only:
        query = query.filter(Hospital.is_emergency_active == True)

    if search:
        search_fmt = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Hospital.name.ilike(search_fmt),
                Hospital.locality.ilike(search_fmt),
                Hospital.address.ilike(search_fmt),
                Hospital.pincode.ilike(search_fmt),
                Hospital.hospital_code.ilike(search_fmt)
            )
        )

    if locality and locality != "ALL":
        query = query.filter(Hospital.locality.ilike(f"%{locality}%"))

    hospitals = query.all()

    # If filtering by specific bed type availability (e.g., ICU beds > 0)
    if bed_type and bed_type.upper() != "ALL":
        target_type = bed_type.upper()
        filtered = []
        for h in hospitals:
            has_bed = any(b.bed_type.upper() == target_type and b.available_beds > 0 for b in h.beds)
            if has_bed:
                filtered.append(h)
        return filtered

    return hospitals

@router.get("/hospitals/{hospital_id}", response_model=HospitalOut)
def get_hospital_by_id(hospital_id: int, db: Session = Depends(get_db)):
    hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found")
    return hosp

@router.get("/localities", response_model=List[str])
def get_localities(db: Session = Depends(get_db)):
    """Returns list of distinct localities for the dropdown filter."""
    localities = db.query(Hospital.locality).distinct().all()
    return sorted([loc[0] for loc in localities if loc[0]])

@router.post("/staff/login", response_model=StaffLoginResponse)
def staff_login(req: StaffLoginRequest, db: Session = Depends(get_db)):
    """Verifies staff PIN for quick authentication during shifts."""
    hosp = db.query(Hospital).filter(Hospital.id == req.hospital_id).first()
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found")

    staff = db.query(Staff).filter(
        Staff.hospital_id == req.hospital_id,
        Staff.pin_code == req.pin_code.strip()
    ).first()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Hospital PIN Code. Please check with your supervisor."
        )

    return StaffLoginResponse(
        authenticated=True,
        hospital_id=hosp.id,
        hospital_name=hosp.name,
        staff_name=staff.full_name,
        role=staff.role,
        token=f"auth_token_hosp_{hosp.id}_{staff.id}"
    )

@router.post("/hospitals/{hospital_id}/beds/update")
async def update_bed_status(
    hospital_id: int,
    action: BedUpdateAction,
    db: Session = Depends(get_db)
):
    """
    Hospital staff endpoint to update bed counts.
    Triggers instant broadcast via WebSocket to all connected patients and dashboards!
    """
    hosp = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not hosp:
        raise HTTPException(status_code=404, detail="Hospital not found")

    target_type = action.bed_type.upper().strip()
    bed = db.query(BedCategory).filter(
        BedCategory.hospital_id == hospital_id,
        BedCategory.bed_type == target_type
    ).first()

    if not bed:
        raise HTTPException(status_code=404, detail=f"Bed category '{target_type}' not found for this hospital")

    prev_avail = bed.available_beds
    prev_occ = bed.occupied_beds
    act = action.action.lower()

    if act == "increment":
        # New bed made available (patient discharged or bed sanitized)
        if bed.available_beds >= bed.total_beds:
            raise HTTPException(status_code=400, detail="Cannot exceed total bed capacity")
        bed.available_beds += 1
        bed.occupied_beds = max(0, bed.total_beds - bed.available_beds)
        change_desc = "+1 Bed Vacated / Available"

    elif act == "decrement":
        # Bed occupied (emergency admission)
        if bed.available_beds <= 0:
            raise HTTPException(status_code=400, detail="No available beds left in this category to occupy")
        bed.available_beds -= 1
        bed.occupied_beds = min(bed.total_beds, bed.total_beds - bed.available_beds)
        change_desc = "-1 Bed Occupied / Admitted"

    elif act == "set":
        # Direct count update
        if action.value is None or action.value < 0:
            raise HTTPException(status_code=400, detail="Valid non-negative value required for 'set'")
        if action.value > bed.total_beds:
            raise HTTPException(status_code=400, detail=f"Cannot set available beds ({action.value}) greater than total capacity ({bed.total_beds})")
        bed.available_beds = action.value
        bed.occupied_beds = bed.total_beds - bed.available_beds
        change_desc = f"Count Set to {action.value}"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {act}")

    now = datetime.now(timezone.utc)
    bed.last_updated = now
    hosp.last_updated = now

    # Create audit log entry
    log_entry = BedAuditLog(
        hospital_id=hospital_id,
        bed_type=target_type,
        change_type=act.upper(),
        previous_count=prev_avail,
        new_count=bed.available_beds,
        updated_by=action.updated_by or "Ward Staff",
        timestamp=now
    )
    db.add(log_entry)
    db.commit()
    db.refresh(bed)

    # BROADCAST REAL-TIME WEBSOCKET EVENT
    ws_event = {
        "event": "BED_UPDATED",
        "timestamp": now.isoformat(),
        "hospital_id": hospital_id,
        "hospital_name": hosp.name,
        "locality": hosp.locality,
        "bed_type": target_type,
        "previous_available": prev_avail,
        "available_beds": bed.available_beds,
        "occupied_beds": bed.occupied_beds,
        "total_beds": bed.total_beds,
        "change_desc": change_desc,
        "updated_by": action.updated_by
    }
    await ws_manager.broadcast(ws_event)

    return {
        "success": True,
        "message": f"Successfully updated {target_type} beds for {hosp.name}",
        "bed": {
            "bed_type": bed.bed_type,
            "available_beds": bed.available_beds,
            "occupied_beds": bed.occupied_beds,
            "total_beds": bed.total_beds
        }
    }

@router.get("/audit-logs", response_model=List[BedAuditLogOut])
def get_audit_logs(limit: int = 30, db: Session = Depends(get_db)):
    """Returns recent bed audit updates for transparency and monitoring."""
    logs = db.query(BedAuditLog).order_by(BedAuditLog.timestamp.desc()).limit(limit).all()
    return logs
