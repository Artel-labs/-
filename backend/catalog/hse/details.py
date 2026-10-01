import json
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

from catalog.hse.client import is_hse_url
from catalog.hse.text import clean_text

MIN_DESCRIPTION_LENGTH = 40
MAX_ADVANTAGES = 8
MAX_ADMISSION_DOCUMENTS = 10
MIN_ADMISSION_DOCUMENTS = 2
MIN_LIST_ITEM_LENGTH = 4
MDASH_ENTITY = "&mdash;"
EN_DASH = "–"
SITE_WIDE_PDFS = ("1107177138.pdf", "1107177832.pdf")
MODULE_NUMBER = re.compile(r"^\d+[.)]\s*")
RUBLES = re.compile(r"^([\d\s]{3,12})рублей$", re.I)
TAX = re.compile(r"налогов", re.I)
ADMISSION_HEADING = re.compile(r"Документы для (?:приёма|обучения)")
CONTACT_NOISE = re.compile(r"@|телефон|адрес|переулок", re.I)
DISCOUNT = re.compile(r"скидк", re.I)
DISCOUNT_SENTENCE = re.compile(r"^\s*Скидк.{10,300}$", re.S)


@dataclass(frozen=True)
class ModuleData:
    title: str
    hours: str
    topics: list[str]


@dataclass(frozen=True)
class FileData:
    kind: str
    title: str
    size: str
    url: str


@dataclass(frozen=True)
class NoticeData:
    date: str
    text: str
    url: str


@dataclass(frozen=True)
class TeacherData:
    name: str
    about: str
    photo_url: str


@dataclass(frozen=True)
class ReviewData:
    text: str
    author: str


@dataclass(frozen=True)
class FaqData:
    question: str
    answer: str


@dataclass
class ProgramDetails:
    tagline: str = ""
    about: str = ""
    audience_intro: str = ""
    audience: list[str] = field(default_factory=list)
    results: list[str] = field(default_factory=list)
    modules: list[ModuleData] = field(default_factory=list)
    hours: str = ""
    language: str = ""
    schedule: str = ""
    tax_refund: str = ""
    discounts: list[str] = field(default_factory=list)
    admission_documents: list[str] = field(default_factory=list)
    advantages: list[str] = field(default_factory=list)
    files: list[FileData] = field(default_factory=list)
    notice: NoticeData | None = None
    faq: list[FaqData] = field(default_factory=list)
    teachers: list[TeacherData] = field(default_factory=list)
    reviews: list[ReviewData] = field(default_factory=list)
    image_url: str = ""


def text_of(node: Tag | None) -> str:
    return clean_text(node.get_text(" ")) if node else ""


def texts_of(nodes: list[Tag]) -> list[str]:
    return [text for text in (text_of(node) for node in nodes) if text]


def anchored(soup: BeautifulSoup, anchor: str) -> Tag | None:
    mark = soup.find(id=anchor)
    if not isinstance(mark, Tag):
        return None
    if mark.name == "section":
        return mark
    following = mark.find_next("section")
    return following if isinstance(following, Tag) else None


def section(soup: BeautifulSoup, name: str, exclude: str = "") -> Tag | None:
    for node in soup.select(f".dpo-section.{name}"):
        if exclude and exclude in (node.get("class") or []):
            continue
        return node if node.name == "section" else node.find_parent("section") or node
    return None


def audience(soup: BeautifulSoup) -> tuple[str, list[str]]:
    block = section(soup, "dpo-target")
    if not block:
        return "", []
    return text_of(block.select_one(".dpo-target__subtitle")), texts_of(block.select(".dpo-target__feature"))


def is_large_card(card: Tag) -> bool:
    classes = " ".join(card.get("class") or [])
    return "_large" in classes or bool(card.select_one(".dpo-cards__buttons"))


