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
- Enhanced debugging and diagnostic capabilities for pagination issues
- Detailed pagination tracking with page numbers, skip values, and progress logging
- Consecutive empty page detection to prevent infinite loops
- Rate limiting protection with configurable delays between requests
- Warning system for suspiciously low ticket counts
- Diagnostic script (debug_mava_sync.py) for API pagination testing
- Database state check script (check_database.py) for data integrity analysis
- Enhanced error handling with detailed API response logging

### Changed
- **BREAKING CHANGE**: Complete rewrite of data storage from single table to normalized multi-table schema
- Enhanced error handling to continue processing even if individual table upserts fail
- Improved logging to show progress across all tables
- Updated README with comprehensive multi-table schema documentation
- Restructured code with better separation of concerns for data transformation
- Enhanced sync_all_pages function with better debugging and error recovery
- Improved fetch_page function with detailed response format handling

### Fixed
- Fixed type checking error for ticket_id parameter in message processing
- Enhanced error handling for Mava API 400 Bad Request errors with detailed debugging information
- Added specific logging for request URLs, parameters, and response bodies in authentication tests
- Improved error messages for all HTTP status codes (400, 401, 403, 429, 5xx) with response body details
- Fixed 400 Bad Request error in authentication test by using complete API parameters
- Fixed minimum limit requirement: Mava API requires limit >= 10 (was using limit=1)
- Fixed pagination logic to handle edge cases and prevent early termination
- Enhanced error recovery to continue processing after temporary API failures

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