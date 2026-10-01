from dataclasses import dataclass
from pathlib import Path

from django.conf import settings
from PIL import Image

from catalog.models import Program

THUMB_WIDTH = 640
JPEG_QUALITY = 80
WEBP_QUALITY = 80
THUMBS_DIR = "programs/thumbs"


@dataclass(frozen=True)
class Cover:
    src: str
    srcset: str
    webp_srcset: str
    width: int
    height: int
    alt: str


def media_url(relative: str) -> str:
    return f"{settings.MEDIA_URL}{relative}"


def is_fresh(target: Path, source: Path) -> bool:
    return target.exists() and target.stat().st_mtime >= source.stat().st_mtime


def save_variant(source: Path, target: Path, width: int | None, image_format: str, quality: int) -> None:
    if is_fresh(target, source):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        picture = image.convert("RGB")
        if width and picture.width > width:
            picture = picture.resize((width, round(picture.height * width / picture.width)), Image.Resampling.LANCZOS)
        picture.save(target, image_format, quality=quality)


@dataclass(frozen=True)
class Variants:
    thumb: str
    thumb_webp: str
    full_webp: str
    width: int
    height: int


@dataclass(frozen=True)
class Thumb:
    src: str
    webp: str
    alt: str


def cover_alt(program: Program) -> str:
    return f"Обложка программы «{program.title}»"


def variants(program: Program) -> Variants | None:
    if not program.image:
        return None
    source = Path(program.image.path)
    if not source.exists():
        return None
    root = Path(settings.MEDIA_ROOT)
    stem = program.hse_id
    thumb, thumb_webp = f"{THUMBS_DIR}/{stem}.jpg", f"{THUMBS_DIR}/{stem}.webp"
    full_webp = f"{Path(program.image.name).with_suffix('.webp')}"
    save_variant(source, root / thumb, THUMB_WIDTH, "JPEG", JPEG_QUALITY)
    save_variant(source, root / thumb_webp, THUMB_WIDTH, "WEBP", WEBP_QUALITY)
    if full_webp != program.image.name:
        save_variant(source, root / full_webp, None, "WEBP", WEBP_QUALITY)
    with Image.open(root / thumb) as image:
        width, height = image.size
    return Variants(thumb, thumb_webp, full_webp, width, height)


def cover(program: Program) -> Cover | None:
    found = variants(program)
    if found is None:
        return None
    return Cover(
        src=media_url(found.thumb),
        srcset=f"{media_url(found.thumb)} 1x, {program.image.url} 2x",
        webp_srcset=f"{media_url(found.thumb_webp)} 1x, {media_url(found.full_webp)} 2x",
        width=found.width,
        height=found.height,
        alt=cover_alt(program),
    )


def thumb(program: Program) -> Thumb | None:
    found = variants(program)
    if found is None:
        return None
    return Thumb(src=media_url(found.thumb), webp=media_url(found.thumb_webp), alt=cover_alt(program))
