"""Chainable sprite processing pipeline.

Each step operates on an internal image list and returns self for method chaining.
Can be used programmatically (e.g. from a notebook) or via the CLI.

Usage (programmatic):
    from scripts.sprite_pipeline import SpritePipeline

    # Full pipeline
    (SpritePipeline()
        .generate(prompt, reference="ref.png")
        .split(frames=4)
        .remove_bg("local")
        .resize(100)
        .save("idle"))

    # Process existing images (skip generation)
    (SpritePipeline()
        .load("raw_sprites/*.png")
        .remove_bg("local")
        .resize(100)
        .save("idle"))

Usage (CLI):
    uv run python scripts/sprite_pipeline.py generate \\
        --behavior idle --frames 4 --reference ref.png \\
        --prompt "Your prompt..." --bg-removal local --size 100

    uv run python scripts/sprite_pipeline.py process \\
        --behavior idle --input "raw/*.png" --bg-removal local --size 100
"""

from __future__ import annotations

import argparse
import glob
import io
import logging
import os
import re
import sys
from pathlib import Path

from PIL import Image

# Ensure project root is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BEHAVIORS_DIR = PROJECT_ROOT / "behaviors"

logger = logging.getLogger(__name__)


def _natural_sort_key(path: str) -> list:
    """Sort key that handles embedded numbers naturally (frame_2 before frame_10)."""
    return [int(c) if c.isdigit() else c.lower() for c in re.split(r"(\d+)", str(path))]


