# deSEC Nameserver

This is a docker-compose application to run a nameserver. Zone data is automatically provided to this application via database replication. The application consists of

- `ns`: Actual DNS server.
- `replicator`: Python container running a replication loop.
- `openvpn-client`: OpenVPN client container providing network services for `ns` and `replicator`.


## Requirements

Although most configuration is contained in this repository, some external dependencies need to be met before the application can be run. Dependencies are:

1.  We run this software with the `--userland-proxy=false` flag of the `dockerd` daemon, and recommend you do the same.

2.  Set sensitive information and network topology using environment variables or an `.env` file. You need (you can use the `env` file as a template):
    - network
      - `DESEC_NS_IPV6_SUBNET`: IPv6 net, ideally /80
      - `DESEC_NS_IPV6_ADDRESS`: IPv6 address of frontend container
    - ns-related
      - `DESEC_NS_APIKEY`: `ns` API key needed for replication operations
      - `DESEC_NS_CARBONSERVER`: pdns `carbon-server` setting (optional)
      - `DESEC_NS_CARBONOURNAME`: pdns `carbon-ourname` setting (optional)
      - `DESEC_NS_NAME`: name under which this name server will be reached, e.g. ns1.example.com (optional unless
        `DESEC_NS_SIGNALING_DOMAIN_ZONE_PRIVATE_KEY_B64` is defined, see below)
    - primary-related
      - `DESECSTACK_VPN_SERVER`: VPN server hostname

3.  Set up secrets for the VPN: Before setting up a deSEC nameserver, you will have to deploy the [deSEC main stack](https://github.com/desec-io/desec-stack) so that the nameserver can connect to it in order to fetch DNS data.
    In the process of setting up the stack deployment, you will have created a PKI, for example using [easy-rsa](https://github.com/OpenVPN/easy-rsa) and [this tutorial](https://github.com/OpenVPN/easy-rsa/blob/master/README.quickstart.md).
    Use this PKI now in order to create a new `client.key` and `client.crt` pair, and transfer these file securely to the nameserver, along with `ca.crt` and `ta.key` from the main stack deployment, and copy them into `openvpn-client/secrets/`.
    (You can also create `client.key` locally on the nameserver application and transfer a certificate signing request to the host at which your PKI is located.)

4. (Optional) To set up DNSSEC Bootstrapping, a key for signing the zone in which the Signaling Domain is hosted.
    The private key must be provided in `DESEC_NS_SIGNALING_DOMAIN_ZONE_PRIVATE_KEY_B64` in a format compatible with
    `pdnsutil import-zone-key`, but encoded in base64. One way of obtaining such a key is by using `pdnsutil`:

    pdnsutil generate-zone-key ksk ecdsa256 | grep -E 'Private-key-format:|Algorithm:|PrivateKey:' | base64 | tr -d '\n'

    If using DNSSEC Bootstrapping, the `DESEC_NS_SIGNALING_DOMAIN_SOA_MNAME`, `DESEC_NS_SIGNALING_DOMAIN_SOA_RNAME`
    environment variables should be provided for the Signaling Domain zone SOA record.

## How to Run

    $ docker-compose build
    $ docker-compose up

This fires up the various services, connects to the VPN, starts replicating from the master, and fires up the nameserver.


## LMDB Database Backups

### Create backup

Given a nameserver of any freshness (may be up to date or stale or empty), do the following:

  1. Make sure the docker-compose application is not running.
  2. Run `./dump.sh`. This fires up `ns` and `replicator` to perform a sync, waits until nothing is left to do, and then shuts everything down. Next, the script starts a `lmdb-backup` container which contains a manually built version of lmdb tooling, runs `mdb_dump` to export the database, creates a tar.gz file with everything, and puts it into `./lmdb-backup/backup/`.

Caveat: Running such a dump nameserver on the [stack](https://github.com/desec-io/desec-stack) host fails because that requires an OpenVPN client and server on the same machine, which does not work. In other words, the dump has to run somewhere else. This may be an OpenVPN limitation, so there may not even be a fix.

### Restore Backup

Take a backup file created in the previous step and store it at `./lmdb-backup/backup/`.

  1. Run `./load.sh $FILENAME`, where `$FILENAME` is the name of one of the files in `./lmdb-backup/backup/`. This starts a `lmdb-backup` container, extracts the file in it, runs `mdb_load`, and puts all files into the PowerDNS storage directory. The script aborts if that directory is not empty.
  2. Start nameserver normally to resume regular operation, including replication.


## Notes on Networking

  - It is not necessary to start the Docker daemon with `--ipv6` or `--fixed-cidr-v6`. However, it is recommended to run `dockerd` with `--userland-proxy=false` to avoid 
    exposing ports on the host IPv6 address through `docker-proxy`.

  - This stack is IPv6-capable. To prevent evil people from abusing this app for DNS amplification attacks, it is highly recommended to rate limit requests by IP (or take 
    some smarter precaution). In particular, consider using he nameserver's policy settings, or the iptables hashlimit module.

    When using iptables, note that whenever you restart the docker daemon or this application (`docker-compose down; docker-compose up`), docker will insert its own rules 
    at the top of the chain. You therefore have to make sure that these rules get re-applied whenever docker decides to jump the queue.
    See [this issue](https://github.com/docker/docker/issues/24848) for details and progress on this.
