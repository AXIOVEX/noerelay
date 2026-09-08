# /noerelay-status

Check the current NoeRelay project state and report back.

## Instructions

1. Run this command to check project state:
```bash
curl -s -X POST http://localhost:8080/v1/noerelay/projects/audit \
  -H "Authorization: Bearer noerelay-local-development-key-0001" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "default"}'
```

2. Also check gateway health:
```bash
curl -s http://localhost:8080/ready
```

3. Report:
   - Gateway status (ready/degraded)
   - Project state (new/in-progress, run count, last activity)
   - Available models: `curl -s http://localhost:8080/v1/models -H "Authorization: Bearer noerelay-local-development-key-0001"`

4. If the project is in-progress, summarize what was done previously based on the audit response.
