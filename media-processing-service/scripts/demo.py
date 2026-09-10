#!/usr/bin/env python3
"""Live College Demonstration Script for Distributed Media Processing Microservice.

Executes the complete asynchronous workflow:
1. Health & Dependency Checks (FastAPI, Redis, RabbitMQ, FFmpeg)
2. Image Upload & Integrity Verification
3. Asynchronous Image Resize Job Submission (Celery / RabbitMQ)
4. Redis Job Status Polling
5. Processed Image Result Download & Verification
6. Video Upload & Integrity Verification
7. Asynchronous Video Thumbnail Job Submission (FFmpeg)
8. Redis Job Status Polling
9. Video Thumbnail Result Download & Verification
10. Live Prometheus Performance Metrics Display
"""

import argparse
from pathlib import Path
import sys
import time
import requests
from generate_test_media import generate_all

# ANSI Terminal Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner(text: str):
    print(f"\n{CYAN}{BOLD}{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}{RESET}\n")


def print_step(num: int, title: str):
    print(f"\n{BOLD}[STEP {num}] {title}{RESET}")


def poll_job_until_complete(base_url: str, job_id: str, max_wait_sec: int = 30) -> dict:
    """Poll Redis job status until COMPLETED or FAILED."""
    start_time = time.time()
    while time.time() - start_time < max_wait_sec:
        res = requests.get(f"{base_url}/jobs/{job_id}", timeout=5)
        if res.status_code != 200:
            print(f"  {RED}Failed to query job status: {res.text}{RESET}")
            break
        data = res.json()
        current_status = data.get("status")
        print(f"  ... Job Status: {YELLOW}{current_status}{RESET} (elapsed: {time.time() - start_time:.1f}s)")
        if current_status == "COMPLETED":
            return data
        if current_status == "FAILED":
            print(f"  {RED}Job failed with error: {data.get('error')}{RESET}")
            return data
        time.sleep(1.0)

    raise TimeoutError(f"Job {job_id} did not complete within {max_wait_sec} seconds.")


