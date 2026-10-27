#!/usr/bin/env python3
"""Create an idempotent GitHub GCP platform issue hierarchy via GitHub CLI.
Default is dry-run. Requires gh auth login and repo issue permissions for --apply.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

DEFAULT_DATA = Path(__file__).with_name('gcp_roadmap.json')


def gh(*args, method=None, fields=None):
    cmd = ['gh', 'api']
    if method:
        cmd += ['--method', method]
    if fields:
        for key, val in fields.items():
            cmd += ['-f' if isinstance(val, str) else '-F', f'{key}={val}']
    cmd += list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(f"GitHub API failed: {' '.join(cmd[:3])}\n{result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def get_issues(repo):
    # Pagination includes closed issues: never recreate something simply because it was closed.
    issues = gh(f'repos/{repo}/issues?state=all&per_page=100', '--paginate', '--slurp')
    return [i for page in issues for i in page if 'pull_request' not in i]


def normalize(s):
    return ' '.join(s.casefold().split())


def index_issues(issues):
    out = {}
    for item in issues:
        out.setdefault(normalize(item['title']), []).append(item)
    return out


def body_parent(phase):
    checklist = '\n'.join(f"- [ ] {t['title']}" for t in phase['tasks'])
    return f"""## Objective

{phase['objective']}

## Planned technical issues

{checklist}

## Lab workflow

For each exercise: prepare a reproducible scenario, inspect symptoms, investigate with kubectl/logs/events/metrics, identify root cause, apply a fix, verify recovery, and write a short runbook and interview explanation.

## Completion criteria

- [ ] All technical scenarios implemented and validated
- [ ] Root causes and verification commands documented
- [ ] Sanitized manifests, runbooks, and incident reports committed

**Planning only:** these unchecked tasks are not implemented yet.
"""


def body_task(task):
    return f"""## Objective

{task['objective']}

## Checklist

- [ ] Prepare a safe, reproducible lab scenario
- [ ] Record symptoms and initial observations
- [ ] Investigate using kubectl, events, logs, and metrics where applicable
- [ ] Identify and document root cause
- [ ] Apply a fix and verify the result
- [ ] Save sanitized manifests, commands, and a short runbook
- [ ] Write a concise interview-ready explanation

## Completion criteria

- [ ] Reproduction, diagnosis, and recovery verified
- [ ] Findings documented in the public lab repository
"""


def create_issue(repo, title, body):
    return gh(f'repos/{repo}/issues', method='POST', fields={'title': title, 'body': body})


def subissue_ids(repo, parent_number):
    items = gh(f'repos/{repo}/issues/{parent_number}/sub_issues?per_page=100')
    return {x['id'] for x in items}


def attach_subissue(parent_repo, parent_number, child_id, strict=True):
    try:
        existing = subissue_ids(parent_repo, parent_number)
        if child_id in existing:
            return 'already linked'
        gh(f'repos/{parent_repo}/issues/{parent_number}/sub_issues', method='POST', fields={'sub_issue_id': child_id})
        return 'linked'
    except RuntimeError as exc:
        if strict:
            raise
        print(f'  WARNING: Could not link sub-issue: {exc}', file=sys.stderr)
        return 'link failed'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help='Write issues to GitHub; without this, preview only')
    ap.add_argument('--owner', default='ChistelleOps')
    ap.add_argument('--lab-repo', required=True, help='Exact GitHub repository slug, not a project display name')
    ap.add_argument('--planning-repo', default='engineering-project-management')
    ap.add_argument('--roadmap-issue', type=int, default=2)
    ap.add_argument('--start', default='GCP-01')
    ap.add_argument('--end', default='GCP-12')
    ap.add_argument('--data', type=Path, default=DEFAULT_DATA)
    ap.add_argument('--allow-unlinked', action='store_true', help='Continue if a GitHub parent/sub-issue link is unsupported; print warnings')
    args = ap.parse_args()
    data = json.loads(args.data.read_text())
    phases = data['phases']
    keys = [p['key'] for p in phases]
    if args.start not in keys or args.end not in keys or keys.index(args.start) > keys.index(args.end):
        ap.error(f'Choose a valid range from {keys}')
    selected = phases[keys.index(args.start):keys.index(args.end)+1]
    lab = f'{args.owner}/{args.lab_repo}'
    planning = f'{args.owner}/{args.planning_repo}'
    print(f"Mode: {'APPLY (writes to GitHub)' if args.apply else 'DRY RUN (no writes)'}")
    print(f'Lab: {lab}; roadmap: {planning}#{args.roadmap_issue}')
    print(f"Phases: {len(selected)}; technical issues: {sum(len(p['tasks']) for p in selected)}")
    for p in selected:
        print(f"  {p['title']} ({len(p['tasks'])} technical issues)")
    if not args.apply:
        print('\nNo GitHub changes made. Use --apply after reviewing the plan.')
        return 0

    # Preflight: validate repositories, parent issue, and access before writing anything.
    gh(f'repos/{lab}')
    roadmap = gh(f'repos/{planning}/issues/{args.roadmap_issue}')
    if 'GCP' not in roadmap.get('title', '').upper():
        raise RuntimeError(f"Roadmap issue #{args.roadmap_issue} title does not mention GCP: {roadmap.get('title')}")
    existing = index_issues(get_issues(lab))
    failures = []
    created = reused = linked = 0

    def ensure(title, body):
        nonlocal created, reused
        matches = existing.get(normalize(title), [])
        if len(matches) > 1:
            raise RuntimeError(f'Ambiguous duplicate title in {lab}: {title}. Resolve manually.')
        if matches:
            reused += 1
            print(f'REUSE #{matches[0]["number"]}: {title}')
            return matches[0]
        issue = create_issue(lab, title, body)
        existing[normalize(title)] = [issue]
        created += 1
        print(f'CREATE #{issue["number"]}: {title}')
        return issue

    for phase in selected:
        try:
            parent = ensure(phase['title'], body_parent(phase))
            # A phase belongs under the existing roadmap in the planning repo.
            result = attach_subissue(planning, args.roadmap_issue, parent['id'], not args.allow_unlinked)
            linked += result == 'linked'
            for task in phase['tasks']:
                child = ensure(task['title'], body_task(task))
                result = attach_subissue(lab, parent['number'], child['id'], not args.allow_unlinked)
                linked += result == 'linked'
        except Exception as exc:
            failures.append(f"{phase['key']}: {exc}")
            print(f'ERROR in {phase["key"]}: {exc}', file=sys.stderr)
            # Stop on link failures by default; re-running is safe after resolution.
            if not args.allow_unlinked:
                break
    print(f'\nCreated: {created}; reused: {reused}; new parent/sub-issue links: {linked}')
    if failures:
        print('Errors:\n' + '\n'.join(failures), file=sys.stderr)
        return 1
    print('Finished. Verify the hierarchy in GitHub before marking anything complete.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
