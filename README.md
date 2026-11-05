# oodo

A lightweight integration connecting Odoo with a mock implementation of KSeF (Polish National e-Invoicing System).

It automatically picks up posted customer invoices from Odoo, pushes them to KSeF, and writes the generated KSeF reference number back to the original invoice in Odoo.

```
Odoo ──XML-RPC──► Celery (Django) ──HTTP──► KSeF mock (FastAPI)
  ▲                     │
  └──── ksef_number ────┘
```

## Architecture Overview

- **`addons/ksef_number`**: An Odoo 18 module that extends customer invoices with `ksef_number` and `is_overdue` fields.
- **`app`**: Django + Celery backend handling sync scheduling, retries, and status tracking (accessible via Django Admin).
- **`ksef_mock`**: FastAPI mock service emulating KSeF behavior, featuring idempotency keys and configurable HTTP 503 error rates for testing resilience.

## Quickstart

Start the entire stack using Docker Compose:

```bash
docker compose up --build
```

### Service Access

| Service | URL | Credentials |
| --- | --- | --- |
| **Odoo** | [http://localhost:8069](http://localhost:8069) | `admin` / `admin` |
| **Django Admin** | [http://localhost:8000/admin](http://localhost:8000/admin) | `admin` / `admin` |
| **KSeF Mock API Docs** | [http://localhost:8001/docs](http://localhost:8001/docs) | —   |

> **Note:** On the initial run, Odoo takes roughly a minute to initialize database schemas and install modules.

### Testing the Workflow

1. Log into Odoo, open the **Invoicing** app, create a customer invoice, and click **Confirm**.
2. Within ~30 seconds, the job will be picked up by Celery and reflected in the Django Admin.
3. Once accepted by the mock KSeF, the `ksef_number` will automatically populate back on the Odoo invoice.

To test retry behavior under unstable network conditions, bump up the mock's failure rate:

```bash
KSEF_FAILURE_RATE=0.8 docker compose up -d ksef
```

## Local Development

Manage dependencies locally using `uv`:

```bash
uv sync
```

### Running Tests

```bash
docker compose run --rm web pytest
```

### Linting & Formatting

```bash
uv run ruff check .
uv run ruff format --check .
```
