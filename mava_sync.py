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
        "is_button_in_flow_root_clicked": ticket_data.get("isButtonInFlowRootClicked"),
        "force_button_selection": ticket_data.get("forceButtonSelection"),
        # User interaction
        "is_user_rating_requested": ticket_data.get("isUserRatingRequested"),
        "is_visible": ticket_data.get("isVisible"),
        "mentions": ticket_data.get("mentions", []),
        # Timing information
        "first_customer_message_created_at": ticket_data.get(
            "firstCustomerMessageCreatedAt"
        ),
        "first_agent_message_created_at": ticket_data.get("firstAgentMessageCreatedAt"),
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


# ───────── core sync functions ─────────


def test_mava_auth() -> bool:
    """Test Mava API authentication."""
    try:
        session = requests.Session()
        headers = {"X-Auth-Token": MAVA_AUTH_TOKEN}

        # Use the same parameters as fetch_page to avoid 400 errors
        params: dict[str, str | int] = {
            "limit": 10,  # API requires limit >= 10
            "skip": 0,
            "sort": "LAST_MODIFIED",
            "order": "DESCENDING",
            "skipEmptyMessages": "true",
        }

        # Make a minimal request to test authentication
        r = session.get(MAVA_API_URL, params=params, headers=headers, timeout=10)

        if r.status_code == 200:
            logger.info("Mava API authentication successful")
            return True
        elif r.status_code == 400:
            logger.error(
                "Mava API bad request (400): Invalid parameters or request format"
            )
            logger.error("Response body: %s", r.text)
            logger.error("Request URL: %s", r.url)
            logger.error("Request headers: %s", dict(r.request.headers))
            return False
        elif r.status_code == 401:
            logger.error("Mava API authentication failed: Invalid or expired token")
            logger.error("Please check your MAVA_AUTH_TOKEN environment variable")
            logger.error("Response body: %s", r.text)
            return False
        elif r.status_code == 403:
            logger.error("Mava API access forbidden: Insufficient permissions")
            logger.error("Response body: %s", r.text)
            return False
        else:
            logger.error("Mava API test failed with status code: %d", r.status_code)
            logger.error("Response body: %s", r.text)
            return False

    except Exception as e:
        logger.error("Mava API authentication test failed: %s", e)
        return False


def health_check() -> bool:
    """Basic health check to verify API connectivity."""
    try:
        # Test Supabase connection with main tables
        supabase = get_supabase_client()
        supabase.table("mava_tickets").select("id").limit(1).execute()
        logger.info("Supabase health check passed")

        # Test Mava API authentication
        if not test_mava_auth():
            logger.error("Mava API health check failed")
            return False

        logger.info("Health check passed")
        return True
    except Exception as e:
        logger.error("Health check failed: %s", e)
        return False


def check_existing_tickets() -> None:
    """Check how many tickets currently exist in Supabase."""
    try:
        supabase = get_supabase_client()
        # Get count of existing tickets
        result = supabase.table("mava_tickets").select("id").execute()
        ticket_count = len(result.data) if result.data else 0

        # Get count of existing customers
        customer_result = supabase.table("mava_customers").select("id").execute()
        customer_count = len(customer_result.data) if customer_result.data else 0

        logger.info(
            "Current Supabase state: %d tickets, %d customers",
            ticket_count,
            customer_count,
        )

        # Get some recent tickets for reference
        recent_tickets = (
            supabase.table("mava_tickets")
            .select("id,status,created_at")
            .order("created_at", desc=True)
            .limit(5)
            .execute()
        )
        if recent_tickets.data:
            logger.info("Recent tickets in database:")
            for ticket in recent_tickets.data:
                logger.info(
                    "  - %s: %s (created: %s)",
                    ticket.get("id"),
                    ticket.get("status"),
                    ticket.get("created_at"),
                )

    except Exception as e:
        logger.error("Failed to check existing tickets: %s", e)