class SpritePipeline:
    """Chainable sprite processing pipeline.

    Each step operates on self.images (list[Image]) and returns self.
    """

    def __init__(self) -> None:
        self.images: list[Image.Image] = []

    # ── Entry points (populate self.images) ──────────────────────

    def generate(
        self,
        prompt: str,
        *,
        reference: str,
        model: str = "gemini-2.0-flash-preview-image-generation",
    ) -> SpritePipeline:
        """Call Gemini with a reference image + prompt.

        Stores the generated sprite sheet in self.images.
        Requires GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION env vars.
        """
        from dotenv import load_dotenv

        load_dotenv()

        from google import genai

        project = os.environ["GOOGLE_CLOUD_PROJECT"]
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")

        client = genai.Client(vertexai=True, project=project, location=location)

        ref_image = Image.open(reference)
        buf = io.BytesIO()
        ref_image.save(buf, format="PNG")

        logger.info("Calling Gemini model %s...", model)
        response = client.models.generate_content(
            model=model,
            contents=[
                genai.types.Part.from_bytes(data=buf.getvalue(), mime_type="image/png"),
                prompt,
            ],
            config=genai.types.GenerateContentConfig(response_modalities=["IMAGE", "TEXT"]),
        )

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                img = Image.open(io.BytesIO(part.inline_data.data))
                self.images.append(img)
                logger.info("Generated sprite sheet: %dx%d", img.width, img.height)
                break
        else:
            raise RuntimeError("Gemini response contained no image data")

        return self

    def load(self, *paths: str) -> SpritePipeline:
        """Load images from file paths or glob patterns.

        Appends to self.images so multiple loads can be chained.
        Files are sorted in natural order (frame_2 before frame_10).
        """
        for pattern in paths:
            matched = glob.glob(pattern)
            if not matched:
                raise FileNotFoundError(f"No files matched pattern: {pattern}")
            matched.sort(key=_natural_sort_key)
            for filepath in matched:
                img = Image.open(filepath)
                img.load()  # force read so file handle is released
                self.images.append(img)
                logger.info("Loaded: %s (%dx%d)", filepath, img.width, img.height)

        return self

    # ── Processing steps (transform self.images) ─────────────────

    def split(
        self,
        frames: int,
        *,
        rows: int | None = None,
        cols: int | None = None,
    ) -> SpritePipeline:
        """Split a single sprite sheet into individual frames.

        Replaces self.images with the split frames.
        Auto-detects grid layout if rows/cols not given.
        """
        if len(self.images) != 1:
            raise ValueError(
                f"split() expects exactly 1 image (the sprite sheet), got {len(self.images)}"
            )

        sheet = self.images[0]

        if rows is not None and cols is not None:
            r, c = rows, cols
        else:
            r, c = _detect_grid(frames, sheet.width, sheet.height)

        if r * c != frames:
            raise ValueError(f"Grid {r}x{c} = {r * c} cells, but expected {frames} frames")

        cell_w = sheet.width // c
        cell_h = sheet.height // r

        result = []
        for row in range(r):
            for col in range(c):
                box = (col * cell_w, row * cell_h, (col + 1) * cell_w, (row + 1) * cell_h)
                result.append(sheet.crop(box))

        self.images = result
        logger.info(
            "Split into %d frames (%dx%d each, %d rows x %d cols)", frames, cell_w, cell_h, r, c
        )
        return self

    def remove_bg(self, method: str = "local") -> SpritePipeline:
        """Remove background from each image.

        Args:
            method: 'local' (backgroundremover) or 'none' (passthrough).
        """
        if method == "none":
            logger.info("Background removal: skipped (method='none')")
            return self

        if method == "local":
            try:
                from backgroundremover.bg import remove
            except ImportError:
                raise ImportError(
                    "backgroundremover is not installed. Install with: uv sync --extra sprites"
                ) from None

            processed = []
            for i, img in enumerate(self.images):
                # backgroundremover takes/returns bytes
                buf_in = io.BytesIO()
                img.save(buf_in, format="PNG")
                result_bytes = remove(buf_in.getvalue())
                result = Image.open(io.BytesIO(result_bytes)).convert("RGBA")
                processed.append(result)
                logger.info("Removed background: frame %d/%d", i + 1, len(self.images))
            self.images = processed
            return self

        raise ValueError(f"Unknown background removal method: {method!r} (use 'local' or 'none')")

    def crop(self, *, padding: int = 0) -> SpritePipeline:
        """Crop each image to its content bounding box.

        Trims transparent pixels around the sprite, normalizing frames
        before resize. Run after remove_bg() for best results.
        Optional padding adds pixels around the content.
        """
        processed = []
        for i, img in enumerate(self.images):
            img = img.convert("RGBA")
            bbox = img.getbbox()
            if bbox is None:
                # Fully transparent — keep as-is
                processed.append(img)
                continue

            if padding > 0:
                left, top, right, bottom = bbox
                left = max(0, left - padding)
                top = max(0, top - padding)
                right = min(img.width, right + padding)
                bottom = min(img.height, bottom + padding)
                bbox = (left, top, right, bottom)

            cropped = img.crop(bbox)
            processed.append(cropped)
            logger.info(
                "Cropped frame %d/%d: %dx%d -> %dx%d",
                i + 1,
                len(self.images),
                img.width,
                img.height,
                cropped.width,
                cropped.height,
            )

        self.images = processed
        return self

    def resize(self, size: int) -> SpritePipeline:
        """Resize each image to fit within size x size, maintaining aspect ratio.

        Uses NEAREST resampling for pixel-art crispness.
        Centers on a transparent RGBA canvas.
        """
        processed = []
        for img in self.images:
            img = img.convert("RGBA")

            # Fit within size x size maintaining aspect ratio
            ratio = min(size / img.width, size / img.height)
            new_w = int(img.width * ratio)
            new_h = int(img.height * ratio)
            resized = img.resize((new_w, new_h), Image.Resampling.NEAREST)

            # Center on transparent canvas
            canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            offset_x = (size - new_w) // 2
            offset_y = (size - new_h) // 2
            canvas.paste(resized, (offset_x, offset_y))
            processed.append(canvas)

        self.images = processed
        logger.info("Resized %d frames to %dx%d", len(self.images), size, size)
        return self

    # ── Output ───────────────────────────────────────────────────

    def to_gif(
        self, behavior: str, *, fps: int = 8, loop: bool = True, output_dir: str | None = None
    ) -> SpritePipeline:
        """Save frames as a single animated GIF.

        Default output_dir: behaviors/{behavior}/media/
        """
        if not self.images:
            raise ValueError("No images to save")

        out = Path(output_dir) if output_dir else BEHAVIORS_DIR / behavior / "media"
        out.mkdir(parents=True, exist_ok=True)

        filepath = out / f"{behavior}.gif"
        duration_ms = 1000 // fps

        # Convert RGBA to palette with transparency
        gif_frames = []
        for frame in self.images:
            frame = frame.convert("RGBA")
            alpha = frame.split()[3]
            p_frame = frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
            mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
            p_frame.paste(255, mask)
            gif_frames.append(p_frame)

        save_kwargs = {
            "save_all": True,
            "append_images": gif_frames[1:],
            "duration": duration_ms,
            "transparency": 255,
            "disposal": 2,
        }
        if loop:
            save_kwargs["loop"] = 0

        gif_frames[0].save(filepath, **save_kwargs)
        logger.info("Saved GIF: %s (%d frames, %d fps)", filepath, len(self.images), fps)
        return self

    def save(self, behavior: str, *, output_dir: str | None = None) -> SpritePipeline:
        """Save as animated GIF (default) and individual PNGs.

        Default output_dir: behaviors/{behavior}/media/
        """
        self.to_gif(behavior, output_dir=output_dir)
        self.save_frames(behavior, output_dir=output_dir)
        return self

    def save_frames(self, behavior: str, *, output_dir: str | None = None) -> SpritePipeline:
        """Save frames as individual PNGs: {behavior}_1.png, {behavior}_2.png, ...

        Useful for editing in Aseprite.
        """
        if output_dir:
            out = Path(output_dir)
        else:
            out = BEHAVIORS_DIR / behavior / "media"

        out.mkdir(parents=True, exist_ok=True)

        for i, img in enumerate(self.images, start=1):
            filepath = out / f"{behavior}_{i}.png"
            img.save(filepath, "PNG")
            logger.info("Saved: %s", filepath)

        logger.info("Saved %d frames to %s", len(self.images), out)
        return self


