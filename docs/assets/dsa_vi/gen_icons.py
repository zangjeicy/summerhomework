#!/usr/bin/env python3
"""
Generate .ico files from source PNG. Uses largest available from iconset or source.
Legacy icons keep their original sizes; the browser favicon adds 48px.
"""
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Pillow required: pip install Pillow")

ICON_DIR = Path(__file__).parent
LEGACY_SIZES = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512)]
FAVICON_SIZES = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]


def make_ico(name: str, source: Path, sizes=LEGACY_SIZES) -> None:
    """Create multi-resolution .ico from source image."""
    img = Image.open(source).convert("RGBA")
    out = ICON_DIR / f"{name}.ico"
    img.save(out, format="ICO", sizes=sizes)
    print(f"Created {out}")


def main() -> None:
    for name in ("darklogo", "lightlogo"):
        src = ICON_DIR / f"{name}.png"
        if src.exists():
            make_ico(name, src)
        else:
            print(f"Skip {name}: {src} not found")

    brand_icon = ICON_DIR / "icon-512.png"
    if brand_icon.exists():
        make_ico("favicon", brand_icon, FAVICON_SIZES)
    else:
        print(f"Skip favicon: {brand_icon} not found")


if __name__ == "__main__":
    main()
