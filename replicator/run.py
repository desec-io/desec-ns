import json
import os
import re
from time import sleep, time

import dns.message, dns.query, dns.rdatatype
import requests


catalog_domain = 'catalog.internal.'
primary_ip = '172.16.7.3'
config = {
    'base_url': 'http://ns:8081/api/v1/servers/localhost',
    'headers': {
        'Accept': 'application/json',
        'User-Agent': 'desec-ns',
        'X-API-Key': os.environ['DESEC_NS_APIKEY'],
    },
}


class PDNSException(Exception):
    def __init__(self, response=None):
        self.response = response
        super().__init__(f'pdns response code: {response.status_code}, pdns response body: {response.text}')


def pdns_id(name):
    # See also pdns code, apiZoneNameToId() in ws-api.cc (with the exception of forward slash)
    if not re.match(r'^[a-zA-Z0-9_.-]+$', name):
        raise ValueError('Invalid hostname ' + name)

    name = name.translate(str.maketrans({'/': '=2F', '_': '=5F'}))
    return name.rstrip('.') + '.'


def pdns_request(method, *, path, body=None):
    data = json.dumps(body) if body else None

    # On timeout, we don't retry, as we don't know whether the request already had a side-effect on pdns
    r = requests.request(method, config['base_url'] + path, data=data, headers=config['headers'], timeout=10)
    if r.status_code not in range(200, 300):
        raise PDNSException(response=r)

    return r


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
        r = requests.get('https://{}/api/v1/serials/'.format(os.environ['DESECSTACK_VPN_SERVER']), timeout=10)
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

    def perform_full_zone_sync(self):
        remote_zones = set(self.serials.keys())
        local_serials = {zone['name']: zone['edited_serial'] for zone in pdns_request('get', path='/zones').json()}
        local_zones = set(local_serials.keys())

        # Compute changes
        additions = remote_zones - local_zones
        deletions = local_zones - remote_zones
        modifications = {zone for zone, serial in local_serials.items() if self.serials.get(zone, 0) > serial}

        # Apply additions
        for zone in additions:
            print(f'Adding zone {zone} ...')
            pdns_request('post', path='/zones', body={'name': zone, 'kind': 'SLAVE', 'masters': [primary_ip]})
            local_zones.add(zone)
            print(f'Queueing initial AXFR for zone {zone} ...')
            pdns_request('put', path='/zones/{}/axfr-retrieve'.format(pdns_id(zone)))

        # Apply modifications
        for zone in modifications:
            print(f'Queueing AXFR for stale zone {zone} ...')
            pdns_request('put', path='/zones/{}/axfr-retrieve'.format(pdns_id(zone)))

        # Apply deletions
        for zone in deletions:
            print(f'Deleting zone {zone} ...')
            path = '/zones/{}'.format(pdns_id(zone))
            try:
                pdns_request('delete', path=path)
                pdns_request('get', path=path)  # confirm deletion
            except PDNSException as e:
                if e.response.status_code == 404:
                    local_zones.discard(zone)
                    print(f'Zone {zone} deleted.')
                else:
                    raise e

        return additions, deletions, modifications


def main():
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
        additions, deletions, modifications = catalog.perform_full_zone_sync()

        # Make a note that we processed this catalog version
        processed_serial = catalog.serial


if __name__ == '__main__':
    main()
