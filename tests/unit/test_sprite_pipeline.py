"""Tests for scripts/sprite_pipeline.py — SpritePipeline class and CLI."""

import os
import sys
from unittest.mock import patch

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.sprite_pipeline import SpritePipeline, _build_parser, _detect_grid


def _make_image(width: int, height: int, color: tuple = (255, 0, 0, 255)) -> Image.Image:
    """Create a solid-color RGBA test image."""
    return Image.new("RGBA", (width, height), color)


@pytest.mark.unit
class TestLoad:
    def test_load_single_file(self, tmp_path):
        img = _make_image(50, 50)
        path = tmp_path / "frame.png"
        img.save(path)

        pipe = SpritePipeline().load(str(path))
        assert len(pipe.images) == 1
        assert pipe.images[0].size == (50, 50)

    def test_load_glob_pattern(self, tmp_path):
        for i in range(3):
            _make_image(50, 50).save(tmp_path / f"frame_{i + 1}.png")

        pipe = SpritePipeline().load(str(tmp_path / "frame_*.png"))
        assert len(pipe.images) == 3

    def test_load_natural_sort_order(self, tmp_path):
        """frame_2 should come before frame_10."""
        for i in [1, 2, 10]:
            _make_image(10 * i, 10, color=(i, 0, 0, 255)).save(tmp_path / f"frame_{i}.png")

        pipe = SpritePipeline().load(str(tmp_path / "frame_*.png"))
        widths = [img.width for img in pipe.images]
        assert widths == [10, 20, 100]

    def test_load_no_match_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="No files matched"):
            SpritePipeline().load(str(tmp_path / "nonexistent_*.png"))

    def test_load_multiple_patterns(self, tmp_path):
        _make_image(50, 50).save(tmp_path / "a.png")
        _make_image(60, 60).save(tmp_path / "b.png")

        pipe = SpritePipeline().load(str(tmp_path / "a.png"), str(tmp_path / "b.png"))
        assert len(pipe.images) == 2

    def test_load_returns_self(self, tmp_path):
        _make_image(50, 50).save(tmp_path / "frame.png")
        pipe = SpritePipeline()
        result = pipe.load(str(tmp_path / "frame.png"))
        assert result is pipe


@pytest.mark.unit
class TestDetectGrid:
    def test_4_frames_square_sheet(self):
        # 200x200 sheet, 4 frames -> 2x2 (100x100 cells, ratio 1.0)
        assert _detect_grid(4, 200, 200) == (2, 2)

    def test_4_frames_wide_sheet(self):
        # 400x100 sheet, 4 frames -> 1x4 (100x100 cells)
        assert _detect_grid(4, 400, 100) == (1, 4)

    def test_4_frames_tall_sheet(self):
        # 100x400 sheet, 4 frames -> 4x1 (100x100 cells)
        assert _detect_grid(4, 100, 400) == (4, 1)

    def test_6_frames_landscape(self):
        # 300x200 sheet, 6 frames -> 2x3 (100x100) or 3x2 (150x66)
        # 2x3 gives 100x100 cells (ratio 1.0), 3x2 gives 150x66 (ratio 2.27)
        assert _detect_grid(6, 300, 200) == (2, 3)

    def test_prime_frames(self):
        # 5 frames: only 1x5 or 5x1
        r, c = _detect_grid(5, 500, 100)
        assert r * c == 5


@pytest.mark.unit
class TestSplit:
    def test_split_2x2(self):
        sheet = _make_image(200, 200)
        pipe = SpritePipeline()
        pipe.images = [sheet]

        pipe.split(4, rows=2, cols=2)
        assert len(pipe.images) == 4
        assert all(img.size == (100, 100) for img in pipe.images)

    def test_split_1x4(self):
        sheet = _make_image(400, 100)
        pipe = SpritePipeline()
        pipe.images = [sheet]

        pipe.split(4, rows=1, cols=4)
        assert len(pipe.images) == 4
        assert all(img.size == (100, 100) for img in pipe.images)

    def test_split_auto_detect(self):
        sheet = _make_image(200, 200)
        pipe = SpritePipeline()
        pipe.images = [sheet]

        pipe.split(4)
        assert len(pipe.images) == 4

    def test_split_wrong_image_count_raises(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(100, 100), _make_image(100, 100)]

        with pytest.raises(ValueError, match="exactly 1 image"):
            pipe.split(4)

    def test_split_grid_mismatch_raises(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(200, 200)]

        with pytest.raises(ValueError, match="Grid 2x3 = 6 cells, but expected 4"):
            pipe.split(4, rows=2, cols=3)

    def test_split_returns_self(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(200, 200)]
        result = pipe.split(4)
        assert result is pipe