def results(soup: BeautifulSoup) -> list[str]:
    block = section(soup, "dpo-result")
    if not block:
        return []
    found = []
    for card in block.select("li.dpo-cards__item"):
        if is_large_card(card):
            continue
        parts = [text_of(card.select_one(".dpo-cards__title")), text_of(card.select_one(".dpo-cards__text"))]
        text = " ".join(part for part in parts if part)
        if text:
            found.append(text)
    return found


def accordion_items(block: Tag) -> list[Tag]:
    return block.select("li.dpo-program__li")


def modules(soup: BeautifulSoup) -> list[ModuleData]:
    block = section(soup, "dpo-program", exclude="dpo-program_faq")
    if not block:
        return []
    found = []
    for item in accordion_items(block):
        title = MODULE_NUMBER.sub("", text_of(item.select_one(".dpo-program__caption-title")))
        if not title:
            continue
        content = item.select_one(".dpo-program__content")
        topics = texts_of(content.select("li")) if content else []
        found.append(ModuleData(title, text_of(item.select_one(".dpo-program__badge")), topics))
    return found


def format_facts(soup: BeautifulSoup) -> dict[str, str]:
    facts = {"hours": "", "language": "", "schedule": ""}
    block = anchored(soup, "format")
    if not block:
        return facts
    for name in block.select(".dpo-format__term, .dpo-program-card__property-name"):
        value = name.find_next(class_=["dpo-format__value", "dpo-program-card__property-value"])
        label, text = text_of(name).lower(), text_of(value) if isinstance(value, Tag) else ""
        if not text:
            continue
        if "часах" in label:
            facts["hours"] = text
        elif "язык" in label:
            facts["language"] = text
        elif "график" in label:
            facts["schedule"] = text
    return facts


def tax_refund_amount(block: Tag) -> str:
    for item in block.select(".dpo-price__li"):
        amount = RUBLES.match(text_of(item.select_one(".dpo-price__caption")))
        if amount and TAX.search(text_of(item.select_one(".dpo-price__text"))):
            return f"{clean_text(amount.group(1))} рублей"
    return ""


def price_terms(soup: BeautifulSoup) -> tuple[str, list[str]]:
    block = anchored(soup, "price")
    if not block:
        return "", []
    tax_refund = tax_refund_amount(block)
    nodes = block.select(".dpo-price__discount-title, .dpo-price__discount, .dpo-price__text")
    discounts = [text for text in texts_of(nodes) if DISCOUNT.search(text)]
    if not discounts:
        for string in block.find_all(string=DISCOUNT_SENTENCE):
            text = clean_text(str(string))
            if text not in discounts:
                discounts.append(text)
    return tax_refund, discounts


def admission_documents(soup: BeautifulSoup) -> list[str]:
    for heading in soup.find_all(string=ADMISSION_HEADING):
        listing = heading.parent.find_next(["ol", "ul"]) if heading.parent else None
        if not isinstance(listing, Tag):
            continue
        items = [
            text
            for text in texts_of(listing.find_all("li"))
            if len(text) >= MIN_LIST_ITEM_LENGTH and not CONTACT_NOISE.search(text)
        ]
        if len(items) >= MIN_ADMISSION_DOCUMENTS:
            return items[:MAX_ADMISSION_DOCUMENTS]
    return []


def advantages(soup: BeautifulSoup) -> list[str]:
    block = anchored(soup, "advantages")
    if not block:
        return []
    return texts_of(block.select(".dpo-features__text"))[:MAX_ADVANTAGES]


def https_url(raw: str) -> str:
    return raw if raw.startswith("https://") else ""


def notice(soup: BeautifulSoup) -> NoticeData | None:
    block = soup.select_one(".dpo-notice")
    text = text_of(block.select_one(".dpo-notice__text")) if block else ""
    if not block or not text:
        return None
    more = block.select_one(".dpo-notice__more")
    url = https_url(str(more.get("href") or "")) if more else ""
    return NoticeData(text_of(block.select_one(".dpo-notice__date")), text, url)


