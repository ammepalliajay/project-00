"""Script to generate realistic test media: JPEG, PNG, WEBP, and video."""

import os
from pathlib import Path
import subprocess
from PIL import Image, ImageDraw


def generate_images(output_dir: Path) -> dict:
    """Generate sample JPEG, PNG, and WEBP images."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    # 1. JPEG sample (colorful pattern with high-frequency variations)
    jpg_path = output_dir / "sample.jpg"
    img_rgb = Image.new("RGB", (640, 480))
    pixels = img_rgb.load()
    for y in range(480):
        for x in range(640):
            pixels[x, y] = ((x * 3) % 256, (y * 2) % 256, (x + y) % 256)
    draw = ImageDraw.Draw(img_rgb)
    draw.rectangle([50, 50, 590, 430], outline=(255, 255, 255), width=4)
    draw.text((100, 200), "SAMPLE JPEG - 640x480", fill=(255, 255, 0))
    img_rgb.save(jpg_path, format="JPEG", quality=95)
    paths["jpg"] = jpg_path

    # 2. PNG sample (RGBA with transparency)
    png_path = output_dir / "sample.png"
    img_rgba = Image.new("RGBA", (640, 480), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img_rgba)
    draw.ellipse([80, 80, 560, 400], fill=(200, 50, 50, 200), outline=(255, 255, 255, 255), width=3)
    draw.text((120, 220), "SAMPLE PNG (RGBA)", fill=(255, 255, 255, 255))
    img_rgba.save(png_path, format="PNG")
    paths["png"] = png_path

    # 3. WEBP sample
    webp_path = output_dir / "sample.webp"
    img_rgb.save(webp_path, format="WEBP", quality=80)
    paths["webp"] = webp_path

    # 4. Corrupted image for failure testing
    corrupt_path = output_dir / "corrupted.jpg"
    corrupt_path.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"random_corrupted_garbage_bytes" * 5)
    paths["corrupt"] = corrupt_path

    return paths


def generate_videos(output_dir: Path) -> dict:
    """Generate sample MP4 and AVI videos using FFmpeg lavfi filters if available."""
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}

    mp4_path = output_dir / "sample.mp4"
    avi_path = output_dir / "sample.avi"

    cmd_mp4 = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=2:size=320x240:rate=15",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=440:duration=2",
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        "-pix_fmt",
        "yuv420p",
        str(mp4_path),
    ]

    cmd_avi = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=duration=1:size=320x240:rate=15",
        "-c:v",
        "mpeg4",
        str(avi_path),
    ]

    try:
        subprocess.run(cmd_mp4, capture_output=True, timeout=15)
        if mp4_path.exists():
            paths["mp4"] = mp4_path

        subprocess.run(cmd_avi, capture_output=True, timeout=15)
        if avi_path.exists():
            paths["avi"] = avi_path
    except Exception as exc:
        print(f"Video generation skipped: {exc}")

    return paths


def generate_all(target_dir: str = "./test_media") -> dict:
    """Generate full suite of test media files."""
    dest = Path(target_dir).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    results = {}
    results.update(generate_images(dest))
    results.update(generate_videos(dest))
    print(f"Generated test media in {dest}: {list(results.keys())}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate deterministic test media files (JPEG, PNG, WEBP, MP4, AVI)")
    parser.add_argument("--output", "-o", default="./test_media", help="Target directory for generated media files")
    args = parser.parse_args()
    generate_all(args.output)