def _make_padded_image(content_size: int, padding: int, color=(255, 0, 0, 255)):
    """Create an image with content centered in transparent padding."""
    total = content_size + 2 * padding
    img = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    img.paste(
        Image.new("RGBA", (content_size, content_size), color),
        (padding, padding),
    )
    return img


@pytest.mark.unit
class TestCrop:
    def test_crop_trims_transparent_border(self):
        img = _make_padded_image(content_size=20, padding=10)
        assert img.size == (40, 40)

        pipe = SpritePipeline()
        pipe.images = [img]
        pipe.crop()

        assert pipe.images[0].size == (20, 20)

    def test_crop_with_padding(self):
        img = _make_padded_image(content_size=20, padding=10)
        pipe = SpritePipeline()
        pipe.images = [img]
        pipe.crop(padding=5)

        # Content is 20x20, +5 padding on each side = 30x30
        assert pipe.images[0].size == (30, 30)

    def test_crop_padding_clamped_to_image_bounds(self):
        img = _make_padded_image(content_size=20, padding=3)
        pipe = SpritePipeline()
        pipe.images = [img]
        pipe.crop(padding=10)  # padding exceeds available space

        # Should clamp to image bounds (26x26), not exceed it
        assert pipe.images[0].size == (26, 26)

    def test_crop_fully_transparent(self):
        img = Image.new("RGBA", (50, 50), (0, 0, 0, 0))
        pipe = SpritePipeline()
        pipe.images = [img]
        pipe.crop()

        # Fully transparent image kept as-is
        assert pipe.images[0].size == (50, 50)

    def test_crop_no_transparent_border(self):
        img = _make_image(50, 50)
        pipe = SpritePipeline()
        pipe.images = [img]
        pipe.crop()

        # No transparent border to trim
        assert pipe.images[0].size == (50, 50)

    def test_crop_multiple_images(self):
        pipe = SpritePipeline()
        pipe.images = [
            _make_padded_image(20, 10),
            _make_padded_image(30, 5),
        ]
        pipe.crop()

        assert pipe.images[0].size == (20, 20)
        assert pipe.images[1].size == (30, 30)

    def test_crop_returns_self(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]
        result = pipe.crop()
        assert result is pipe


@pytest.mark.unit
class TestRemoveBg:
    def test_none_passthrough(self):
        images = [_make_image(50, 50), _make_image(60, 60)]
        pipe = SpritePipeline()
        pipe.images = images.copy()

        pipe.remove_bg("none")
        assert len(pipe.images) == 2
        assert pipe.images[0].size == (50, 50)
        assert pipe.images[1].size == (60, 60)

    def test_invalid_method_raises(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]

        with pytest.raises(ValueError, match="Unknown background removal method"):
            pipe.remove_bg("invalid")

    def test_local_without_backgroundremover_raises(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]

        with patch.dict("sys.modules", {"backgroundremover": None, "backgroundremover.bg": None}):
            with pytest.raises(ImportError, match="backgroundremover is not installed"):
                pipe.remove_bg("local")

    def test_remove_bg_returns_self(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]
        result = pipe.remove_bg("none")
        assert result is pipe


@pytest.mark.unit
class TestResize:
    def test_resize_square(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(200, 200)]

        pipe.resize(100)
        assert pipe.images[0].size == (100, 100)

    def test_resize_landscape(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(200, 100)]

        pipe.resize(100)
        img = pipe.images[0]
        assert img.size == (100, 100)
        assert img.mode == "RGBA"

    def test_resize_portrait(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(100, 200)]

        pipe.resize(100)
        img = pipe.images[0]
        assert img.size == (100, 100)
        assert img.mode == "RGBA"

    def test_resize_converts_to_rgba(self):
        pipe = SpritePipeline()
        pipe.images = [Image.new("RGB", (50, 50), (255, 0, 0))]

        pipe.resize(100)
        assert pipe.images[0].mode == "RGBA"

    def test_resize_transparent_padding(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(200, 100)]  # 2:1 aspect ratio

        pipe.resize(100)
        img = pipe.images[0]
        # Top-left corner should be transparent (padding)
        assert img.getpixel((0, 0))[3] == 0

    def test_resize_multiple_images(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(200, 200), _make_image(300, 300)]

        pipe.resize(50)
        assert all(img.size == (50, 50) for img in pipe.images)

    def test_resize_returns_self(self):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]
        result = pipe.resize(100)
        assert result is pipe


