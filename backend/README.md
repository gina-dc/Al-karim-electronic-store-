# Backend — Al-Karim electric service

Run these commands from the project root in the first terminal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-local-db.ps1
cd backend
uv run aerich upgrade
uv run uvicorn app.main:app --reload
```

For first-time owner setup, run `uv run python -m app.bootstrap` once from `backend` in another terminal. It asks for the owner credentials interactively.

From the project root in a separate terminal:

```powershell
cd frontend
npm.cmd ci --include=dev
npm.cmd run dev
```

Open **http://localhost:5173**. Keep the backend and frontend terminals running. API docs are at http://localhost:8000/api/docs.

## Receipt identity

**الکریم الیکٹرک سروس — Al-Karim electric service**

Phone: **03017458983 / 03346141413**

Address: **اظہر کلینک کے سامنے، مسلم پبلک ہائی اسکول کے قریب، پیپلز کالونی، ممتاز آباد، ملتان**

English: In front of Azhar clinic near muslim public high school peoples colony mumtaz abad multan.

Migration 7 adds editable Urdu name/address settings alongside English. Browser receipts and PDFs use those settings. Receipt counterparties are labelled خریدار (buyer) for sales, فروخت کنندہ (seller) for purchases, and گاہک (customer) for repairs, with their recorded name, phone and address. Select the saved party while creating a receipt; enter missing contact details under Customers. User-entered names and descriptions are never automatically translated.

After pulling changes, run `uv run aerich upgrade` and restart the backend. Shop identity can be changed through Settings.

Entry point: `app.main:app`. PostgreSQL is required; startup never recreates tables. See the root README and docs for accounting policy, testing, deployment and backups.

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

## Opening the correct page

Use http://localhost:5173 for the shop interface. The API root at http://127.0.0.1:8000 shows a status page and frontend link. `/api/v1/auth/me` returns 401 until you log in; this is expected. Dashboard graphs were removed at the owner's request; financial totals and record tables remain.
