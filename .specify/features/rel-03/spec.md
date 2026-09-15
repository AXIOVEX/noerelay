# Spec: REL-03 — Seven-consecutive-day controlled pilot

> Work package `REL-03` · NoeRelay GA Completion Program
> Source: `docs/ga-completion-orchestrator-plan.md` §6/§7 · `spec/coverage-manifest.json`
> Primary owner: `ROLE-ORCH`, `ROLE-HUMAN` · Depends on: `REL-01`, `REL-02`

## Problem

Run a seven-consecutive-day controlled pilot for the named customer-like cohort with a spend ceiling and no unresolved launch blocker.

## Goals

- Run a seven-consecutive-day controlled pilot.
- Stay within the approved spend and error budget.
- Close all launch blockers and rerun the regression suite.

## Non-goals

- No pilot day with an unresolved launch blocker.
- No spend beyond the approved ceiling.

## Requirements

Supporting capability package: `REL-03` is not a primary owner of any MUST requirement in `spec/coverage-manifest.json`. It contributes to the routed capabilities and is exercised through the release tests of the packages that own the requirements it supports.

## Acceptance criteria

- [ ] Seven consecutive days with no unresolved launch blocker and within budget.
- [ ] The regression suite is rerun and passes at the end of the window.
