#!/usr/bin/env python3
"""
Database Check Script

This script checks the current state of the Supabase database
to help diagnose why only 943 tickets are being exported.
"""

import logging
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

def check_database_state():
    """Check the current state of all tables in the database."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        return
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("Connected to Supabase successfully")
    except Exception as e:
        logger.error("Failed to connect to Supabase: %s", e)
        return
    
    # Check each table
    tables = ["tickets", "customers", "messages", "ticket_attributes", "customer_attributes"]
    
    for table in tables:
        try:
            # Get count
            count_response = supabase.table(table).select("*").execute()
            count = len(count_response.data) if count_response.data else 0
            
            logger.info("Table '%s': %d records", table, count)
            
            # Get sample data for tickets table
            if table == "tickets" and count > 0:
                sample_response = supabase.table(table).select("*").limit(5).execute()
                if sample_response.data:
                    logger.info("Sample ticket IDs: %s", 
                              [ticket.get("id", "unknown") for ticket in sample_response.data[:3]])
                    
                    # Check date range
                    created_dates = [ticket.get("created_at") for ticket in sample_response.data if ticket.get("created_at")]
                    if created_dates:
                        logger.info("Sample ticket creation dates: %s", created_dates[:3])
            
            # Get date range for all tables
            if count > 0:
                try:
                    # Get oldest and newest records
                    oldest_response = supabase.table(table).select("created_at").order("created_at", desc=False).limit(1).execute()
                    newest_response = supabase.table(table).select("created_at").order("created_at", desc=True).limit(1).execute()
                    
                    if oldest_response.data and newest_response.data:
                        oldest_date = oldest_response.data[0].get("created_at")
                        newest_date = newest_response.data[0].get("created_at")
                        logger.info("Table '%s' date range: %s to %s", table, oldest_date, newest_date)
                except Exception as e:
                    logger.debug("Could not get date range for table '%s': %s", table, e)
                    
        except Exception as e:
            logger.error("Error checking table '%s': %s", table, e)

def check_ticket_distribution():
    """Check ticket distribution by status, date, etc."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        # Check tickets by status
        logger.info("=== TICKET STATUS DISTRIBUTION ===")
        status_response = supabase.table("tickets").select("status").execute()
        
        status_counts = {}
        for ticket in status_response.data:
            status = ticket.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status, count in sorted(status_counts.items()):
            logger.info("Status '%s': %d tickets", status, count)
        
        # Check tickets by month
        logger.info("=== TICKET CREATION BY MONTH ===")
        monthly_response = supabase.table("tickets").select("created_at").execute()
        
        monthly_counts = {}
        for ticket in monthly_response.data:
            created_at = ticket.get("created_at")
            if created_at:
                try:
                    # Parse date and get month
                    if isinstance(created_at, str):
                        date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        date_obj = created_at
                    
                    month_key = f"{date_obj.year}-{date_obj.month:02d}"
                    monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
                except Exception as e:
                    logger.debug("Could not parse date %s: %s", created_at, e)
        
        for month, count in sorted(monthly_counts.items()):
            logger.info("Month %s: %d tickets", month, count)
            
    except Exception as e:
        logger.error("Error checking ticket distribution: %s", e)

def check_for_duplicates():
    """Check for duplicate tickets in the database."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        return
    
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        
        logger.info("=== CHECKING FOR DUPLICATES ===")
        
        # Get all ticket IDs
        response = supabase.table("tickets").select("id").execute()
        ticket_ids = [ticket.get("id") for ticket in response.data if ticket.get("id")]
        
        # Check for duplicates
        unique_ids = set(ticket_ids)
        duplicate_count = len(ticket_ids) - len(unique_ids)
        
        logger.info("Total ticket records: %d", len(ticket_ids))
        logger.info("Unique ticket IDs: %d", len(unique_ids))
        logger.info("Duplicate records: %d", duplicate_count)
        
        if duplicate_count > 0:
            logger.warning("Found %d duplicate ticket records!", duplicate_count)
            
    except Exception as e:
        logger.error("Error checking for duplicates: %s", e)

if __name__ == "__main__":
    logger.info("Starting database state check")
    
    check_database_state()
    check_ticket_distribution()
    check_for_duplicates()
    
    logger.info("Database check complete") 