@pytest.mark.unit
class TestSave:
    def test_save_creates_files(self, tmp_path):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50), _make_image(50, 50)]

        pipe.save("idle", output_dir=str(tmp_path))

        assert (tmp_path / "idle_1.png").exists()
        assert (tmp_path / "idle_2.png").exists()

    def test_save_creates_directory(self, tmp_path):
        out = tmp_path / "new_dir" / "sprites"
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]

        pipe.save("test", output_dir=str(out))
        assert (out / "test_1.png").exists()

    def test_save_default_dir(self, tmp_path):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]

        with patch("scripts.sprite_pipeline.BEHAVIORS_DIR", tmp_path):
            pipe.save("idle")

        assert (tmp_path / "idle" / "sprites" / "idle_1.png").exists()

    def test_save_returns_self(self, tmp_path):
        pipe = SpritePipeline()
        pipe.images = [_make_image(50, 50)]
        result = pipe.save("test", output_dir=str(tmp_path))
        assert result is pipe


@pytest.mark.unit
class TestChaining:
    def test_full_chain(self, tmp_path):
        """Load → split → remove_bg → crop → resize → save works end-to-end."""
        sheet = _make_image(200, 200)
        sheet.save(tmp_path / "sheet.png")

        pipe = (
            SpritePipeline()
            .load(str(tmp_path / "sheet.png"))
            .split(4)
            .remove_bg("none")
            .crop()
            .resize(50)
            .save("test", output_dir=str(tmp_path / "output"))
        )

        assert isinstance(pipe, SpritePipeline)
        assert len(pipe.images) == 4
        for i in range(1, 5):
            assert (tmp_path / "output" / f"test_{i}.png").exists()

    def test_load_process_chain(self, tmp_path):
        """Load individual frames → remove_bg → resize → save."""
        for i in range(3):
            _make_image(200, 200).save(tmp_path / f"frame_{i + 1}.png")

        pipe = (
            SpritePipeline()
            .load(str(tmp_path / "frame_*.png"))
            .remove_bg("none")
            .resize(80)
            .save("walk", output_dir=str(tmp_path / "out"))
        )

        assert len(pipe.images) == 3
        for i in range(1, 4):
            saved = Image.open(tmp_path / "out" / f"walk_{i}.png")
            assert saved.size == (80, 80)


@pytest.mark.unit
class TestCLIArgs:
    def test_generate_required_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--behavior",
                "idle",
                "--frames",
                "4",
                "--reference",
                "ref.png",
                "--prompt",
                "test prompt",
            ]
        )
        assert args.command == "generate"
        assert args.behavior == "idle"
        assert args.frames == 4
        assert args.reference == "ref.png"
        assert args.prompt == "test prompt"

    def test_generate_defaults(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--behavior",
                "idle",
                "--frames",
                "4",
                "--reference",
                "ref.png",
                "--prompt",
                "test",
            ]
        )
        assert args.bg_removal == "none"
        assert args.size == 100
        assert args.rows is None
        assert args.cols is None
        assert args.crop_padding is None
        assert args.verbose is False

    def test_generate_prompt_file(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "generate",
                "--behavior",
                "idle",
                "--frames",
                "4",
                "--reference",
                "ref.png",
                "--prompt-file",
                "prompts/idle.txt",
            ]
        )
        assert args.prompt is None
        assert args.prompt_file == "prompts/idle.txt"

    def test_process_required_args(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "process",
                "--behavior",
                "idle",
                "--input",
                "raw/*.png",
            ]
        )
        assert args.command == "process"
        assert args.behavior == "idle"
        assert args.input == ["raw/*.png"]

    def test_process_with_split(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "process",
                "--behavior",
                "idle",
                "--input",
                "sheet.png",
                "--frames",
                "6",
                "--rows",
                "2",
                "--cols",
                "3",
            ]
        )
        assert args.frames == 6
        assert args.rows == 2
        assert args.cols == 3

    def test_process_multiple_inputs(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "process",
                "--behavior",
                "idle",
                "--input",
                "a.png",
                "b.png",
            ]
        )
        assert args.input == ["a.png", "b.png"]

    def test_crop_padding_arg(self):
        parser = _build_parser()
        args = parser.parse_args(
            [
                "process",
                "--behavior",
                "idle",
                "--input",
                "raw/*.png",
                "--crop-padding",
                "5",
            ]
        )
        assert args.crop_padding == 5