def _detect_grid(frames: int, width: int, height: int) -> tuple[int, int]:
    """Auto-detect grid layout for a sprite sheet.

    Scores candidate layouts (integer factorizations of frames) by how close
    each cell's aspect ratio is to square. Returns (rows, cols).
    """
    best = (1, frames)
    best_score = float("inf")

    for r in range(1, frames + 1):
        if frames % r != 0:
            continue
        c = frames // r
        cell_w = width / c
        cell_h = height / r
        # Score: how far the cell aspect ratio is from 1:1
        ratio = max(cell_w, cell_h) / max(min(cell_w, cell_h), 1e-9)
        if ratio < best_score:
            best_score = ratio
            best = (r, c)

    return best


# ── CLI ──────────────────────────────────────────────────────────


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sprite generation and processing pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── generate subcommand ──
    gen = subparsers.add_parser("generate", help="Generate sprites from Gemini + process them")
    gen.add_argument("--behavior", required=True, help="Behavior name (e.g. idle, wander)")
    gen.add_argument("--frames", type=int, required=True, help="Number of frames in sprite sheet")
    gen.add_argument("--reference", required=True, help="Path to reference image")
    prompt_group = gen.add_mutually_exclusive_group(required=True)
    prompt_group.add_argument("--prompt", help="Prompt text for Gemini")
    prompt_group.add_argument("--prompt-file", help="Path to file containing prompt text")
    gen.add_argument(
        "--model", default="gemini-2.0-flash-preview-image-generation", help="Gemini model name"
    )
    gen.add_argument("--rows", type=int, help="Manual grid rows (auto-detect if omitted)")
    gen.add_argument("--cols", type=int, help="Manual grid cols (auto-detect if omitted)")
    gen.add_argument(
        "--crop-padding", type=int, help="Crop to content with N pixels padding (skip if omitted)"
    )
    gen.add_argument(
        "--bg-removal", choices=["local", "none"], default="none", help="Background removal method"
    )
    gen.add_argument("--size", type=int, default=100, help="Output sprite size (pixels)")
    gen.add_argument("--output-dir", help="Custom output directory")
    gen.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    # ── process subcommand ──
    proc = subparsers.add_parser("process", help="Process existing images (skip generation)")
    proc.add_argument("--behavior", required=True, help="Behavior name (e.g. idle, wander)")
    proc.add_argument(
        "--input", required=True, nargs="+", help="Input file path(s) or glob pattern(s)"
    )
    proc.add_argument("--frames", type=int, help="Number of frames (triggers split if provided)")
    proc.add_argument("--rows", type=int, help="Manual grid rows")
    proc.add_argument("--cols", type=int, help="Manual grid cols")
    proc.add_argument(
        "--crop-padding", type=int, help="Crop to content with N pixels padding (skip if omitted)"
    )
    proc.add_argument(
        "--bg-removal", choices=["local", "none"], default="none", help="Background removal method"
    )
    proc.add_argument("--size", type=int, default=100, help="Output sprite size (pixels)")
    proc.add_argument("--output-dir", help="Custom output directory")
    proc.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )

    pipe = SpritePipeline()

    if args.command == "generate":
        prompt = args.prompt
        if args.prompt_file:
            prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()

        pipe.generate(prompt, reference=args.reference, model=args.model)
        pipe.split(args.frames, rows=args.rows, cols=args.cols)

    elif args.command == "process":
        pipe.load(*args.input)
        if args.frames:
            pipe.split(args.frames, rows=args.rows, cols=args.cols)

    pipe.remove_bg(args.bg_removal)
    if args.crop_padding is not None:
        pipe.crop(padding=args.crop_padding)
    pipe.resize(args.size)
    pipe.save(args.behavior, output_dir=args.output_dir)

    print(f"Done! {len(pipe.images)} sprites saved for '{args.behavior}'.")


if __name__ == "__main__":
    main()
