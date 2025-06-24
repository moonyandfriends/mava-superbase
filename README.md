# Mava Supabase Sync

A Python service that synchronizes support tickets from Mava API to Supabase database.

## Features

- 🔄 **Continuous Sync**: Automatically syncs tickets at configurable intervals
- 🚀 **Railway Ready**: Optimized for deployment on Railway with zero configuration
- 📊 **Comprehensive Logging**: Detailed logs for monitoring and debugging
- 🛡️ **Error Handling**: Robust error handling with retry mechanisms
- 🔍 **Health Checks**: Built-in health checks for monitoring
- 📦 **Containerized**: Docker support for consistent deployments

## Quick Start

### 1. Local Development

```bash
# Clone the repository
git clone https://github.com/yourusername/mava-superbase.git
cd mava-superbase

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env

# Edit .env with your credentials
nano .env

# Run the sync
python mava_sync.py
```

### 2. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)

**Manual Deployment:**

1. Fork this repository
2. Connect your GitHub account to Railway
3. Create a new project from this repository
4. Set the required environment variables in Railway dashboard
5. Deploy!

### 3. Docker Deployment

```bash
# Build the image
docker build -t mava-sync .

# Run with environment variables
docker run -d \
  -e MAVA_AUTH_TOKEN=your_token \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_SERVICE_KEY=your_key \
  mava-sync
```

## Configuration

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `MAVA_AUTH_TOKEN` | Bearer token for Mava API | `your_mava_token_here` |
| `SUPABASE_URL` | Your Supabase project URL | `https://xyz.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | `your_service_key_here` |

### Optional Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PAGE_SIZE` | `50` | Number of tickets per API request |
| `LOG_LEVEL` | `INFO` | Python logging level |

## Database Setup

The application requires 5 tables in your Supabase database. You can set up the database schema in one of two ways:

### Option 1: Use the provided SQL file (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to the SQL Editor
3. Copy and paste the contents of `database_schema.sql` into the editor
4. Run the SQL script

### Option 2: Manual table creation

If you prefer to create tables manually, here are the required tables:

#### Customers Table
```sql
CREATE TABLE customers (
    id TEXT PRIMARY KEY,
    discord_author_id TEXT,
    client TEXT,
    name TEXT,
    avatar_url TEXT,
    discord_joined_at TIMESTAMP WITH TIME ZONE,
    wallet_address TEXT,
    discord_roles JSONB DEFAULT '[]',
    custom_fields JSONB DEFAULT '[]',
    notes JSONB DEFAULT '[]',
    user_ratings JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    raw_data JSONB
);
```

#### Tickets Table
```sql
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers(id),
    client TEXT,
    status TEXT,
    priority TEXT,
    source_type TEXT,
    category TEXT,
    assigned_to TEXT,
    discord_thread_id TEXT,
    interaction_identifier TEXT,
    is_discord_thread_deleted BOOLEAN DEFAULT FALSE,
    discord_users JSONB DEFAULT '[]',
    ai_status TEXT,
    is_ai_enabled_in_flow_root BOOLEAN DEFAULT FALSE,
    is_button_in_flow_root_clicked BOOLEAN DEFAULT FALSE,
    force_button_selection BOOLEAN DEFAULT FALSE,
    is_user_rating_requested BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    mentions JSONB DEFAULT '[]',
    first_customer_message_created_at TIMESTAMP WITH TIME ZONE,
    first_agent_message_created_at TIMESTAMP WITH TIME ZONE,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    disabled BOOLEAN DEFAULT FALSE,
    raw_data JSONB
);
```

