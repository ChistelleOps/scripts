# Engineering backlog bootstrap

Creates **seven public lab repositories** and their GitHub issues, preserving the existing planning issues in `ChistelleOps/engineering-project-management` (#4 through #10). Each lab has five phase issues and five technical sub-issues per phase: **35 phase issues + 175 technical issues**.

## Requirements

- Python 3.9+
- GitHub CLI (`gh`), authenticated with `gh auth login`
- Permission to create repositories and issues and link GitHub sub-issues (including across repositories)

## Usage

```bash
gh auth status
python3 build.py                           # offline dry run: no changes
python3 build.py --only cicd-gitops-automation  # preview one repository
python3 build.py --apply --only cicd-gitops-automation  # create/test first
python3 build.py --apply                   # remaining six, skip existing
```

Use `--private-all` only if you want **newly created** repositories private. It does not alter visibility of existing repositories.

## Safety

- Dry-run is the default. It reads local JSON and does not contact GitHub.
- Apply verifies the existing planning issue, reuses existing repositories and issues, and checks both open and closed issues by title.
- If multiple issues share the same title, it stops rather than guessing.
- On rerun, existing issues are reused and existing parent/sub-issue relationships are skipped.
- If GitHub denies cross-repository sub-issue links, it stops and reports the failure. Fix permissions or structure before retrying.
- No GitHub Project board sync, cloud deployments, or issue closure is performed.
- **Inspect `roadmaps.json` first.** The 5-phase structure for each roadmap is a proposed expansion, not an exact transcription of the existing issue descriptions.
- To avoid unexpected public repositories, review visibility and names before applying.

## Personal interview playbook

Create separately as **private** when ready:

```bash
gh repo create ChistelleOps/devops-sre-interview-playbook --private --add-readme
```

No interview playbook is created by `build.py`.
