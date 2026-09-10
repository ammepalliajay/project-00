"""Image processing engine using Pillow: resize, crop, compress, convert, watermark."""

from pathlib import Path
from typing import Any, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps
from app.core.logging import logger
from app.models.jobs import OperationType


class ImageProcessor:
    """Performs image operations using Pillow."""

    @staticmethod
    def _normalize_mode_for_format(image: Image.Image, target_format: str) -> Image.Image:
        """Convert RGBA/P images appropriately when saving to JPEG."""
        fmt = target_format.upper()
        if fmt in ("JPEG", "JPG"):
            if image.mode in ("RGBA", "LA", "P"):
                # Create a solid white background and paste with alpha mask
                bg = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                alpha = image.split()[-1] if "A" in image.mode else None
                bg.paste(image, mask=alpha)
                return bg
            elif image.mode != "RGB":
                return image.convert("RGB")
        return image

    def resize(
        self,
        image: Image.Image,
        width: int,
        height: int,
        preserve_aspect_ratio: bool = True,
    ) -> Image.Image:
        """Resize image with optional aspect ratio preservation."""
        orig_w, orig_h = image.size

        if width <= 0 or height <= 0:
            raise ValueError(f"Invalid dimensions for resize: {width}x{height}")

        if preserve_aspect_ratio:
            ratio = min(width / orig_w, height / orig_h)
            new_w = max(1, int(orig_w * ratio))
            new_h = max(1, int(orig_h * ratio))
            return image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
        else:
            return image.resize((width, height), resample=Image.Resampling.LANCZOS)

    def crop(
        self,
        image: Image.Image,
        left: int,
        top: int,
        right: int,
        bottom: int,
    ) -> Image.Image:
        """Crop rectangle (left, top, right, bottom) from image."""
        w, h = image.size

        # Clamp boundaries safely
        left = max(0, min(left, w - 1))
        top = max(0, min(top, h - 1))
        right = max(left + 1, min(right, w))
        bottom = max(top + 1, min(bottom, h))

        if left >= right or top >= bottom:
            raise ValueError(f"Invalid crop box: ({left}, {top}, {right}, {bottom}) for image size {w}x{h}")

        return image.crop((left, top, right, bottom))

    def compress(
        self,
        image: Image.Image,
        quality: int = 70,
    ) -> Tuple[Image.Image, Dict[str, Any]]:
        """Prepare image for compression with specified quality."""
        q = max(1, min(100, int(quality)))
        save_params = {"quality": q, "optimize": True}
        return image, save_params

    def convert(
        self,
        image: Image.Image,
        target_format: str,
    ) -> Tuple[Image.Image, str]:
        """Convert image mode to match target format."""
        norm_fmt = target_format.upper()
        if norm_fmt == "JPG":
            norm_fmt = "JPEG"
        if norm_fmt not in ("JPEG", "PNG", "WEBP"):
            raise ValueError(f"Unsupported target format: {target_format}. Supported: JPEG, PNG, WEBP")

        converted = self._normalize_mode_for_format(image, norm_fmt)
        return converted, norm_fmt

    def watermark(
        self,
        image: Image.Image,
        text: str = "CONFIDENTIAL",
        opacity: float = 0.6,
        position: str = "bottom-right",
    ) -> Image.Image:
        """Apply transparent text watermark overlay to image."""
        # Convert base to RGBA for blending
        base_rgba = image.convert("RGBA")
        overlay = Image.new("RGBA", base_rgba.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)

        # Estimate font size relative to image width
        w, h = base_rgba.size
        font_size = max(18, int(min(w, h) * 0.05))

        try:
            font = ImageFont.load_default()
        except Exception:
            font = None

        # Determine bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        # Calculate position coordinates
        margin = 20
        if position == "center":
            x = (w - text_w) // 2
            y = (h - text_h) // 2
        elif position == "top-left":
            x = margin
            y = margin
        elif position == "top-right":
            x = w - text_w - margin
            y = margin
        elif position == "bottom-left":
            x = margin
            y = h - text_h - margin
        else:  # bottom-right default
            x = w - text_w - margin
            y = h - text_h - margin

        x = max(0, x)
        y = max(0, y)

        alpha_val = int(255 * max(0.1, min(1.0, opacity)))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, alpha_val))

        # Composite overlay over base image
        watermarked = Image.alpha_composite(base_rgba, overlay)
        # Restore original mode if needed
        return self._normalize_mode_for_format(watermarked, image.format or "PNG")

    def execute(
        self,
        input_path: Path,
        output_path: Path,
        operation: OperationType,
        parameters: Dict[str, Any],
    ) -> Path:
        """Dispatch image operation and save output safely."""
        with Image.open(input_path) as raw_img:
            # Determine format before exif_transpose creates a new image instance without .format
            ext = output_path.suffix.lower().lstrip(".")
            if ext in ("jpg", "jpeg"):
                inferred_format = "JPEG"
            elif ext == "webp":
                inferred_format = "WEBP"
            elif ext == "png":
                inferred_format = "PNG"
            else:
                inferred_format = raw_img.format or "JPEG"

            target_format = inferred_format
            save_params: Dict[str, Any] = {}

            # Handle orientation from EXIF if present
            img = ImageOps.exif_transpose(raw_img) or raw_img

            if operation == OperationType.RESIZE_IMAGE:
                w = int(parameters.get("width", 800))
                h = int(parameters.get("height", 600))
                preserve = bool(parameters.get("preserve_aspect_ratio", True))
                quality = int(parameters.get("quality", 85))
                processed = self.resize(img, w, h, preserve_aspect_ratio=preserve)
                save_params["quality"] = quality

            elif operation == OperationType.CROP_IMAGE:
                l = int(parameters.get("left", 0))
                t = int(parameters.get("top", 0))
                r = int(parameters.get("right", img.width))
                b = int(parameters.get("bottom", img.height))
                processed = self.crop(img, l, t, r, b)

            elif operation == OperationType.COMPRESS_IMAGE:
                q = int(parameters.get("quality", 70))
                processed, save_params = self.compress(img, quality=q)

            elif operation == OperationType.CONVERT_IMAGE:
                fmt = str(parameters.get("format", "JPEG")).upper()
                processed, target_format = self.convert(img, fmt)
                if target_format == "JPEG":
                    save_params["quality"] = int(parameters.get("quality", 85))

            elif operation == OperationType.WATERMARK_IMAGE:
                text = str(parameters.get("text", "WATERMARK"))
                pos = str(parameters.get("position", "bottom-right"))
                opacity = float(parameters.get("opacity", 0.6))
                processed = self.watermark(img, text=text, position=pos, opacity=opacity)

            else:
                raise ValueError(f"Unsupported image operation: {operation}")

            # Ensure safe mode for target format
            norm_fmt = target_format.upper()
            if norm_fmt == "JPG":
                norm_fmt = "JPEG"
            processed = self._normalize_mode_for_format(processed, norm_fmt)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            processed.save(output_path, format=norm_fmt, **save_params)

        logger.info(f"Image processing completed: {operation.value} -> {output_path}")
        return output_path
