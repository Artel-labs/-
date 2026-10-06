from ninja import Schema


class LinkOut(Schema):
    href: str
    title: str


class MenuSphereOut(Schema):
    href: str
    title: str
    count: str
    programs: list[LinkOut]
    more: LinkOut | None


class MenuOut(Schema):
    spheres: list[MenuSphereOut]
    total: int


class SphereCardOut(Schema):
    slug: str
    href: str
    index: str
    title: str
    lead: str
    facts: list[str]


class FormatDocOut(Schema):
    file: str
    ext: str
    height: int
    name: str


class FormatStatOut(Schema):
    key: str
    value: str


class FormatCtaOut(Schema):
    href: str
    label: str
    external: bool
    application: bool


class FormatOut(Schema):
    step: int
    index: str
    title: str
    desc: str
    document: str
    doc: FormatDocOut | None
    stats: list[FormatStatOut]
    start: str
    count: str
    cta: FormatCtaOut


class TeacherProgramOut(Schema):
    t: str
    h: str


class TeacherPayloadOut(Schema):
    name: str
    about: str
    programs: list[TeacherProgramOut]
    url: str


class TeacherPhotoOut(Schema):
    src: str
    webp: str
    alt: str


class TeacherCardOut(Schema):
    payload: str
    initials: str
    photo: TeacherPhotoOut | None
    name: str
    page: str
    more_label: str
    count: str
    about: str


class StartStripOut(Schema):
    path: str
    label: str
    big: str
    small: str
    is_month: bool
    title: str


class ReviewCardOut(Schema):
    text: str
    author: str
    path: str
    program: str


class TopProgramOut(Schema):
    image: str
    image_webp: str
    id: str
    start: str
    title: str
    kind: str
    format: str
    format_tip: str
    doc: str
    doc_tip: str
    duration: str
    path: str


class LandingOut(Schema):
    canonical_url: str
    branches: list[str]
    image_url: str
    menu: MenuOut
    spheres: list[SphereCardOut]
    formats: list[FormatOut]
    teachers: list[TeacherCardOut]
    starts: list[StartStripOut]
    reviews: list[ReviewCardOut]
    top: list[TopProgramOut]