def faq(soup: BeautifulSoup) -> list[FaqData]:
    block = section(soup, "dpo-program_faq")
    if not block:
        return []
    found = []
    for item in accordion_items(block):
        question = text_of(item.select_one(".dpo-program__caption-title"))
        answer = text_of(item.select_one(".dpo-program__content"))
        if question and answer:
            found.append(FaqData(question, answer))
    return found


def file_kind(title: str) -> str:
    lowered = title.lower()
    if "учебн" in lowered and "план" in lowered:
        return "plan"
    if "расписан" in lowered:
        return "schedule"
    return ""


def files(soup: BeautifulSoup) -> list[FileData]:
    found: list[FileData] = []
    for name in soup.select(".dpo-file__name"):
        link = name.find_parent("a")
        url = str(link.get("href") or "") if link else ""
        if not url.lower().endswith(".pdf") or any(pdf in url for pdf in SITE_WIDE_PDFS) or not is_hse_url(url):
            continue
        size = text_of(name.select_one(".dpo-file__size"))
        for span in name.find_all("span"):
            span.extract()
        title = text_of(name)
        kind = file_kind(title)
        if kind and all(existing.kind != kind for existing in found):
            found.append(FileData(kind, title, size, url))
    return found


def teachers(soup: BeautifulSoup) -> list[TeacherData]:
    found = []
    for slider in soup.select("section.dpo-slider"):
        if not slider.select_one(".dpo-sponsor__img_person"):
            continue
        for card in slider.select("li.dpo-sponsor__card"):
            name = text_of(card.select_one(".dpo-caption"))
            if not name:
                continue
            photo = card.select_one("img.dpo-sponsor__img_person")
            photo_url = str(photo.get("src") or "").strip() if photo else ""
            found.append(TeacherData(name, text_of(card.select_one(".dpo-sponsor__text")), photo_url))
    return found


def reviews(soup: BeautifulSoup) -> list[ReviewData]:
    found = []
    for card in soup.select("li.dpo-feedback"):
        text = text_of(card.select_one(".dpo-feedback__text"))
        author = text_of(card.select_one(".dpo-feedback__author"))
        if text and author:
            found.append(ReviewData(text, author))
    return found


def meta_content(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find("meta", attrs={"property": prop})
    return str(tag.get("content") or "").strip() if isinstance(tag, Tag) else ""


def structured_description(soup: BeautifulSoup) -> str:
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
        except json.JSONDecodeError:
            continue
        for node in data if isinstance(data, list) else [data]:
            if isinstance(node, dict) and node.get("description"):
                return " ".join(str(node["description"]).split())
    return ""


def lead(soup: BeautifulSoup) -> str:
    for node in soup.select(".dpo-program-card__desc"):
        text = text_of(node)
        if len(text) > MIN_DESCRIPTION_LENGTH:
            return text
    block = section(soup, "dpo-about")
    if not block:
        return ""
    content = block.select_one(".dpo-about__content") or block
    for video in content.select(".dpo-video"):
        video.extract()
    text = text_of(content)
    return text if len(text) > MIN_DESCRIPTION_LENGTH else ""


def parse_details(html: str) -> ProgramDetails:
    soup = BeautifulSoup(html.replace(MDASH_ENTITY, EN_DASH), "html.parser")
    intro, audience_items = audience(soup)
    facts = format_facts(soup)
    tax_refund, discounts = price_terms(soup)
    return ProgramDetails(
        tagline=meta_content(soup, "og:description"),
        about=structured_description(soup) or lead(soup),
        audience_intro=intro,
        audience=audience_items,
        results=results(soup),
        modules=modules(soup),
        hours=facts["hours"],
        language=facts["language"],
        schedule=facts["schedule"],
        tax_refund=tax_refund,
        discounts=discounts,
        admission_documents=admission_documents(soup),
        advantages=advantages(soup),
        files=files(soup),
        notice=notice(soup),
        faq=faq(soup),
        teachers=teachers(soup),
        reviews=reviews(soup),
        image_url=meta_content(soup, "og:image"),
    )
