# Contributing

Keep contributions small, clear, and focused.

## Commits

Use short commit messages in this format:

```text
type: brief description
type(scope): brief description
```

Examples:

```text
feat: add mongo-express for db visualization
fix: correct backend environment variable name
docs: update setup guide for Linux users
chore: clean up docker configuration
feat(backend): add profile update endpoint
```

Common types:

- `feat` for new functionality
- `fix` for bug fixes
- `docs` for documentation changes
- `chore` for tooling, config, or maintenance
- `refactor` for internal code cleanup without changing behavior
- `test` for adding or updating tests

## Pull Requests

Keep each pull request focused on one change or one related set of changes.

Use a clear PR title that matches the commit style:

```text
feat: add onboarding page
fix(backend): handle missing token
docs: update setup instructions
```

Use this structure in the PR description:

```md
## Summary
Briefly describe what changed and why.

## How to review
Mention the main files or areas to check.
```
