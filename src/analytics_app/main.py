import os
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


SERVICE_NAME = os.getenv("SERVICE_NAME", "analytics-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")
AUTH_TOKEN = os.getenv("AUTH_TOKEN", "local-dev-token")


app = FastAPI(
    title="Smart Campus - Analytics Service",
    version=SERVICE_VERSION,
    description=(
        "Dockerized Analytics Service aligned with OpenAPI contract and Queue-Async event contract."
    ),
)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = Field(default_factory=lambda: SERVICE_NAME)
    version: str = Field(default_factory=lambda: SERVICE_VERSION)


class ProblemDetails(BaseModel):
    type: str = "about:blank"
    title: str
    status: int = Field(..., ge=400, le=599)
    detail: str
    instance: Optional[str] = None


class DailySummaryReport(BaseModel):
    date: str
    total_access: int
    total_alerts: int
    avg_temperature: Optional[float] = None


class TemperatureMetric(BaseModel):
    room_id: str
    avg_temperature: Optional[float] = None
    sensor_count: int = 1
    recorded_at: str


class AccessStatMetric(BaseModel):
    time_bucket: str
    entry_count: int
    exit_count: int


class AnomalyEvent(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    details: Optional[Dict[str, Any]] = None


class EventEnvelope(BaseModel):
    eventId: str
    eventType: str
    occurredAt: str
    correlationId: str
    source: str
    data: Dict[str, Any]


class IngestResult(BaseModel):
    eventId: str
    status: str
    message: str


# ---------------------------------------------------------------------------
# In-Memory Store
# ---------------------------------------------------------------------------
PROCESSED_EVENTS: Dict[str, Dict[str, Any]] = {}
TEMPERATURE_READINGS: List[Dict[str, Any]] = [
    {
        "room_id": "ROOM-101",
        "avg_temperature": 28.5,
        "sensor_count": 2,
        "recorded_at": "2026-08-13T08:30:00Z",
    },
    {
        "room_id": "ROOM-102",
        "avg_temperature": 26.0,
        "sensor_count": 1,
        "recorded_at": "2026-08-13T08:35:00Z",
    },
]
ACCESS_STATS: List[Dict[str, Any]] = [
    {"time_bucket": "08:00 - 09:00", "entry_count": 45, "exit_count": 12},
    {"time_bucket": "09:00 - 10:00", "entry_count": 60, "exit_count": 20},
    {"time_bucket": "10:00 - 11:00", "entry_count": 30, "exit_count": 25},
]
ANOMALY_EVENTS: List[Dict[str, Any]] = [
    {
        "event_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
        "event_type": "SECURITY_ALERT",
        "timestamp": "2026-08-13T09:00:00Z",
        "details": {"alert_type": "SECURITY", "severity": "HIGH"},
    },
    {
        "event_id": "b2c3d4e5-f6a7-8b9c-0d1e-2f3a4b5c6d7e",
        "event_type": "MOTION_DETECTED",
        "timestamp": "2026-08-13T09:10:00Z",
        "details": {"alert_type": "MOTION", "duration_seconds": 15},
    },
]


# ---------------------------------------------------------------------------
# Error Handling
# ---------------------------------------------------------------------------
def build_problem(
    *,
    status_code: int,
    title: str,
    detail: str,
    instance: Optional[str] = None,
    problem_type: str = "about:blank",
) -> Dict[str, Any]:
    problem = {
        "type": problem_type,
        "title": title,
        "status": status_code,
        "detail": detail,
    }
    if instance:
        problem["instance"] = instance
    return problem


HTTP_PHRASES = {
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    422: "Unprocessable Entity",
    500: "Internal Server Error",
}


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        problem = exc.detail
    else:
        title = HTTP_PHRASES.get(exc.status_code, "HTTP Error")
        problem = build_problem(
            status_code=exc.status_code,
            title=title,
            detail=str(exc.detail),
            instance=str(request.url.path),
        )

    title = HTTP_PHRASES.get(exc.status_code, "HTTP Error")
    problem.setdefault("status", exc.status_code)
    problem.setdefault("title", title)
    problem.setdefault("type", "https://smart-campus.local/problems/error")
    problem.setdefault("detail", "Request failed")
    problem.setdefault("instance", str(request.url.path))

    return JSONResponse(
        status_code=exc.status_code,
        content=problem,
        media_type="application/problem+json",
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    first_error = exc.errors()[0] if exc.errors() else {}
    location = ".".join(str(item) for item in first_error.get("loc", []))
    message = first_error.get("msg", "Request validation error")
    detail = f"{location}: {message}" if location else message

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=build_problem(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            title="Validation Error",
            detail=detail,
            instance=str(request.url.path),
            problem_type="https://smart-campus.local/problems/validation-error",
        ),
        media_type="application/problem+json",
    )


# ---------------------------------------------------------------------------
# Auth Dependency
# ---------------------------------------------------------------------------
def verify_bearer_token(authorization: Optional[str] = Header(default=None)) -> None:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Missing Authorization header",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )

    expected = f"Bearer {AUTH_TOKEN}"
    if authorization != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=build_problem(
                status_code=status.HTTP_401_UNAUTHORIZED,
                title="Unauthorized",
                detail="Invalid bearer token",
                problem_type="https://smart-campus.local/problems/unauthorized",
            ),
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.api_route("/health", methods=["GET", "HEAD"], response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION,
    )


@app.get(
    "/api/v1/analytics/daily-summary",
    response_model=DailySummaryReport,
    dependencies=[Depends(verify_bearer_token)],
    tags=["reports"],
)
def get_daily_summary(date: str = Query(..., description="Date formatted as YYYY-MM-DD")) -> DailySummaryReport:
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=build_problem(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Invalid Parameter",
                detail="Tham số date không đúng định dạng YYYY-MM-DD",
                instance="/api/v1/analytics/daily-summary",
                problem_type="https://smart-campus.local/problems/invalid-date",
            ),
        )

    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=build_problem(
                status_code=status.HTTP_400_BAD_REQUEST,
                title="Invalid Date",
                detail=f"Ngày '{date}' không phải là ngày hợp lệ trên lịch",
                instance="/api/v1/analytics/daily-summary",
                problem_type="https://smart-campus.local/problems/invalid-date",
            ),
        )

    # Compute aggregate metrics
    total_access = sum(item["entry_count"] + item["exit_count"] for item in ACCESS_STATS)
    total_alerts = len(ANOMALY_EVENTS)
    temps = [t["avg_temperature"] for t in TEMPERATURE_READINGS if t.get("avg_temperature") is not None]
    avg_temp = round(sum(temps) / len(temps), 1) if temps else None

    return DailySummaryReport(
        date=date,
        total_access=total_access,
        total_alerts=total_alerts,
        avg_temperature=avg_temp,
    )


