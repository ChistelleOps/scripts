# Kubernetes Production Operations — GitHub Issue Automation

Creates the remaining **K8S-06 through K8S-15** phase issues and 80 technical issues in `ChistelleOps/Kubernetes-Production-Operations`, then links phase issues under the existing `ChistelleOps/engineering-project-management#3` roadmap and technical issues under their phase. **Does not touch K8S-00 through K8S-05.**

## Requirements

- Python 3.9+
- GitHub CLI (`gh`) installed and authenticated with `gh auth login`
- Permission to create issues in the lab repo and to modify issue hierarchy in both repos
- The `Kubernetes-Production-Operations` repository already created, with Issues enabled
- GitHub's sub-issue feature available for these repositories; cross-repository linking may depend on GitHub permissions or feature limitations

## Preview (no GitHub writes)

```bash
python3 create_k8s_issues.py
```

## Apply

```bash
gh auth status
python3 create_k8s_issues.py --apply
```

## Smaller batch

```bash
python3 create_k8s_issues.py --start K8S-06 --end K8S-06
python3 create_k8s_issues.py --apply --start K8S-06 --end K8S-06
```

## Safety and behavior

- Default is **dry-run**, which reads only the local JSON plan and makes no GitHub requests.
- Apply mode checks both repositories and the existing roadmap before writing.
- Existing open **or closed** issues with the exact normalized title are reused, not recreated.
- Existing sub-issue links are checked before attempting to add links.
- If a parent/sub-issue link fails, the script stops by default. Resolve the error and rerun safely. The `--allow-unlinked` option lets issue creation continue but may leave orphaned issues; use only intentionally.
- No issues are closed, updated, deleted, or marked done. Existing descriptions are not overwritten.
- No GitHub Project board membership is modified. This script builds the **GitHub Issues hierarchy** only.
- If your GitHub instance rejects cross-repository sub-issue links, keep phase issues and the technical issues in the lab repository and link to roadmap #3 manually, or adapt the planning approach.

## Edit the plan

All phase names, titles, and technical objectives are in `k8s_roadmap.json`. Edit it before applying. Every technical issue receives a common troubleshooting checklist; customize descriptions after creation if desired.

## Notes

The `gh api` REST sub-issue endpoints require a GitHub version/account with sub-issue support. The script uses the issue's REST `id` (not its issue number) to attach it. GitHub API or permission errors are printed; no credentials are embedded in this project.
