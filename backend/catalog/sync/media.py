from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image

from catalog.hse.client import HseClient, HseError
from catalog.models import FileKind, Program, ProgramFile, Teacher
from catalog.slugs import slugify

MAX_PDF_BYTES = 4 * 1024 * 1024
PDF_SIGNATURE = b"%PDF"
TEACHER_PHOTO_WIDTH = 160
JPEG_QUALITY = 82
IMAGE_EXTENSIONS = {"image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png", "image/webp": "webp"}


def content_type(raw: str) -> str:
    return raw.split(";")[0].strip().lower()


def fetch_image(client: HseClient, url: str) -> tuple[bytes, str]:
    response = client.get(url, "image/*")
    extension = IMAGE_EXTENSIONS.get(content_type(response.headers.get("content-type", "")))
    if not extension or not response.content:
        raise HseError(f"Не картинка: {url}")
    return response.content, extension


def fetch_pdf(client: HseClient, url: str) -> bytes:
    response = client.get(url, "application/pdf")
    body = response.content
    is_pdf = content_type(response.headers.get("content-type", "")) == "application/pdf"
    if not is_pdf or not body.startswith(PDF_SIGNATURE):
        raise HseError(f"Не PDF: {url}")
    if len(body) > MAX_PDF_BYTES:
        raise HseError(f"Слишком большой PDF ({len(body)} байт): {url}")
    return body


def shrink_to_jpeg(raw: bytes, width: int) -> bytes:
    with Image.open(BytesIO(raw)) as image:
        picture = image.convert("RGB")
        if picture.width > width:
            picture = picture.resize((width, round(picture.height * width / picture.width)), Image.Resampling.LANCZOS)
        output = BytesIO()
        picture.save(output, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()


def ensure_cover(client: HseClient, program: Program, url: str) -> bool:
    if program.image or not url:
        return False
    body, extension = fetch_image(client, url)
    program.image.save(f"{program.hse_id}.{extension}", ContentFile(body))
    return True


def ensure_teacher_photo(client: HseClient, teacher: Teacher, url: str) -> bool:
    if teacher.photo or not url:
        return False
    body, _ = fetch_image(client, url)
    teacher.photo.save(f"{slugify(teacher.name)}.jpg", ContentFile(shrink_to_jpeg(body, TEACHER_PHOTO_WIDTH)))
    return True


def refresh_document(client: HseClient, document: ProgramFile) -> bool:
    if document.file and document.kind != FileKind.SCHEDULE:
        return False
    body = fetch_pdf(client, document.source_url)
    document.file.delete(save=False)
    document.file.save(f"{document.program.hse_id}-{document.kind}.pdf", ContentFile(body))
    return True
