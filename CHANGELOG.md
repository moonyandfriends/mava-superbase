# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial Mava to Supabase sync functionality
- Railway deployment configuration
- Docker containerization support
- Comprehensive logging and error handling
- Health check functionality
- Continuous sync mode for cloud deployment
- Environment-based configuration
- Detailed documentation and setup guides
- Added dev-requirements.txt for development dependencies
- Added type stubs (types-requests, types-python-dateutil) for better mypy support

### Changed
- N/A

### Fixed
- Fixed pytest module import issues by adding pythonpath configuration
- Fixed mypy type checking errors by improving type annotations
- Fixed trailing whitespace and newline issues in test files
- Updated deprecated GitHub Actions upload-artifact from v3 to v4

### Removed
- N/A

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