"""sumal-map.ro endpoints and credential loading.

Authentication flow (captured from browser traffic, 2026-07-19, app v2.7.6.4):
  1. GET  /login                  -> 302 to /auth/oauth/authorize?client_id=sumal&...
  2. GET  /auth/oauth/authorize   -> 302 to /auth/login (not yet authenticated)
  3. GET  /auth/login             -> HTML form with hidden _csrf token
  4. POST /auth/login             -> form fields: _csrf, username, password
                                     (+ captcha field when the server demands it)
  5. 302 chain: /auth/oauth/authorize -> /login?code=...&state=... -> /
     The authorization code is exchanged server-side; the session is carried by
     the SESSION cookie (path "/") set on the final redirect.
  6. GET  /auth/user              -> 200 JSON => authenticated
"""

import json
import os

BASE_URL = "https://sumal-map.ro"
LOGIN_PAGE_URL = f"{BASE_URL}/login"
AUTH_LOGIN_URL = f"{BASE_URL}/auth/login"
AUTH_USER_URL = f"{BASE_URL}/auth/user"
USER_COMPANIES_URL = f"{BASE_URL}/api/getUserCompanies"

# Session cookies expire after 24h (Max-Age=86400) — every run logs in fresh.

# Data endpoints (mapped from HAR captures, 2026-07-09; CSV export live-proven).
# All /agent/api list endpoints are Spring pageables: POST with a JSON filter
# body and page/size/sort query params, responding {content, totalElements, ...}.
EP_AVIZE_FILTER = f"{BASE_URL}/agent/api/findAllAvizFiltrare"   # body: {"deLa": "dd-MM-yyyy", "panaLa": ...}
EP_AVIZE_EXPORT = f"{BASE_URL}/agent/api/exportAvizElectronic"  # -> Aviz .xlsx
EP_AVIZ_CSV = f"{BASE_URL}/agent/api/aviz/V2/export-csv/{{id_aviz}}"  # GET -> notice CSV
EP_INTRARI_FILTER = f"{BASE_URL}/agent/api/intrari/filter"      # body: {dataInceput, dataSfarsit, idDepozit}
EP_INTRARI_EXPORT = f"{BASE_URL}/agent/api/intrari/export"      # -> Intrari .xlsx
EP_DEPOZITE_LIST = f"{BASE_URL}/agent/api/getDepoziteByCurrentCompany"
EP_DEPOZITE_EXPORT = f"{BASE_URL}/agent/api/exportDepozite"     # -> Depozite .xlsx

# Catalog endpoints — SUMAL's official reference data (GET, no body)
EP_SORTIMENTE = f"{BASE_URL}/agent/api/findSortimentByStatusActive"
EP_SPECII = f"{BASE_URL}/agent/api/findSpecieByStatusActive"    # full tree: groups (nivel 0) + species (nivel 1)
EP_TIP_OPERATIUNI = f"{BASE_URL}/agent/api/tipOperatiuni"

API_DATE_FORMAT = "%d-%m-%Y"  # date format in JSON filter bodies

# The company's principal deposit — all Intrari filters/exports are scoped to it
PRINCIPAL_DEPOSIT_ID = int(os.environ.get("SUMAL_PRINCIPAL_DEPOSIT_ID", "7230"))  # VALENII DE MURES 95

SECRETS_FILENAME = "secrets.local.json"

# ---------------------------------------------------------------------- #

def load_credentials(project_root: str) -> tuple[str, str]:
    """Resolve SUMAL credentials: environment variables take precedence,
    then the git-ignored secrets.local.json next to the project root."""
    username = os.environ.get("SUMAL_USERNAME", "")
    password = os.environ.get("SUMAL_PASSWORD", "")
    if username and password:
        return username, password

    secrets_path = os.path.join(project_root, SECRETS_FILENAME)
    if os.path.exists(secrets_path):
        with open(secrets_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        username = data.get("username", "")
        password = data.get("password", "")
        if username and password:
            return username, password

    from core.sr_error import SRError
    raise SRError(
        "Lipsesc credențialele SUMAL.\n"
        "Setează variabilele de mediu SUMAL_USERNAME / SUMAL_PASSWORD\n"
        f"sau creează fișierul {SECRETS_FILENAME} cu: "
        '{"username": "...", "password": "..."}',
        title="Eroare credențiale SUMAL"
    )
