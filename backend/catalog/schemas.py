from ninja import Schema


class SphereOut(Schema):
    slug: str
    title: str


class CoverOut(Schema):
    src: str
    srcset: str
    webp_srcset: str
    width: int
    height: int
    alt: str


class AboutOut(Schema):
    lead: str
    body: str
    items: list[str]


class AudienceOut(Schema):
    intro: str
    items: list[str]


class ModuleOut(Schema):
    title: str
    hours: str
    topics: list[str]


class FileOut(Schema):
    label: str
    size: str
    url: str


class TeacherOut(Schema):
    name: str
    about: str
    page_url: str


class ReviewOut(Schema):
    text: str
    author: str


class FaqOut(Schema):
    question: str
    answer: str


class NoticeOut(Schema):
    date: str
    text: str
    url: str
    host: str


class FactOut(Schema):
    label: str
    value: str


class CredentialOut(Schema):
    tag: str
    name: str
    note: str


class SiblingOut(Schema):
    title: str
    path: str


class SiblingsOut(Schema):
    sphere_title: str
    count_label: str
    items: list[SiblingOut]


class ProgramPageOut(Schema):
    hse_id: str
    title: str
    path: str
    canonical_url: str
    page_title: str
    description: str
    image_url: str
    structured_data: list[str]
    crumb: str
    chips: list[str]
    cover: CoverOut | None
    notice: NoticeOut | None
    about: AboutOut | None
    audience: AudienceOut | None
    results: list[str]
    advantages: list[str]
    modules: list[ModuleOut]
    modules_label: str
    files: list[FileOut]
    teachers_heading: str
    teachers: list[TeacherOut]
    reviews: list[ReviewOut]
    admission_documents: list[str]
    faq: list[FaqOut]
    siblings: SiblingsOut | None
    price: str
    price_terms: list[str]
    facts: list[FactOut]
    pay_url: str
    hse_url: str
    credential: CredentialOut | None


class ThumbOut(Schema):
    src: str
    webp: str
    alt: str


class TagOut(Schema):
    kind: str
    text: str
    tip: str


class CompareOut(Schema):
    format: str
    duration: str
    start: str
    modules: str
    teachers: int
    audience: str


class CardOut(Schema):
    hse_id: str
    title: str
    path: str
    type_short: str
    format: str
    sphere: str
    sphere_title: str
    duration: str
    price_sort: int
    start_sort: int
    title_sort: str
    search: str
    thumb: ThumbOut | None
    tags: list[TagOut]
    start: str
    price: str
    compare: CompareOut


class ChipOut(Schema):
    label: str
    value: str
    active: bool


class FiltersOut(Schema):
    type: list[ChipOut]
    format: list[ChipOut]
    sphere: list[ChipOut]
    duration: list[ChipOut]


class MonthOut(Schema):
    label: str
    count: int
    left: int
    width: int
    scroll: int


class TickOut(Schema):
    left: int
    kind: str


class StartOut(Schema):
    lane: str
    left: int
    pin: int
    path: str
    hint: str
    when: str
    title: str
    sphere: str
    meta: str
    price: str


class StartsOut(Schema):
    width: int
    months: list[MonthOut]
    ticks: list[TickOut]
    today: int | None
    items: list[StartOut]


class CatalogPageOut(Schema):
    total: int
    canonical_url: str
    image_url: str
    filters: FiltersOut
    cards: list[CardOut]
    starts: StartsOut | None
    structured_data: str


class ProgramOptionOut(Schema):
    id: str
    title: str
    url: str
    sphere: str


class SitemapEntryOut(Schema):
    loc: str
    changefreq: str
    priority: str


class BotProgramOut(Schema):
    id: str
    title: str
    url: str
    sphere: str
    type: str
    format: str
    format_label: str
    price: int | None
    price_label: str
    duration: str | None
    hours: str | None
    schedule: str | None
    start: str | None
    start_iso: str | None
    keywords: list[str]
