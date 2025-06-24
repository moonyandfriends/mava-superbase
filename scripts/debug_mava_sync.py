#!/usr/bin/env python3
"""
Mava Sync Debug Script

This script helps diagnose why only 943 tickets are being exported.
It will test the API pagination and provide detailed logging.
"""

import logging
import os
import sys
from typing import Any

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MAVA_API_URL = "https://gateway.mava.app/ticket/list"
MAVA_AUTH_TOKEN = os.getenv("MAVA_AUTH_TOKEN")
PAGE_SIZE = int(os.getenv("PAGE_SIZE", "50"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def test_api_pagination():
    """Test API pagination to understand the issue."""
    if not MAVA_AUTH_TOKEN:
        logger.error("MAVA_AUTH_TOKEN not set")
        return
    
    session = requests.Session()
    headers = {"X-Auth-Token": MAVA_AUTH_TOKEN}
    
    total_tickets = 0
    page_count = 0
    skip = 0
    
    logger.info("Starting API pagination test with PAGE_SIZE=%d", PAGE_SIZE)
    
    while True:
        page_count += 1
        params = {
            "limit": PAGE_SIZE,
            "skip": skip,
            "sort": "LAST_MODIFIED",
            "order": "DESCENDING",
            "skipEmptyMessages": "true",
        }
        
        logger.info("Fetching page %d (skip=%d, total_tickets=%d)", page_count, skip, total_tickets)
        
        try:
            response = session.get(MAVA_API_URL, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Log response headers
            logger.info("Response status: %d", response.status_code)
            logger.info("Response headers: %s", dict(response.headers))
            
            data = response.json()
            
            # Handle different response formats
            tickets = []
            if isinstance(data, dict):
                if "tickets" in data:
                    tickets = data["tickets"]
                elif "data" in data:
                    tickets = data["data"]
                else:
                    logger.warning("Unexpected response structure. Keys: %s", list(data.keys()))
                    # Try to find tickets in any array field
                    for key, value in data.items():
                        if isinstance(value, list) and value and isinstance(value[0], dict):
                            if "_id" in value[0]:
                                tickets = value
                                logger.info("Found tickets in '%s' field", key)
                                break
            elif isinstance(data, list):
                tickets = data
            else:
                logger.error("Unexpected response type: %s", type(data))
                break
            
            logger.info("Page %d: Received %d tickets", page_count, len(tickets))
            
            if not tickets:
                logger.info("Empty page received, stopping pagination")
                break
            
            # Log first and last ticket info
            if tickets:
                first_ticket = tickets[0]
                last_ticket = tickets[-1]
                logger.info("Page %d ticket range: %s to %s", 
                          page_count, 
                          first_ticket.get("_id", "unknown"),
                          last_ticket.get("_id", "unknown"))
                logger.info("First ticket created: %s", first_ticket.get("createdAt"))
                logger.info("Last ticket created: %s", last_ticket.get("createdAt"))
            
            total_tickets += len(tickets)
            skip += PAGE_SIZE
            
            # Add delay to avoid rate limiting
            import time
            time.sleep(0.2)
            
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error on page %d: %s", page_count, e)
            logger.error("Response body: %s", response.text if 'response' in locals() else "N/A")
            break
        except Exception as e:
            logger.error("Error on page %d: %s", page_count, e)
            break
    
    logger.info("=== PAGINATION TEST RESULTS ===")
    logger.info("Total pages processed: %d", page_count)
    logger.info("Total tickets found: %d", total_tickets)
    logger.info("Average tickets per page: %.1f", total_tickets / page_count if page_count > 0 else 0)
    
    if total_tickets == 943:
        logger.warning("Exactly 943 tickets found - this suggests a potential issue:")
        logger.warning("1. API rate limiting after ~19 pages")
        logger.warning("2. Authentication token expiration")
        logger.warning("3. API pagination bug")
        logger.warning("4. Network timeout or connection issues")
    
    return total_tickets, page_count

def test_api_limits():
    """Test different page sizes to understand API limits."""
    logger.info("=== TESTING DIFFERENT PAGE SIZES ===")
    
    page_sizes = [10, 25, 50, 100, 200]
    
    for size in page_sizes:
        logger.info("Testing PAGE_SIZE=%d", size)
        params = {
            "limit": size,
            "skip": 0,
            "sort": "LAST_MODIFIED",
            "order": "DESCENDING",
            "skipEmptyMessages": "true",
        }
        
        headers = {"X-Auth-Token": MAVA_AUTH_TOKEN}
        
        try:
            response = requests.get(MAVA_API_URL, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            tickets = []
            
            if isinstance(data, dict):
                tickets = data.get("tickets", data.get("data", []))
            elif isinstance(data, list):
                tickets = data
            
            logger.info("PAGE_SIZE=%d: Received %d tickets", size, len(tickets))
            
        except Exception as e:
            logger.error("PAGE_SIZE=%d failed: %s", size, e)

if __name__ == "__main__":
    logger.info("Starting Mava API diagnostic")
    
    # Test pagination
    total_tickets, page_count = test_api_pagination()
    
    # Test different page sizes
    test_api_limits()
    
    logger.info("Diagnostic complete") 