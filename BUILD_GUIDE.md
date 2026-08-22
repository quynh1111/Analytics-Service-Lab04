# HƯỚNG DẪN BUILD VÀ VẬN HÀNH DOCKER (BUILD GUIDE)
## Học phần: FIT4110 – Dịch vụ kết nối và Công nghệ nền tảng (Lab 04)
### Dự án: Smart Campus – Analytics Service (`team-analytics`)

---

## 1. Yêu cầu môi trường (Prerequisites)

Trước khi tiến hành build và chạy dự án, hãy đảm bảo máy tính đã cài đặt các công cụ sau:

- **Docker Desktop** (hoặc Docker Engine): Đang ở trạng thái `Running`.
- **Node.js**: Phiên bản `v18.x` hoặc `v20.x` LTS trở lên (đi kèm `npm`).
- **Python**: Phiên bản `3.11+` (nếu muốn chạy thử local không dùng container).
- **Git**: Dùng để quản lý mã nguồn.

Kiểm tra nhanh phiên bản các công cụ:
```bash
docker --version
node --version
npm --version
```

---

## 2. Cấu trúc thư mục dự án

```text
FIT4110_lab04_docker_packaging/
├── Dockerfile                  # Cấu hình build Docker image (Multi-stage + Non-root)
├── .dockerignore               # Loại trừ file rác giúp build nhanh và nhẹ image
├── .env.example                # File mẫu biến môi trường (Environment variables)
├── Makefile                    # Các lệnh build/run/test nhanh
├── package.json                # Dependencies cho Newman, Spectral, Prism
├── requirements.txt            # Python dependencies (FastAPI, Uvicorn, Pydantic)
├── contracts/
│   └── analytics-service.openapi.yaml   # Hợp đồng OpenAPI 3.1.0 chuẩn hóa
├── src/
│   └── analytics_app/
│       ├── __init__.py
│       └── main.py             # Mã nguồn FastAPI service xử lý REST API & Events
├── postman/
│   ├── collections/
│   │   └── FIT4110_lab04_analytics_docker.postman_collection.json # Test suite 27 assertions
│   └── environments/
│       ├── FIT4110_lab04_local.postman_environment.json           # Môi trường chạy container
│       └── FIT4110_lab04_mock.postman_environment.json            # Môi trường chạy Prism mock
├── reports/                    # Chứa báo cáo Newman JUnit XML & HTML Extra
├── docs/
│   └── docker-evidence.md      # Tài liệu minh chứng kết quả build/test/healthcheck
├── BUILD_GUIDE.md              # File hướng dẫn chi tiết này
└── RUN_LOCAL.md                # Hướng dẫn chạy nhanh 3-5 bước
```

---

## 3. Quy trình thực hiện chi tiết từ A đến Z

### Bước 1: Cài đặt dependencies kiểm thử (Node.js)
Mở terminal tại thư mục gốc `FIT4110_lab04_docker_packaging`:

```bash
npm install
```

### Bước 2: Kiểm tra OpenAPI Contract bằng Spectral Lint
Đảm bảo hợp đồng API không có lỗi cú pháp hoặc vi phạm quy tắc OAS:

```bash
npm run lint:openapi
```
> Kết quả mong đợi: `No results with a severity of 'error' found!`

---

### Bước 3: Build Docker Image

Thực hiện lệnh build Docker image bằng Dockerfile đa tầng (Multi-stage build):

```bash
docker build -t fit4110/analytics-service:lab04 .
```

**Cơ chế tối ưu của Dockerfile:**
- **Stage 1 (Builder)**: Cài đặt thư viện Python vào virtual environment `/opt/venv`.
- **Stage 2 (Runtime)**: Chỉ copy `/opt/venv` và mã nguồn vào image chạy thực tế.
- **Bảo mật**: Tạo user `appuser` (non-root) để chạy ứng dụng, không chạy bằng quyền `root`.
- **Healthcheck**: Tự động kiểm tra trạng thái sống của app qua endpoint `/health` mỗi 30s.

---

### Bước 4: Gán Tag cho Image (Tagging Convention)

Gán tag chuẩn để định danh team và version:

