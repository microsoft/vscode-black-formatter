# Copilot Instructions for vscode-black-formatter

## Development Guidelines

- When introducing new functionality, add basic tests following the existing repo test structure.
- Always make sure all tests pass before submitting changes.
- Always ensure documents and code are linted before submitting.
- Do multiple rounds of review and refinement.
- Do not feature creep — keep changes focused on the task at hand.

## Pull Request Guidelines

- Every PR must have at least one label (e.g., `debt`, `bug`, `feature`). The "Ensure Required Labels" status check will block merging without one.
- Always enable auto-merge (squash) on PRs after creating them: `gh pr merge <number> --repo microsoft/vscode-black-formatter --squash --auto`
- PRs require approval from someone other than the last pusher before merging.
