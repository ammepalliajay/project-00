# Distributed Media Processing Microservice

An enterprise-grade, event-driven distributed media processing backend service designed for asynchronous image and video transformations at scale. Built with **FastAPI**, **RabbitMQ**, **Celery**, **Redis**, **Pillow**, and **FFmpeg**.

---

## 1. System Architecture

```text
                               +-----------------------------+
                               |     Client / API Consumer   |
                               +-----------------------------+
                                     |                ^
                1. Upload / Job POST |                | 4. Poll Status / Download
                                     v                |
                        +-----------------------------------+
                        |       FastAPI Web Service         |
                        | (Validation, Auth, Job Producer)  |
                        +-----------------------------------+
                               |                      ^
                      2. Queue |                      | 3. Read/Write
                          Task |                      |    Job State
                               v                      v
                +---------------------+       +--------------------+
                |  RabbitMQ (Broker)  |       |   Redis (State)    |
                |  Exchange & Queues  |       |  Job Status Cache  |
                +---------------------+       +--------------------+
                               |                      ^
                      Consume  |                      |
                        Events |                      | Update Status /
                               v                      | Processing Time
                        +-----------------------------------+
                        |      Celery Worker Cluster        |
                        | (Heavy Asynchronous Media Engine) |
                        +-----------------------------------+
                               |                      |
                               v                      v
                      +------------------+   +------------------+
                      |  Pillow Engine   |   |   FFmpeg Engine  |
                      | (Resize, Crop,   |   | (Thumbnail, CRF  |
                      |  Convert, Water) |   |  Compress, Trans)|
                      +------------------+   +------------------+
                                        \     /
                                         v   v
                              +-------------------------+
                              |   Storage Subsystem     |
                              |  (Local Shared Disk /   |
                              |    AWS S3 via Boto3)    |
                              +-------------------------+
```

### Key Architectural Principles
- **Strict Decoupling**: The FastAPI API process never performs heavy CPU-bound media transformations. Uploads are quickly validated, assigned UUIDs, stored, and enqueued.
- **Worker Isolation**: Celery workers run independently with fine-grained concurrency control (`-c 2` default, prefetch multiplier 1) and task timeouts (`task_acks_late=True`).
- **Resilient State Persistence**: Job states (`PENDING` -> `PROCESSING` -> `COMPLETED` / `FAILED`) are stored in Redis with structured error telemetry and processing durations.
- **Pluggable Storage Backend**: Zero-code switching between local shared disk and AWS S3 via standard environment configuration.

---

## 2. Supported Media Operations

### Image Operations (Pillow Engine)
| Operation | Key Parameters | Description |
| :--- | :--- | :--- |
| `resize_image` | `width`, `height`, `preserve_aspect_ratio`, `quality` | High-quality Lanczos downsampling / upsampling |
| `crop_image` | `left`, `top`, `right`, `bottom` | Coordinate bounding box extraction with boundary clamping |
| `compress_image` | `quality` (1-100), `optimize` | Web-optimized compression preserving color gamut |
| `convert_image` | `format` (`"JPEG"`, `"PNG"`, `"WEBP"`), `quality` | Alpha-aware format conversion with RGB flattening |
| `watermark_image` | `text`, `position`, `opacity` | Alpha-blended dynamic text watermarking |

### Video Operations (FFmpeg Engine)
| Operation | Key Parameters | Description |
| :--- | :--- | :--- |
| `video_thumbnail` | `timestamp_sec`, `width` | Accurate frame seek (`-ss`) and JPEG extraction |
| `video_compress` | `crf` (18-36), `preset` (`"fast"`, `"ultrafast"`) | H.264 video + AAC audio compression |
| `video_transcode` | `resolution` (`"1280x720"`), `fps` (24, 30, 60) | Cross-container container and codec re-encoding |

---

## 3. Docker Desktop Setup & Local Verification (Windows & Cross-Platform)

Follow these exact step-by-step instructions to run and verify the distributed stack on **Windows 10/11 with Docker Desktop** (or macOS / Linux):

### Step 1: Install Docker Desktop
- Download and install [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/).
- Ensure the **WSL 2 backend** is enabled in Docker Desktop settings (`Settings > General > Use the WSL 2 based engine`).
- Start Docker Desktop and verify it is running in your Windows taskbar.

