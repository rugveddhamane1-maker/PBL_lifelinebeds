import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine, SessionLocal
from app.seed_data import seed_database
from app.models import Hospital, BedCategory

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()
    yield

def test_health_check():
    """Test health check returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_home_page():
    """Test home page HTML loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert "LifeLine" in response.text

def test_staff_page():
    """Test staff console HTML loads successfully."""
    response = client.get("/staff")
    assert response.status_code == 200
    assert "Staff Console" in response.text

def test_analytics_page():
    """Test analytics dashboard HTML loads successfully."""
    response = client.get("/analytics")
    assert response.status_code == 200
    assert "City Health" in response.text

def test_get_hospitals_list():
    """Test public hospital listing endpoint."""
    response = client.get("/api/hospitals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 5
    first_hosp = data[0]
    assert "name" in first_hosp
    assert "beds" in first_hosp
    assert len(first_hosp["beds"]) >= 4

def test_search_hospitals():
    """Test keyword search."""
    response = client.get("/api/hospitals?search=Civil")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert "Civil" in data[0]["name"]

def test_filter_by_bed_type():
    """Test filtering by available ICU beds."""
    response = client.get("/api/hospitals?bed_type=ICU")
    assert response.status_code == 200
    data = response.json()
    for h in data:
        icu = next((b for b in h["beds"] if b["bed_type"] == "ICU"), None)
        assert icu is not None
        assert icu["available_beds"] > 0

def test_staff_login_invalid_pin():
    """Test rejection of unauthorized PIN code."""
    response = client.post(
        "/api/staff/login",
        json={"hospital_id": 1, "pin_code": "9999"}
    )
    assert response.status_code == 401

def test_staff_login_valid_pin():
    """Test staff authentication with valid PIN code."""
    response = client.post(
        "/api/staff/login",
        json={"hospital_id": 1, "pin_code": "1234"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert "token" in data

def test_bed_update_flow():
    """Test incrementing and decrementing beds and audit logging."""
    # Get current ICU count for hospital 1
    h_before = client.get("/api/hospitals/1").json()
    icu_before = next(b for b in h_before["beds"] if b["bed_type"] == "ICU")
    initial_avail = icu_before["available_beds"]

    # 1. Admit patient (-1 available)
    res_dec = client.post(
        "/api/hospitals/1/beds/update",
        json={"bed_type": "ICU", "action": "decrement", "updated_by": "Test Nurse"}
    )
    assert res_dec.status_code == 200
    assert res_dec.json()["bed"]["available_beds"] == initial_avail - 1

    # 2. Discharge patient (+1 available)
    res_inc = client.post(
        "/api/hospitals/1/beds/update",
        json={"bed_type": "ICU", "action": "increment", "updated_by": "Test Nurse"}
    )
    assert res_inc.status_code == 200
    assert res_inc.json()["bed"]["available_beds"] == initial_avail

    # 3. Verify audit log entry was created
    audit_res = client.get("/api/audit-logs?limit=5")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) > 0
    assert logs[0]["bed_type"] == "ICU"

def test_analytics_summary():
    """Test city health department aggregation summary."""
    response = client.get("/api/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_hospitals"] >= 5
    assert data["total_beds"] > 0
    assert data["total_available_beds"] >= 0
    assert 0.0 <= data["city_occupancy_percentage"] <= 100.0

def test_websocket_connection():
    """Test real-time WebSocket connection handshake."""
    with client.websocket_connect("/ws/beds") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "CONNECTED"
        assert data["status"] == "LIVE_SYNC"
        
        # Test ping-pong heartbeat
        websocket.send_text("ping")
        resp = websocket.receive_json()
        assert resp["event"] == "pong"
