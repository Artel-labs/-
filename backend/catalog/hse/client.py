from types import TracebackType
from urllib.parse import urlsplit

import httpx

USER_AGENT = "Mozilla/5.0 (compatible; dpo-pravo-hse/2.0; +https://pravo.hse.ru/dpo)"
TIMEOUT_SECONDS = 20
HSE_DOMAIN = "hse.ru"


class HseError(RuntimeError):
    pass


def is_hse_url(url: str) -> bool:
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    return parts.scheme == "https" and (host == HSE_DOMAIN or host.endswith(f".{HSE_DOMAIN}"))


class HseClient:
    def __init__(self, transport: httpx.BaseTransport | None = None) -> None:
        self._http = httpx.Client(
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
            follow_redirects=True,
            transport=transport,
        )

    def __enter__(self) -> "HseClient":
        return self

    def __exit__(
        self, kind: type[BaseException] | None, error: BaseException | None, trace: TracebackType | None
    ) -> None:
        self._http.close()

    def get(self, url: str, accept: str) -> httpx.Response:
        if not is_hse_url(url):
            raise HseError(f"Адрес не на hse.ru: {url}")
        response = self._http.get(url, headers={"Accept": accept})
        if not is_hse_url(str(response.url)):
            raise HseError(f"hse.ru перенаправил на чужой адрес: {response.url}")
        if response.is_error:
            raise HseError(f"hse.ru ответил {response.status_code} на {url}")
        return response

    def html(self, url: str) -> str:
        return self.get(url, "text/html").text
