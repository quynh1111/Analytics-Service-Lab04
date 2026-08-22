# Docker Readiness Checklist – Analytics Service

## Dockerfile

- [x] Có base image hợp lý (`python:3.11-slim`).
- [x] Có `WORKDIR` (`/app`).
- [x] Có copy dependency trước source để tận dụng cache (`requirements.txt` -> pip install -> `COPY src/`).
- [x] Có `EXPOSE 8000`.
- [x] Có `CMD` (`uvicorn analytics_app.main:app`).
- [x] Có `HEALTHCHECK` (kiểm tra `GET /health` mỗi 30s).
- [x] Có user non-root (`appuser:appgroup`).
- [x] Không chứa secret thật (quản lý qua `.env.example`).

## Runtime

- [x] Container chạy được (`fit4110-analytics-lab04`).
- [x] Port map đúng (`-p 8000:8000`).
- [x] `/health` trả `200 OK` (JSON: `{"status":"ok","service":"analytics-service","version":"1.0.0"}`).
- [x] Log khởi động rõ ràng.
- [x] Cấu hình qua ENV (`APP_HOST`, `APP_PORT`, `SERVICE_NAME`, `AUTH_TOKEN`).

## Testing

- [x] Chạy lại Postman Collection từ Lab 03 trên Container (`FIT4110_lab04_analytics_docker.postman_collection.json`).
- [x] Newman report sinh ra trong `reports/` (`newman-lab04-local.xml`, `newman-lab04-local.html`).
- [x] Functional test pass (200/201 OK cho Health, Ingest, Summary, Metrics).
- [x] Auth test pass trên local/container (401 cho missing/invalid token).
- [x] Negative test pass trên local/container (400/422 kèm ProblemDetails RFC 7807/9457).
- [x] Boundary test pass (Limit 100 accepted, limit 101 rejected, idempotent ingestion).

## Evidence

- [x] Có log `docker build` (trong `docs/docker-evidence.md`).
- [x] Có log `docker run` và `docker ps` `(healthy)` (trong `docs/docker-evidence.md`).
- [x] Có log `curl /health` và non-root `whoami` (trong `docs/docker-evidence.md`).
- [x] Có Newman HTML/XML report (27/27 assertions PASS 100%).
- [x] Có tag image đúng quy ước (`ghcr.io/quynhdinhtrong/team-analytics:v0.1.0-team-analytics`).
