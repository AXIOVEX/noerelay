# /noerelay-resume

Resume work on this project using prior NoeRelay state.

## Instructions

1. Run the audit to check prior state:
```bash
curl -s -X POST http://localhost:8080/v1/noerelay/projects/audit \
  -H "Authorization: Bearer noerelay-local-development-key-0001" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "default"}'
```

2. If `status` is `"in_progress"`:
   - Report the run count and last activity
   - Read `PLAN.md` or `docs/` for the current plan
   - Ask: "Where should I pick up from?"

3. If `status` is `"no_prior_work"`:
   - Tell the user there's no prior state
   - Suggest running `/noerelay-new` instead
