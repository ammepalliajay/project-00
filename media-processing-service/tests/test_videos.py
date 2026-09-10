"""Tests for FFmpeg video operations: thumbnail, compression, transcoding."""

from pathlib import Path
from app.models.jobs import OperationType
from app.services.video_processor import VideoProcessor


def test_ffmpeg_available():
    """Verify system FFmpeg is accessible."""
    ok, details = VideoProcessor.check_ffmpeg()
    assert ok is True
    assert "ffmpeg" in details.lower() or "version" in details.lower()


def test_video_thumbnail(tmp_path, sample_media):
    """Verify video thumbnail frame extraction."""
    if "mp4" not in sample_media:
        return
    processor = VideoProcessor()
    input_path = sample_media["mp4"]
    output_path = tmp_path / "thumbnail.jpg"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.VIDEO_THUMBNAIL,
        parameters={"timestamp_sec": 0.5, "width": 320},
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_video_compression(tmp_path, sample_media):
    """Verify video compression with H.264/AAC."""
    if "mp4" not in sample_media:
        return
    processor = VideoProcessor()
    input_path = sample_media["mp4"]
    output_path = tmp_path / "compressed.mp4"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.VIDEO_COMPRESS,
        parameters={"crf": 32, "preset": "ultrafast"},
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_video_transcoding(tmp_path, sample_media):
    """Verify video transcoding to MP4 container."""
    if "avi" not in sample_media:
        return
    processor = VideoProcessor()
    input_path = sample_media["avi"]
    output_path = tmp_path / "transcoded.mp4"

    processor.execute(
        input_path=input_path,
        output_path=output_path,
        operation=OperationType.VIDEO_TRANSCODE,
        parameters={"resolution": "640x360", "fps": 24},
    )

    assert output_path.exists()
    assert output_path.stat().st_size > 0
