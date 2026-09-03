# AGENTS.md

## Purpose

This repository is a beginner-friendly learning project for Python, FastAPI,
HTTP APIs, testing, documentation, and eventually Microsoft Azure.

## Working principles

- Explain planned changes in plain language before making them.
- Prefer small, readable examples over production complexity.
- Keep the application runnable locally without an Azure account.
- Add or update tests when behavior changes.
- Update `README.md` when setup steps, routes, or commands change.
- Never commit secrets, credentials, subscription IDs, or local `.env` files.

## Azure safety rule

Do not deploy, sign in to Azure, run infrastructure changes, or create paid (or
potentially paid) Azure resources without the user's explicit approval first.
Before requesting approval, explain what would be created, why it is needed,
how it can be removed, and the likely cost implications.

Read-only explanations and local configuration examples are allowed. Prefer
local emulators or free local tooling when they meet the lesson's goal.

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload
```

Run tests with:

```bash
python -m pytest
```

## Code conventions

- Target Python 3.11 or newer.
- Add type hints to functions.
- Use Pydantic models for API request and response bodies.
- Return appropriate HTTP status codes and useful error details.
- Keep routes simple until the learning objective requires more structure.
