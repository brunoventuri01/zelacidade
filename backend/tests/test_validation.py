import os
os.environ.setdefault("DATABASE_URL", "postgresql://invalid")
os.environ.setdefault("ROBOT_API_KEY", "test-key")
from pydantic import ValidationError
from app.main import OccurrenceIn, RobotOccurrenceIn

def test_occurrence_coordinates():
    item = OccurrenceIn(kind="Buraco", description="Teste", latitude=-23.5, longitude=-46.6)
    assert item.kind == "Buraco"

def test_robot_rejects_negative_distance():
    try:
        RobotOccurrenceIn(robot_id="r1", event_type="obstacle", distance_cm=-1, test_location="lab", simulated=True)
    except ValidationError:
        return
    raise AssertionError("Distância negativa deveria ser rejeitada")