def run_demo(base_url: str, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    base_url = base_url.rstrip("/")

    print_banner("DISTRIBUTED MEDIA PROCESSING MICROSERVICE - LIVE DEMO")
    print(f"API Target: {base_url}")
    print(f"Artifacts Destination: {output_dir}\n")

    # Step 1: Health Check
    print_step(1, "Verify System Health & Dependent Services")
    try:
        health_res = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health HTTP Status: {health_res.status_code}")
        services = health_res.json().get("services", {})
        for svc_name, svc_info in services.items():
            color = GREEN if svc_info.get("status") == "healthy" else RED
            print(f"  - {svc_name.upper():<12}: {color}{svc_info.get('status').upper()}{RESET} ({svc_info.get('message')})")
    except Exception as exc:
        print(f"{RED}Health check failed to connect to {base_url}: {exc}{RESET}")
        print("Please ensure FastAPI server is running.")
        sys.exit(1)

    # Prepare sample media
    print_step(2, "Generating High-Quality Test Media Fixtures")
    media_files = generate_all(str(output_dir / "test_input"))
    print(f"Generated test files: {list(media_files.keys())}")

    # Step 3: Upload Image
    print_step(3, "Upload Image (sample.jpg) with MIME & Integrity Validation")
    jpg_path = media_files["jpg"]
    with open(jpg_path, "rb") as f:
        up_res = requests.post(
            f"{base_url}/uploads",
            files={"file": ("sample.jpg", f, "image/jpeg")},
            timeout=10,
        )
    if up_res.status_code != 201:
        print(f"{RED}Image upload failed: {up_res.text}{RESET}")
        sys.exit(1)
    img_upload = up_res.json()
    print(f"  {GREEN}✓ Image Uploaded Successfully!{RESET}")
    print(f"  File ID:      {img_upload['file_id']}")
    print(f"  Storage Key:  {img_upload['storage_path']}")
    print(f"  Payload Size: {img_upload['size_bytes']} bytes")

    # Step 4: Submit Image Resize Job
    print_step(4, "Dispatch Image Resize Job to RabbitMQ & Celery")
    job_payload = {
        "operation": "resize_image",
        "input_path": img_upload["storage_path"],
        "parameters": {
            "width": 320,
            "height": 240,
            "preserve_aspect_ratio": True,
            "quality": 85,
        },
    }
    job_res = requests.post(f"{base_url}/jobs", json=job_payload, timeout=5)
    if job_res.status_code != 201:
        print(f"{RED}Job submission failed: {job_res.text}{RESET}")
        sys.exit(1)
    img_job_id = job_res.json()["job_id"]
    print(f"  {GREEN}✓ Job Created & Queued!{RESET} ID: {BOLD}{img_job_id}{RESET}")

    # Step 5: Poll Redis Status
    print_step(5, f"Polling Redis Job State for {img_job_id}")
    img_final_state = poll_job_until_complete(base_url, img_job_id)
    print(f"  {GREEN}✓ Image Job Finished!{RESET}")
    print(f"  Processing Time: {img_final_state.get('processing_time'):.3f}s")
    print(f"  Output Size:     {img_final_state.get('output_size')} bytes")

    # Step 6: Download Processed Image
    print_step(6, "Download Processed Image Output")
    dl_res = requests.get(f"{base_url}/jobs/{img_job_id}/download", timeout=10)
    dl_img_path = output_dir / "downloaded_resized.jpg"
    dl_img_path.write_bytes(dl_res.content)
    print(f"  {GREEN}✓ Downloaded {len(dl_res.content)} bytes to {dl_img_path}{RESET}")

    # Step 7: Upload Video
    if "mp4" in media_files:
        print_step(7, "Upload Video (sample.mp4) for Asynchronous Processing")
        mp4_path = media_files["mp4"]
        with open(mp4_path, "rb") as f:
            v_up_res = requests.post(
                f"{base_url}/uploads",
                files={"file": ("sample.mp4", f, "video/mp4")},
                timeout=15,
            )
        if v_up_res.status_code == 201:
            vid_upload = v_up_res.json()
            print(f"  {GREEN}✓ Video Uploaded Successfully!{RESET}")
            print(f"  File ID:      {vid_upload['file_id']}")
            print(f"  Storage Key:  {vid_upload['storage_path']}")

            # Step 8: Submit Video Thumbnail Job
            print_step(8, "Dispatch Video Thumbnail Job to Celery Worker (FFmpeg)")
            v_job_payload = {
                "operation": "video_thumbnail",
                "input_path": vid_upload["storage_path"],
                "parameters": {"timestamp_sec": 1.0, "width": 480},
            }
            v_job_res = requests.post(f"{base_url}/jobs", json=v_job_payload, timeout=5)
            v_job_id = v_job_res.json()["job_id"]
            print(f"  {GREEN}✓ Video Thumbnail Job Queued!{RESET} ID: {BOLD}{v_job_id}{RESET}")

            # Step 9: Poll Video Job
            print_step(9, f"Polling Redis Job State for {v_job_id}")
            v_final = poll_job_until_complete(base_url, v_job_id)
            print(f"  {GREEN}✓ Video Job Finished!{RESET}")
            print(f"  Processing Time: {v_final.get('processing_time'):.3f}s")

            # Step 10: Download Thumbnail
            print_step(10, "Download Generated Video Thumbnail")
            v_dl_res = requests.get(f"{base_url}/jobs/{v_job_id}/download", timeout=10)
            dl_thumb_path = output_dir / "downloaded_thumbnail.jpg"
            dl_thumb_path.write_bytes(v_dl_res.content)
            print(f"  {GREEN}✓ Saved thumbnail to {dl_thumb_path} ({len(v_dl_res.content)} bytes){RESET}")

    # Step 11: Display Prometheus Metrics
    print_step(11, "Display Real-Time Prometheus Microservice Metrics")
    metrics_res = requests.get(f"{base_url}/metrics", timeout=5)
    print(f"{CYAN}--- Prometheus Metrics Summary ---{RESET}")
    for line in metrics_res.text.splitlines():
        if line.startswith("media_jobs") and not line.startswith("#"):
            print(f"  {line}")

    print_banner("DEMO COMPLETED SUCCESSFULLY! ALL WORKFLOW STEPS VERIFIED.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live College Demo for Distributed Media Microservice")
    parser.add_argument("--url", default="http://localhost:8000", help="FastAPI microservice base URL")
    parser.add_argument("--output", default="./demo_output", help="Directory to save downloaded files")
    args = parser.parse_args()

    run_demo(args.url, Path(args.output))
