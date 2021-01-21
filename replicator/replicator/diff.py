import logging
import os
from typing import Tuple, List

from .git import Repository


logger = logging.getLogger(__name__)


class Diff:

    def obtain(self, from_state) -> Tuple[List[str], List[str], List[str], str]:
        raise NotImplementedError

    def all_zones(self) -> Tuple[List[str], str]:
        raise NotImplementedError


class GitDiff(Diff):

    def __init__(self, path: str) -> None:
        super().__init__()
        self.repo = Repository(path)
        if not os.path.exists(os.path.join(path, '.git')):
            self.repo.clone(origin=f'ssh://git@desec.{os.environ["DESECSTACK_DOMAIN"]}:222/zones')

    def all_zones(self) -> Tuple[List[str], str]:
        self.repo.pull()
        _, _, files = next(os.walk(self.repo.path))
        return [f[:-5] for f in files if f.endswith('.zone')], self.repo.get_head()[1]

    def obtain(self, from_state: str) -> Tuple[List[str], List[str], List[str], str]:
        self.repo.pull()
        diff = self.repo.diff_files(from_state)

        added, modified, deleted = list(), list(), list()
        for t, f in diff:

            if f.endswith('.zone'):
                f = f[:-5]
            else:
                continue

            if t == 'A':
                added.append(f)
            elif t == 'M':
                modified.append(f)
            elif t == 'D':
                deleted.append(f)
            else:
                raise ValueError(f'Unknown diff type "{t}" for file "{f}" in diff of '
                                 f'{from_state}..{self.repo.get_head()[1]}.')

        logger.debug(f'{len(added)} zones added, {len(modified)} modified, {len(deleted)} deleted')
        return added, modified, deleted, self.repo.get_head()[1]
