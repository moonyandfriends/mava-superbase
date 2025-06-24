#!/usr/bin/env python3
"""
Mava → Supabase Sync Service

Run this script periodically (e.g. via Railway cron job) to pull **all** tickets
from the Mava support API and upsert them into normalized Supabase tables.

Environment variables required:
  MAVA_AUTH_TOKEN        → bearer token for the Mava API
  SUPABASE_URL           → https://<your‑project>.supabase.co
  SUPABASE_SERVICE_KEY   → service‑role key with insert/update rights
Optional environment variables:
  PAGE_SIZE              → API page size (default: 50)
  LOG_LEVEL              → Python logging level (default: INFO)

Railway cron schedule: "0 * * * *" (runs every hour)

This version creates and populates multiple normalized tables:
- tickets: Main ticket information
- customers: Customer profiles and metadata
- messages: Individual ticket messages
- ticket_attributes: Ticket-level attributes
- customer_attributes: Customer-level attributes

Updated: 2025-01-27 - Fixed 400 error in authentication test
"""
from __future__ import annotations

import logging
import os
import sys
import time
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

# Lazy Supabase client creation to avoid import-time failures in tests
_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """Get or create the Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        # We know these are not None due to the validation above
        assert SUPABASE_URL is not None
        assert SUPABASE_SERVICE_KEY is not None
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    return _supabase_client


# ───────── data transformation helpers ─────────


def transform_customer(customer_data: dict[str, Any]) -> dict[str, Any]:
    """Transform customer data for the customers table."""
    return {
        "id": customer_data.get("_id"),
        "discord_author_id": customer_data.get("discordAuthorId"),
        "client": customer_data.get("client"),
        "name": customer_data.get("name"),
        "avatar_url": customer_data.get("avatarURL"),
        "discord_joined_at": customer_data.get("discordJoinedAt"),
        "wallet_address": customer_data.get("walletAddress"),
        "discord_roles": customer_data.get("discordRoles", []),
        "custom_fields": customer_data.get("customFields", []),
        "notes": customer_data.get("notes", []),
        "user_ratings": customer_data.get("userRatings", []),
        "created_at": customer_data.get("createdAt"),
        "updated_at": customer_data.get("updatedAt"),
        "version": customer_data.get("__v"),
        "raw_data": customer_data,
    }


def transform_ticket(ticket_data: dict[str, Any]) -> dict[str, Any]:
    """Transform ticket data for the tickets table."""
    customer = ticket_data.get("customer", {})

    return {
        "id": ticket_data.get("_id"),
        "customer_id": customer.get("_id"),
        "client": ticket_data.get("client"),
        "status": ticket_data.get("status"),
        "priority": ticket_data.get("priority"),
        "source_type": ticket_data.get("sourceType"),
        "category": ticket_data.get("category"),
        "assigned_to": ticket_data.get("assignedTo"),
        # Discord-specific fields
        "discord_thread_id": ticket_data.get("discordThreadId"),
        "interaction_identifier": ticket_data.get("interactionIdentifier"),
        "is_discord_thread_deleted": ticket_data.get("isDiscordThreadDeleted"),
        "discord_users": ticket_data.get("discordUsers", []),
        # AI and automation
        "ai_status": ticket_data.get("aiStatus"),
        "is_ai_enabled_in_flow_root": ticket_data.get("isAIEnabledInFlowRoot"),
        "is_button_in_flow_root_clicked": ticket_data.get(
            "isButtonInFlowRootClicked"
        ),
        "force_button_selection": ticket_data.get("forceButtonSelection"),
        # User interaction
        "is_user_rating_requested": ticket_data.get("isUserRatingRequested"),
        "is_visible": ticket_data.get("isVisible"),
        "mentions": ticket_data.get("mentions", []),
        # Timing information
        "first_customer_message_created_at": ticket_data.get(
            "firstCustomerMessageCreatedAt"
        ),
        "first_agent_message_created_at": ticket_data.get(
            "firstAgentMessageCreatedAt"
        ),
        # Tags (stored as array)
        "tags": ticket_data.get("tags", []),
        # System fields
        "created_at": ticket_data.get("createdAt"),
        "updated_at": ticket_data.get("updatedAt"),
        "version": ticket_data.get("__v"),
        "disabled": ticket_data.get("disabled", False),
        # Raw data preservation
        "raw_data": ticket_data,
    }


def transform_message(message_data: dict[str, Any], ticket_id: str) -> dict[str, Any]:
    """Transform message data for the messages table."""
    return {
        "id": message_data.get("_id"),
        "ticket_id": ticket_id,
        "sender": message_data.get("sender"),
        "sender_reference_type": message_data.get("senderReferenceType"),
        "from_customer": message_data.get("fromCustomer"),
        "content": message_data.get("content"),
        "is_picture": message_data.get("isPicture"),
        "is_read": message_data.get("isRead"),
        "message_type": message_data.get("messageType"),
        "message_status": message_data.get("messageStatus"),
        "is_edited": message_data.get("isEdited"),
        "is_deleted": message_data.get("isDeleted"),
        "read_by": message_data.get("readBy", []),
        "mentions": message_data.get("mentions", []),
        "pre_submission_identifier": message_data.get("preSubmissionIdentifier"),
        "foreign_identifier": message_data.get("foreignIdentifier"),
        "action_log_from": message_data.get("actionLogFrom"),
        "action_log_to": message_data.get("actionLogTo"),
        "replied_to": message_data.get("repliedTo"),
        "client": message_data.get("client"),
        "attachments": message_data.get("attachments", []),
        "reactions": message_data.get("reactions", []),
        "created_at": message_data.get("createdAt"),
        "updated_at": message_data.get("updatedAt"),
        "version": message_data.get("__v"),
        "raw_data": message_data,
    }


def transform_ticket_attributes(ticket_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Transform ticket attributes for the ticket_attributes table."""
    ticket_id = ticket_data.get("_id")
    attributes = ticket_data.get("attributes", [])

    transformed_attributes = []
    for attr in attributes:
        transformed_attributes.append(
            {
                "id": attr.get("_id") or attr.get("id"),
                "ticket_id": ticket_id,
                "attribute": attr.get("attribute"),
                "content": attr.get("content"),
                "raw_data": attr,
            }
        )

    return transformed_attributes


