import logging
import traceback

import time

from replicator.diff import GitDiff
from replicator.nameserver import KnotDNS
from replicator.replicator import Replicator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    try:
        d = '/zones'

        diff = GitDiff(d)
        nameserver = KnotDNS()
        replicator = Replicator(diff, nameserver, '/zones/STATE')

        while True:
            try:
                replicator.update()
            except Exception as e:
                logger.error('Replication error')
                logger.error(e)
                logger.error(e.__dict__)
                logger.error(traceback.format_exc())
                # TODO is there a way to escalate this error, e.g. to shut down anycast route announcement?
            time.sleep(2)

    except Exception as e:
        logger.error('Replication initialization error')
        logger.error(e)
        logger.error(e.__dict__)
        exit(1)


if __name__ == '__main__':
    main()
