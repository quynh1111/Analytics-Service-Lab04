# TỔNG QUAN HỆ THỐNG KẾT NỐI VÀ HỢP ĐỒNG DỊCH VỤ
## Smart Campus Operations Platform – Analytics Service Ecosystem

Thư mục `contracts/` chứa đầy đủ các hợp đồng dịch vụ (OpenAPI REST Contracts & Queue-Async Event Contracts) cho toàn bộ hệ sinh thái dịch vụ của hệ thống **Smart Campus**.

---

## 1. Sơ đồ ma trận kết nối dịch vụ (Service Topology)

```text
                                    ┌────────────────────────┐
                                    │     Dashboard App      │
                                    │      (API Client)      │
                                    └───────────▲────────────┘
                                                │
                                                │ REST API (GET /daily-summary, /metrics/...)
                                                │ Provider: Analytics Service
                                                │ Contract: analytics-service.openapi.yaml
                                                │
                                    ┌───────────┴────────────┐
                                    │   ANALYTICS SERVICE    │
                                    │      (Product A)       │
                                    └───────────▲────────────┘
                                                │
                 Queue-Async Ingestion (Event Envelope: eventId, eventType, data)
   ┌───────────────────────┬────────────────────┴──────────────────┬──────────────────────┐
   │                       │                                       │                      │
┌──┴───────────────┐ ┌─────┴─────────────────┐ ┌───────────────────┴──┐ ┌────────────────┴──┐
│   IoT Ingestion   │ │   Camera / AI Vision  │ │    Core Business    │ │    Access Gate     │
│     (Pair 06)    │ │       (Pair 07)       │ │      (Pair 08)      │ │     (Pair 09)      │
│   (Producer)     │ │      (Producer)       │ │     (Producer)      │ │     (Producer)     │
└──────────────────┘ └───────────────────────┘ └─────────────────────┘ └────────────────────┘
```

---

## 2. Danh mục đầy đủ các Hợp đồng REST API (`contracts/*.openapi.yaml`)

| File Hợp đồng | Dịch vụ | Vai trò | Mục đích |
|---|---|---|---|
| **[`analytics-service.openapi.yaml`](file:///d:/daihoc/DichVuKetNoiVaCongNgheNenTang/FIT4110_lab04_docker_packaging/contracts/analytics-service.openapi.yaml)** | **Analytics Service** (Chính) | **Provider** | Cung cấp REST API cho Dashboard (`/daily-summary`, `/metrics/temperature`, `/metrics/access-stats`, `/metrics/events`, `/events/ingest`). |
| **[`iot-ingestion.openapi.yaml`](file:///d:/daihoc/DichVuKetNoiVaCongNgheNenTang/FIT4110_lab04_docker_packaging/contracts/iot-ingestion.openapi.yaml)** | **IoT Ingestion Service** | **Provider (Pair 06)** | Nhận dữ liệu đo lường cảm biến nhiệt độ, độ ẩm (`/readings`, `/readings/latest`). |
| **[`ai-vision.openapi.yaml`](file:///d:/daihoc/DichVuKetNoiVaCongNgheNenTang/FIT4110_lab04_docker_packaging/contracts/ai-vision.openapi.yaml)** | **AI Vision Service** | **Provider (Pair 07)** | Nhận diện đối tượng (người/xe) trong ảnh từ camera (`/detect`). |
| **[`core-business.openapi.yaml`](file:///d:/daihoc/DichVuKetNoiVaCongNgheNenTang/FIT4110_lab04_docker_packaging/contracts/core-business.openapi.yaml)** | **Core Business Service** | **Provider (Pair 08)** | Đánh giá chính sách an ninh, sức chứa (`/policies/evaluate`). |
| **[`access-gate.openapi.yaml`](file:///d:/daihoc/DichVuKetNoiVaCongNgheNenTang/FIT4110_lab04_docker_packaging/contracts/access-gate.openapi.yaml)** | **Access Gate Service** | **Provider (Pair 09)** | Xác thực quẹt thẻ ra vào cổng (`/gates/verify`). |

---

## 3. Danh mục 4 Hợp đồng Bất đồng bộ (Queue-Async Event Contracts)

Các sự kiện được đẩy qua Message Queue / Event Bus tới **Analytics Service** để tổng hợp báo cáo:

| Pair | Producer | Topic/Queue | Danh sách Events | Mục đích tổng hợp sang Analytics |
|---|---|---|---|---|
| **Pair 06** | IoT Ingestion | `iot.telemetry` | `telemetry.ingested`, `device.status.changed` | Tính nhiệt độ trung bình `TemperatureMetric`, theo dõi trạng thái thiết bị online/offline. |
| **Pair 07** | Camera Stream / AI Vision | `camera.events` | `camera.motion.detected`, `camera.frame.analyzed`, `camera.status.changed` | Ghi nhận chuyển động và tạo sự kiện bất thường `AnomalyEvent`. |
| **Pair 08** | Core Business | `business.events` | `business.alert.created`, `business.policy.decision.created`, `business.alert.resolved` | Tổng hợp số lượng cảnh báo `total_alerts` và vòng đời xử lý cảnh báo. |
| **Pair 09** | Access Gate | `access.events` | `access.log.created`, `access.denied` | Thống kê tổng lượt ra/vào `total_access` và mật độ theo giờ `AccessStatMetric`. |

---

## 4. Kiểm tra hợp lệ bằng Spectral Lint

Kiểm tra toàn bộ 5 hợp đồng OpenAPI đồng thời:
```bash
npm run lint:openapi
```
> **Kết quả:** `No results with a severity of 'error' found!` (0 lỗi).
