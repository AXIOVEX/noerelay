# Project Constitution

> Living document. Update as the project evolves. Keep entries short and testable.

## Principles

1. **Spec before code.** Every feature starts from a spec, then a plan, then tasks.
2. **Evidence over assertion.** Claims about behavior are backed by a test or a run receipt.
3. **Small, reversible steps.** Prefer changes that are easy to review and roll back.
4. **Document state.** `docs/STATE.md` always reflects where the project stands.

## Conventions

- Feature work lives under `.specify/features/<feature>/` with `spec.md`, `plan.md`, `tasks.md`.
- Open gaps are tracked in `.noerelay/GAPS.md`.
- The verification matrix lives at `.noerelay/verification-matrix.md`.

## Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-09-10 | Reconcile spec-kit with the GA completion program: generate 51 work-package feature folders from `spec/coverage-manifest.json` + `docs/requirements.md` via `scripts/generate_specify_features.py`; treat the two G0–G8 taxonomies (plan §9.2 release-authority ladder; manifest evidence-collection ladder) as distinct and never rename manifest keys. | Evidence over assertion: requirement/test IDs are parsed from the machine contract at generation time, keeping the spec-kit layer in sync with `xtask` coverage/gate checks instead of re-typed copies. |
