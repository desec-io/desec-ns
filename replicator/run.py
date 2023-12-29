import json
import os
import re
from time import sleep, time
from typing import Dict

import dns.message, dns.query, dns.rdatatype
import libknot.control
import requests


ssl_verify = os.environ.get('DESEC_NS_E2E2') is None
catalog_domain = 'catalog.internal.'
primary_ip = '172.16.7.3'


class Nameserver:

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_local_zone_serials(self) -> Dict[str, int]:
        """Returns a dictionary mapping all local zone names to their current serial."""
        pass

    def add_zone(self, name: str) -> None:
        """Adds a new zone"""
        pass

    def axfr(self, name: str) -> None:
        """Schedules AXFR for the zone with the given name."""
        pass

    def remove_zone(self, name: str) -> None:
        """Removes the zone with the given name."""
        pass


class PDNSNameserver(Nameserver):

    class PDNSException(Exception):
        def __init__(self, response=None):
            self.response = response
            super().__init__(f'pdns response code: {response.status_code}, pdns response body: {response.text}')

    @staticmethod
    def pdns_id(name):
        # See also pdns code, apiZoneNameToId() in ws-api.cc (with the exception of forward slash)
        if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
            raise ValueError('Invalid hostname ' + name)

        name = name.translate(str.maketrans({'/': '=2F', '_': '=5F'}))
        return name.rstrip('.') + '.'

    @classmethod
    def pdns_request(cls, method, *, path, body=None):
        data = json.dumps(body) if body else None

        # On timeout, we don't retry, as we don't know whether the request already had a side-effect on pdns
        r = requests.request(
            method,
            'http://ns:8081/api/v1/servers/localhost' + path,
            data=data,
            headers={
                'Accept': 'application/json',
                'User-Agent': 'desec-ns',
                'X-API-Key': os.environ['DESEC_NS_APIKEY'],
            },
            timeout=10
        )
        if r.status_code not in range(200, 300):
            raise cls.PDNSException(response=r)

        return r

    def get_local_zone_serials(self) -> Dict[str, int]:
        return {
            zone['name']: zone['edited_serial']
            for zone in self.pdns_request('get', path='/zones').json()
            if zone['kind'] == 'Slave'  # we only care about zones with 'Slave' status
        }

    def add_zone(self, name: str) -> None:
        self.pdns_request('post', path='/zones', body={'name': name, 'kind': 'SLAVE', 'masters': [primary_ip]})
        print(f'Queueing initial AXFR for zone {name} ...')
        self.axfr(name)

    def axfr(self, name: str) -> None:
        self.pdns_request('put', path='/zones/{}/axfr-retrieve'.format(self.pdns_id(name)))

    def remove_zone(self, name: str) -> None:
        path = '/zones/{}'.format(self.pdns_id(name))
        try:
            self.pdns_request('delete', path=path)
            self.pdns_request('get', path=path)  # confirm deletion
        except self.PDNSException as e:
            if e.response.status_code == 404:
                pass
            else:
                raise e


class KnotNameserver(Nameserver, libknot.control.KnotCtl):
    transaction = False

    def __enter__(self):
        self.connect("/rundir/knot.sock")
        self.set_timeout(60)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.transaction:
            self._send_receive_block(cmd="conf-commit")
        self.send(libknot.control.KnotCtlType.END)
        self.close()

    def _send_receive_block(self, *args, **kwargs):
        self.send_block(*args, **kwargs)
        return self.receive_block()

    def get_local_zone_serials(self) -> Dict[str, int]:
        resp = self._send_receive_block(cmd="zone-status")
        return {
            name: None if values['serial'] == '-' else int(values['serial'])
            for name, values in resp.items()
        }

    def _ensure_conf_transaction(self):
        if not self.transaction:
            self._send_receive_block(cmd="conf-begin")
            self.transaction = True

    def add_zone(self, name: str) -> None:
        try:
            self._ensure_conf_transaction()
            self._send_receive_block(cmd="conf-set", section="zone", item="domain", data=name)
        except libknot.control.KnotCtlErrorRemote:
            self._send_receive_block(cmd="conf-abort")

    def axfr(self, name: str) -> None:
        try:
            self._send_receive_block(cmd="zone-retransfer", zone=name)
        except libknot.control.KnotCtlErrorRemote as e:
            print(f"AXFR request for {name} failed: {e}")

    def remove_zone(self, name: str) -> None:
        try:
            self._ensure_conf_transaction()
            self._send_receive_block(cmd="conf-unset", section="zone", item="domain", data=name)
        except libknot.control.KnotCtlErrorRemote:
            self._send_receive_block(cmd="conf-abort")


