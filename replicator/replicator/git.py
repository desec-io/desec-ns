import logging
import os
import subprocess
from datetime import datetime


# TODO this is a copy of the implementation in desec-stack/api/replication.py!
from typing import List, Iterator, Iterable, Tuple


logger = logging.getLogger(__name__)


class ReplicationException(Exception):

    def __init__(self, message, **kwargs):
        super().__init__(message)
        for k, v in kwargs.items():
            self.__setattr__(k, v)


class GitRepositoryException(ReplicationException):
    pass


# TODO this is a copy of the implementation in desec-stack/api/replication.py!
class Repository:

    def __init__(self, path):
        self.path = path

    def _git(self, *args):
        cmd = ['/usr/bin/git'] + list(args)
        logger.debug('>>> ' + str(cmd))

        with subprocess.Popen(
                cmd,
                bufsize=0,
                cwd=self.path,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                env={  # avoid accessing $HOME/.config/git, our permissions are insufficient
                    'GIT_AUTHOR_NAME': 'deSEC API',
                    'GIT_COMMITTER_NAME': 'deSEC API',
                    'GIT_AUTHOR_EMAIL': 'api@desec.internal',
                    'GIT_COMMITTER_EMAIL': 'api@desec.internal',
                    'GIT_CONFIG': '/dev/null',
                },
        ) as p:
            rcode = p.wait()
            stderr = p.stderr.read()
            stdout = p.stdout.read()
            try:
                stderr, stdout = stderr.decode(), stdout.decode()
            except UnicodeDecodeError:
                GitRepositoryException('git stdout or stderr was not valid unicode!', cmd=cmd, rcode=rcode, stderr=stderr, stdout=stdout)

        logger.debug('\n'.join('<<< ' + s for s in stdout.split('\n')))
        return cmd, rcode, stdout, stderr

    def _git_do(self, *args, ignore_stderr=False):  # TODO modification of desec-stack version
        cmd, rcode, stdout, stderr = self._git(*args)

        if rcode != 0:
            raise GitRepositoryException(f'{cmd} returned nonzero error code', cmd=cmd, rcode=rcode, stdout=stdout, stderr=stderr)

        if stderr.strip() and not ignore_stderr:
            raise GitRepositoryException(f'{cmd} returned non-empty error output', cmd=cmd, rcode=rcode, stdout=stdout, stderr=stderr)

        return stdout

    def _git_check(self, *args):
        _, rcode, _, _ = self._git(*args)
        return rcode

    def commit_all(self, msg=None):
        self._git_do('add', '.')
        if self._git_do('diff', '--numstat', '--staged'):
            self._git_do('commit', '-m', msg or 'update')

    # modified
    def init(self, origin: str = None):
        self._git_do('init')
        if origin:
            self._git_do('remote', 'add', 'origin', origin)

    def get_head(self):
        return self.get_commit('HEAD')

    def get_commit(self, rev):
        try:
            commit_msg = self._git_do('show', rev, '--format=%s', '-s')[:-1]
            commit_hash = self._git_do('show', rev, '--format=%H', '-s')[:-1]
            return commit_msg, commit_hash
        except GitRepositoryException as e:
            return None, None

    def remove_history(self, before: datetime):
        rev = self._git_do('log', f'--before={before.isoformat()}Z', '-1', '--format=%H')
        with open(os.path.join(self.path, '.git', 'shallow'), 'w') as f:
            f.writelines([rev])
        self._git_do('reflog', 'expire', '--expire=now', '--all')
        self._git_do('gc', '--prune=now')

    # TODO locally added code below
    def clone(self, origin) -> str:
        return self._git_do(
            'clone', origin, '.',
            ignore_stderr=True,  # TODO this ignores a warning that the IP may be unknown for that key. Better ideas?
        )

    def pull(self) -> str:
        return self._git_do('pull', ignore_stderr=True)  # TODO this ignores a warning that the IP may be unknown for that key. Better ideas?

    def diff_files(self, rev1: str, rev2: str = 'HEAD') -> List[Tuple[str, str]]:
        diff = self._git_do('diff', '--name-status', '--no-renames', '-z', f'{rev1}..{rev2}')
        i = iter(diff.split('\x00'))
        ret = [(t, f) for t, f in zip(i, i)]  # take two consecutive elements from the list for each iteration of the loop
        return ret
