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
