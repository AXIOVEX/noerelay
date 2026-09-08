# Skill: Git via GitHub CLI (gh)

## Overview
Use `gh` CLI for all GitHub operations. Requires `gh auth login` to be completed.

## Key Commands

### Repository Operations
```bash
gh repo clone owner/repo
gh repo create my-project --private
gh repo view owner/repo
gh repo list --limit 10
```

### Pull Requests
```bash
gh pr create --title "Title" --body "Description"
gh pr list --state open
gh pr view 42
gh pr merge 42 --squash
gh pr diff 42
gh pr checkout 42
```

### Issues
```bash
gh issue create --title "Bug" --body "Details"
gh issue list --state open
gh issue view 15
gh issue close 15 --comment "Fixed in PR #42"
```

### Releases
```bash
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes"
gh release view v1.0.0
gh release list
```

### Actions / CI
```bash
gh run list --limit 5
gh run view <run-id>
gh run watch <run-id>
gh run view <run-id> --log-failed
gh workflow list
gh workflow run <workflow.yml>
```

### API (fallback for anything else)
```bash
gh api repos/owner/repo/contents/path/to/file
gh api repos/owner/repo/pulls --jq '.[].title'
```

## Platform Notes
- **Windows**: `gh` works in both PowerShell 5 and 7. Use `gh` directly.
- **macOS/Linux**: Install via `brew install gh` or `apt install gh`.
- **Auth**: `gh auth login` (interactive) or set `GITHUB_TOKEN` env var.

## Best Practices
- Always use `gh pr diff` before merging to review changes
- Use `gh run view --log-failed` for CI debugging
- Prefer `gh api` for complex queries over parsing JSON manually
