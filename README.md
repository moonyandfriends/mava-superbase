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

Create a table in your Supabase database:

```sql
CREATE TABLE tickets (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE,
    status TEXT,
    title TEXT,
    description TEXT,
    -- Add other fields as needed based on Mava API response
);

-- Enable Row Level Security (recommended)
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Create policy for service role
CREATE POLICY "Service role can manage tickets" ON tickets
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

- **Table**: `tickets`
- **Operation**: `UPSERT` (insert or update)
- **Conflict Resolution**: Uses `id` field as primary key

## Troubleshooting

### Common Issues

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

**Database Connection**
```
Health check failed: connection error
```
→ Verify Supabase URL and service key

### Railway-Specific Issues

**Service Not Starting**
```
Process exited with code 1
```
→ Check Railway logs for environment variable issues

**Memory Limits**
→ Consider optimizing `PAGE_SIZE` for large datasets

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
