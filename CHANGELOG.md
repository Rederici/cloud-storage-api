## v0.2.4 (2026-09-12)

### Fix

- **ci**: remove depends_on from backend service

## v0.2.3 (2026-09-12)

### Fix

- **ci**: authenticate deploy jobs against the container registry

## v0.2.2 (2026-09-12)

### Fix

- **ci**: fix service name mismatch in deploy jobs (app -> backend)

## v0.2.1 (2026-09-12)

### Fix

- **ci**: fix recursive pipeline call in version release

## v0.2.0 (2026-09-12)

### Feat

- **api**: configure API documentation via environment
- **redis**: support password authentication
- **api**: add health check endpoint
- add resource search endpoint
- add resource move endpoint

### Fix

- **ci**: add git package for version release job
- **ci**: fix gitleaks job execution
- ignore .cache/ directory in coverage and pyright
- fix alembic url parsing issue
- update error codes, error messages, and Swagger schema

### Refactor

- add --stats flag to pyright
- **storage**: replace MinIO with RustFS
- replace first_level with recursive param in list_directory
