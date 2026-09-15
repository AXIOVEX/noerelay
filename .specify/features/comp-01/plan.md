# Plan: COMP-01 — Versioned compliance framework mappings

## Approach

Include SOC 2/ISO 27001/privacy mappings only when selected by authorized reviewers. Never print certified or compliant solely from a passing automated check.

## Components

- `docs/ (compliance mapping documents)`
- `xtask/ (evidence linkage for controls)`

## Risks

- A mapping claims certification without observed evidence.
- A control has no owner or review date.
