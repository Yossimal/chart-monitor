# chart-monitor Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-18

## Active Technologies
- Python 3.11+ (Backend), Vanilla JS (Frontend) + FastAPI, RestrictedPython, sqlite3 (stdlib), sql.js (bundled WASM v1.13) (006-sql-collector)
- In-memory SQLite (ephemeral per collect() call, backend), in-memory sql.js (ephemeral per query, frontend) (006-sql-collector)

- Python 3.11+ (Backend), Vanilla JS (Frontend) + FastAPI, RestrictedPython, DuckDB (backend SQL engine), sql.js (frontend SQL engine, bundled WASM) (004-sql-support)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src; pytest; ruff check .

## Code Style

Python 3.11+ (Backend), Vanilla JS (Frontend): Follow standard conventions

## Recent Changes
- 006-sql-collector: Added Python 3.11+ (Backend), Vanilla JS (Frontend) + FastAPI, RestrictedPython, sqlite3 (stdlib), sql.js (bundled WASM v1.13)

- 004-sql-support: Added Python 3.11+ (Backend), Vanilla JS (Frontend) + FastAPI, RestrictedPython, DuckDB (backend SQL engine), sql.js (frontend SQL engine, bundled WASM)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
