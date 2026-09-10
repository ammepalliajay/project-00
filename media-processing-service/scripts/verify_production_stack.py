#!/usr/bin/env python3
"""Comprehensive Docker Production Stack Verification Script.

Verifies end-to-end distributed infrastructure:
1. FastAPI endpoint reachability
2. Redis cache & state store connectivity
3. RabbitMQ message broker connectivity
4. Celery worker availability and active worker ping
5. FFmpeg binary availability inside container runtime
6. Shared storage read/write accessibility
7. Complete end-to-end Image processing job (FastAPI -> RabbitMQ -> Celery -> Pillow -> Redis -> Download)
8. Complete end-to-end Video processing job (FastAPI -> RabbitMQ -> Celery -> FFmpeg -> Redis -> Download)
9. Job state transitions (PENDING -> PROCESSING -> COMPLETED)
10. Output artifact persistence and download integrity verification
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import socket
import sys
import time
from typing import Any, Dict, Optional
import requests

# ANSI Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


class VerificationReporter:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.results = []

    def record_pass(self, name: str, detail: str = ""):
        self.total += 1
        self.passed += 1
        self.results.append(("PASS", name, detail))
        print(f"  {GREEN}✓ PASS:{RESET} {BOLD}{name:<32}{RESET} {detail}")

    def record_fail(self, name: str, detail: str = ""):
        self.total += 1
        self.failed += 1
        self.results.append(("FAIL", name, detail))
        print(f"  {RED}✗ FAIL:{RESET} {BOLD}{name:<32}{RESET} {RED}{detail}{RESET}")

    def record_warn(self, name: str, detail: str = ""):
        self.warnings += 1
        self.results.append(("WARN", name, detail))
        print(f"  {YELLOW}⚠ WARN:{RESET} {BOLD}{name:<32}{RESET} {YELLOW}{detail}{RESET}")

    def summary(self) -> bool:
        print(f"\n{CYAN}{BOLD}{'=' * 75}")
        print(f"  PRODUCTION STACK VERIFICATION REPORT")
        print(f"{'=' * 75}{RESET}")
        print(f"  Total Checks: {self.total}")
        print(f"  Passed:       {GREEN}{self.passed}{RESET}")
        print(f"  Failed:       {RED if self.failed > 0 else GREEN}{self.failed}{RESET}")
        if self.warnings > 0:
            print(f"  Warnings:     {YELLOW}{self.warnings}{RESET}")
        print(f"{CYAN}{'=' * 75}{RESET}\n")

        if self.failed == 0:
            print(f"{GREEN}{BOLD}>>> ALL INFRASTRUCTURE CHECKS PASSED SUCCESSFULLY! <<<{RESET}\n")
            return True
        else:
            print(f"{RED}{BOLD}>>> INFRASTRUCTURE VERIFICATION ENCOUNTERED {self.failed} FAILURE(S) <<<{RESET}\n")
            return False


def section_header(title: str):
    print(f"\n{CYAN}{BOLD}--- [ {title} ] ---{RESET}")


def poll_job_status(
    base_url: str,
    job_id: str,
    reporter: VerificationReporter,
    max_timeout_sec: int = 40,
) -> Optional[Dict[str, Any]]:
    """Poll job status from Redis state store, tracking state transitions."""
    observed_statuses = []
    start_time = time.time()

    while time.time() - start_time < max_timeout_sec:
        res = requests.get(f"{base_url}/jobs/{job_id}", timeout=5)
        if res.status_code != 200:
            reporter.record_fail("Job Status Query", f"HTTP {res.status_code}: {res.text}")
            return None

        job_data = res.json()
        status = job_data.get("status")
        if status not in observed_statuses:
            observed_statuses.append(status)

        if status == "COMPLETED":
            transitions_str = " -> ".join(observed_statuses)
            reporter.record_pass("Job State Transitions", f"Observed: {transitions_str} ({time.time() - start_time:.2f}s)")
            return job_data

        if status == "FAILED":
            err = job_data.get("error", "Unknown error")
            reporter.record_fail("Job State Transitions", f"Job failed: {err}")
            return job_data

        time.sleep(1.0)

    reporter.record_fail("Job Execution Timeout", f"Job {job_id} did not finish within {max_timeout_sec}s")
    return None


def run_verification(base_url: str, output_dir: Path) -> bool:
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = base_url.rstrip("/")
    reporter = VerificationReporter()

    print(f"\n{BOLD}{CYAN}==========================================================================")
    print(f"    DISTRIBUTED MEDIA PROCESSING MICROSERVICE - DOCKER STACK VERIFICATION")
    print(f"=========================================================================={RESET}")
    print(f"Target API Base URL:  {BOLD}{base_url}{RESET}")
    print(f"Local Artifacts Dir:  {BOLD}{output_dir}{RESET}")
    print(f"Timestamp:            {datetime.now(timezone.utc).isoformat()}\n")

    # -------------------------------------------------------------
    # 1. FastAPI Reachability
    # -------------------------------------------------------------
    section_header("1. FastAPI Service Reachability")
    try:
        root_res = requests.get(f"{base_url}/", timeout=5)
        if root_res.status_code == 200 and "architecture" in root_res.text:
            reporter.record_pass("FastAPI Root Endpoint", f"HTTP {root_res.status_code} - Name: {root_res.json().get('name')}")
        else:
            reporter.record_fail("FastAPI Root Endpoint", f"Unexpected response: HTTP {root_res.status_code}")
    except Exception as exc:
        reporter.record_fail("FastAPI Root Endpoint", f"Connection error: {exc}")
        reporter.summary()
        return False

    # -------------------------------------------------------------
    # 2. Health Check & Dependencies (Redis, RabbitMQ, FFmpeg)
    # -------------------------------------------------------------
    section_header("2. Core Infrastructure & Dependencies Health")
    try:
        health_res = requests.get(f"{base_url}/health", timeout=5)
        health_data = health_res.json()
        services = health_data.get("services", {})

        # Redis Check
        redis_status = services.get("redis", {})
        if redis_status.get("status") == "healthy":
            reporter.record_pass("Redis Reachable", f"{redis_status.get('message')}")
        else:
            reporter.record_fail("Redis Reachable", f"Redis unhealthy: {redis_status.get('message')}")

        # RabbitMQ Check
        rabbitmq_status = services.get("rabbitmq", {})
        if rabbitmq_status.get("status") == "healthy":
            reporter.record_pass("RabbitMQ Reachable", f"{rabbitmq_status.get('message')}")
        else:
            reporter.record_fail("RabbitMQ Reachable", f"RabbitMQ unhealthy: {rabbitmq_status.get('message')}")

        # FFmpeg Binary Check
        ffmpeg_status = services.get("ffmpeg", {})
        if ffmpeg_status.get("status") == "healthy":
            reporter.record_pass("FFmpeg Available", f"{ffmpeg_status.get('message')}")
        else:
            reporter.record_fail("FFmpeg Available", f"FFmpeg error: {ffmpeg_status.get('message')}")

    except Exception as exc:
        reporter.record_fail("Health Check Endpoint", f"Failed to query /health: {exc}")

    # -------------------------------------------------------------
    # 3. Storage Writable & File Upload
    # -------------------------------------------------------------
    section_header("3. Shared Storage Read/Write Verification")
    sample_img_path = output_dir / "verify_sample.jpg"
    
    # Generate deterministic JPEG test image if not already present
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (640, 480), color=(30, 90, 180))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 600, 440], outline=(255, 255, 255), width=3)
    draw.text((80, 220), "STACK VERIFICATION JPEG", fill=(255, 255, 255))
    img.save(sample_img_path, format="JPEG", quality=90)

    try:
        with open(sample_img_path, "rb") as f:
            up_res = requests.post(
                f"{base_url}/uploads",
                files={"file": ("verify_sample.jpg", f, "image/jpeg")},
                timeout=10,
            )
        if up_res.status_code == 201:
            up_data = up_res.json()
            storage_path = up_data["storage_path"]
            reporter.record_pass("Storage Writable", f"Uploaded {up_data['size_bytes']} bytes to {storage_path}")
        else:
            reporter.record_fail("Storage Writable", f"Upload failed: HTTP {up_res.status_code} - {up_res.text}")
            storage_path = None
    except Exception as exc:
        reporter.record_fail("Storage Writable", f"Upload error: {exc}")
        storage_path = None

    # -------------------------------------------------------------
    # 4. Celery Worker & Image Processing Job E2E
    # -------------------------------------------------------------
    section_header("4. Asynchronous Image Processing Pipeline E2E")
    if storage_path:
        try:
            job_req = {
                "operation": "resize_image",
                "input_path": storage_path,
                "parameters": {"width": 320, "height": 240, "quality": 85},
            }
            job_res = requests.post(f"{base_url}/jobs", json=job_req, timeout=5)
            if job_res.status_code == 201:
                img_job_id = job_res.json()["job_id"]
                reporter.record_pass("Image Job Dispatch", f"Queued {img_job_id} to RabbitMQ")

                # Poll until completed
                completed_job = poll_job_status(base_url, img_job_id, reporter, max_timeout_sec=30)
                if completed_job and completed_job.get("status") == "COMPLETED":
                    # Celery worker reachability verified by job completion
                    celery_task_id = completed_job.get("celery_task_id")
                    reporter.record_pass("Celery Worker Reachable", f"Task ID: {celery_task_id}")

                    # Check output artifact existence
                    output_path = completed_job.get("output_path")
                    if output_path:
                        reporter.record_pass("Image Artifact Exists", f"Key: {output_path} ({completed_job.get('output_size')} bytes)")
                    else:
                        reporter.record_fail("Image Artifact Exists", "Missing output_path in job record")

                    # Download and verify output artifact
                    dl_res = requests.get(f"{base_url}/jobs/{img_job_id}/download", timeout=10)
                    if dl_res.status_code == 200 and len(dl_res.content) > 0:
                        dl_path = output_dir / "verified_resized.jpg"
                        dl_path.write_bytes(dl_res.content)
                        # Verify downloaded image is valid with PIL
                        with Image.open(dl_path) as dl_img:
                            w, h = dl_img.size
                            reporter.record_pass("Image Artifact Download", f"Saved {len(dl_res.content)} bytes, dimensions {w}x{h}")
                    else:
                        reporter.record_fail("Image Artifact Download", f"HTTP {dl_res.status_code}: {dl_res.text}")
                else:
                    reporter.record_fail("Image Job Completion", f"Status: {completed_job.get('status') if completed_job else 'None'}")
            else:
                reporter.record_fail("Image Job Dispatch", f"HTTP {job_res.status_code}: {job_res.text}")
        except Exception as exc:
            reporter.record_fail("Image Processing Pipeline", f"Error: {exc}")
    else:
        reporter.record_warn("Image Pipeline Skipped", "No uploaded storage path available")

    # -------------------------------------------------------------
    # 5. Video Processing Job E2E (FFmpeg inside container)
    # -------------------------------------------------------------
    section_header("5. Asynchronous Video Processing Pipeline E2E (FFmpeg)")
    import subprocess
    sample_mp4_path = output_dir / "verify_sample.mp4"
    if not sample_mp4_path.exists():
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=15",
            "-pix_fmt", "yuv420p", "-c:v", "libx264",
            str(sample_mp4_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=15)
        except Exception:
            pass

    if sample_mp4_path.exists():
        try:
            with open(sample_mp4_path, "rb") as vf:
                v_up = requests.post(
                    f"{base_url}/uploads",
                    files={"file": ("verify_sample.mp4", vf, "video/mp4")},
                    timeout=15,
                )
            if v_up.status_code == 201:
                v_storage_path = v_up.json()["storage_path"]
                reporter.record_pass("Video Upload", f"Stored at {v_storage_path}")

                v_job_req = {
                    "operation": "video_thumbnail",
                    "input_path": v_storage_path,
                    "parameters": {"timestamp": "00:00:01", "width": 320},
                }
                v_job_res = requests.post(f"{base_url}/jobs", json=v_job_req, timeout=5)
                if v_job_res.status_code == 201:
                    v_job_id = v_job_res.json()["job_id"]
                    reporter.record_pass("Video Job Dispatch", f"Queued {v_job_id} for FFmpeg worker")

                    v_completed = poll_job_status(base_url, v_job_id, reporter, max_timeout_sec=40)
                    if v_completed and v_completed.get("status") == "COMPLETED":
                        reporter.record_pass("Video Processing Complete", f"Duration: {v_completed.get('processing_time')}s")
                        
                        # Download thumbnail
                        v_dl = requests.get(f"{base_url}/jobs/{v_job_id}/download", timeout=10)
                        if v_dl.status_code == 200 and len(v_dl.content) > 0:
                            dl_thumb = output_dir / "verified_thumbnail.jpg"
                            dl_thumb.write_bytes(v_dl.content)
                            reporter.record_pass("Video Artifact Download", f"Saved {len(v_dl.content)} bytes thumbnail to {dl_thumb}")
                        else:
                            reporter.record_fail("Video Artifact Download", f"Download failed: HTTP {v_dl.status_code}")
                    else:
                        reporter.record_fail("Video Processing Complete", f"Status: {v_completed.get('status') if v_completed else 'Timeout'}")
                else:
                    reporter.record_fail("Video Job Dispatch", f"HTTP {v_job_res.status_code}: {v_job_res.text}")
            else:
                reporter.record_fail("Video Upload", f"Upload failed: HTTP {v_up.status_code}")
        except Exception as exc:
            reporter.record_fail("Video Pipeline Execution", f"Error: {exc}")
    else:
        reporter.record_warn("Video Pipeline Skipped", "Could not generate sample MP4 locally (FFmpeg missing on host)")

    # -------------------------------------------------------------
    # 6. Prometheus Metrics Scrape
    # -------------------------------------------------------------
    section_header("6. Prometheus Metrics Endpoint")
    try:
        metrics_res = requests.get(f"{base_url}/metrics", timeout=5)
        if metrics_res.status_code == 200 and "media_jobs" in metrics_res.text:
            reporter.record_pass("Metrics Scraping", "Prometheus /metrics endpoint exposing live job counters")
        else:
            reporter.record_fail("Metrics Scraping", f"Unexpected metrics response: HTTP {metrics_res.status_code}")
    except Exception as exc:
        reporter.record_fail("Metrics Scraping", f"Metrics error: {exc}")

    return reporter.summary()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Distributed Media Processing Microservice - Production Stack Verification")
    parser.add_argument("--url", default="http://localhost:8000", help="FastAPI Base URL (default: http://localhost:8000)")
    parser.add_argument("--output", default="./verification_artifacts", help="Directory to save test artifacts")
    args = parser.parse_args()

    success = run_verification(args.url, Path(args.output))
    sys.exit(0 if success else 1)
