# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Multi-table database schema support for comprehensive Mava data storage
- Normalized data structure with separate tables for customers, tickets, messages, and attributes
- Enhanced data transformation functions for proper schema mapping
- Customer deduplication logic to prevent duplicate customer records
- Support for ticket attributes and customer attributes in separate tables
- Comprehensive database views for common queries and analytics
- Raw data preservation in JSONB columns for future schema evolution
- Foreign key relationships and referential integrity constraints
- Performance optimizations with strategic indexing
- Row Level Security (RLS) policies for all tables
- Detailed schema documentation with field mappings and example queries
- Enhanced debugging and monitoring capabilities with detailed logging
- Database state checking functions to verify sync completeness
- Standalone `schema.sql` file for easy database setup with indexes, views, and triggers
- Team members sync functionality
  - New `mava_team_members` table with comprehensive member data
  - Automatic team member synchronization during sync process
  - Support for member types, notifications, and filter configurations
  - Active team members view for easy querying
- Client/Organization data sync functionality
  - New `mava_clients` table with comprehensive client configuration
  - Automatic client data synchronization during sync process
  - Support for client settings, tags, categories, and integrations
  - Client summary view for easy configuration overview

### Changed
- **BREAKING CHANGE**: Complete rewrite of data storage from single table to normalized multi-table schema
- **BREAKING CHANGE**: All database tables and views now use `mava_` prefix for better namespace organization
- Enhanced error handling to continue processing even if individual table upserts fail
- Improved logging to show progress across all tables
- Updated README with comprehensive multi-table schema documentation
- Restructured code with better separation of concerns for data transformation
- Removed `skipEmptyMessages` filter to include all tickets in sync
- Enhanced pagination logging to track sync progress across pages

### Fixed
- Fixed type checking error for ticket_id parameter in message processing
- Enhanced error handling for Mava API 400 Bad Request errors with detailed debugging information
- Added specific logging for request URLs, parameters, and response bodies in authentication tests
- Improved error messages for all HTTP status codes (400, 401, 403, 429, 5xx) with response body details
- Fixed 400 Bad Request error in authentication test by using complete API parameters
- Fixed minimum limit requirement: Mava API requires limit >= 10 (was using limit=1)
- Fixed issue where tickets without messages were being excluded from sync
- Fixed setuptools package discovery errors by explicitly defining py_modules
- Updated license format to use SPDX expression instead of deprecated table format
- Removed deprecated license classifier to comply with setuptools warnings
- Added main() function entry point for proper script installation
- Fixed MyPy type checking error in fetch_client_data function by adding explicit type annotation
- Fixed test_sync_all_pages test failure by adding proper mocking for sync_team_members and sync_client_data functions
- Fixed test environment variable setup by setting variables before module import

### Removed
- FLATTEN_MESSAGES environment variable (replaced with always-on multi-table approach)

## [1.2.0] - 2025-01-27

### Changed
- Converted from continuous sync service to Railway cron job for better efficiency
- Removed SYNC_INTERVAL environment variable (no longer needed)
- Updated railway.json with hourly cron schedule "0 * * * *"
- Simplified service to single-run mode only

### Fixed
- Removed invalid --show-source argument from ruff command in CI
- Updated pyproject.toml to new [tool.ruff.lint] format
- Fixed deprecated typing.List/Dict imports to use lowercase list/dict
- Resolved multiple linting errors and import issues

## [1.1.0] - 2025-01-27

### Fixed
- Added required environment variables for CI testing
- Fixed GitHub Actions cancellation due to missing test variables

## [1.0.0] - 2025-01-27

### Added
- Initial Mava-Supabase sync service with Railway deployment
- Support for paginated API fetching from Mava
- Upsert functionality to Supabase with conflict resolution
- Health check endpoint for service monitoring
- Comprehensive test suite with pytest
- Docker containerization with security best practices
- CI/CD pipeline with GitHub Actions
- Environment-based configuration
- Railway deployment configuration
- Modern Python project structure with Poetry/Rye support
- Code quality tools: ruff, black, mypy
- Security scanning with bandit and safety 