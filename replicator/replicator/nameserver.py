import logging
import os
import subprocess
from typing import List, Iterable

logger = logging.getLogger(__name__)


class Nameserver:

    def update(self, added: Iterable[str], modified: Iterable[str], deleted: Iterable[str]):
        raise NotImplementedError

    def zones(self) -> List[str]:
        raise NotImplementedError


class KnotDNS(Nameserver):

    class KnotDNSException(Exception):

        def __init__(self, message, **kwargs):
            super().__init__(message)
            for k, v in kwargs.items():
                self.__setattr__(k, v)

    def _knotc(self, *args, stdin: str = None):
        cmd = ['/usr/sbin/knotc', '-s', '/rundir/knot/knot.sock'] + list(args)
        logger.debug('>>CMD> ' + str(cmd))

        with subprocess.Popen(
                cmd,
                bufsize=0,
                cwd=os.environ.get('HOME', '/'),
                stdin=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
        ) as p:
            logger.debug('\n'.join('>>>IN> ' + s for s in stdin.split('\n')))
            stdout, stderr = p.communicate(stdin.encode() + b'\n', timeout=5)
            p.stdin.close()
            try:
                rcode = p.wait(timeout=5)
            except TimeoutError:
                self.KnotDNSException('knotc unresponsive after stdin close', cmd=cmd)
            try:
                stderr, stdout = stderr.decode(), stdout.decode()
            except UnicodeDecodeError:
                self.KnotDNSException('knotc stdout or stderr was not valid unicode!',
                                      cmd=cmd, rcode=rcode, stderr=stderr, stdout=stdout)

        if stdout:
            logger.debug('\n'.join('<<OUT< ' + s for s in stdout.split('\n')))

        if stderr:
            logger.debug('\n'.join('<<ERR< ' + s for s in stderr.split('\n')))
            self.KnotDNSException('knotc gave error output:\n' + stderr,
                                  cmd=cmd, rcode=rcode, stderr=stderr, stdout=stdout)

        if rcode:
            self.KnotDNSException('knotc gave non-zero exit status ' + str(rcode),
                                  cmd=cmd, rcode=rcode, stderr=stderr, stdout=stdout)

        return cmd, rcode, stdout, stderr

    def update(self, added: Iterable[str], modified: Iterable[str], deleted: Iterable[str]):
        cmds = []
        # TODO sanitize input

        for zone in modified:
            cmds.append(f"zone-reload '{zone}'")

        if added or deleted:
            cmds.append('conf-begin')

            for zone in added:
                cmds.append(f"conf-set 'zone[{zone}]'")
                cmds.append(f"conf-set 'zone[{zone}].file' '/zones/{zone}.zone'")

            for zone in deleted:
                cmds.append(f"conf-unset 'zone[{zone}]'")

            cmds.append('conf-commit')

        for cmd in cmds:
            logger.info('>>> KNOTC >>> '+ cmd)

        if cmds:
            self._knotc(stdin='\n'.join(cmds))

    def zones(self) -> List[str]:
        _, _, stdout, _ = self._knotc(stdin="zone-status")
        # stdout will be a list in the following format:
        # [example.com.] bla bla bla
        # [foobar.com.] bla bla bla
        # TODO what if there is a space in the domain name?
        return [l.split(' ', maxsplit=1)[0][1:-1].rstrip('.') for l in stdout.split('\n') if l]
