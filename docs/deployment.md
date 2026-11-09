# Deployment, backups and recovery

## Production preparation

The Docker and HTTPS configuration is provided but has not been executed on this machine, where Docker is not installed. Before live use, build the images, verify the configuration on a staging host, restore a backup into a separate database, inspect Urdu PDFs with actual shop data and verify the intended printer. Browser printing opens the system dialog; the application cannot guarantee a connected printer.

Use a Linux host with Docker Compose, a domain pointing at the host and ports 80/443 available. Copy `deploy/.env.production.example` to root `.env`. Set distinct random migration/database and app-role passwords, URL-encode them in their connection strings, and set the domain. Keep `.env` private and restrict filesystem access.

```sh
docker compose -f compose.production.yaml config --quiet
docker compose -f compose.production.yaml build
docker compose -f compose.production.yaml up -d
# Create the first owner interactively; no default shop password exists.
docker compose -f compose.production.yaml run --rm --no-deps api python -m app.bootstrap
```

Caddy obtains an HTTPS certificate for the domain. Only Caddy publishes host ports; PostgreSQL and FastAPI remain internal. Persistent volumes retain PostgreSQL data and certificates. A separate migration service applies Aerich upgrades before the API starts. The runtime database user receives DML privileges, not schema-creation privileges. The initial database role script runs only on a fresh volume. Existing databases need equivalent grants applied by their administrator; do not erase volumes to rerun initialization.

Secure cookies and HTTPS origin validation are required in production. Caddy sets a restrictive content security policy and transport headers. PDF fonts and logos are served locally. Public registration is absent. API documentation is disabled in production. Rate limiting uses the API connection's source address; behind the supplied proxy the small shop shares the login attempt budget. Do not trust arbitrary forwarded IP headers.

## Back up

Take daily PostgreSQL custom-format backups, encrypt off-host copies, and retain multiple generations. Database backups include shop settings and logos. Keep configuration/secrets separately with restricted access. Do not rely solely on the Docker volume.

```sh
docker compose -f compose.production.yaml exec -T db pg_dump -U shop -d shop -Fc > shop-backup.dump
```

Check the command exit status and backup size before accepting a backup. Test restoration regularly. Protect dumps as confidential customer and financial records.

For local Windows backups, use `.tools/pgsql/bin/pg_dump.exe` with `-h 127.0.0.1 -p 55432 -U shop -d shop -Fc -f <backup-path>`, entering credentials interactively or through a protected pgpass file. Avoid PowerShell binary redirection on older versions.

## Restore into an isolated database

```sh
# Choose a fresh target, leaving the live database untouched.
docker compose -f compose.production.yaml exec db createdb -U shop shop_restore_test
cat shop-backup.dump | docker compose -f compose.production.yaml exec -T db pg_restore -U shop -d shop_restore_test --no-owner
```

Inspect users, receipt counts, payment totals, balances, stock lots/movements, worker earnings and the latest receipts. Run read-only reconciliation before planning a production switch. Do not run `--clean`, drop databases, reset migrations or remove volumes without explicit approval and a verified backup.

## Updates

Back up first, review dependency changes and migrations, then run checks and build images. Schema upgrades are transactional where supported. Do not automatically downgrade financial schemas or roll back databases after new records have been written. Rollback plans must preserve those records.

## Known verification limits

Local PostgreSQL migrations, backend tests, frontend build/lint/component tests and headless Edge workflows are checked in this workspace. Docker image execution, certificate issuance, off-host restoration, physical printers and touch hardware require the target environment. Development-tool npm advisories and Aerich's Windows event-loop deprecation warnings are documented in README; check current advisories before a release.
