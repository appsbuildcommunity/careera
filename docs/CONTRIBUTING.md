# Contributing

Keep contributions small, clear, and focused.

## Commits

We follow [Conventional Commits](https://www.conventionalcommits.org/).

To make this easy, we have provided a Git commit template. Configure your local repository to use it by running:

```bash
git config --local commit.template .gitmessage
```

The template contains all the rules and types you need as comments (they won't be included in your final commit message).

To use the template, simply run:
```bash
git commit
```
This will open your terminal editor with the template pre-loaded.

For quick, simple commits, you can bypass the template by manually providing the message:
```bash
git commit -m "type: your brief message here"
```

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

## Edits
List the main areas or files that were edited.
```