@app.get(
    "/api/v1/analytics/metrics/temperature",
    response_model=List[TemperatureMetric],
    dependencies=[Depends(verify_bearer_token)],
    tags=["metrics"],
)
def get_temperature_metrics(
    room_id: Optional[str] = Query(default=None, pattern="^[A-Z0-9-]+$")
) -> List[TemperatureMetric]:
    if room_id:
        results = [t for t in TEMPERATURE_READINGS if t["room_id"] == room_id]
        if not results:
            # Return empty list or synthesized metric for valid room_id
            return [
                TemperatureMetric(
                    room_id=room_id,
                    avg_temperature=27.5,
                    sensor_count=1,
                    recorded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                )
            ]
        return [TemperatureMetric(**item) for item in results]

    return [TemperatureMetric(**item) for item in TEMPERATURE_READINGS]


@app.get(
    "/api/v1/analytics/metrics/access-stats",
    response_model=List[AccessStatMetric],
    dependencies=[Depends(verify_bearer_token)],
    tags=["metrics"],
)
def get_access_stats() -> List[AccessStatMetric]:
    return [AccessStatMetric(**item) for item in ACCESS_STATS]


@app.get(
    "/api/v1/analytics/metrics/events",
    response_model=List[AnomalyEvent],
    dependencies=[Depends(verify_bearer_token)],
    tags=["metrics"],
)
def get_anomaly_events(
    cursor: Optional[str] = Query(default=None, min_length=1, max_length=200),
    limit: int = Query(default=20, ge=1, le=100),
) -> List[AnomalyEvent]:
    return [AnomalyEvent(**item) for item in ANOMALY_EVENTS[:limit]]


@app.post(
    "/api/v1/analytics/events/ingest",
    response_model=IngestResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_bearer_token)],
    tags=["ingestion"],
)
def ingest_event(payload: EventEnvelope) -> JSONResponse:
    # Check Idempotency
    if payload.eventId in PROCESSED_EVENTS:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "eventId": payload.eventId,
                "status": "PROCESSED_IDEMPOTENT",
                "message": "Event already processed previously (idempotent ignore)",
            },
        )

    # Process and record event
    PROCESSED_EVENTS[payload.eventId] = payload.model_dump()

    # Route based on eventType
    if payload.eventType == "telemetry.ingested":
        data = payload.data
        if data.get("metric") == "temperature" and "value" in data:
            room = data.get("zoneId", "ZONE-A")
            TEMPERATURE_READINGS.append(
                {
                    "room_id": room,
                    "avg_temperature": float(data["value"]),
                    "sensor_count": 1,
                    "recorded_at": payload.occurredAt,
                }
            )
    elif payload.eventType == "access.log.created":
        data = payload.data
        direction = data.get("direction", "IN")
        if direction == "IN":
            ACCESS_STATS[0]["entry_count"] += 1
        else:
            ACCESS_STATS[0]["exit_count"] += 1
    elif payload.eventType == "business.alert.created":
        data = payload.data
        ANOMALY_EVENTS.append(
            {
                "event_id": payload.eventId,
                "event_type": "SECURITY_ALERT",
                "timestamp": payload.occurredAt,
                "details": data,
            }
        )
    elif payload.eventType == "camera.motion.detected":
        data = payload.data
        ANOMALY_EVENTS.append(
            {
                "event_id": payload.eventId,
                "event_type": "MOTION_DETECTED",
                "timestamp": payload.occurredAt,
                "details": data,
            }
        )

    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
            "eventId": payload.eventId,
            "status": "PROCESSED",
            "message": f"Successfully ingested {payload.eventType} event",
        },
    )
