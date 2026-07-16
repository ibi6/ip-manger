# Changelog

All notable changes to **NetLedger** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [1.6.0] - 2026-07-16

### Added
- Revocable JWT credential version; password changes and admin resets invalidate old tokens
- Strong password policy and production-only bootstrap administrator flow
- Security response headers, trusted-proxy control, and failure-only login throttling
- Alembic 0002 migration for device inventory, device binding, unique MACs, and auth versions
- Frontend Node tests, backend Ruff checks, and expanded authentication/validation tests
- Production deployment and test runbooks
- Light, dark, and system-following themes with pre-paint initialization and persisted preference

### Changed
- NetLedger product branding replaces assignment/demo language in the application shell
- Mobile navigation now exposes account context, logout, Escape handling, and accessible names
- Form labels are programmatically associated with controls; feedback uses live regions
- Browser tokens use tab-scoped session storage instead of persistent local storage
- Site subnet counts use one grouped query instead of N+1 queries
- Backend container runs as a non-root user and migrates before startup

### Security
- Production never creates demo accounts and fails fast without an explicit bootstrap password
- Device creation prevents department users from assigning inventory to another department

## [1.5.0] - 2026-07-15

### Added
- Address list pagination (`/ip-addresses/page`) and UI paging
- Batch IP release API and multi-select UI
- Subnet soft-archive / restore workflow
- Department create API (admin)
- Device MAC uniqueness enforcement
- Reserve with optional remark

### Changed
- Subnet delete defaults to archive-first safety

## [1.4.1] - 2026-07-15

### Added
- Device edit UI, device CSV export
- Full allocate dialog on address detail (device binding)

## [1.4.0] - 2026-07-15

### Added
- Disable / enable IP lifecycle
- Allocate-next free address per subnet
- Change-password endpoint and settings UI
- Request access logging middleware + `X-Request-ID`

## [1.3.x] - 2026-07-15

### Added
- Device inventory module
- Operation logs page
- User administration
- SQLite schema migrate helper

## [1.2.0] - 2026-07-15

### Added
- Login rate limiting
- Conditional allocate (concurrency-safe)
- Secret key production guards
- pytest suite foundation
- Alembic baseline migration

## [1.0.0] - 2026-07-15

### Added
- Initial IPAM: sites, subnets, IP pool generation, allocate/release
- JWT RBAC, dashboard, conflicts (simulate), CSV, Docker Compose
