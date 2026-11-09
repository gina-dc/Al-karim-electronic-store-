# Frontend

React, TypeScript, Vite and Tailwind interface with Urdu RTL support.

From this directory:

```powershell
npm.cmd ci --include=dev
npm.cmd run dev
```

Open http://localhost:5173. The FastAPI backend must also run on port 8000 for login and business records. See the root README for database setup, migrations and first-owner creation.

Checks: `npm.cmd run build`, `npm.cmd run lint`, `npm.cmd run test`, `npm.cmd run test:e2e`.

The optional `.env.example` contains only the local API proxy URL; never put database credentials in frontend environment files.

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
