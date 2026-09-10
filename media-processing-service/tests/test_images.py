"""Tests for Pillow image processing engine."""

from pathlib import Path
from PIL import Image
from app.models.jobs import OperationType
from app.services.image_processor import ImageProcessor


def test_image_resize(tmp_path, sample_media):
    """Verify resize functionality with aspect ratio preservation."""
    processor = ImageProcessor()
    input_path = sample_media["jpg"]
    output_path = tmp_path / "resized.jpg"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.RESIZE_IMAGE,
        parameters={"width": 320, "height": 240, "preserve_aspect_ratio": True},
    )

    assert output_path.exists()
    with Image.open(output_path) as img:
        # Original 640x480 -> ratio 0.5 -> 320x240
        assert img.width <= 320
        assert img.height <= 240


def test_image_crop(tmp_path, sample_media):
    """Verify image cropping with boundary enforcement."""
    processor = ImageProcessor()
    input_path = sample_media["png"]
    output_path = tmp_path / "cropped.png"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.CROP_IMAGE,
        parameters={"left": 100, "top": 100, "right": 300, "bottom": 250},
    )

    assert output_path.exists()
    with Image.open(output_path) as img:
        assert img.width == 200
        assert img.height == 150


def test_image_compress(tmp_path, sample_media):
    """Verify image compression reduces or controls file size."""
    processor = ImageProcessor()
    input_path = sample_media["jpg"]
    orig_size = input_path.stat().st_size
    output_path = tmp_path / "compressed.jpg"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.COMPRESS_IMAGE,
        parameters={"quality": 30},
    )

    assert output_path.exists()
    assert output_path.stat().st_size <= orig_size


def test_image_convert_formats(tmp_path, sample_media):
    """Verify format conversions (PNG -> JPEG, JPEG -> WEBP, etc.)."""
    processor = ImageProcessor()

    # 1. RGBA PNG to JPEG (tests alpha handling and white background)
    png_input = sample_media["png"]
    jpg_out = tmp_path / "converted_from_png.jpg"
    processor.execute(
        input_path=png_input,
        output_path=jpg_out,
        operation=OperationType.CONVERT_IMAGE,
        parameters={"format": "JPEG"},
    )
    assert jpg_out.exists()
    with Image.open(jpg_out) as img:
        assert img.format == "JPEG"
        assert img.mode == "RGB"

    # 2. JPEG to WEBP
    jpg_input = sample_media["jpg"]
    webp_out = tmp_path / "converted.webp"
    processor.execute(
        input_path=jpg_input,
        output_path=webp_out,
        operation=OperationType.CONVERT_IMAGE,
        parameters={"format": "WEBP"},
    )
    assert webp_out.exists()
    with Image.open(webp_out) as img:
        assert img.format == "WEBP"


def test_image_watermark(tmp_path, sample_media):
    """Verify watermark text is applied onto image."""
    processor = ImageProcessor()
    input_path = sample_media["jpg"]
    output_path = tmp_path / "watermarked.jpg"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.WATERMARK_IMAGE,
        parameters={
            "text": "DEMO WATERMARK",
            "position": "bottom-right",
            "opacity": 0.8,
        },
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0
