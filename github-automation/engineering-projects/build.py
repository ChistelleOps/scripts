#!/usr/bin/env python3
"""Idempotent GitHub repository and issue bootstrap. Dry-run by default."""
import argparse,json,subprocess,sys,re
from pathlib import Path
DATA=Path(__file__).with_name('roadmaps.json')
def run(args, input_data=None):
 p=subprocess.run(args,input=input_data,text=True,capture_output=True)
 if p.returncode: raise RuntimeError(f"{' '.join(args[:3])}: {p.stderr.strip()}")
 return p.stdout.strip()
def api(path,method='GET',data=None):
 args=['gh','api',path,'--method',method]
 if data is not None: args+=['--input','-']
 out=run(args,json.dumps(data) if data is not None else None)
 return json.loads(out) if out else {}
def issues(repo):
 out=run(['gh','api',f'repos/{repo}/issues?state=all&per_page=100','--paginate','--slurp'])
 return [i for page in json.loads(out) for i in page if 'pull_request' not in i]
def norm(s): return ' '.join(s.casefold().split())
def ensure_issue(repo,index,title,body):
 matches=index.get(norm(title),[])
 if len(matches)>1: raise RuntimeError(f'Duplicate issue titles in {repo}: {title}')
 if matches:
  print('REUSE',repo,title);return matches[0]
 item=api(f'repos/{repo}/issues','POST',{'title':title,'body':body})
 index[norm(title)]=[item];print('CREATE',repo,item['number'],title);return item
def attach(repo,num,child):
 endpoint=f'repos/{repo}/issues/{num}/sub_issues'
 existing=api(endpoint)
 if any(x['id']==child['id'] for x in existing):return
 api(endpoint,'POST',{'sub_issue_id':child['id']})
 print('LINK',f'{repo}#{num}','->',child['number'])
def body_phase(phase):
 return '## Objective\n\n'+phase['objective']+'\n\n## Technical issues\n\n'+'\n'.join('- [ ] '+t for t in phase['tasks'])+'\n\n## Completion criteria\n\n- [ ] Labs implemented and tested\n- [ ] Documentation and evidence committed\n\n**Planning only: no implementation completed.**\n'
def body_task(t):
 return '## Objective\n\n'+t+'\n\n## Tasks\n\n- [ ] Plan a safe, reproducible implementation\n- [ ] Implement the configuration, code, or test\n- [ ] Validate expected behavior and troubleshoot failures\n- [ ] Document commands, results, and lessons learned\n- [ ] Remove temporary cloud resources and verify costs where applicable\n\n**Status: planned, not implemented.**\n'
def main():
 p=argparse.ArgumentParser()
 p.add_argument('--apply',action='store_true',help='Create repositories and issues; default only previews')
 p.add_argument('--owner',default='ChistelleOps')
 p.add_argument('--only',nargs='*',help='Repository slugs to process; default all seven')
 p.add_argument('--private-all',action='store_true',help='Make all newly created repositories private')
 p.add_argument('--data',type=Path,default=DATA)
 a=p.parse_args();data=json.loads(a.data.read_text()); selected=[x for x in data if not a.only or x['repo'] in a.only]
 if a.only and len(selected)!=len(set(a.only)):p.error('Unknown --only repository slug')
 print('APPLY' if a.apply else 'DRY RUN (no writes)')
 for d in selected:
  print(f"{d['repo']}: roadmap #{d['roadmap']}; {len(d['phases'])} phases; {sum(len(p['tasks']) for p in d['phases'])} technical issues; visibility: {'private' if a.private_all else d['visibility']}")
 if not a.apply:return
 planning=f'{a.owner}/engineering-project-management'
 for d in selected:
  repo=f"{a.owner}/{d['repo']}"
  roadmap=api(f"repos/{planning}/issues/{d['roadmap']}")
  if not roadmap.get('title'):raise RuntimeError('Roadmap issue not found')
  try:api(f'repos/{repo}');print('REUSE REPO',repo)
  except RuntimeError as e:
   if '404' not in str(e):raise
   args=['gh','repo','create',repo,'--description',d['description'],'--add-readme', '--private' if a.private_all or d['visibility']=='private' else '--public']
   run(args);print('CREATE REPO',repo)
  index={}
  for i in issues(repo):index.setdefault(norm(i['title']),[]).append(i)
  for ph in d['phases']:
   parent=ensure_issue(repo,index,ph['title'],body_phase(ph))
   attach(planning,d['roadmap'],parent)
   for i,t in enumerate(ph['tasks'],1):
    title=f"{ph['key']}.{i} — {t}"
    child=ensure_issue(repo,index,title,body_task(t))
    attach(repo,parent['number'],child)
 print('Completed. Verify hierarchy in GitHub. No board synchronization attempted.')
if __name__=='__main__':
 try:main()
 except (RuntimeError,ValueError) as e:print('ERROR:',e,file=sys.stderr);sys.exit(1)
