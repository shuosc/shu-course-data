import datetime
import os
import time

from github import Github

from helpers import DataRepo
from utils import is_major_change, term_diff

DATA = 'data'
INTERVAL_CRAWLER_TASK_RESULT = 'interval-crawler-task-result'

access_token = os.environ['GITHUB_TOKEN']
repository = os.environ['GITHUB_REPOSITORY']
g = Github(access_token)

old_repo = DataRepo(DATA)
new_repo = DataRepo(INTERVAL_CRAWLER_TASK_RESULT)


def is_major_update():
    if old_repo.current_term_id_list != new_repo.current_term_id_list:
        return True
    return False
    # disabled
    for term_id in new_repo.current_term_id_list:
        diff = term_diff(old_repo.terms_dict[term_id], new_repo.terms_dict[term_id])
        if any(is_major_change(*x) for x in diff):
            return True
    return False


def git_push(branch_name: str, force: bool):
    os.system(f'git add {INTERVAL_CRAWLER_TASK_RESULT}')
    os.system('git commit -am "$(TZ=Asia/Shanghai date)"')
    os.system(f'git subtree split --prefix {INTERVAL_CRAWLER_TASK_RESULT} --branch {INTERVAL_CRAWLER_TASK_RESULT}')
    os.system(f'git push{" --force" if force else ""} origin {INTERVAL_CRAWLER_TASK_RESULT}:{branch_name}')


def create_pull_request():
    git_push(INTERVAL_CRAWLER_TASK_RESULT, force=True)
    body_text = ''
    repo = g.get_repo(repository)
    pulls = repo.get_pulls(state='open', base=DATA, head=INTERVAL_CRAWLER_TASK_RESULT)
    edit_flag = False
    for i, pull in enumerate(pulls):
        if i > 0 or datetime.datetime.now() - pull.created_at > datetime.timedelta(days=15):
            pull.edit(state='closed')
        else:
            pull.edit(body=body_text)
            edit_flag = True
    if not edit_flag:
        repo.create_pull(title='chore: auto update', body=body_text, base=DATA, head=INTERVAL_CRAWLER_TASK_RESULT)


def close_pull_request_and_push_directly():
    repo = g.get_repo(repository)
    pulls = repo.get_pulls(state='open', base=DATA, head=INTERVAL_CRAWLER_TASK_RESULT)
    for pull in pulls:
        pull.edit(state='closed')
    git_push(DATA, force=False)


if __name__ == '__main__':
    if len(new_repo.current_term_id_list) == 0:
        print('Current term is empty. Failed to push.')
        exit(1)
    print('Check if this is a major update or not...')
    res = is_major_update()
    time.sleep(0.5)
    if res:
        print('Yes. Create a pull request...')
        create_pull_request()
    else:
        print('No. Push to data branch directly...')
        close_pull_request_and_push_directly()
    print('Finished.')
