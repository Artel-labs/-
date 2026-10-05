UNKNOWN = "неизвестно"
BROWSERS = (
    ("Edg/", "Edge"),
    ("YaBrowser/", "Яндекс Браузер"),
    ("OPR/", "Opera"),
    ("Firefox/", "Firefox"),
    ("Chrome/", "Chrome"),
    ("Safari/", "Safari"),
)
SYSTEMS = (
    ("Windows", "Windows"),
    ("iPhone", "iOS"),
    ("iPad", "iPadOS"),
    ("Android", "Android"),
    ("Mac OS X", "macOS"),
    ("Linux", "Linux"),
)


def first_match(agent: str, known: tuple[tuple[str, str], ...]) -> str:
    return next((label for marker, label in known if marker in agent), "")


def short_agent(agent: str) -> str:
    parts = [first_match(agent, BROWSERS), first_match(agent, SYSTEMS)]
    return ", ".join(part for part in parts if part) or UNKNOWN
