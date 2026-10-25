# Team workflow

Repository: https://github.com/SaqlainSQX/adhd_ivp

Clone the repository, install the locked environment, and create a short-lived
feature branch for one bounded task:

```powershell
git clone https://github.com/SaqlainSQX/adhd_ivp.git
cd adhd_ivp
uv sync --frozen --extra dev
git switch -c feature/source-inventory
```

Before requesting review:

```powershell
uv run ruff check .
uv run pytest
git add <specific-files>
git commit -m "Describe the resulting change"
git push -u origin feature/source-inventory
```

Open a pull request against `main`, explain the behavior and record validation.
For an experiment include the input/checkpoint hashes, source partition, configuration,
label costs and limitations. Do not commit data or weights to solve a missing-input
problem. Do not copy source-specific private paths into shared configurations.

Keep `main` reviewable. Repository administrators should enable required PR review
and CI branch protection in GitHub when the team is ready; the local configuration
does not enforce these remote settings. Collaborators need GitHub access separately.
No teammate invitations or branch-protection changes have been made automatically.

Before starting more work:

```powershell
git switch main
git pull --ff-only
git switch -c feature/next-task
```

Discuss methodology changes in their own PR. Keep a revision history and declare
any evaluation data already inspected. Tests should verify statistical behavior,
data boundaries or failure conditions, rather than mirroring implementation steps.
