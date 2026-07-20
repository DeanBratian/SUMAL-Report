"""Syncs SUMAL's reference catalog into the local database.

The site is the single source of truth for species (specii + grupe specii),
good types (sortimente) and operation types — fetched from the catalog
endpoints and upserted, so re-syncing is always safe.
"""

import sqlite3
from datetime import datetime, timezone

from core.logger import Logger
from sumal.client import SumalClient
from sumal.config import EP_SORTIMENTE, EP_SPECII, EP_TIP_OPERATIUNI

def sync_catalog(client: SumalClient, conn: sqlite3.Connection, logger: Logger) -> dict[str, int]:
    """Fetch the three catalog lists and upsert them. Returns per-table counts."""
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    sortimente = client.session.get(EP_SORTIMENTE, timeout=client.REQUEST_TIMEOUT).json()
    specii = client.session.get(EP_SPECII, timeout=client.REQUEST_TIMEOUT).json()
    operatiuni = client.session.get(EP_TIP_OPERATIUNI, timeout=client.REQUEST_TIMEOUT).json()

    with conn:
        conn.executemany(
            "INSERT INTO catalog_sortiment (id_sortiment, nume, cod, status, synced_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(id_sortiment) DO UPDATE SET "
            "nume=excluded.nume, cod=excluded.cod, status=excluded.status, synced_at=excluded.synced_at",
            [
                (s["idSortiment"], s["numeSortiment"].strip(), s.get("codSortiment"),
                 int(bool(s.get("statusSortiment", True))), now)
                for s in sortimente
            ],
        )
        conn.executemany(
            "INSERT INTO catalog_specie (id_specie, nume, cod, id_parinte, nume_parinte, nivel, status, synced_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id_specie) DO UPDATE SET "
            "nume=excluded.nume, cod=excluded.cod, id_parinte=excluded.id_parinte, "
            "nume_parinte=excluded.nume_parinte, nivel=excluded.nivel, "
            "status=excluded.status, synced_at=excluded.synced_at",
            [
                (s["idSpecie"], s["numeSpecie"].strip(), s.get("codSpecie"),
                 s.get("idParinte"), (s.get("numeParinte") or "").strip() or None,
                 s.get("nivel"), int(bool(s.get("statusSpecie", True))), now)
                for s in specii
            ],
        )
        conn.executemany(
            "INSERT INTO catalog_tip_operatiune (cod, nume, are_iesiri, status, synced_at) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(cod) DO UPDATE SET "
            "nume=excluded.nume, are_iesiri=excluded.are_iesiri, "
            "status=excluded.status, synced_at=excluded.synced_at",
            [
                (o["codTipOperatiune"], o["numeTipOperatiune"].strip(),
                 int(bool(o.get("areIesiri", False))),
                 int(bool(o.get("statusTipOperatiune", True))), now)
                for o in operatiuni
            ],
        )

    counts = {
        "sortimente": len(sortimente),
        "specii (grupe + specii)": len(specii),
        "tipuri operatiuni": len(operatiuni),
    }
    logger.info(f"Catalog synced: {counts}")
    _log_catalog(specii, sortimente, operatiuni, logger)
    return counts

# ---------------------------------------------------------------------- #

def _log_catalog(specii: list[dict], sortimente: list[dict], operatiuni: list[dict], logger: Logger) -> None:
    """Write the full catalog contents to the logfile, grouped and readable."""
    groups = sorted(
        (s for s in specii if s.get("nivel") == 0),
        key=lambda s: s["numeSpecie"]
    )
    logger.info(
        "Catalog - grupe de specii (%d): %s" % (
            len(groups),
            ", ".join(f"{g['numeSpecie'].strip()} ({g.get('codSpecie')})" for g in groups)
        )
    )
    for group in groups:
        members = sorted(
            (s["numeSpecie"].strip() for s in specii if s.get("idParinte") == group["idSpecie"]),
        )
        logger.info(f"Catalog - {group['numeSpecie'].strip()} ({len(members)} specii): {', '.join(members)}")

    logger.info(
        "Catalog - sortimente (%d): %s" % (
            len(sortimente),
            ", ".join(
                f"{s['numeSortiment'].strip()} ({s.get('codSortiment')})"
                for s in sorted(sortimente, key=lambda x: x["idSortiment"])
            )
        )
    )
    logger.info(
        "Catalog - tipuri operatiuni (%d): %s" % (
            len(operatiuni),
            ", ".join(
                o["numeTipOperatiune"].strip() + (" [are iesiri]" if o.get("areIesiri") else "")
                for o in sorted(operatiuni, key=lambda x: x["codTipOperatiune"])
            )
        )
    )
