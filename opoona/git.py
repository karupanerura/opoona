# -*- coding: utf-8 -*-

import re
import subprocess
from collections import namedtuple

import six

RepositoryInfo = namedtuple('RepositoryInfo', ['host', 'owner', 'name'])

def _execute(command):
    proc = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output, _ =  proc.communicate()
    return output.strip().decode('utf-8')

def get_repository_info():
    url = _execute('git config remote.origin.url')

    match = re.match(r'^[^@]+@([^:]+):([-_a-zA-Z0-9]+)/([-_a-zA-Z0-9]+)\.git$', url)
    if match is None:
        match = re.match(r'^(?:ssh|https?)://[^@]+@([^:]+)(?::[0-9]+)?/([-_a-zA-Z0-9]+)/([-_a-zA-Z0-9]+)\.git$', url)

    if match:
        return RepositoryInfo(host=match.group(1), owner=match.group(2), name=match.group(3))
    return None

def is_inside_work_tree():
    if _execute('git rev-parse --is-inside-work-tree') == 'true':
        return True
    return False

def is_dirty():
    if len(_execute('git diff --raw')) > 0:
        return True
    if len(_execute('git diff --cached --raw')) > 0:
        return True
    return False

def get_branch():
    return _execute('git rev-parse --symbolic --abbrev-ref HEAD')

def has_branch(name):
    return len(_execute('git rev-parse --verify {0} --quiet'.format(name))) > 0

def checkout(branch):
    print('checkout {0}'.format(branch))
    _execute('git checkout -b {0}'.format(branch))

def commit(branch):
    print('create empty commit')
    message = six.u('chore(empty): begin task')
    _execute(six.u('git commit --allow-empty  -m \'{0}\'').format(message))

def push(branch):
    print('pushing to origin...')
    _execute('git push -u origin {0}'.format(branch))