def transform_customer_attributes(
    customer_data: dict[str, Any],
) -> list[dict[str, Any]]:
    """Transform customer attributes for the customer_attributes table."""
    customer_id = customer_data.get("_id")
    attributes = customer_data.get("attributes", [])

    transformed_attributes = []
    for attr in attributes:
        transformed_attributes.append(
            {
                "id": attr.get("_id") or attr.get("id"),
                "customer_id": customer_id,
                "attribute": attr.get("attribute"),
                "content": attr.get("content"),
                "raw_data": attr,
            }
        )

    return transformed_attributes


# ───────── API interaction ─────────


def test_mava_auth() -> bool:
    """Test Mava API authentication with a minimal request."""
    try:
        headers = {
            "Authorization": f"Bearer {MAVA_AUTH_TOKEN}",
            "Content-Type": "application/json",
        }

        # Make a minimal request to test auth
        response = requests.get(
            MAVA_API_URL,
            headers=headers,
            params={"limit": 1, "skip": 0},
            timeout=10,
        )

        if response.status_code == 200:
            logger.info("Mava API authentication successful")
            return True
        elif response.status_code == 401:
            logger.error("Mava API authentication failed: 401 Unauthorized")
            return False
        elif response.status_code == 403:
            logger.error("Mava API authentication failed: 403 Forbidden")
            return False
        else:
            logger.error(
                "Mava API authentication test failed: %d %s",
                response.status_code,
                response.text,
            )
            return False

    except requests.exceptions.RequestException as e:
        logger.error("Mava API connection failed: %s", e)
        return False


