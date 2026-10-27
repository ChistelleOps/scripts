# GCP Platform Engineering — GitHub issue automation

Creates **12 phase issues and 107 technical issues** from `gcp_roadmap.json` in your chosen implementation repository. Links each phase to the existing **`ChistelleOps/engineering-project-management#2`** roadmap and links each technical issue to its phase.

**Planning only:** Creating GitHub issues does not create GCP resources or incur cloud infrastructure costs.

## Prerequisites

- Python 3.9+ and GitHub CLI (`gh`)
- `gh auth login` and `gh auth status`
- Permission to create issues in the target repository and link sub-issues in the private planning repository. GitHub may require extra authorization or token scopes for issue sub-issue endpoints.
- The implementation repository must already exist, with Issues enabled. **Use its exact URL slug, not the GitHub Project name or issue title.**

Find repository names:

```bash
gh repo list ChistelleOps --limit 100
```

For commands below, replace `YOUR-GCP-REPO` with the exact repository slug. If the repo does not exist yet, create it on GitHub first (public for portfolio, with no credentials).

## 1. Preview (no changes)

```bash
python3 create_gcp_issues.py --lab-repo YOUR-GCP-REPO
```

## 2. Test one phase

```bash
python3 create_gcp_issues.py --apply --lab-repo YOUR-GCP-REPO --start GCP-01 --end GCP-01
```

Confirm GitHub shows GCP-01 under `engineering-project-management#2` and its eight technical sub-issues underneath it.

## 3. Create remaining phases

```bash
python3 create_gcp_issues.py --apply --lab-repo YOUR-GCP-REPO --start GCP-02 --end GCP-12
```

## Behavior and safety

- Default is dry-run. `--apply` is required for writes.
- Reads **open and closed** issues and reuses an issue with the same normalized title instead of creating another.
- Rechecks existing parent/sub-issue links and skips links already present.
- Stops on GitHub API/link errors; re-run after correcting them.
- Does not update issue descriptions on reused issues, delete anything, or mark implementation tasks complete.
- `--allow-unlinked` exists only as an explicit workaround if linking is unavailable; normally leave it off.
- Does not add issues to a GitHub Project board automatically; the issue hierarchy and board membership are separate concepts.
- Does not validate the exact content of the original GCP roadmap #2: the JSON is a proposed detailed implementation of the previously discussed 12-phase GCP plan. **Review the JSON and preview before applying**; adjust titles/tasks to avoid conflicting with existing roadmap work.

## Custom options

```bash
python3 create_gcp_issues.py --help
```

For a repo in a different organization, pass `--owner`. The planning repo and roadmap issue can be changed with `--planning-repo` and `--roadmap-issue`.
