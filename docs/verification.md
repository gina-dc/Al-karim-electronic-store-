# Verification record

Verified locally on 9 November 2026 (Asia/Karachi), using Python 3.14.6, uv 0.11.23, PostgreSQL 17.11, Node.js 24 and headless Microsoft Edge.

| Check | Result |
| --- | --- |
| Backend Pytest suite | 18 passed |
| Ruff lint | Passed |
| Frontend TypeScript/Vite production build | Passed |
| ESLint | Passed |
| Frontend component test | 1 passed |
| Desktop/mobile Playwright workflows | 4 passed |
| All six Aerich migrations on a new PostgreSQL database | Passed |
| Applying migrations again | No pending migrations |
| Python pip-audit of installed dependencies | No known vulnerabilities found |
| npm production dependency audit | Zero vulnerabilities |
| Compose YAML parsing | Passed |
| Urdu, Roman Urdu, English and numeric PDF text | Embedded fonts and rendered output verified |
| Browser print layout | A4 PDFs generated in browser tests |
| Simulated unavailable printer | Saved receipt remained accessible; download fallback shown |

Browser workflows cover Urdu login/RTL, English switching, customer and inventory registration, purchases, sales, repairs, job assignment/completion, partial worker payment, partial/full customer payment, refresh persistence, PDF download, mobile navigation, printing fallback and Urdu receipt tables.

The development-only npm audit still reports 15 advisories (2 low and 13 moderate) in the existing shadcn/lint dependency tree. No forced breaking-version changes were applied. Aerich emits Windows event-loop deprecation warnings under Python 3.14.

Docker builds/running containers, production TLS issuance, off-host backup restoration, physical printers and physical mobile devices have not been verified here. Use the staging/release procedure in deployment.md before live business use. No production deployment was performed.

The shop database contains no test login or synthetic business records. Tests use separate databases. The first real owner must be created with the interactive bootstrap command documented in README.md.
