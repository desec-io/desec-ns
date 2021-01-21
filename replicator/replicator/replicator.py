import logging
from typing import Iterable

from .diff import Diff
from .nameserver import Nameserver

logger = logging.getLogger(__name__)


class Replicator:

    def __init__(self, diff: Diff, nameserver: Nameserver, state_path: str) -> None:
        super().__init__()
        self.diff = diff
        self.nameserver = nameserver
        self._state = state_path

    def get_state(self) -> str:
        try:
            with open(self._state, 'r') as f:
                return f.read()
        except FileNotFoundError:
            return ''

    def update_state(self, new_state: str) -> None:
        with open(self._state, 'w') as f:
            f.write(new_state)

    def update(self):
        if not self.get_state():
            self.recover()
        else:
            self.poll()

    def poll(self):
        # TODO metric for update time
        zones_added, zones_modified, zones_deleted, new_state = self.diff.obtain(self.get_state())
        self._digest_changes(zones_added, zones_modified, zones_deleted, new_state)
        if zones_added or zones_modified or zones_deleted:
            logger.info(f'Updated to {new_state}:')
            logger.info(f'Added:    {", ".join(zones_added) or "(none)"}')
            logger.info(f'Modified: {", ".join(zones_modified) or "(none)"}')
            logger.info(f'Deleted:  {", ".join(zones_deleted) or "(none)"}')

    def recover(self):
        # TODO metric for recovery and recovery time
        ns_zones = set(self.nameserver.zones())
        upstream_zones, new_state = self.diff.all_zones()
        upstream_zones = set(upstream_zones)

        zones_added = upstream_zones - ns_zones
        zones_modified = upstream_zones & ns_zones  # we assume that all zones already known by the NS require updates
        zones_deleted = ns_zones - upstream_zones

        self._digest_changes(zones_added, zones_modified, zones_deleted, new_state)
        logger.warning(f'Recovered to {new_state} (added {len(zones_added)}, modified all {len(zones_modified)}, '
                       f'deleted {len(zones_deleted)}).')

    def _digest_changes(self, zones_added: Iterable[str], zones_modified: Iterable[str], zones_deleted: Iterable[str],
                        new_state: str):

        try:
            self.nameserver.update(zones_added, zones_modified, zones_deleted)
        except Exception as e:
            logger.error(f'Update of nameserver {self.nameserver} to {new_state} failed: {e}')
            self.update_state('')  # mark state as unknown/broken
            raise
        else:
            self.update_state(new_state)
