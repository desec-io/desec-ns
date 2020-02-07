import json
import os
import re
import sys
from time import sleep, time

import dns.message, dns.query, dns.rdatatype
import requests


catalog_domain = 'catalog.internal.'
master_ip = '172.16.7.3'
slave_ip = '10.16.3.3'
config = {
    'base_url': 'http://ns:8081/api/v1/servers/localhost',
    'headers': {
        'Accept': 'application/json',
        'User-Agent': 'desecslave',
        'X-API-Key': os.environ['DESECSLAVE_NS_APIKEY'],
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

    r = requests.request(method, config['base_url'] + path, data=data, headers=config['headers'])
    if r.status_code not in range(200, 300):
        raise PDNSException(response=r)

    return r


def query_serial(zone, server):
    query = dns.message.make_query(zone, 'SOA')
    response = dns.query.tcp(query, server)

    for rrset in response.answer:
        if rrset.rdtype == dns.rdatatype.SOA:
            return int(rrset[0].serial)
    return None


class Catalog:
    data = {}
    last_full_check = 0  # assume last check was done a long time ago

    def __init__(self):
        # Provision catalog slave zone
        print('Creating empty catalog zone if it does not exist yet ...')
        try:
            pdns_request('post', path='/zones', body={'name': catalog_domain, 'kind': 'SLAVE', 'masters': [master_ip]})
        except PDNSException as e:
            if e.response.status_code == 409:
                print('Catalog zone already present.')
            else:
                raise e
        else:
            print('Catalog zone created.')
            self.last_full_check = time() + 300  # Give some time for all AXFRs to run before checking serials

    @property
    def domain_id(self):
        return pdns_id(catalog_domain)

    @property
    def serial(self):
        return self.data.get('serial')

    def _retrieve(self):
        self.data = pdns_request('get', path=f'/zones/{self.domain_id}').json()

    def _queue_axfr(self):
        remote_catalog_serial = query_serial(catalog_domain, master_ip)
        if self.serial != remote_catalog_serial:
            print(f'Queueing catalog AXFR from {self.serial} to {remote_catalog_serial} ...')
            pdns_request('put', path=f'/zones/{self.domain_id}/axfr-retrieve')

    def update(self):
        if self.serial != query_serial(catalog_domain, slave_ip):
            self._retrieve()

        # Fetch the catalog freshly from master in the background if necessary
        self._queue_axfr()

    def parse(self):
        members = set()
        for rrset in self.data['rrsets']:
            m = re.match(r'^([0-9a-f]{40}).zones.catalog.internal.$', rrset['name'])
            if m is None:
                continue

            if rrset['type'] != 'PTR':
                print('Ignoring spurious catalog rrset %s' % rrset, file=sys.stderr)
                continue

            name = rrset['records'][0]['content']
            if name in members:
                print('Ignoring duplicate name in catalog rrset %s' % rrset, file=sys.stderr)
                continue

            members.add(name)

        if not members:
            raise Exception('Catalog is empty. Assuming an error condition.')
        return members

    def check_all_serials(self):
        now = time()

        if now - self.last_full_check < 60:
            return

        print('Checking for stale zones ...')  # e.g. zone updates where the NOTIFY went lost
        r = requests.get('https://{}/api/v1/serials/'.format(os.environ['DESECSTACK_VPN_SERVER']))
        if r.status_code not in range(200, 300):
            print(r.__dict__)
            raise Exception()
        serials = r.json()

        local_serials = {zone['name']: zone['edited_serial'] for zone in pdns_request('get', path='/zones').json()}
        stale_zones = {zone for zone, serial in serials.items() if serial > local_serials.get(zone, 0)}

        for zone in stale_zones:
            print(f'Queueing AXFR for stale zone {zone} ...')
            pdns_request('put', path='/zones/{}/axfr-retrieve'.format(pdns_id(zone)))

        self.last_full_check = now


def main():
    print('Loading local zone serials ...')
    local_zones = {zone['name'] for zone in pdns_request('get', path='/zones').json() if zone['name'] != catalog_domain}
    print(f'Done. Number of local zones is {len(local_zones)}.')

    catalog = Catalog()
    processed_serial = 0

    while True:
        # Note that there may be AXFRs pending from the previous loop iteration. However, it is still useful to fetch
        # the new catalog right away, because:
        #   - it helps discarding useless intermediate states, e.g. if a domain is quickly deleted and recreated,
        #   - if replication is stuck because the catalog is invalid, a new catalog improves chances of recovery,
        #   - waiting for all tasks to be completed would allow long-running AXFRs to hold up new catalog changes.
        catalog.update()

        # See if the last parsed catalog is the current one
        if processed_serial == catalog.serial:
            print(f'Nothing to do (catalog {processed_serial} with {len(local_zones)} zones up to date).')
            catalog.check_all_serials()
            sleep(1)
            continue

        # Parse current state of catalog zone and determine slave-side changes
        catalog_zones = catalog.parse()

        # Compute changes
        deletions = local_zones - catalog_zones
        additions = catalog_zones - local_zones

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

        # Apply additions
        for zone in additions:
            print(f'Adding zone {zone} ...')
            pdns_request('post', path='/zones', body={'name': zone, 'kind': 'SLAVE', 'masters': [master_ip]})
            local_zones.add(zone)
            print(f'Queueing initial AXFR for zone {zone} ...')
            pdns_request('put', path='/zones/{}/axfr-retrieve'.format(pdns_id(zone)))

        # Make a note that we processed this catalog version
        if len(deletions) + len(additions) == 0:
            print(f'Done processing catalog with serial {catalog.serial}')
            processed_serial = catalog.serial

        catalog.check_all_serials()


if __name__ == '__main__':
    main()