#### Messages Table
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES tickets(id),
    sender TEXT,
    sender_reference_type TEXT,
    from_customer BOOLEAN DEFAULT FALSE,
    content TEXT,
    is_picture BOOLEAN DEFAULT FALSE,
    is_read BOOLEAN DEFAULT FALSE,
    message_type TEXT,
    message_status TEXT,
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    read_by JSONB DEFAULT '[]',
    mentions JSONB DEFAULT '[]',
    pre_submission_identifier TEXT,
    foreign_identifier TEXT,
    action_log_from TEXT,
    action_log_to TEXT,
    replied_to TEXT,
    client TEXT,
    attachments JSONB DEFAULT '[]',
    reactions JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    raw_data JSONB
);
```

#### Ticket Attributes Table
```sql
CREATE TABLE ticket_attributes (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES tickets(id),
    attribute TEXT,
    content TEXT,
    raw_data JSONB
);
```

#### Customer Attributes Table
```sql
CREATE TABLE customer_attributes (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers(id),
    attribute TEXT,
    content TEXT,
    raw_data JSONB
);
```

### Enable Row Level Security

After creating the tables, enable Row Level Security and create policies:

```sql
-- Enable RLS on all tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE ticket_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_attributes ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
CREATE POLICY "Service role can manage customers" ON customers
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage tickets" ON tickets
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage messages" ON messages
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage ticket_attributes" ON ticket_attributes
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Service role can manage customer_attributes" ON customer_attributes
    FOR ALL USING (auth.role() = 'service_role');
```

## How It Works

1. **Fetches Data**: Retrieves all tickets from Mava API using pagination
2. **Upserts Records**: Updates existing tickets or inserts new ones in Supabase
3. **Handles Errors**: Retries on failures and logs all operations
4. **Runs on Schedule**: In Railway, runs as a cron job (hourly by default)

## Monitoring

### Logs

The service provides comprehensive logging:

```
2024-01-15 10:00:00 [INFO] Health check passed
2024-01-15 10:00:01 [INFO] Starting Mava → Supabase sync
2024-01-15 10:00:02 [INFO] Upserted 25 tickets
2024-01-15 10:00:03 [INFO] Sync complete — 150 tickets processed
2024-01-15 10:00:04 [INFO] Finished in 2.1s
```

### Health Checks

The service includes built-in health checks that verify:
- Supabase database connectivity
- API credentials validity

### Railway Cron Scheduling

The service runs as a Railway cron job with the schedule `"0 * * * *"` (every hour).

**Common Cron Schedules:**
- `"0 * * * *"` - Every hour (default)
- `"*/30 * * * *"` - Every 30 minutes
- `"0 */2 * * *"` - Every 2 hours
- `"0 9-17 * * *"` - Every hour during business hours (9 AM - 5 PM)
- `"0 0 * * *"` - Once daily at midnight

To change the schedule, modify the `cronSchedule` in `railway.json`.

## Development

### Project Structure

```
mava-superbase/
├── mava_sync.py        # Main sync script
├── database_schema.sql # Database schema definition
├── requirements.txt    # Python dependencies
├── Dockerfile         # Container configuration
├── railway.json       # Railway deployment config
├── env.example        # Environment template
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

### Local Testing

```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug logging
LOG_LEVEL=DEBUG python mava_sync.py

# Run single sync (default behavior)
python mava_sync.py
```

## API Reference

### Mava API

The script uses the Mava tickets API:
- **Endpoint**: `https://gateway.mava.app/ticket/list`
- **Method**: `GET`
- **Authentication**: Bearer token
- **Pagination**: Uses `limit` and `skip` parameters

### Supabase Operations

- **Tables**: `customers`, `tickets`, `messages`, `ticket_attributes`, `customer_attributes`
- **Operation**: `UPSERT` (insert or update)
- **Conflict Resolution**: Uses `id` field as primary key

## Troubleshooting

### Common Issues

**Database Schema Errors**
```
Health check failed: relation "public.tickets" does not exist
```
→ Run the database schema setup using `database_schema.sql`

**Authentication Errors**
```
[FATAL] Environment variables must be set
```
→ Ensure all required environment variables are set

**API Rate Limits**
```
API request failed at skip=100
```
→ Consider reducing `PAGE_SIZE` or adding delays

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- 🐛 [GitHub Issues](https://github.com/yourusername/mava-superbase/issues)
- 📧 [Email Support](mailto:your-email@example.com)
- 💬 [Discord Community](https://discord.gg/your-server)

---

**Made with ❤️ for seamless Mava-Supabase integration**