### Step 2: Clone Repository
Open PowerShell or Windows Terminal:
```powershell
git clone <repository_url>
cd <repository_root>/media-processing-service
```

### Step 3: Copy `.env.example` to `.env`
In PowerShell:
```powershell
Copy-Item .env.example .env
# Or in Command Prompt:
# copy .env.example .env
```

### Step 4: Configure Optional AWS Credentials
If using AWS S3 for storage instead of local disk, open `.env` and set:
```env
STORAGE_BACKEND=s3
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_REGION=us-east-1
AWS_S3_BUCKET=your_bucket_name
```
*Note: For standard local testing, leave `STORAGE_BACKEND=local` (default). No AWS account is needed.*

### Step 5: Build the Docker Images
Compile the container images containing Python 3.10, FFmpeg 4.4+, Pillow, and all dependencies:
```powershell
docker compose build
```

### Step 6: Start the Distributed Stack
Launch all 4 containers (`rabbitmq`, `redis`, `api`, `worker`) in detached mode:
```powershell
docker compose up -d
```

### Step 7: Check Container Status
Verify that all 4 containers are running and reported healthy:
```powershell
docker compose ps
```
You should see:
- `media-rabbitmq` (healthy, ports 5672, 15672)
- `media-redis` (healthy, port 6379)
- `media-api` (healthy, port 8000)
- `media-worker` (running, Celery worker cluster)

### Step 8: Run the Automated Verification Script
Run the comprehensive verification suite to test all distributed components:
```powershell
# Executing inside the API container (zero host Python setup required):
docker compose exec api python scripts/verify_production_stack.py

# Or run from host machine if Python 3 and requests are installed:
python scripts/verify_production_stack.py --url http://localhost:8000
```
This script checks:
- FastAPI reachability
- Redis PING connectivity
- RabbitMQ socket connectivity
- Celery worker execution & task acknowledgment
- FFmpeg binary execution inside the worker container
- Storage read/write permissions
- Complete asynchronous image processing job with status transitions (`PENDING` -> `PROCESSING` -> `COMPLETED`)
- Complete asynchronous video processing job with FFmpeg thumbnail extraction
- Output artifact existence & download verification

