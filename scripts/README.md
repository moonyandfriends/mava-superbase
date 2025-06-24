# Diagnostic Scripts

This directory contains diagnostic and debugging scripts for the Mava-Supabase sync service.

## Scripts

### `debug_mava_sync.py`
A diagnostic script to test Mava API pagination and identify issues with ticket export limits.

**Usage:**
```bash
python scripts/debug_mava_sync.py
```

**Features:**
- Tests API pagination step by step
- Checks different page sizes to understand API limits
- Identifies where the sync stops (e.g., exactly at 943 tickets)
- Logs detailed response headers and API behavior
- Provides warnings for common issues (rate limiting, auth problems, etc.)

### `check_database.py`
A script to check the current state of the Supabase database and analyze data integrity.

**Usage:**
```bash
python scripts/check_database.py
```

**Features:**
- Checks current database state across all tables
- Analyzes ticket distribution by status and date
- Detects duplicate records
- Verifies data integrity
- Shows date ranges for all tables

## Environment Variables

Both scripts require the same environment variables as the main sync service:

- `MAVA_AUTH_TOKEN` - Your Mava API bearer token
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_KEY` - Your Supabase service role key
- `PAGE_SIZE` - API page size (optional, default: 50)
- `LOG_LEVEL` - Logging level (optional, default: INFO)

## Troubleshooting

If you're experiencing issues with only 943 tickets being exported:

1. **Run the debug script first** to understand the API behavior
2. **Check the database state** to see what's currently stored
3. **Look for patterns** in the logs (rate limiting, auth issues, etc.)
4. **Try different page sizes** to see if that affects the results

The enhanced logging in the main `mava_sync.py` will also provide detailed information about the sync process. 