# Submission Checklist – Lab 04 (Analytics Service)

Nộp các minh chứng sau:

- [x] `Dockerfile` (Multi-stage build, Non-root `appuser`, `HEALTHCHECK` `/health`)
- [x] `.dockerignore` (Loại bỏ `.git`, `node_modules`, `reports`, `__pycache__`, `.venv`)
- [x] `.env.example` (Cấu hình `SERVICE_NAME`, `SERVICE_VERSION`, `APP_HOST`, `APP_PORT`, `AUTH_TOKEN`)
- [x] `RUN_LOCAL.md` (Hướng dẫn chạy lại 3-5 bước cho người chấm)
- [x] Contract OpenAPI đã dùng (`contracts/analytics-service.openapi.yaml`)
- [x] Postman Collection đã chạy trên container (`postman/collections/FIT4110_lab04_analytics_docker.postman_collection.json`)
- [x] Postman Environment local/docker (`postman/environments/FIT4110_lab04_local.postman_environment.json`)
- [x] Newman report XML/HTML (`reports/newman-lab04-local.xml`, `reports/newman-lab04-local.html`)
- [x] Log build Docker (`docs/docker-evidence.md`)
- [x] Log chạy container & non-root user (`docs/docker-evidence.md`)
- [x] Log `GET /health` trả về 200 OK (`docs/docker-evidence.md`)
- [x] Tên image tag đã push / tạo (`ghcr.io/quynhdinhtrong/team-analytics:v0.1.0-team-analytics`)
