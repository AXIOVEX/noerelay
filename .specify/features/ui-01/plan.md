# Plan: UI-01 — Operator console for onboarding, runs, evidence, cost, approvals, policy

## Approach

Generate the TypeScript client from OpenAPI. The console never owns authority and never receives secrets after creation. Pass role-scoped browser/API end-to-end, accessibility, secret-redaction, pagination/export, and pilot usability tests.

## Components

- `crates/noerelay-gateway/src/admin.rs (console backend APIs)`
- `tests/test_dashboard_ui.py (dashboard UI tests)`
- `tests/dashboard_requirements.py (dashboard requirements)`

## Risks

- The console displays a secret after creation.
- A role-scoped view leaks a foreign tenant's data.
