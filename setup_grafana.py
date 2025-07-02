#!/usr/bin/env python3
"""
Grafana Setup Script for Mava Support Analytics

This script helps you set up Grafana with Supabase connection and import dashboards.
"""

import json
import os
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()


class GrafanaSetup:
    def __init__(self, grafana_url: str, api_key: str):
        self.grafana_url = grafana_url.rstrip("/")
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def test_connection(self) -> bool:
        """Test connection to Grafana."""
        try:
            response = requests.get(
                f"{self.grafana_url}/api/health", headers=self.headers
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to connect to Grafana: {e}")
            return False

    def add_supabase_datasource(self, datasource_config: dict[str, Any]) -> bool:
        """Add Supabase as a PostgreSQL data source."""
        try:
            response = requests.post(
                f"{self.grafana_url}/api/datasources",
                headers=self.headers,
                json=datasource_config,
            )

            if response.status_code == 200:
                print("✅ Supabase data source added successfully")
                return True
            else:
                print(f"❌ Failed to add data source: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error adding data source: {e}")
            return False

    def import_dashboard(self, dashboard_json: dict[str, Any]) -> bool:
        """Import a dashboard from JSON."""
        try:
            # Prepare the import payload
            import_payload = {
                "dashboard": dashboard_json["dashboard"],
                "overwrite": True,
            }

            response = requests.post(
                f"{self.grafana_url}/api/dashboards/db",
                headers=self.headers,
                json=import_payload,
            )

            if response.status_code == 200:
                result = response.json()
                print(
                    f"✅ Dashboard imported successfully: {result.get('title', 'Unknown')}"
                )
                print(f"   URL: {self.grafana_url}{result.get('url', '')}")
                return True
            else:
                print(f"❌ Failed to import dashboard: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error importing dashboard: {e}")
            return False


def create_supabase_datasource_config() -> dict[str, Any]:
    """Create Supabase PostgreSQL data source configuration."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        return {}

    # Extract host from Supabase URL
    host = supabase_url.replace("https://", "").replace("http://", "")

    return {
        "name": "Mava Supabase",
        "type": "postgres",
        "url": f"{host}:5432",
        "user": "postgres",
        "secureJsonData": {"password": supabase_key},
        "jsonData": {
            "database": "postgres",
            "sslmode": "require",
            "maxOpenConns": 100,
            "maxIdleConns": 100,
            "connMaxLifetime": 14400,
            "postgresVersion": 1200,
            "timescaledb": False,
        },
        "access": "proxy",
        "isDefault": False,
    }


def load_dashboard_json(filename: str) -> dict[str, Any]:
    """Load dashboard JSON from file."""
    try:
        with open(filename) as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return {}


def main():
    """Main setup function."""
    print("🚀 Mava Support Grafana Setup")
    print("=" * 40)

    # Get Grafana configuration
    grafana_url = os.getenv("GRAFANA_URL")
    grafana_api_key = os.getenv("GRAFANA_API_KEY")

    if not grafana_url or not grafana_api_key:
        print("❌ Please set GRAFANA_URL and GRAFANA_API_KEY environment variables")
        print("\nExample:")
        print("export GRAFANA_URL='http://localhost:3000'")
        print("export GRAFANA_API_KEY='your-grafana-api-key'")
        return

    # Initialize Grafana setup
    grafana = GrafanaSetup(grafana_url, grafana_api_key)

    # Test connection
    print("🔍 Testing Grafana connection...")
    if not grafana.test_connection():
        print("❌ Cannot connect to Grafana. Please check your URL and API key.")
        return

    print("✅ Connected to Grafana successfully")

    # Add Supabase data source
    print("\n📊 Adding Supabase data source...")
    datasource_config = create_supabase_datasource_config()
    if not datasource_config:
        return

    if not grafana.add_supabase_datasource(datasource_config):
        print("❌ Failed to add data source. Please check your Supabase credentials.")
        return

    # Import dashboards
    print("\n📈 Importing dashboards...")

    dashboard_files = [
        "grafana_dashboard_overview.json",
        "grafana_dashboard_realtime.json",
    ]

    for filename in dashboard_files:
        print(f"\n📋 Importing {filename}...")
        dashboard_json = load_dashboard_json(filename)
        if dashboard_json:
            grafana.import_dashboard(dashboard_json)
        else:
            print(f"❌ Skipping {filename} due to loading error")

    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Open Grafana in your browser")
    print("2. Navigate to the imported dashboards")
    print("3. Configure alerts based on the thresholds in grafana_dashboards.md")
    print("4. Customize the dashboards as needed")


if __name__ == "__main__":
    main()