```bash
docker tag fit4110/analytics-service:lab04 ghcr.io/quynhdinhtrong/team-analytics:v0.1.0-team-analytics
```

Kiểm tra danh sách image trên máy:
```bash
docker images | grep analytics
```

---

### Bước 5: Khởi chạy Docker Container

Khởi chạy container ở chế độ chạy nền (`-d`), mở port `8000` và nạp biến môi trường từ `.env.example`:

```bash
docker run -d \
  --name fit4110-analytics-lab04 \
  -p 8000:8000 \
  --env-file .env.example \
  fit4110/analytics-service:lab04
```

---

### Bước 6: Xác thực Container & Kiểm tra Healthcheck

#### 1. Kiểm tra container đang chạy:
```bash
docker ps --filter "name=fit4110-analytics-lab04"
```
> Trạng thái phải hiển thị: `Up ... (healthy)`

#### 2. Kiểm tra non-root user bên trong container:
```bash
docker exec fit4110-analytics-lab04 whoami
```
> Kết quả trả về: `appuser`

#### 3. Kiểm tra endpoint `/health`:
```bash
curl -i http://localhost:8000/health
```
> Kết quả mong đợi:
> ```json
> {
>   "status": "ok",
>   "service": "analytics-service",
>   "version": "1.0.0"
> }
> ```

---

### Bước 7: Chạy kiểm thử tự động bằng Newman trên Container

Chạy toàn bộ 27 assertions kiểm thử (Functional, Auth, Negative, Boundary, RFC ProblemDetails, SLA Latency):

```bash
npm run test:local
```

Kết quả kiểm thử:
- **Assertions**: `27 / 27 PASS (0 failed)`.
- **Báo cáo JUnit XML**: được tạo tại `reports/newman-lab04-local.xml`.
- **Báo cáo giao diện HTML**: được tạo tại `reports/newman-lab04-local.html`.

> **Mẹo:** Bạn có thể mở trực tiếp file `reports/newman-lab04-local.html` bằng trình duyệt (Chrome/Edge) để xem dashboard kết quả kiểm thử trực quan.

---

### Bước 8: Dừng và dọn dẹp Container

Khi hoàn thành phiên làm việc hoặc muốn dừng container:

```bash
docker stop fit4110-analytics-lab04
docker rm fit4110-analytics-lab04
```

---

## 4. Bảng tổng hợp lệnh nhanh với Makefile

Nếu hệ thống hỗ trợ lệnh `make` (Linux, macOS, hoặc Windows WSL / Git Bash):

| Thao tác | Lệnh Makefile | Lệnh tương đương |
|---|---|---|
| **Cài đặt thư viện** | `make install` | `npm install` |
| **Lint OpenAPI** | `make lint` | `npm run lint:openapi` |
| **Build Docker Image** | `make build` | `docker build -t fit4110/analytics-service:lab04 .` |
| **Chạy Container nền** | `make run-detached`| `docker run -d --name ... -p 8000:8000 ...` |
| **Kiểm tra Health** | `make health` | `curl http://localhost:8000/health` |
| **Chạy Newman Tests** | `make test-docker` | `npm run test:local` |
| **Dừng Container** | `make stop` | `docker stop fit4110-analytics-lab04` |

---

## 5. Xử lý sự cố thường gặp (Troubleshooting)

### 1. Lỗi cổng 8000 đã bị chiếm dụng (`port is already allocated`)
- **Nguyên nhân:** Container cũ vẫn đang chạy hoặc tiến trình khác đang chiếm cổng `8000`.
- **Cách xử lý:**
  ```bash
  docker rm -f fit4110-analytics-lab04
  ```

### 2. Docker daemon chưa khởi động (`Cannot connect to the Docker daemon`)
- **Cách xử lý:** Mở ứng dụng **Docker Desktop** trên máy và đợi thanh trạng thái chuyển sang màu xanh lá cây (`Docker Engine is running`).

### 3. Newman báo lỗi kết nối `ECONNREFUSED 127.0.0.1:8000`
- **Nguyên nhân:** Container chưa khởi động xong hoặc đã bị stop.
- **Cách xử lý:**
  Kiểm tra log của container để xem lỗi:
  ```bash
  docker logs fit4110-analytics-lab04
  ```
