# Electronics Shop Management System

Urdu-first electronics sales, purchases, repairs, inventory and worker payments for an owner and a small staff. React/TypeScript/Vite frontend; FastAPI/Tortoise/PostgreSQL backend. All business records are persisted. There are no production demo accounts or seeded business transactions.

## Start locally on this Windows workspace

Python 3.14, uv and Node.js are installed. PostgreSQL 17 binaries are available in the ignored `.tools/pgsql` directory; this directory is local tooling and is not part of the source distribution.

```powershell
# From the project root
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-db.ps1
uv sync --all-packages
cd backend
uv run aerich upgrade
uv run python -m app.bootstrap
uv run uvicorn app.main:app --reload
```

The bootstrap command asks for the owner's username, display name and a password of at least 12 characters. It does not accept a second initial owner once one exists. Create the other accounts from Settings after signing in. No password is hardcoded for the real shop database.

In a second terminal:

```powershell
cd frontend
npm.cmd ci --include=dev
npm.cmd run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/api/docs. The database binds only to `127.0.0.1:55432`; it persists in `.runtime/postgres-data`. Generated local credentials are in ignored files. `backend/.env` takes precedence over the example configuration; do not publish it.

To use an existing PostgreSQL server, copy `backend/.env.example` to `backend/.env` and set `DATABASE_URL`. To start a Docker development database instead, copy root `.env.example` to `.env`, set a random password, and run `docker compose up -d db`; configure the backend URL to match port 5432 and those credentials. Never point tests at your shop database.

## Implemented workflows

- Argon2id login; expiring server-side sessions; HttpOnly cookies; CSRF validation; owner/manager/staff permissions; audit logs; owner account administration.
- Reusable customers, walk-ins, searchable receipts, editable drafts, transaction-safe sequential numbering, atomic posting with initial payment, later partial payments, balance calculation, and payment corrections.
- Stock purchases and sales, FIFO cost lots, serialized-unit validation, separate condition/availability, reservation of a complete catalog entry, movement history, and controlled erroneous-receipt voids.
- Workers without automatic logins, receipt-item-linked jobs, completion-based earnings, duplicate-safe partial payroll, monthly statements and payment receipt PDFs.
- Real dashboard KPIs, record tables, date-filtered financial reports, expenses, CSV/PDF exports, and owner-only financial summaries.
- Shop identity, logo, Urdu/English, light/dark themes, A4/80 mm PDF receipt formats, browser printing and mobile navigation.

The application intentionally excludes tax, returns, exchanges, customer credit accounts and opening balances. Receipt dues and partial payments remain supported. See [accounting policy](docs/accounting-policy.md) for recognition and correction rules.

## Verification

```powershell
# Root: dedicated PostgreSQL test database only
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/test-backend.ps1
cd backend
uv run ruff check app tests
uv run ruff format --check app tests
cd ../frontend
npm.cmd run build
npm.cmd run lint
npm.cmd run test
npm.cmd run test:e2e
npm.cmd audit --omit=dev
```

Browser tests use installed Microsoft Edge in headless mode, an isolated `shop_e2e_test` database, and ports 8001/5174. They create actual test transactions there. The test-only login is defined in `backend/tests/seed_e2e.py` and is never created in the shop database. Integration tests use `shop_test`, validate its name and apply the actual Aerich migrations before clearing test data. Screenshots and PDF inspections are saved in ignored `.runtime/`.

Tests cover receipt numbering races, atomic rollback, repeated payments, partial/complete balances, purchase accounting, stock deductions and overselling, completed worker earnings, payroll limits, unauthorized access, corrections, mixed-script PDFs, refresh persistence and mobile workflows.

Aerich currently emits Python 3.14 event-loop deprecation warnings on Windows. Frontend development tooling has npm.cmd audit advisories; the production-only dependency audit is checked separately. See [deployment](docs/deployment.md) for release checks and limitations.

## Repository layout

```text
backend/app/{api/v1,core,db,models,schemas,security,services,documents}
backend/migrations/models/
backend/tests/
frontend/src/{components,pages,lib}
frontend/e2e/
scripts/
deploy/
docs/
```

The root Git repository tracks both backend and frontend. Application entry point: `backend/app/main.py`.

## Shop receipt identity

Migration 6 configures the editable database settings used by browser receipts and PDFs:

- Name: Al-Karim electric service
- Phone: 03017458983 / 03346141413
- Address: In front of Azhar clinic near muslim public high school peoples colony mumtaz abad multan

Run `uv run aerich upgrade` from `backend` to apply this configuration. Existing logo, theme, receipt format, header and footer settings are preserved.

## Urdu receipts and buyer/seller details

Receipts and PDFs include both configured Urdu and English shop details:

- **الکریم الیکٹرک سروس** — Al-Karim electric service
- **فون:** 03017458983 / 03346141413
- **پتہ:** اظہر کلینک کے سامنے، مسلم پبلک ہائی اسکول کے قریب، پیپلز کالونی، ممتاز آباد، ملتان

The counterparty is labelled **خریدار / Buyer** for sales, **فروخت کنندہ / Seller** for purchases, and **گاہک / Customer** for repairs. Select a saved customer/party when creating the receipt to include their name, phone and address. Add missing contact information through Customers. Walk-in receipts remain available; missing details are not invented. Names and descriptions entered in Urdu, Roman Urdu or English are preserved without automatic translation.

Apply migration 7 with `uv run aerich upgrade` from `backend`, then restart the backend. Edit the Urdu and English identity fields in Settings. Existing receipts use the latest saved identity when viewed or downloaded again.

## Windows PowerShell troubleshooting

If PowerShell blocks the unsigned `npm.ps1` script, use `npm.cmd` explicitly:

```powershell
npm.cmd ci --include=dev
npm.cmd run dev
```

No execution-policy change is needed. Open http://localhost:5173 after Vite starts; keep the backend running in another terminal.

The owner password must contain **12 to 128 characters**. Typing in the password prompt is hidden. Setup now explains invalid passwords or confirmation mismatches and lets you retry without printing the password. From `backend`, run `uv run python -m app.bootstrap`. An account rejected during validation was not saved.

For the earlier `address_ur` migration error, use the corrected project files and run `uv run aerich upgrade` from `backend`. The migration supplies defaults for existing rows; do not reset migrations or delete the database.

If `vite is not recognized` appears, the local development dependencies are missing. Run `npm.cmd ci --include=dev` inside `frontend`, wait for it to finish successfully, then run `npm.cmd run dev`. Vite is a project dependency; no global Vite installation is needed.

### Windows EPERM while installing dependencies

Stop the running frontend with **Ctrl+C in its terminal before running `npm.cmd ci`**. Vite loads native files such as Lightning CSS that Windows locks while they are in use. Run `npm.cmd ci --include=dev` only for initial setup or when dependencies change; for normal startup, run only `npm.cmd run dev`. If an installation was interrupted, stop Vite and rerun the install command before restarting it. Do not delete the lockfile or run all terminals as Administrator to work around a running-server file lock.


