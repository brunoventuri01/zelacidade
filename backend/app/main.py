import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Literal

import psycopg
from fastapi import Depends, FastAPI, Header, HTTPException, status
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, Field

DATABASE_URL = os.environ["DATABASE_URL"]
ROBOT_API_KEY = os.environ["ROBOT_API_KEY"]


def connection():
    return psycopg.connect(DATABASE_URL)


@asynccontextmanager
async def lifespan(_: FastAPI):
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS occurrences (
              id BIGSERIAL PRIMARY KEY,
              kind TEXT NOT NULL,
              description TEXT NOT NULL,
              latitude DOUBLE PRECISION,
              longitude DOUBLE PRECISION,
              source TEXT NOT NULL DEFAULT 'citizen',
              robot_id TEXT,
              distance_cm DOUBLE PRECISION,
              simulated BOOLEAN NOT NULL DEFAULT FALSE,
              created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
    yield


app = FastAPI(title="ZelaCidade API", version="0.1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


class OccurrenceIn(BaseModel):
    kind: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=3, max_length=1000)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


class RobotOccurrenceIn(BaseModel):
    robot_id: str = Field(min_length=2, max_length=80)
    event_type: Literal["obstacle", "pothole", "other"]
    distance_cm: float = Field(gt=0, le=1000)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    test_location: str = Field(min_length=2, max_length=200)
    simulated: bool
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)


def require_robot_key(x_api_key: str = Header(...)):
    if x_api_key != ROBOT_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")


@app.get("/health")
def health():
    with connection() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/api/v1/occurrences", status_code=201)
def create_occurrence(item: OccurrenceIn):
    with connection() as conn:
        row = conn.execute(
            """INSERT INTO occurrences(kind, description, latitude, longitude)
               VALUES (%s, %s, %s, %s) RETURNING id, created_at""",
            (item.kind, item.description, item.latitude, item.longitude),
        ).fetchone()
    return {"id": row[0], "created_at": row[1]}


@app.get("/api/v1/occurrences")
def list_occurrences():
    with connection() as conn:
        rows = conn.execute(
            """SELECT id, kind, description, latitude, longitude, source,
                      robot_id, distance_cm, simulated, created_at
               FROM occurrences ORDER BY created_at DESC LIMIT 200"""
        ).fetchall()
    keys = ["id", "kind", "description", "latitude", "longitude", "source", "robot_id", "distance_cm", "simulated", "created_at"]
    return [dict(zip(keys, row)) for row in rows]


@app.post("/api/v1/robot/occurrences", status_code=201, dependencies=[Depends(require_robot_key)])
def create_robot_occurrence(item: RobotOccurrenceIn):
    description = f"{item.event_type} detectado em {item.test_location}"
    with connection() as conn:
        row = conn.execute(
            """INSERT INTO occurrences(kind, description, latitude, longitude, source,
                                          robot_id, distance_cm, simulated, created_at)
               VALUES (%s, %s, %s, %s, 'robot', %s, %s, %s, %s)
               RETURNING id, created_at""",
            (item.event_type, description, item.latitude, item.longitude, item.robot_id,
             item.distance_cm, item.simulated, item.timestamp),
        ).fetchone()
    return {"id": row[0], "created_at": row[1]}
