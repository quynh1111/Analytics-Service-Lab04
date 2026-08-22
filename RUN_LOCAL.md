# RUN_LOCAL.md – Hướng dẫn chạy Lab 04 (Analytics Service)

Tài liệu này hướng dẫn chạy service **Analytics Service** (`team-analytics`) trong Docker container và kiểm thử tự động với Newman.

---

## 1. Cài đặt dependencies kiểm thử (Newman / Spectral / Prism)

```bash
npm install
```

Kiểm tra OpenAPI contract:
```bash
npm run lint:openapi
```

---

## 2. Build Docker Image

```bash
docker build -t fit4110/analytics-service:lab04 .
```

Gán tag image theo quy chuẩn bài lab:
```bash
docker tag fit4110/analytics-service:lab04 ghcr.io/quynhdinhtrong/team-analytics:v0.1.0-team-analytics
```

---

## 3. Khởi chạy Docker Container

```bash
docker run -d --name fit4110-analytics-lab04 -p 8000:8000 --env-file .env.example fit4110/analytics-service:lab04
```

Kiểm tra trạng thái container và healthcheck:
```bash
docker ps
curl http://localhost:8000/health
```

Kết quả mong đợi:
```json
{
  "status": "ok",
  "service": "analytics-service",
  "version": "1.0.0"
}
```

Kiểm tra non-root user bên trong container:
```bash
docker exec fit4110-analytics-lab04 whoami
# Kết quả: appuser
```

---

## 4. Chạy bộ kiểm thử Newman trên Container

```bash
npm run test:local
```

Báo cáo kiểm thử tự động được xuất tại:
- Báo cáo JUnit XML: `reports/newman-lab04-local.xml`
- Báo cáo chi tiết HTML: `reports/newman-lab04-local.html`

---

## 5. Dừng Container

```bash
docker stop fit4110-analytics-lab04
docker rm fit4110-analytics-lab04
```

---

## 6. Lệnh nhanh (Quick Commands)

Nếu sử dụng `make`:
```bash
make build          # Build Docker image
make run-detached   # Chạy container nền
make health         # Kiểm tra /health
make test-docker    # Chạy Newman tests trên container
make stop           # Dừng container
```