def health_check() -> bool:
    """Perform health checks for all dependencies."""
    logger.info("Performing health checks...")

    # Test Mava API authentication
    if not test_mava_auth():
        logger.error("Mava API health check failed")
        return False

    # Test Supabase connection
    try:
        supabase = get_supabase_client()
        # Try a simple query to test connection
        supabase.table("tickets").select("id").limit(1).execute()
        logger.info("Supabase health check successful")
    except Exception as e:
        logger.error("Supabase health check failed: %s", e)
        return False

    logger.info("All health checks passed")
    return True


def fetch_page(session: requests.Session, skip: int) -> list[dict[str, Any]]:
    """Fetch a single page of tickets from the Mava API."""
    headers = {
        "Authorization": f"Bearer {MAVA_AUTH_TOKEN}",
        "Content-Type": "application/json",
    }

    params = {
        "limit": PAGE_SIZE,
        "skip": skip,
    }

    logger.debug("Fetching page: skip=%d, limit=%d", skip, PAGE_SIZE)

    try:
        r = session.get(MAVA_API_URL, headers=headers, params=params, timeout=30)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error("API request failed: %s", e)
        raise

    try:
        data = r.json()
    except ValueError as e:
        logger.error("Failed to parse JSON response: %s", e)
        logger.error("Response text: %s", r.text[:500])
        raise

    # Handle different response structures
    tickets = []
    if isinstance(data, dict):
        if "data" in data:
            tickets = data["data"]
            logger.debug("Found tickets in 'data' field")
        elif "tickets" in data:
            tickets = data["tickets"]
            logger.debug("Found tickets in 'tickets' field")
        elif "results" in data:
            tickets = data["results"]
            logger.debug("Found tickets in 'results' field")
        else:
            logger.warning(
                "Unexpected response structure. Available keys: %s", list(data.keys())
            )
            # Try to find tickets in any array field
            for key, value in data.items():
                if isinstance(value, list) and value and isinstance(value[0], dict):
                    if "_id" in value[0]:  # Likely tickets
                        tickets = value
                        logger.debug("Found tickets in '%s' field", key)
                        break
    elif isinstance(data, list):
        tickets = data
        logger.debug("Response is direct array of tickets")
    else:
        logger.error("Unexpected response type: %s", type(data))
        logger.error("Response data: %s", data)

    logger.debug("Received %d tickets from API (skip=%d)", len(tickets), skip)

    # Log response headers for debugging
    logger.debug("Response headers: %s", dict(r.headers))

    # Check for pagination hints in headers
    if "X-Total-Count" in r.headers:
        total_count = r.headers["X-Total-Count"]
        logger.info("API indicates total count: %s", total_count)

    return tickets


def upsert_to_table(
    table_name: str, records: list[dict[str, Any]], conflict_column: str = "id"
) -> None:
    """Generic upsert function for any table."""
    if not records:
        return

    try:
        supabase = get_supabase_client()
        resp = (
            supabase.table(table_name)
            .upsert(records, on_conflict=conflict_column, ignore_duplicates=False)
            .execute()
        )

        if not hasattr(resp, "data") or resp.data is None:
            logger.error("Supabase upsert error for table %s: %s", table_name, resp)
            raise RuntimeError(f"Supabase upsert failed for table {table_name}")

        logger.info("Upserted %d records to %s table", len(records), table_name)

    except Exception:
        logger.error("Failed to upsert to table %s", table_name)
        # Don't raise the exception to continue with other tables


