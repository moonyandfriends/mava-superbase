#!/usr/bin/env python3
"""mava_sync.py — Sync Mava support tickets to Supabase

Run this script periodically (e.g. via Railway cron job) to pull **all** tickets
from the Mava support API and upsert them into a Supabase table called `tickets`.

Environment variables required:
  MAVA_AUTH_TOKEN        → bearer token for the Mava API
  SUPABASE_URL           → https://<your‑project>.supabase.co
  SUPABASE_SERVICE_KEY   → service‑role key with insert/update rights
Optional environment variables:
  PAGE_SIZE              → API page size (default: 50)
  LOG_LEVEL              → Python logging level (default: INFO)

Railway cron schedule: "0 * * * *" (runs every hour)

The Supabase table should have at minimum a primary‑key column `id` matching the
`id` field in each ticket. All other fields will be upserted as received.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from typing import Any

import requests
from dotenv import load_dotenv
from supabase import Client, create_client

# ───────── configuration & setup ─────────
load_dotenv()

MAVA_API_URL = "https://gateway.mava.app/ticket/list"
MAVA_AUTH_TOKEN = os.getenv("MAVA_AUTH_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "50"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
# SYNC_INTERVAL removed - now using Railway cron jobs instead

if not all([MAVA_AUTH_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
    sys.stderr.write(
        "[FATAL] Environment variables MAVA_AUTH_TOKEN, SUPABASE_URL, and "
        "SUPABASE_SERVICE_KEY must be set. Aborting.\n"
    )
    sys.exit(1)

# Type assertion after validation
assert SUPABASE_URL is not None
assert SUPABASE_SERVICE_KEY is not None

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ───────── helpers ─────────


def health_check() -> bool:
    """Basic health check to verify API connectivity."""
    try:
        # Test Supabase connection
        supabase.table("tickets").select("id").limit(1).execute()
        logger.info("Health check passed")
        return True
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return False


def fetch_page(session: requests.Session, skip: int) -> list[dict[str, Any]]:
    """Return a single page of tickets from the Mava API."""
    params = {
        "limit": PAGE_SIZE,
        "skip": skip,
        "sort": "LAST_MODIFIED",
        "order": "DESCENDING",
        "skipEmptyMessages": "true",
    }

    headers = {"Authorization": f"Bearer {MAVA_AUTH_TOKEN}"}

    r = session.get(MAVA_API_URL, params=params, headers=headers, timeout=30)
    r.raise_for_status()

    data = r.json()

    # Adjust this according to the structure Mava returns.
    tickets: list[dict[str, Any]] = data.get("tickets") or data.get("data") or data
    return tickets


def upsert_tickets(tickets: list[dict[str, Any]]) -> None:
    """Bulk upsert a list of ticket dictionaries into Supabase."""
    if not tickets:
        return

    # Supabase upsert (on_conflict=column_name) uses the primary key `id`.
    resp = (
        supabase.table("tickets")
        .upsert(tickets, on_conflict="id", ignore_duplicates=False)
        .execute()
    )
    # Check if response has data (successful upsert)
    if not hasattr(resp, "data") or resp.data is None:
        logger.error("Supabase upsert error: %s", resp)
        raise RuntimeError("Supabase upsert failed")

    logger.info("Upserted %d tickets", len(tickets))


# ───────── main sync loop ─────────


def sync_all_pages() -> None:
    """Sync all pages of tickets from Mava to Supabase."""
    logger.info("Starting Mava → Supabase sync")
    session = requests.Session()
    skip = 0
    total = 0

    while True:
        try:
            page = fetch_page(session, skip)
        except Exception:
            logger.exception("API request failed at skip=%d", skip)
            raise

        if not page:
            break

        upsert_tickets(page)
        total += len(page)
        skip += PAGE_SIZE

    logger.info("Sync complete — %d tickets processed", total)


if __name__ == "__main__":
    # Always run in single-run mode (perfect for Railway cron jobs)
    try:
        # Initial health check
        if not health_check():
            logger.error("Health check failed, exiting")
            sys.exit(1)

        start = datetime.utcnow()
        sync_all_pages()
        duration = (datetime.utcnow() - start).total_seconds()
        logger.info("Finished in %.1fs", duration)
    except Exception:
        logger.exception("Uncaught error — sync aborted")
        sys.exit(1)
