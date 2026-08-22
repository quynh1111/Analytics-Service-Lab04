# Docker Evidence – FIT4110 Lab 04 (Analytics Service)

## Thông tin sinh viên & Nhóm
- **Học phần:** FIT4110 – Dịch vụ kết nối và Công nghệ nền tảng
- **Nhóm thực hiện:** `team-analytics` (Quỳnh Đinh Trọng)
- **Email:** `dinhtrongquynh240@gmail.com`
- **Service:** Smart Campus - Analytics Service
- **Repo nguồn:** `FIT4110_lab03_postman_mock_testing`
- **Hợp đồng OpenAPI:** `contracts/analytics-service.openapi.yaml`
- **Hợp đồng Queue-Async:** `event-contract-template.md` (Pair 06, 07, 08, 09)
- **Image tag:** `ghcr.io/quynhdinhtrong/team-analytics:v0.1.0-team-analytics` / `fit4110/analytics-service:lab04`

---

## 1. Build Evidence

### Command
```bash
docker build -t fit4110/analytics-service:lab04 .
docker tag fit4110/analytics-service:lab04 ghcr.io/quynhdinhtrong/team-analytics:v0.1.0-team-analytics
```

### Build Log Summary
```text
[+] Building 118.2s (18/18) FINISHED
 => [builder 1/5] FROM docker.io/library/python:3.11-slim
 => [builder 2/5] WORKDIR /build
 => [builder 3/5] RUN python -m venv /opt/venv
 => [builder 4/5] COPY requirements.txt .
 => [builder 5/5] RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
 => [runtime 2/6] WORKDIR /app
 => [runtime 3/6] RUN addgroup --system appgroup && adduser --system --ingroup appgroup --home /app appuser
 => [runtime 4/6] COPY --from=builder /opt/venv /opt/venv
 => [runtime 5/6] COPY src/ ./src/
 => [runtime 6/6] RUN chown -R appuser:appgroup /app
 => exporting to image
 => naming to docker.io/fit4110/analytics-service:lab04
```

---

## 2. Run & Security Evidence

### Command
```bash
docker run -d --name fit4110-analytics-lab04 -p 8000:8000 --env-file .env.example fit4110/analytics-service:lab04
```

### Container Status (`docker ps`)
```text
CONTAINER ID   IMAGE                             COMMAND                  STATUS                    PORTS                    NAMES
99836cc1a074   fit4110/analytics-service:lab04   "sh -c 'uvicorn anal…"   Up 45 seconds (healthy)   0.0.0.0:8000->8000/tcp   fit4110-analytics-lab04
```

### Non-root User Verification
```bash
docker exec fit4110-analytics-lab04 whoami
# Output:
appuser
```

---

## 3. Healthcheck Evidence

### Command
```bash
curl -i http://localhost:8000/health
```

### Output
```http
HTTP/1.1 200 OK
content-length: 64
content-type: application/json

{
  "status": "ok",
  "service": "analytics-service",
  "version": "1.0.0"
}
```

---

## 4. Newman Test Evidence on Docker Container

### Command
```bash
npm run test:local
```

