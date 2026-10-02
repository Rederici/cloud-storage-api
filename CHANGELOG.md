## v0.2.8 (2026-10-02)

### Fix

- **deps**: bump urllib3 to 2.8.0
- **api**: correct redoc path from /redocs to /redoc

### Refactor

- **storage**: make user root implicit and move key mapping to s3 adapter

## v0.2.7 (2026-09-30)

### Fix

- **tests**: resolve pytest import errors
- **storage**: align recursive default between port and adapter
- **compose**: fall back to sane defaults when .env vars are unset
- **deps**: add yaml extra to pydantic-settings for config.yaml support
- **docker**: set PYTHONPATH to src for cloud_storage package resolution

### Refactor

- **auth**: move cookie security into auth/http/dependencies.py
- **auth**: extract PasswordHasher port
- **auth**: restructure module along hexagonal boundaries
- **storage**: restructure module along hexagonal boundaries
- rename alembic/ dir to migrations/ to avoid import shadowing
- merge user service into auth
- move src/ package into src/cloud_storage/
- move constant variable to config.yaml

## v0.2.6 (2026-09-13)

### Fix

- prevent folder duplication on move

## v0.2.5 (2026-09-12)

### Fix

- guard types_aiobotocore_s3 import behind TYPE_CHECKING

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
