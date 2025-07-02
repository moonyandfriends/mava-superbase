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

The easiest way to set up your database is to run the provided schema file:

```bash
# In your Supabase SQL editor, run:
# Copy and paste the contents of schema.sql
```

Alternatively, you can create the tables manually. Here's the complete schema:

```sql
-- Customers table
CREATE TABLE mava_customers (
    id TEXT PRIMARY KEY,
    discord_author_id TEXT,
    client TEXT,
    name TEXT,
    avatar_url TEXT,
    discord_joined_at TIMESTAMP WITH TIME ZONE,
    wallet_address TEXT,
    discord_roles JSONB,
    custom_fields JSONB,
    notes JSONB,
    user_ratings JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    raw_data JSONB
);

-- Main tickets table
CREATE TABLE mava_tickets (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES mava_customers(id),
    client TEXT,
    status TEXT,
    priority TEXT,
    source_type TEXT,
    category TEXT,
    assigned_to TEXT,
    discord_thread_id TEXT,
    interaction_identifier TEXT,
    is_discord_thread_deleted BOOLEAN,
    discord_users JSONB,
    ai_status TEXT,
    is_ai_enabled_in_flow_root BOOLEAN,
    is_button_in_flow_root_clicked BOOLEAN,
    force_button_selection BOOLEAN,
    is_user_rating_requested BOOLEAN,
    is_visible BOOLEAN,
    mentions JSONB,
    first_customer_message_created_at TIMESTAMP WITH TIME ZONE,
    first_agent_message_created_at TIMESTAMP WITH TIME ZONE,
    tags JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    disabled BOOLEAN,
    raw_data JSONB
);

-- Messages table
CREATE TABLE mava_messages (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES mava_tickets(id),
    sender TEXT,
    sender_reference_type TEXT,
    from_customer BOOLEAN,
    content TEXT,
    is_picture BOOLEAN,
    is_read BOOLEAN,
    message_type TEXT,
    message_status TEXT,
    is_edited BOOLEAN,
    is_deleted BOOLEAN,
    read_by JSONB,
    mentions JSONB,
    pre_submission_identifier TEXT,
    foreign_identifier TEXT,
    action_log_from TEXT,
    action_log_to TEXT,
    replied_to TEXT,
    client TEXT,
    attachments JSONB,
    reactions JSONB,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    version INTEGER,
    raw_data JSONB
);

-- Ticket attributes table
CREATE TABLE mava_ticket_attributes (
    id TEXT PRIMARY KEY,
    ticket_id TEXT REFERENCES mava_tickets(id),
    attribute TEXT,
    content TEXT,
    raw_data JSONB
);

-- Customer attributes table
CREATE TABLE mava_customer_attributes (
    id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES mava_customers(id),
    attribute TEXT,
    content TEXT,
    raw_data JSONB
);

-- Enable Row Level Security on all tables
ALTER TABLE mava_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_ticket_attributes ENABLE ROW LEVEL SECURITY;
ALTER TABLE mava_customer_attributes ENABLE ROW LEVEL SECURITY;

-- Create policies for service role
CREATE POLICY "Service role can manage mava_tickets" ON mava_tickets
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can manage mava_customers" ON mava_customers
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can manage mava_messages" ON mava_messages
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can manage mava_ticket_attributes" ON mava_ticket_attributes
    FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service role can manage mava_customer_attributes" ON mava_customer_attributes
    FOR ALL USING (auth.role() = 'service_role');
```

## Analytics & Monitoring

### Grafana Dashboards

This project includes comprehensive Grafana dashboards for monitoring your Mava support operations. The dashboards provide real-time insights into ticket volumes, agent performance, customer satisfaction, and operational metrics.

#### Quick Setup

1. **Install Grafana** (if not already installed):
   ```bash
   # Using Docker
   docker run -d -p 3000:3000 grafana/grafana
   
   # Or install locally from https://grafana.com/grafana/download
   ```

2. **Set up environment variables**:
   ```bash
   export GRAFANA_URL='http://localhost:3000'
   export GRAFANA_API_KEY='your-grafana-api-key'
   ```

3. **Run the setup script**:
   ```bash
   python setup_grafana.py
   ```

#### Available Dashboards

- **📊 Support Ticket Overview**: High-level metrics, status distribution, and response times
- **⚡ Real-time Monitoring**: Live activity tracking, SLA breach alerts, and agent workload
- **👥 Customer Analytics**: Customer behavior, satisfaction metrics, and activity patterns
- **👨‍💼 Agent Performance**: Individual agent metrics, response times, and workload distribution
- **💬 Message Analytics**: Message volume trends and customer vs agent communication patterns
- **📈 Category Analysis**: Ticket distribution by category and source type

#### Key Metrics Tracked

- **Operational KPIs**: Ticket volume, resolution times, response times
- **Agent Performance**: Workload distribution, resolution rates, response efficiency
- **Customer Insights**: Activity patterns, satisfaction scores, lifetime value
- **Quality Metrics**: SLA compliance, priority handling, category distribution
- **Real-time Alerts**: High priority tickets, SLA breaches, agent overload

#### Manual Setup

If you prefer to set up manually:

1. **Add Supabase as a PostgreSQL data source** in Grafana:
   - Host: `your-project.supabase.co:5432`
   - Database: `postgres`
   - Username: `postgres`
   - Password: Your Supabase service key
   - SSL Mode: `require`

2. **Import dashboard JSON files**:
   - `grafana_dashboard_overview.json`
   - `grafana_dashboard_realtime.json`

3. **Configure alerts** based on the thresholds in `grafana_dashboards.md`

For detailed SQL queries and advanced analytics, see `grafana_dashboards.md`.

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
├── schema.sql          # Database schema and setup
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

- **Tables**: `mava_tickets`, `mava_customers`, `mava_messages`, `mava_ticket_attributes`, `mava_customer_attributes`
- **Operation**: `UPSERT` (insert or update)
- **Conflict Resolution**: Uses `id` field as primary key for each table
- **Relationships**: Messages and attributes reference tickets/customers via foreign keys

## Troubleshooting

### Common Issues

**Database Schema Errors**
```
Health check failed: relation "public.tickets" does not exist
```
→ Run the database schema setup using `schema.sql`

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
