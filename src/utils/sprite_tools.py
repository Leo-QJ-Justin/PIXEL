"""Sprite conversion utilities (PNG sequence -> animated GIF)."""

from pathlib import Path


def pngs_to_gif(
    png_paths: list[Path], output_path: Path, frame_duration_ms: int = 500, loop: bool = True
) -> None:
    """Convert a sequence of PNG files to an animated GIF with transparency."""
    from PIL import Image

    frames = [Image.open(p).convert("RGBA") for p in png_paths]

    gif_frames = []
    for frame in frames:
        alpha = frame.split()[3]
        p_frame = frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=255)
        mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
        p_frame.paste(255, mask)
        gif_frames.append(p_frame)

    save_kwargs = {
        "save_all": True,
        "append_images": gif_frames[1:],
        "duration": frame_duration_ms,
        "transparency": 255,
        "disposal": 2,
    }
    if loop:
        save_kwargs["loop"] = 0  # loop forever

    gif_frames[0].save(output_path, **save_kwargs)
