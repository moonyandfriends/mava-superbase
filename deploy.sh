#!/bin/bash
# deployment script for Railway

set -e

echo "🚀 Deploying Mava Supabase Sync to Railway..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway. Please run:"
    echo "   railway login"
    exit 1
fi

# Deploy to Railway
echo "📦 Starting deployment..."
railway up

echo "✅ Deployment initiated! Check Railway dashboard for status."
echo "🔗 https://railway.app/dashboard"

# Optional: Set environment variables if not already set
echo ""
echo "📋 Don't forget to set these environment variables in Railway:"
echo "   - MAVA_AUTH_TOKEN"
echo "   - SUPABASE_URL" 
echo "   - SUPABASE_SERVICE_KEY"
echo ""
echo "Optional variables (with defaults):"
echo "   - PAGE_SIZE (default: 50)"
echo "   - LOG_LEVEL (default: INFO)"
echo "   - SYNC_INTERVAL (default: 3600)" 