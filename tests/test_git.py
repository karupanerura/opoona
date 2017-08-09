# -*- coding: utf-8 -*-

import os
import unittest
import tarfile
import subprocess

from backports import tempfile
from mock      import patch
from six       import StringIO

from opoona import git

class TestGetRepositoryInfo(unittest.TestCase):
    def setUp(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        self.tempdir  = tempfile.TemporaryDirectory()
        tarfile.open(os.path.join(self.data_dir, 'git.tar.bz2'), 'r:bz2') \
            .extractall(self.tempdir.name)
        self.git_work_tree     = os.path.join(self.tempdir.name, 'git')
        self.git_dir           = os.path.join(self.git_work_tree, '.git')
        self.old_git_dir       = os.environ.get('GIT_DIR', '')
        self.old_git_work_tree = os.environ.get('GIT_WORK_TREE', '')
        self.old_cwd           = os.getcwd()
        os.environ['GIT_DIR']       = self.git_dir
        os.environ['GIT_WORK_TREE'] = self.git_work_tree
        os.chdir(self.git_work_tree)

    def tearDown(self):
        os.environ['GIT_DIR']       = self.old_git_dir
        os.environ['GIT_WORK_TREE'] = self.old_git_work_tree
        os.chdir(self.old_cwd)
        self.tempdir.cleanup()

    def test_get_repository_info_for_basic_style(self):
        url     = 'git@github.com:FOO/BAR.git'
        command = 'git config remote.origin.url {0}'.format(url)
        subprocess.call(command, shell=True)

        repository = git.get_repository_info()
        self.assertEqual(repository.host, 'github.com')
        self.assertEqual(repository.owner, 'FOO')
        self.assertEqual(repository.name, 'BAR')

    def test_get_repository_info_for_enterprize(self):
        url     = 'git@github.example.com:BAR/BUZ.git'
        command = 'git config remote.origin.url {0}'.format(url)
        subprocess.call(command, shell=True)

        repository = git.get_repository_info()
        self.assertEqual(repository.host, 'github.example.com')
        self.assertEqual(repository.owner, 'BAR')
        self.assertEqual(repository.name, 'BUZ')

    def test_get_repository_info_for_ssh_with_port(self):
        url     = 'ssh://example-user@github.example.com:8080/FOO/BUZ.git'
        command = 'git config remote.origin.url {0}'.format(url)
        subprocess.call(command, shell=True)

        repository = git.get_repository_info()
        self.assertEqual(repository.host, 'github.example.com')
        self.assertEqual(repository.owner, 'FOO')
        self.assertEqual(repository.name, 'BUZ')

    def test_get_repository_info_for_https(self):
        url     = 'https://example-user@github.example.com/FOO/BUZ.git'
        command = 'git config remote.origin.url {0}'.format(url)
        subprocess.call(command, shell=True)

        repository = git.get_repository_info()
        self.assertEqual(repository.host, 'github.example.com')
        self.assertEqual(repository.owner, 'FOO')
        self.assertEqual(repository.name, 'BUZ')

    def test_is_inside_work_tree_yes(self):
        self.assertTrue(git.is_inside_work_tree())

    def test_is_inside_work_tree_no(self):
        d = tempfile.TemporaryDirectory()
        os.chdir(d.name)
        os.environ['GIT_WORK_TREE'] = d.name
        os.environ['GIT_DIR']       = ''
        self.assertFalse(git.is_inside_work_tree())
        d.cleanup()

    def test_is_dirty_not_dirty(self):
        self.assertFalse(git.is_dirty())

    def test_is_dirty_untracked(self):
        path = os.path.join(self.git_work_tree, 'FOO')
        with open(path, 'a') as f:
            f.write('FOO')
        self.assertFalse(git.is_dirty())

    def test_is_dirty_not_added(self):
        path = os.path.join(self.git_work_tree, 'README.md')
        with open(path, 'a') as f:
            f.write('FOO')
        self.assertTrue(git.is_dirty())

    def test_is_dirty_added(self):
        path = os.path.join(self.git_work_tree, 'FOO')
        with open(path, 'a') as f:
            f.write('FOO')
        subprocess.call('git add --all', shell=True)
        self.assertTrue(git.is_dirty())

    def test_get_branch(self):
        self.assertEqual(git.get_branch(), 'master')

    def test_has_branch_exists(self):
        self.assertTrue(git.has_branch('master'))

    def test_has_branch_not_exists(self):
        self.assertFalse(git.has_branch('XXX-unknown'))

    @patch('sys.stdout', new_callable=StringIO)
    def test_checkout(self, stdout):
        self.assertEqual(git.get_branch(), 'master')
        git.checkout('new-branch')
        self.assertEqual(git.get_branch(), 'new-branch')
        self.assertEqual(stdout.getvalue(), 'checkout new-branch\n')

    @patch('sys.stdout', new_callable=StringIO)
    def test_commit(self, stdout):
        git.commit('new-branch')
        command = 'git log -n 1 --pretty="format:%s"'
        message = subprocess.check_output(command, shell=True).decode('utf-8')
        self.assertEqual(message, 'chore(empty): begin task')
        self.assertEqual(stdout.getvalue(), 'create empty commit\n')

    @patch('sys.stdout', new_callable=StringIO)
    def test_push(self, stdout):
        # setup bare git repository
        temp      = tempfile.TemporaryDirectory()
        tar_path  = os.path.join(self.data_dir, 'bare.git.tar.bz2')
        bare_path = os.path.join(temp.name, 'bare.git')
        tarfile.open(tar_path, 'r:bz2').extractall(temp.name)

        # set remote branch
        command = 'git remote add origin {0}'.format(bare_path)
        subprocess.call(command, shell=True)

        # push to remote repository
        git.push('master')

        # check
        command = 'git ls-remote origin master'
        remote  = subprocess.check_output(command, shell=True).decode('utf-8')
        self.assertGreater(len(remote), 0)
        self.assertEqual(stdout.getvalue(), 'pushing to origin...\n')

        # cleanup
        temp.cleanup()
