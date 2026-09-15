# Plan: REL-03 — Seven-consecutive-day controlled pilot

## Approach

Operate the named profile for seven consecutive days under a spend and error budget. Track launch blockers and resolve them. Rerun the regression suite at the end of the window.

## Components

- `docs/ (pilot plan and daily records)`
- `evidence/ (pilot telemetry and blocker log)`

## Risks

- An unresolved launch blocker is carried past the seven-day window.
- Spend exceeds the approved ceiling during the pilot.