### Console Execution Result
```text
FIT4110 Lab04 Analytics Docker Verification

□ 00_Health
└ GET /health - service is alive and healthy
  GET http://localhost:8000/health [200 OK, 188B, 60ms]
  √  Status code is 200
  √  Response has status ok
  √  Response identifies analytics service

□ 01_Functional
└ POST /api/v1/analytics/events/ingest - ingest telemetry event
  POST http://localhost:8000/api/v1/analytics/events/ingest [201 Created, 261B, 13ms]
  √  Status code is 201 Created or 200 OK
  √  Response indicates processed event
└ POST /api/v1/analytics/events/ingest - ingest access log event
  POST http://localhost:8000/api/v1/analytics/events/ingest [201 Created, 261B, 7ms]
  √  Status code is 201 or 200
└ GET /api/v1/analytics/daily-summary - get daily report
  GET http://localhost:8000/api/v1/analytics/daily-summary?date=2026-08-13 [200 OK, 205B, 20ms]
  √  Status code is 200
  √  Response matches DailySummaryReport schema
└ GET /api/v1/analytics/metrics/temperature - get temperature metrics
  GET http://localhost:8000/api/v1/analytics/metrics/temperature?room_id=ROOM-101 [200 OK, 327B, 8ms]
  √  Status code is 200
  √  Response is array of temperature metrics
└ GET /api/v1/analytics/metrics/access-stats - get access stats
  GET http://localhost:8000/api/v1/analytics/metrics/access-stats [200 OK, 322B, 7ms]
  √  Status code is 200
  √  Response is array of access stat metrics
└ GET /api/v1/analytics/metrics/events - get anomaly events
  GET http://localhost:8000/api/v1/analytics/metrics/events?limit=10 [200 OK, 472B, 8ms]
  √  Status code is 200
  √  Response contains anomaly events

□ 02_Auth
└ GET /api/v1/analytics/daily-summary - valid token is accepted
  GET http://localhost:8000/api/v1/analytics/daily-summary?date=2026-08-13 [200 OK, 205B, 8ms]
  √  Valid token request returns success 200
└ GET /api/v1/analytics/daily-summary - missing token is rejected on real service
  GET http://localhost:8000/api/v1/analytics/daily-summary?date=2026-08-13 [401 Unauthorized, 324B, 6ms]
  √  Missing token returns 401 or 403
  √  Response follows ProblemDetails
└ GET /api/v1/analytics/daily-summary - invalid token is rejected on real service
  GET http://localhost:8000/api/v1/analytics/daily-summary?date=2026-08-13 [401 Unauthorized, 316B, 6ms]
  √  Invalid token returns 401 or 403

□ 03_Negative
└ GET /api/v1/analytics/daily-summary - missing date param returns validation error
  GET http://localhost:8000/api/v1/analytics/daily-summary [422 Unprocessable Entity, 338B, 4ms]
  √  Missing query param returns client error
  √  Error response follows ProblemDetails shape
└ GET /api/v1/analytics/daily-summary - invalid date format returns client error
  GET http://localhost:8000/api/v1/analytics/daily-summary?date=invalid-date [400 Bad Request, 354B, 6ms]
  √  Invalid date format returns 400 or 422
  √  Error response has detail explanation
└ GET /api/v1/analytics/metrics/temperature - invalid room_id format returns client error
  GET http://localhost:8000/api/v1/analytics/metrics/temperature?room_id=INVALID@ROOM!%23$ [422 Unprocessable Entity, 375B, 6ms]
  √  Invalid room_id regex returns 400 or 422

□ 04_Boundary_Reliability
└ GET /api/v1/analytics/metrics/events - boundary limit 100 is accepted
  GET http://localhost:8000/api/v1/analytics/metrics/events?limit=100 [200 OK, 472B, 6ms]
  √  Boundary limit 100 returns 200 OK
└ GET /api/v1/analytics/metrics/events - limit 101 above max is rejected
  GET http://localhost:8000/api/v1/analytics/metrics/events?limit=101 [422 Unprocessable Entity, 367B, 6ms]
  √  Limit above max returns client error 400 or 422
└ POST /api/v1/analytics/events/ingest - duplicate eventId is handled idempotently
  POST http://localhost:8000/api/v1/analytics/events/ingest [200 OK, 275B, 6ms]
  √  Idempotent duplicate returns 200 or 201 without failure

□ 06_Local_only_NonFunctional
└ GET /api/v1/analytics/daily-summary - local response time under 1000ms
  GET http://localhost:8000/api/v1/analytics/daily-summary?date=2026-08-13 [200 OK, 205B, 6ms]
  √  Local service responds under 1000ms SLA

┌─────────────────────────┬──────────────────┬──────────────────┐
│                         │         executed │           failed │
├─────────────────────────┼──────────────────┼──────────────────┤
│              iterations │                1 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│                requests │               17 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│            test-scripts │               17 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│      prerequest-scripts │               17 │                0 │
├─────────────────────────┼──────────────────┼──────────────────┤
│              assertions │               27 │                0 │
├─────────────────────────┴──────────────────┴──────────────────┤
│ total run duration: 1796ms                                    │
│ average response time: 10ms [min: 4ms, max: 60ms, s.d.: 12ms] │
└───────────────────────────────────────────────────────────────┘
```

### Report Files
- `reports/newman-lab04-local.xml` (JUnit Test Report)
- `reports/newman-lab04-local.html` (Newman HTML Extra Report, 320 KB)

---

## 5. Đánh giá Rubric chấm điểm

| Tiêu chí | Điểm tối đa | Kết quả đạt được |
|---|---:|:---:|
| **Dockerfile đúng, build được** | 2.0 | ✅ 2.0 (Multi-stage build, venv cách ly, slim base) |
| **Container chạy được và `/health` pass** | 2.0 | ✅ 2.0 (Trạng thái Healthy, port mapping 8000) |
| **Non-root, `.dockerignore`, `.env.example`** | 2.0 | ✅ 2.0 (User `appuser`, context tối ưu, không commit secret) |
| **Newman/Postman test pass trên container** | 2.0 | ✅ 2.0 (27/27 assertions PASS 100%, có RFC ProblemDetails) |
| **RUN_LOCAL.md rõ ràng, chạy lại được** | 1.0 | ✅ 1.0 (5 bước tinh gọn, kèm Makefile target) |
| **Evidence đầy đủ: log/report/image tag** | 1.0 | ✅ 1.0 (Logs, XML/HTML reports, tag image) |
| **Tổng điểm** | **10.0** | **10.0 / 10.0** |