### Step 9: Open FastAPI Documentation & Dashboards
Open your web browser to:
- **FastAPI Interactive Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **FastAPI ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **System Health Endpoint**: [http://localhost:8000/health](http://localhost:8000/health)
- **Prometheus Metrics**: [http://localhost:8000/metrics](http://localhost:8000/metrics)
- **RabbitMQ Management Dashboard**: [http://localhost:15672](http://localhost:15672) (Username: `guest`, Password: `guest`)

### Step 10: Run an Image Processing Job (via PowerShell)
Generate deterministic test images and upload one:
```powershell
# Generate test media fixtures
python scripts/generate_test_media.py --output test_media

# Upload sample image
curl -X POST http://localhost:8000/uploads -F "file=@test_media/sample.jpg;type=image/jpeg"
```
Submit an image resize job using the returned `storage_path`:
```powershell
curl -X POST http://localhost:8000/jobs `
  -H "Content-Type: application/json" `
  -d '{\"operation\":\"resize_image\",\"input_path\":\"uploads/sample.jpg\",\"parameters\":{\"width\":320,\"height\":240,\"quality\":85}}'
```
Poll status until `COMPLETED`:
```powershell
curl http://localhost:8000/jobs/<job_id>
```
Download the resulting image:
```powershell
curl http://localhost:8000/jobs/<job_id>/download -o resized.jpg
```

### Step 11: Run a Video Processing Job (via PowerShell)
Upload sample MP4 and submit a thumbnail extraction job:
```powershell
# Upload sample video
curl -X POST http://localhost:8000/uploads -F "file=@test_media/sample.mp4;type=video/mp4"

# Submit video thumbnail job
curl -X POST http://localhost:8000/jobs `
  -H "Content-Type: application/json" `
  -d '{\"operation\":\"video_thumbnail\",\"input_path\":\"uploads/sample.mp4\",\"parameters\":{\"timestamp_sec\":1.0,\"width\":480}}'

# Poll and download thumbnail
curl http://localhost:8000/jobs/<job_id>
curl http://localhost:8000/jobs/<job_id>/download -o thumb.jpg
```

### Step 12: Stop the Distributed Stack
When finished, cleanly shut down the containers:
```powershell
docker compose down

# To also remove persistent volumes (clears Redis data, RabbitMQ queues, and stored media):
docker compose down -v
```

---

## 4. Troubleshooting Commands (Windows / Docker)

| Issue | Diagnostic / Recovery Command |
| :--- | :--- |
| **Inspect Live Logs** | `docker compose logs -f` (or specific service: `docker compose logs -f worker`) |
| **Restart Celery Worker** | `docker compose restart worker` |
| **Check Port Conflicts (8000, 6379, 5672)** | `Get-NetTCPConnection -LocalPort 8000, 6379, 5672` in PowerShell |
| **Inspect Shared Volume Contents** | `docker compose exec api ls -la /app/storage/uploads` |
| **Inspect RabbitMQ Queue Status** | `docker compose exec rabbitmq rabbitmqctl list_queues` |
| **Inspect Redis Keys** | `docker compose exec redis redis-cli keys "*"` |
| **Check FFmpeg Inside Worker** | `docker compose exec worker ffmpeg -version` |
| **Rebuild Containers from Scratch** | `docker compose down -v && docker compose build --no-cache && docker compose up -d` |

---

## 4. Manual Setup for Local Development

### Prerequisites
- Python 3.10+
- FFmpeg installed and accessible in your system `PATH`
  - **Ubuntu / Debian**: `sudo apt update && sudo apt install -y ffmpeg`
  - **macOS**: `brew install ffmpeg`
  - **Windows**: `winget install Gyan.FFmpeg` or download from [gyan.dev/ffmpeg](https://www.gyan.dev/ffmpeg/builds/)
- Redis & RabbitMQ instances running locally or via Docker:
  ```bash
  docker run -d -p 6379:6379 --name local-redis redis:7-alpine
  docker run -d -p 5672:5672 -p 15672:15672 --name local-rabbitmq rabbitmq:3.12-management-alpine
  ```

### Installation
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate   # Windows: .\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

### Running the Services
In **Terminal 1** (FastAPI Web Server):
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

In **Terminal 2** (Celery Worker):
```bash
celery -A app.workers.celery_app.celery_app worker -l info -c 2 -Q media_processing
```

---

## 5. API Reference & Curl Examples

### 1. Health Check
```bash
curl -X GET http://localhost:8000/health
```
**Response (200 OK)**:
```json
{
  "status": "healthy",
  "services": {
    "application": {"status": "healthy", "message": "FastAPI is responsive"},
    "redis": {"status": "healthy", "message": "Redis PING successful"},
    "rabbitmq": {"status": "healthy", "message": "Connected to rabbitmq:5672"},
    "ffmpeg": {"status": "healthy", "message": "ffmpeg version 4.4.2-0ubuntu0.22.04.1"}
  }
}
```

### 2. Upload Media File
```bash
curl -X POST http://localhost:8000/uploads \
  -F "file=@test_media/sample.jpg;type=image/jpeg"
```
**Response (201 Created)**:
```json
{
  "file_id": "file_804ca518b958",
  "filename": "file_804ca518b958.jpg",
  "original_name": "sample.jpg",
  "size_bytes": 12235,
  "content_type": "image/jpeg",
  "media_type": "image",
  "storage_path": "uploads/file_804ca518b958.jpg"
}
```

### 3. Submit Image Resize Job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "resize_image",
    "input_path": "uploads/file_804ca518b958.jpg",
    "parameters": {
      "width": 320,
      "height": 240,
      "preserve_aspect_ratio": true,
      "quality": 85
    }
  }'
```
**Response (201 Created)**:
```json
{
  "job_id": "job_36bc1ebca778",
  "status": "PENDING",
  "operation": "resize_image",
  "message": "Job successfully queued for worker processing"
}
```

### 4. Submit Video Thumbnail Extraction Job
```bash
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "video_thumbnail",
    "input_path": "uploads/file_video123.mp4",
    "parameters": {
      "timestamp_sec": 1.5,
      "width": 640
    }
  }'
```

### 5. Poll Job Execution Status
```bash
curl -X GET http://localhost:8000/jobs/job_36bc1ebca778
```
**Response (200 OK - Finished)**:
```json
{
  "job_id": "job_36bc1ebca778",
  "status": "COMPLETED",
  "operation": "resize_image",
  "input_path": "uploads/file_804ca518b958.jpg",
  "output_path": "processed/proc_job_36bc1ebca778.jpg",
  "created_at": "2026-09-07T19:44:17.345123Z",
  "started_at": "2026-09-07T19:44:17.350123Z",
  "completed_at": "2026-09-07T19:44:17.375123Z",
  "error": null,
  "retry_count": 0,
  "input_size": 12235,
  "output_size": 7240,
  "processing_time": 0.025,
  "celery_task_id": "23d8c1c4-5b48-43ff-8bb6-1c2168923058",
  "download_url": "/jobs/job_36bc1ebca778/download"
}
```

### 6. Download Processed Media Result
```bash
curl -X GET http://localhost:8000/jobs/job_36bc1ebca778/download \
  --output resized_result.jpg
```

### 7. Prometheus Metrics
```bash
curl -X GET http://localhost:8000/metrics
```
Exposes:
- `media_jobs_total{operation="...", media_type="image|video"}`
- `media_jobs_completed_total{operation="..."}`
- `media_jobs_failed_total{operation="..."}`
- `media_jobs_active_gauge`
- `media_processing_duration_seconds_bucket{operation="..."}`
- `media_job_retries_total{operation="..."}`

---

## 6. Automated Testing Suite

The project includes 33 unit and integration tests with 100% mocked AWS capabilities (no cloud billing or credentials needed):

```bash
# Run test suite with verbose output
PYTHONPATH=. pytest tests -v
```

### Test Coverage Summary:
- **`tests/test_health.py`**: Validates real dependency checks (FastAPI, Redis ping, RabbitMQ socket probe, FFmpeg binary probe, and degradation alerts).
- **`tests/test_uploads.py`**: Tests MIME types, extension verification, stream size limit enforcement (413), 0-byte detection, and corruption detection.
- **`tests/test_jobs.py`**: Tests full asynchronous lifecycle, eager task execution, Redis job record updates, metrics collection, and downloads.
- **`tests/test_images.py`**: Tests Pillow resize, aspect ratio preservation, coordinate bounding box crop, quality compression, format conversions (JPEG/PNG/WEBP), and watermarking.
- **`tests/test_videos.py`**: Tests FFmpeg binary availability, accurate frame thumbnail extraction, H.264/AAC CRF compression, and MP4 container transcoding.
- **`tests/test_security.py`**: Tests path traversal defenses (`../`, `..\..`), filename sanitizer, logging secret scrubber, and mocked S3 storage backend operations via `moto`.

---

## 7. College Demonstration Guide

Follow this presentation sequence for a 10-minute live demonstration:

### Step 1: Show Architecture & Health (2 Minutes)
1. Open the browser to Swagger UI: `http://localhost:8000/docs`
2. Demonstrate `GET /health` to show real-time connectivity to RabbitMQ, Redis, FFmpeg, and the API.
3. Open RabbitMQ Management UI at `http://localhost:15672` to show the active broker queues.

### Step 2: Run the Automated Live Demo Script (3 Minutes)
Execute the live demonstration CLI script in your terminal:
```bash
python3 scripts/demo.py --url http://localhost:8000
```
Explain the output as each phase is printed in color:
1. Image upload with MIME and corruption verification.
2. Celery event dispatch to the RabbitMQ broker.
3. Live Redis polling showing transition from `PENDING` to `PROCESSING` to `COMPLETED`.
4. Processed file download and verification.
5. Video upload and FFmpeg thumbnail frame extraction.
6. Display of real-time Prometheus throughput counters.

### Step 3: Demonstrate Fault Tolerance & Security (3 Minutes)
1. Attempt to upload an invalid/corrupted file or unsupported extension (`.exe` or `.txt`) and observe the HTTP 400 rejection.
2. Attempt a path traversal attack (`../../etc/passwd`) to show the path traversal guard.
3. Show `GET /metrics` to demonstrate production observability.

### Step 4: Questions & Distributed Systems Architecture (2 Minutes)
- Discuss how workers can scale horizontally by adding additional worker containers (`docker compose up --scale worker=4`).
- Explain how `task_acks_late=True` prevents lost jobs if a worker container crashes during processing.
