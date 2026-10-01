import base64
from urllib.parse import quote, urlsplit

from catalog.hse.client import is_hse_url

CART_URL = "https://www.hse.ru/edu/dpo/{hse_id}?action=cart"
GATEWAY_URL = "https://www.hse.ru/mirror/co-auth/elk/gateway.html?ext=marketplace&i=*{token}"
URI_COMPONENT_SAFE = "!~*'()"
SIGNIN_URL = "https://lk.hse.ru/signin?redirecturl={target}&systemid=27"


def pay_url(hse_id: str) -> str:
    if not hse_id.isdigit():
        return ""
    token = base64.b64encode(CART_URL.format(hse_id=hse_id).encode()).decode()
    return SIGNIN_URL.format(target=quote(GATEWAY_URL.format(token=token), safe=URI_COMPONENT_SAFE))


def safe_hse_url(url: str) -> str:
    return url if url and is_hse_url(url) else ""


def host_label(url: str) -> str:
    host = urlsplit(url).hostname or ""
    return host.removeprefix("www.")
