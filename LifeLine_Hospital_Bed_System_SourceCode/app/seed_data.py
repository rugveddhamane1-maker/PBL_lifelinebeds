from sqlalchemy.orm import Session
from app.models import Hospital, BedCategory, Staff
from app.config import settings

def seed_database(db: Session):
    """Seed initial realistic hospital and bed dataset if database is empty."""
    if db.query(Hospital).first() is not None:
        return  # Already seeded

    hospitals_data = [
        {
            "code": "HOSP-001",
            "name": "City Civil Government Hospital",
            "type": "Government Multi-Speciality",
            "address": "Opposite Central Railway Station, Sector 4",
            "city": settings.CITY_DEFAULT,
            "locality": "Central Ward",
            "pincode": "400001",
            "emergency": "+91 22 2412 1100",
            "reception": "+91 22 2412 1101",
            "ambulance": True,
            "oxygen": True,
            "blood_bank": True,
            "lat": 18.9401,
            "lng": 72.8347,
            "beds": [
                {"type": "ICU", "total": 40, "avail": 6, "occ": 34},
                {"type": "NICU", "total": 20, "avail": 4, "occ": 16},
                {"type": "VENTILATOR", "total": 25, "avail": 3, "occ": 22},
                {"type": "GENERAL", "total": 250, "avail": 45, "occ": 205},
                {"type": "OXYGEN", "total": 100, "avail": 18, "occ": 82},
            ],
            "staff": {"name": "Sister Anita Sharma", "user": "staff_civil", "pin": "1234"}
        },
        {
            "code": "HOSP-002",
            "name": "LifeLine Trauma & Emergency Center",
            "type": "Private Level-1 Trauma",
            "address": "Express Highway Junction, North Sector 12",
            "city": settings.CITY_DEFAULT,
            "locality": "North Corridor",
            "pincode": "400012",
            "emergency": "+91 22 2890 9999",
            "reception": "+91 22 2890 9900",
            "ambulance": True,
            "oxygen": True,
            "blood_bank": True,
            "lat": 19.1176,
            "lng": 72.8465,
            "beds": [
                {"type": "ICU", "total": 35, "avail": 8, "occ": 27},
                {"type": "NICU", "total": 15, "avail": 2, "occ": 13},
                {"type": "VENTILATOR", "total": 20, "avail": 5, "occ": 15},
                {"type": "GENERAL", "total": 120, "avail": 22, "occ": 98},
                {"type": "OXYGEN", "total": 60, "avail": 12, "occ": 48},
            ],
            "staff": {"name": "Dr. Rajesh Kulkarni", "user": "staff_lifeline", "pin": "1234"}
        },
        {
            "code": "HOSP-003",
            "name": "Sunrise Women & Children Care Hospital",
            "type": "Pediatric & Maternity Super-Speciality",
            "address": "Park Road, Green Valley Phase 2",
            "city": settings.CITY_DEFAULT,
            "locality": "West Suburb",
            "pincode": "400050",
            "emergency": "+91 22 2640 4400",
            "reception": "+91 22 2640 4401",
            "ambulance": True,
            "oxygen": True,
            "blood_bank": False,
            "lat": 19.0596,
            "lng": 72.8295,
            "beds": [
                {"type": "ICU", "total": 15, "avail": 2, "occ": 13},
                {"type": "NICU", "total": 35, "avail": 11, "occ": 24},
                {"type": "VENTILATOR", "total": 10, "avail": 2, "occ": 8},
                {"type": "GENERAL", "total": 80, "avail": 19, "occ": 61},
                {"type": "OXYGEN", "total": 40, "avail": 9, "occ": 31},
            ],
            "staff": {"name": "Nurse Mary D'souza", "user": "staff_sunrise", "pin": "1234"}
        },
        {
            "code": "HOSP-004",
            "name": "Apex Heart & Super Speciality Hospital",
            "type": "Cardiac & Critical Care",
            "address": "Ring Road Boulevard, Tech Zone",
            "city": settings.CITY_DEFAULT,
            "locality": "East Zone",
            "pincode": "400076",
            "emergency": "+91 22 2570 8811",
            "reception": "+91 22 2570 8800",
            "ambulance": True,
            "oxygen": True,
            "blood_bank": True,
            "lat": 19.1254,
            "lng": 72.9152,
            "beds": [
                {"type": "ICU", "total": 50, "avail": 1, "occ": 49}, # Critical shortage example
                {"type": "NICU", "total": 10, "avail": 0, "occ": 10},
                {"type": "VENTILATOR", "total": 30, "avail": 1, "occ": 29},
                {"type": "GENERAL", "total": 150, "avail": 8, "occ": 142},
                {"type": "OXYGEN", "total": 80, "avail": 4, "occ": 76},
            ],
            "staff": {"name": "Ward Manager Vikram Roy", "user": "staff_apex", "pin": "1234"}
        },
        {
            "code": "HOSP-005",
            "name": "St. Jude Charitable Trust Hospital",
            "type": "Charitable Community Hospital",
            "address": "St. Anthony Street, Old Port Road",
            "city": settings.CITY_DEFAULT,
            "locality": "South Harbor",
            "pincode": "400009",
            "emergency": "+91 22 2375 1200",
            "reception": "+91 22 2375 1201",
            "ambulance": True,
            "oxygen": True,
            "blood_bank": True,
            "lat": 18.9612,
            "lng": 72.8423,
            "beds": [
                {"type": "ICU", "total": 20, "avail": 5, "occ": 15},
                {"type": "NICU", "total": 10, "avail": 3, "occ": 7},
                {"type": "VENTILATOR", "total": 12, "avail": 4, "occ": 8},
                {"type": "GENERAL", "total": 180, "avail": 35, "occ": 145},
                {"type": "OXYGEN", "total": 70, "avail": 16, "occ": 54},
            ],
            "staff": {"name": "Sr. Catherine Joseph", "user": "staff_stjude", "pin": "1234"}
        },
        {
            "code": "HOSP-006",
            "name": "Fortis Metro Critical Care",
            "type": "Private Multi-Speciality",
            "address": "Grand Mall Road, Sector 18",
            "city": settings.CITY_DEFAULT,
            "locality": "West Suburb",
            "pincode": "400053",
            "emergency": "+91 22 2631 3322",
            "reception": "+91 22 2631 3300",
            "ambulance": True,
            "oxygen": True,
            "blood_bank": True,
            "lat": 19.1351,
            "lng": 72.8335,
            "beds": [
                {"type": "ICU", "total": 30, "avail": 9, "occ": 21},
                {"type": "NICU", "total": 15, "avail": 5, "occ": 10},
                {"type": "VENTILATOR", "total": 18, "avail": 6, "occ": 12},
                {"type": "GENERAL", "total": 110, "avail": 28, "occ": 82},
                {"type": "OXYGEN", "total": 50, "avail": 14, "occ": 36},
            ],
            "staff": {"name": "Coordinator Amit Verma", "user": "staff_fortis", "pin": "1234"}
        }
    ]

    for item in hospitals_data:
        hosp = Hospital(
            hospital_code=item["code"],
            name=item["name"],
            type=item["type"],
            address=item["address"],
            city=item["city"],
            locality=item["locality"],
            pincode=item["pincode"],
            contact_emergency=item["emergency"],
            contact_reception=item["reception"],
            ambulance_available=item["ambulance"],
            oxygen_plant_active=item["oxygen"],
            blood_bank_available=item["blood_bank"],
            latitude=item["lat"],
            longitude=item["lng"],
            is_emergency_active=True
        )
        db.add(hosp)
        db.flush()

        # Seed Bed Categories
        for b in item["beds"]:
            bed = BedCategory(
                hospital_id=hosp.id,
                bed_type=b["type"],
                total_beds=b["total"],
                available_beds=b["avail"],
                occupied_beds=b["occ"]
            )
            db.add(bed)

        # Seed Staff
        staff_info = item["staff"]
        staff = Staff(
            hospital_id=hosp.id,
            username=staff_info["user"],
            full_name=staff_info["name"],
            pin_code=staff_info["pin"],
            role="Ward Incharge"
        )
        db.add(staff)

    db.commit()