def query_serial(zone, server):
    query = dns.message.make_query(zone, 'SOA')
    response = dns.query.tcp(query, server, timeout=5)

    for rrset in response.answer:
        if rrset.rdtype == dns.rdatatype.SOA:
            return int(rrset[0].serial)
    return None


class Catalog:
    serials = {}
    timestamp = 0  # assume last check was done a long time ago

    @property
    def age(self):
        return time() - self.timestamp

    @property
    def remote_serial(self):
        return query_serial(catalog_domain, primary_ip)

    @property
    def serial(self):
        return self.serials.get(catalog_domain, 0)

    def _retrieve(self):
        # Throws Timeout exception if nothing is received for `timeout` seconds
        r = requests.get(
            'https://{}/api/v1/serials/'.format(os.environ['DESECSTACK_VPN_SERVER']),
            timeout=30,
            verify=ssl_verify,
        )
        if r.status_code not in range(200, 300):
            print(r.__dict__)
            raise Exception()
        serials = r.json()

        if len(serials) <= 1:
            raise Exception(f'Catalog contains {len(serials)} elements. Assuming an error condition.')

        self.serials = serials
        self.timestamp = time()

    def update(self):
        # Return if catalog serial is unchanged and 60 second window for comprehensive serial check has not passed
        if self.age < 60 and self.remote_serial == self.serial:
            return False

        print('Retrieving zone list ...')  # e.g. zone updates where the NOTIFY went lost
        self._retrieve()
        return True

    def perform_full_zone_sync(self, ns_class: type[Nameserver]):
        remote_zones = set(self.serials.keys())
        with ns_class() as ns:
            local_serials = ns.get_local_zone_serials()
        local_zones = set(local_serials.keys())

        # Compute changes
        additions = remote_zones - local_zones
        deletions = local_zones - remote_zones
        modifications = {
            zone for zone, local_serial in local_serials.items()
            if local_serial is None or local_serial < self.serials.get(zone, 0)
        }

        if additions or deletions:
            with ns_class() as ns:
                # Apply additions
                for zone in additions:
                    print(f'Adding zone {zone} ...')
                    ns.add_zone(zone)
                    local_zones.add(zone)

                # Apply deletions
                for zone in deletions:
                    print(f'Deleting zone {zone} ...')
                    ns.remove_zone(zone)
                    local_zones.discard(zone)
                    print(f'Zone {zone} deleted.')

        if modifications:
            with ns_class() as ns:
                # Apply modifications
                for zone in modifications:
                    print(f'Queueing AXFR for stale zone {zone} ...')
                    ns.axfr(zone)

        return additions, deletions, modifications


def main():
    ns_class = KnotNameserver
    catalog = Catalog()
    processed_serial = None
    exit_when_done = os.environ.get('DESEC_NS_REPLICATOR_EXIT_WHEN_DONE', 0) == "1"

    while True:
        # Note that there may be AXFRs pending from the previous loop iteration. However, it is still useful to fetch
        # the new catalog right away, because:
        #   - it helps discarding useless intermediate states, e.g. if a domain is quickly deleted and recreated,
        #   - if replication is stuck because the catalog is invalid, a new catalog improves chances of recovery,
        #   - waiting for all tasks to be completed would allow long-running AXFRs to hold up new catalog changes.
        catalog_refreshed = catalog.update()

        # Do nothing if catalog has not changed (no domain additions/deletions) and all serials were compared recently
        if processed_serial == catalog.serial and not catalog_refreshed:
            print(f'Nothing to do (catalog {processed_serial} with {len(catalog.serials)} zones up to date).')
            if exit_when_done:
                if additions | deletions | modifications:
                    print('Dump not yet complete. The following tasks are open:')
                    print(f'additions {len(additions)}:', additions)
                    print(f'deletions {len(deletions)}:', deletions)
                    print(f'modifications {len(modifications)}:', modifications)
                    sleep(10)  # Allow some time for background AXFRs to catch up
                else:
                    print('Dump complete, exiting ...')
                    raise SystemExit
            else:
                sleep(1)
                continue

        # Compute and apply changes. Returns sets of domains names corresponding to added, deleted, modified domains.
        print('Running comprehensive serial check ...')
        additions, deletions, modifications = catalog.perform_full_zone_sync(ns_class)
        sleep(3)  # allow axfrs to complete before checking again

        # Make a note that we processed this catalog version
        processed_serial = catalog.serial


if __name__ == '__main__':
    main()