def fetch_team_members(session: requests.Session) -> list[dict[str, Any]]:
    """Fetch team members from the Mava API."""
    from datetime import datetime, timezone

    # Get current timestamp in ISO format
    current_time = datetime.now(timezone.utc).isoformat()

    params: dict[str, str | int] = {
        "filterVersion": "3",
        "filterLastUpdated": current_time,
    }

    # Mava API uses cookie-based authentication, not Bearer token
    cookies: dict[str, str] = {"x-auth-token": MAVA_AUTH_TOKEN or ""}
    headers = {
        "User-Agent": "Mava-Supabase-Sync/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    logger.debug("Fetching team members from Mava API")
    logger.debug(
        "Using token: %s...", MAVA_AUTH_TOKEN[:10] if MAVA_AUTH_TOKEN else "None"
    )

    try:
        r = session.get("https://gateway.mava.app/team/members", params=params, headers=headers, cookies=cookies, timeout=30)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("401 Unauthorized - Check your MAVA_AUTH_TOKEN")
            logger.error(
                "Token starts with: %s",
                MAVA_AUTH_TOKEN[:10] if MAVA_AUTH_TOKEN else "None",
            )
            logger.error("Response body: %s", e.response.text)
        elif e.response.status_code == 403:
            logger.error(
                "403 Forbidden - Token may be expired or insufficient permissions"
            )
            logger.error("Response body: %s", e.response.text)
        else:
            logger.error("HTTP %d error: %s", e.response.status_code, e.response.text)
        raise

    data = r.json()

    # Log response structure for debugging
    logger.debug(
        "Team members API response type: %s",
        type(data).__name__
    )

    # Handle different response formats
    if isinstance(data, list):
        members = data
    else:
        members = data.get("members") or data.get("data") or []

    logger.debug("Retrieved %d team members from API", len(members))

    # Pause between API calls
    time.sleep(5)

    return members


def transform_team_member(member_data: dict[str, Any]) -> dict[str, Any]:
    """Transform team member data for Supabase storage."""
    return {
        "id": member_data.get("_id"),
        "name": member_data.get("name"),
        "email": member_data.get("email"),
        "type": member_data.get("type"),
        "client": member_data.get("client"),
        "is_archived": member_data.get("isArchived", False),
        "is_custom_signature_enabled": member_data.get("isCustomSignatureEnabled", False),
        "is_sound_notification_enabled": member_data.get("isSoundNotificationEnabled", False),
        "is_email_verified": member_data.get("isEmailVerified", False),
        "avatar": member_data.get("avatar"),
        "custom_signature": member_data.get("customSignature"),
        "user_ratings": member_data.get("userRatings", []),
        "pinned_attributes": member_data.get("pinnedAttributes", []),
        "filter_configurations": member_data.get("filterConfigurations", []),
        "master_notifications": member_data.get("masterNotifications", {}),
        "device_token": member_data.get("deviceToken", []),
        "notifications": member_data.get("notifications", []),
        "two_factor_auth": member_data.get("twoFactorAuth", {}),
        "created_at": member_data.get("createdAt"),
        "updated_at": member_data.get("updatedAt"),
        "version": member_data.get("__v", 0),
        "raw_data": member_data
    }


def fetch_client_data(session: requests.Session) -> dict[str, Any]:
    """Fetch client/organization data from the Mava API."""
    from datetime import datetime, timezone

    # Get current timestamp in ISO format
    current_time = datetime.now(timezone.utc).isoformat()

    params: dict[str, str | int] = {
        "filterVersion": "3",
        "filterLastUpdated": current_time,
    }

    # Mava API uses cookie-based authentication, not Bearer token
    cookies: dict[str, str] = {"x-auth-token": MAVA_AUTH_TOKEN or ""}
    headers = {
        "User-Agent": "Mava-Supabase-Sync/1.0",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    logger.debug("Fetching client data from Mava API")
    logger.debug(
        "Using token: %s...", MAVA_AUTH_TOKEN[:10] if MAVA_AUTH_TOKEN else "None"
    )

    try:
        r = session.get("https://gateway.mava.app/client/get", params=params, headers=headers, cookies=cookies, timeout=30)
        r.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            logger.error("401 Unauthorized - Check your MAVA_AUTH_TOKEN")
            logger.error(
                "Token starts with: %s",
                MAVA_AUTH_TOKEN[:10] if MAVA_AUTH_TOKEN else "None",
            )
            logger.error("Response body: %s", e.response.text)
        elif e.response.status_code == 403:
            logger.error(
                "403 Forbidden - Token may be expired or insufficient permissions"
            )
            logger.error("Response body: %s", e.response.text)
        else:
            logger.error("HTTP %d error: %s", e.response.status_code, e.response.text)
        raise

    data = r.json()

    # Log response structure for debugging
    logger.debug(
        "Client data API response type: %s",
        type(data).__name__
    )

    logger.debug("Retrieved client data from API")
    return data


def transform_client_data(client_data: dict[str, Any]) -> dict[str, Any]:
    """Transform client data for Supabase storage."""
    return {
        "id": client_data.get("_id"),
        "name": client_data.get("name"),
        "creator": client_data.get("creator"),
        "contracts": client_data.get("contracts", []),
        "origin": client_data.get("origin", []),
        "members": client_data.get("members", []),
        "categories": client_data.get("categories", []),
        "is_ai_enabled": client_data.get("isAiEnabled", False),
        "use_template_answers": client_data.get("useTemplateAnswers", False),
        "is_csat_enabled": client_data.get("isCSATEnabled", False),
        "tags": client_data.get("tags", []),
        "hooks": client_data.get("hooks", []),
        "user_ratings": client_data.get("userRatings", []),
        "onboarding": client_data.get("onboarding", {}),
        "template_answers": client_data.get("templateAnswers", []),
        "is_reopening_tickets_enabled": client_data.get("isReopeningTicketsEnabled", False),
        "stripe_customer_id": client_data.get("stripeCustomerId"),
        "token": client_data.get("token"),
        "flow_root": client_data.get("flowRoot"),
        "archived_flows": client_data.get("archivedFlows", []),
        "ai_settings": client_data.get("aiSettings"),
        "created_at": client_data.get("createdAt"),
        "updated_at": client_data.get("updatedAt"),
        "version": client_data.get("__v", 0),
        "raw_data": client_data
    }


def fetch_page(session: requests.Session, skip: int) -> list[dict[str, Any]]:
    """Return a single page of tickets from the Mava API."""
    from datetime import datetime, timezone

    # Get current timestamp in ISO format
    current_time = datetime.now(timezone.utc).isoformat()

    params: dict[str, str | int] = {
        "limit": PAGE_SIZE,
        "skip": skip,
        "sort": "LAST_MODIFIED",
        "order": "DESCENDING",
        "filterVersion": "3",
        "filterLastUpdated": current_time,
        "priority": "",
        "hasPriorityFilter": "false",
        "status": "Open,Pending,Waiting,Resolved,Spam",
        "hasStatusFilter": "true",
        "category": "",
        "hasCategoryFilter": "false",
        "assignedTo": "",
        "hasAgentFilter": "false",
        "tag": "",
        "hasTagFilter": "false",
        "aiStatus": "",
        "hasAiStatusFilter": "false",
        "skipEmptyMessages": "false"
    }

    headers = {"X-Auth-Token": MAVA_AUTH_TOKEN}

    # Log request details for debugging (without exposing the full token)
    if MAVA_AUTH_TOKEN:
        token_preview = (
            MAVA_AUTH_TOKEN[:8] + "..." if len(MAVA_AUTH_TOKEN) > 8 else "***"
        )
    else:
        token_preview = "***"
    logger.debug("Making API request to %s with token: %s", MAVA_API_URL, token_preview)
    logger.debug("Request params: %s", params)

    try:
        r = session.get(MAVA_API_URL, params=params, headers=headers, timeout=30)

        # Handle different HTTP status codes with specific error messages
        if r.status_code == 400:
            logger.error("Bad request (400): Invalid parameters or request format")
            logger.error("Request URL: %s", r.url)
            logger.error("Request params: %s", params)
            logger.error("Response body: %s", r.text)
            raise requests.exceptions.HTTPError(
                "400 Client Error: Bad Request - Invalid parameters or request format"
            )
        elif r.status_code == 401:
            logger.error("Authentication failed (401 Unauthorized)")
            logger.error("Please check your MAVA_AUTH_TOKEN environment variable")
            logger.error("Token preview: %s", token_preview)
            logger.error("Response body: %s", r.text)
            raise requests.exceptions.HTTPError(
                "401 Client Error: Unauthorized - Invalid or expired authentication token"
            )
        elif r.status_code == 403:
            logger.error("Access forbidden (403 Forbidden)")
            logger.error("The token may not have sufficient permissions")
            logger.error("Response body: %s", r.text)
            raise requests.exceptions.HTTPError(
                "403 Client Error: Forbidden - Insufficient permissions"
            )
        elif r.status_code == 429:
            logger.error("Rate limit exceeded (429 Too Many Requests)")
            logger.error("Response body: %s", r.text)
            raise requests.exceptions.HTTPError(
                "429 Client Error: Too Many Requests - Rate limit exceeded"
            )
        elif r.status_code >= 500:
            logger.error("Server error (%d)", r.status_code)
            logger.error("Response body: %s", r.text)
            raise requests.exceptions.HTTPError(
                f"{r.status_code} Server Error: {r.reason}"
            )

        r.raise_for_status()

    except requests.exceptions.Timeout:
        logger.error("Request timeout after 30 seconds")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error("Connection error: %s", e)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Request failed: %s", e)
        raise

    try:
        data = r.json()
    except ValueError as e:
        logger.error("Failed to parse JSON response: %s", e)
        logger.error("Response content: %s", r.text)
        raise

    # Log response structure for debugging
    logger.debug(
        "API response keys: %s",
        list(data.keys()) if isinstance(data, dict) else "Not a dict",
    )

    # Handle different response formats from Mava API
    if isinstance(data, dict) and "tickets" in data:
        tickets: list[dict[str, Any]] = data["tickets"]
    elif isinstance(data, list):
        tickets = data
    else:
        tickets = data.get("tickets") or data.get("data") or []

    logger.debug("Retrieved %d tickets from API", len(tickets))
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

    except Exception as e:
        logger.error("Failed to upsert to table %s: %s", table_name, e)
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
    upsert_to_table("mava_customers", customers_data)
    upsert_to_table("mava_tickets", tickets_data)
    upsert_to_table("mava_messages", messages_data)
    upsert_to_table("mava_ticket_attributes", ticket_attributes_data)
    upsert_to_table("mava_customer_attributes", customer_attributes_data)

    logger.info(
        "Processed batch: %d customers, %d tickets, %d messages, %d ticket attrs, %d customer attrs",
        len(customers_data),
        len(tickets_data),
        len(messages_data),
        len(ticket_attributes_data),
        len(customer_attributes_data),
    )


# ───────── main sync loop ─────────


def sync_team_members(session: requests.Session) -> None:
    """Sync team members from Mava to Supabase."""
    logger.info("Starting team members sync")

    try:
        members = fetch_team_members(session)
        if not members:
            logger.info("No team members found")
            return

        # Transform team members data
        transformed_members = [transform_team_member(member) for member in members]

        # Upsert to team members table
        upsert_to_table("mava_team_members", transformed_members)

        logger.info("Team members sync complete — %d members processed", len(members))

    except Exception:
        logger.exception("Team members sync failed")
        raise


def sync_client_data(session: requests.Session) -> None:
    """Sync client/organization data from Mava to Supabase."""
    logger.info("Starting client data sync")

    try:
        client_data = fetch_client_data(session)
        if not client_data:
            logger.info("No client data found")
            return

        # Transform client data
        transformed_client = transform_client_data(client_data)

        # Upsert to client table
        upsert_to_table("mava_clients", [transformed_client])

        logger.info("Client data sync complete")

    except Exception:
        logger.exception("Client data sync failed")
        raise


def sync_all_pages() -> None:
    """Sync all pages of tickets from Mava to Supabase."""
    logger.info("Starting Mava → Supabase sync (multi-table mode)")
    session = requests.Session()
    skip = 0
    total_tickets = 0
    page_count = 0

    # First sync client data and team members
    sync_client_data(session)
    sync_team_members(session)

    while True:
        try:
            page = fetch_page(session, skip)
        except Exception:
            logger.exception("API request failed at skip=%d", skip)
            raise

        if not page:
            logger.info("No more tickets found at skip=%d, ending sync", skip)
            break

        page_count += 1
        process_tickets_batch(page)
        total_tickets += len(page)
        skip += PAGE_SIZE

        logger.info(
            "Page %d: processed %d tickets (total: %d)",
            page_count,
            len(page),
            total_tickets,
        )

        # Pause between paginated API calls
        time.sleep(5)

    logger.info(
        "Sync complete — %d tickets processed across %d pages",
        total_tickets,
        page_count,
    )


if __name__ == "__main__":
    try:
        # Initial health check
        if not health_check():
            logger.error("Health check failed, exiting")
            sys.exit(1)

        # Check current state before sync
        check_existing_tickets()

        start = datetime.utcnow()
        sync_all_pages()
        duration = (datetime.utcnow() - start).total_seconds()
        logger.info("Finished in %.1fs", duration)

        # Check final state after sync
        check_existing_tickets()
    except Exception:
        logger.exception("Uncaught error — sync aborted")
        sys.exit(1)
