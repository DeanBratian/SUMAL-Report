"""Authenticated HTTP client for sumal-map.ro (see sumal/config.py for the flow)."""

import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from core.logger import Logger
from core.sr_error import SRError
from sumal.config import (
    BASE_URL, LOGIN_PAGE_URL, AUTH_LOGIN_URL, AUTH_USER_URL, USER_COMPANIES_URL
)

XLSX_MAGIC = b"PK"  # .xlsx files are zip archives

class CaptchaRequiredError(SRError):
    """The login form is currently asking for a captcha — cannot proceed headless."""
    def __init__(self):
        super().__init__(
            "SUMAL cere captcha la autentificare (apare de obicei după încercări eșuate).\n"
            "Autentifică-te o dată manual din browser, apoi rulează din nou.",
            title="Eroare captcha SUMAL"
        )

# ---------------------------------------------------------------------- #

class SumalClient:
    """Owns a requests.Session holding the SUMAL cookies. login() must succeed
    before any download; sessions expire after 24h so every run logs in fresh."""

    REQUEST_TIMEOUT = 60  # seconds, applied to every request

    def __init__(self, logger: Logger, username: str, password: str):
        self.logger = logger
        self.username = username
        self.password = password
        self.user_info: dict = {}

        self.session = requests.Session()
        # Present as a regular browser — some gateways reject default python UAs
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) "
                "Gecko/20100101 Firefox/128.0"
            ),
            "Accept-Language": "ro,en;q=0.8",
        })
        # Trace every HTTP exchange (redirect hops included) to the log
        self.session.hooks["response"].append(self._log_http)

        # Unattended runs must survive transient failures (dropped keep-alive
        # connections, gateway hiccups). Every call here is read-only server-side,
        # so retrying POSTs is safe too.
        retry = Retry(
            total=3,
            backoff_factor=2,  # 0s, 2s, 4s between attempts
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    # ---------------------------------------------------------------------- #

    SENSITIVE_FIELDS = ("password", "_csrf", "captcha")

    def _log_http(self, resp: requests.Response, *args, **kwargs) -> None:
        """requests response hook: one log line per HTTP exchange."""
        req = resp.request
        body = ""
        if req.body and "auth/login" not in req.url:
            text = req.body if isinstance(req.body, str) else req.body.decode("utf-8", "replace")
            body = f" body={text[:300]}"
        elif req.body:
            body = " body=<credentials masked>"

        size = len(resp.content or b"") if not resp.is_redirect else 0
        self.logger.debug(
            f"HTTP {req.method} {req.url} -> {resp.status_code} "
            f"({resp.headers.get('Content-Type', '-')}; {size} bytes; "
            f"{resp.elapsed.total_seconds() * 1000:.0f} ms){body}"
        )

    # ---------------------------------------------------------------------- #

    def login(self) -> dict:
        """Perform the full OAuth2 form login. Returns the /auth/user info dict."""
        self.logger.info(f"SUMAL login: starting as '{self.username}'")

        # Step 1-3: land on the /auth/login form (through the authorize redirects)
        resp = self.session.get(LOGIN_PAGE_URL, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()
        html = resp.text

        if self._is_captcha_active(html):
            raise CaptchaRequiredError()

        csrf = self._extract_csrf(html)
        self.logger.debug(f"SUMAL login: got CSRF token, posting credentials to {AUTH_LOGIN_URL}")

        # Step 4-5: post credentials; requests follows the whole redirect chain
        # (authorize -> /login?code=... -> /) and collects the session cookies
        resp = self.session.post(
            AUTH_LOGIN_URL,
            data={"_csrf": csrf, "username": self.username, "password": self.password},
            timeout=self.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()

        # Landing back on the auth form means the credentials were rejected
        if "/auth/login" in resp.url:
            if self._is_captcha_active(resp.text):
                raise CaptchaRequiredError()
            raise SRError(
                "Autentificarea SUMAL a eșuat — utilizator sau parolă greșite.",
                title="Eroare autentificare SUMAL"
            )

        # Step 6: verify the session actually works
        self.user_info = self.get_user_info()
        self.logger.info(
            f"SUMAL login OK: {self.user_info.get('numeUtilizator', '?')} @ "
            f"{self.user_info.get('numeCompanie', '?')} "
            f"(app v{self.user_info.get('appVersion', '?')})"
        )
        return self.user_info

    # ---------------------------------------------------------------------- #

    def get_user_info(self) -> dict:
        """GET /auth/user — raises SRError if the session is not authenticated."""
        resp = self.session.get(AUTH_USER_URL, timeout=self.REQUEST_TIMEOUT)
        if resp.status_code != 200 or "username" not in resp.text:
            self.logger.error(f"SUMAL session check failed: HTTP {resp.status_code} at {resp.url}")
            raise SRError(
                "Sesiunea SUMAL nu este autentificată (verificarea /auth/user a eșuat).",
                title="Eroare sesiune SUMAL"
            )
        return resp.json()

    # ---------------------------------------------------------------------- #

    def get_user_companies(self) -> list[dict]:
        """GET /api/getUserCompanies — company id + idAngajat, needed by data endpoints."""
        resp = self.session.get(USER_COMPANIES_URL, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()
        companies = resp.json()
        self.logger.debug(f"SUMAL companies: {companies}")
        return companies

    # ---------------------------------------------------------------------- #

    def fetch_all_pages(self, url: str, filter_body: dict, sort: str, page_size: int = 100) -> list[dict]:
        """POST a Spring pageable endpoint repeatedly until every page is collected.
        Accepts both paginated ({content, totalElements}) and plain-list responses."""
        items: list[dict] = []
        page = 0
        while True:
            resp = self.session.post(
                url,
                params={"page": page, "size": page_size, "sort": sort},
                json=filter_body,
                timeout=self.REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, list):
                self.logger.debug(f"SUMAL list {url}: plain list, {len(data)} items")
                return data

            content = data.get("content", [])
            items.extend(content)
            total = data.get("totalElements", len(items))
            self.logger.debug(
                f"SUMAL list {url}: page {page}, {len(content)} items, {len(items)}/{total} collected"
            )
            if len(items) >= total or not content:
                return items
            page += 1

    # ---------------------------------------------------------------------- #

    def download_xlsx_export(self, url: str, params: dict, filter_body: dict, dest_path: str) -> None:
        """POST an export endpoint and write the returned .xlsx to dest_path."""
        resp = self.session.post(url, params=params, json=filter_body, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()
        if not resp.content.startswith(XLSX_MAGIC):
            self.logger.error(
                f"SUMAL export {url} did not return an xlsx "
                f"(content-type: {resp.headers.get('Content-Type')}, first bytes: {resp.content[:80]!r})"
            )
            raise SRError(
                f"Exportul SUMAL nu a returnat un fișier Excel valid ({url}).",
                title="Eroare export SUMAL"
            )
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        self.logger.info(f"SUMAL export saved: {dest_path} ({len(resp.content)} bytes)")

    # ---------------------------------------------------------------------- #

    def download_text(self, url: str) -> str:
        """GET a text resource (notice CSV)."""
        resp = self.session.get(url, timeout=self.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _extract_csrf(html: str) -> str:
        match = re.search(r'name="_csrf"\s+value="([^"]+)"', html)
        if not match:
            raise SRError(
                "Pagina de login SUMAL nu conține token-ul CSRF așteptat — "
                "structura site-ului s-a schimbat.",
                title="Eroare pagină login SUMAL"
            )
        return match.group(1)

    # ---------------------------------------------------------------------- #

    @staticmethod
    def _is_captcha_active(html: str) -> bool:
        """The captcha refresh script is always present but dormant; only an actual
        <img id="captchaImg"> / <input name="captcha"> element means it is active."""
        return bool(re.search(r'<img[^>]+captchaImg|<input[^>]+name="captcha', html))

    # ---------------------------------------------------------------------- #

    def close(self) -> None:
        self.session.close()