def process_tickets_batch(tickets: list[dict[str, Any]]) -> None:
    """Process a batch of tickets and upsert to all relevant tables."""
    if not tickets:
        return

    # Collect data for all tables
    customers_data = []
    tickets_data = []
    messages_data = []
    ticket_attributes_data = []
    customer_attributes_data = []

    # Track unique customers to avoid duplicates
    processed_customers = set()

    for ticket in tickets:
        # Process customer data
        customer = ticket.get("customer", {})
        if customer and customer.get("_id"):
            customer_id = customer["_id"]
            if customer_id not in processed_customers:
                customers_data.append(transform_customer(customer))
                processed_customers.add(customer_id)

                # Customer attributes
                customer_attrs = transform_customer_attributes(customer)
                customer_attributes_data.extend(customer_attrs)

        # Process ticket data
        tickets_data.append(transform_ticket(ticket))

        # Process ticket attributes
        ticket_attrs = transform_ticket_attributes(ticket)
        ticket_attributes_data.extend(ticket_attrs)

        # Process messages
        messages = ticket.get("messages", [])
        ticket_id = ticket.get("_id")
        if ticket_id:
            for message in messages:
                messages_data.append(transform_message(message, ticket_id))

    # Upsert to all tables
    # Order matters: customers first, then tickets (which reference customers), then dependent tables
    upsert_to_table("customers", customers_data)
    upsert_to_table("tickets", tickets_data)
    upsert_to_table("messages", messages_data)
    upsert_to_table("ticket_attributes", ticket_attributes_data)
    upsert_to_table("customer_attributes", customer_attributes_data)

    logger.info(
        "Processed batch: %d customers, %d tickets, %d messages, %d ticket attrs, %d customer attrs",
        len(customers_data),
        len(tickets_data),
        len(messages_data),
        len(ticket_attributes_data),
        len(customer_attributes_data),
    )


# ───────── main sync loop ─────────


def sync_all_pages() -> None:
    """Sync all pages of tickets from Mava to Supabase."""
    logger.info("Starting Mava → Supabase sync (multi-table mode)")
    logger.info("Page size: %d", PAGE_SIZE)

    session = requests.Session()
    skip = 0
    total_tickets = 0
    page_count = 0
    consecutive_empty_pages = 0
    max_consecutive_empty = 3  # Stop after 3 consecutive empty pages

    while True:
        page_count += 1
        logger.info(
            "Fetching page %d (skip=%d, total_tickets=%d)",
            page_count,
            skip,
            total_tickets,
        )

        try:
            page = fetch_page(session, skip)
        except Exception:
            logger.exception("API request failed at skip=%d, page=%d", skip, page_count)
            logger.error(
                "Stopping sync due to API error. Total tickets processed: %d",
                total_tickets,
            )
            raise

        if not page:
            consecutive_empty_pages += 1
            logger.warning(
                "Empty page received (consecutive empty pages: %d/%d)",
                consecutive_empty_pages,
                max_consecutive_empty,
            )

            if consecutive_empty_pages >= max_consecutive_empty:
                logger.info(
                    "Stopping sync after %d consecutive empty pages",
                    max_consecutive_empty,
                )
                break
        else:
            consecutive_empty_pages = 0  # Reset counter on successful page
            logger.info("Received %d tickets on page %d", len(page), page_count)

            # Log first and last ticket IDs for debugging
            if page:
                first_ticket_id = page[0].get("_id", "unknown")
                last_ticket_id = page[-1].get("_id", "unknown")
                logger.debug(
                    "Page %d ticket range: %s to %s",
                    page_count,
                    first_ticket_id,
                    last_ticket_id,
                )

        if not page:
            break

        process_tickets_batch(page)
        total_tickets += len(page)
        skip += PAGE_SIZE

        # Add a small delay to avoid rate limiting
        time.sleep(0.1)

    logger.info(
        "Sync complete — %d tickets processed across %d pages", total_tickets, page_count
    )

    # Log final statistics
    if total_tickets > 0:
        logger.info("Average tickets per page: %.1f", total_tickets / page_count)

    # Warn if we got suspiciously few tickets
    if total_tickets < 1000 and page_count < 20:
        logger.warning("Low ticket count detected. This might indicate:")
        logger.warning("1. API rate limiting")
        logger.warning("2. Authentication issues")
        logger.warning("3. API response format changes")
        logger.warning("4. Network connectivity issues")


if __name__ == "__main__":
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
