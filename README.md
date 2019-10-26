deSEC Slave
=====

This is a docker-compose application to run a nameserver frontend server. Zone data is automatically provided to this application via database replication. The application consists of

- `dnsdist`: Frontend DNS load balancer (dnsdist), currently forwarding to the `ns` container. It is mainly there to support more advanced features in the future.
- `ns`: Actual DNS server (PowerDNS).
- `db`: MariaDB database services for `ns`. Connects to another MySQL server to receive zone data via TLS-secured replication.


Requirements
-----

Although most configuration is contained in this repository, some external dependencies need to be met before the application can be run. Dependencies are:

1.  We run this software with the `--userland-proxy=false` flag of the `dockerd` daemon, and recommend you do the same.

2.  Set sensitive information and network topology using environment variables or an `.env` file. You need (you can use the `env` file as a template):
    - network
      - `DESECSLAVE_IPV6_SUBNET`: IPv6 net, ideally /80
      - `DESECSLAVE_IPV6_ADDRESS`: IPv6 address of frontend container
    - certificates
      - `DESECSLAVE_CERT_FOLDER`: `./path/` to slave TLS key (`key.pem`), slave certificate (`crt.pem`), and CA certificate (`ca.pem`).
    - ns-related
      - `DESECSLAVE_ID`: MySQL replication slave `server-id` (must be unique across replication topology!). As this is a 32-bit value, a good value is the integer representation of the host's IPv4 unicast address (given that it is unique). Assuming that the hostname is configured correctly in the DNS, this can easily be obtained by `IFS=. read -r a b c d <<< $(dig A +short $(hostname)); echo $((a * 256 ** 3 + b * 256 ** 2 + c * 256 + d))`.
      - `DESECSLAVE_DB_PASSWORD_pdns`: mysql password for pdns on ns
      - `DESECSLAVE_CARBONSERVER`: pdns `carbon-server` setting (optional)
      - `DESECSLAVE_CARBONOURNAME`: pdns `carbon-ourname` setting (optional)
    - master-related
      - `DESECSTACK_DBMASTER`: MySQL master hostname
      - `DESECSTACK_DBMASTER_USERNAME_replication`: slave replication username. Also used in the MariaDB `log-basename` setting, i.e. it can't contain `.` or `/`.
      - `DESECSTACK_DBMASTER_PASSWORD_replication`: slave replication password. Note: Passwords must have **no more than 32 characters** (MariaDB inherited [this bug](https://bugs.mysql.com/bug.php?id=43439)).


How to Run
-----

    $ docker-compose build
    $ docker-compose up

This fires up the database, retrieves and imports a copy of the pdns database from the database master host, sets up replication, and fires up the nameserver.


Storage
---
All data is stored in the database managed by the `db` container. It uses a Docker volume which, by default, resides in `/var/lib/docker/volumes/desecslave_db_mysql`.
This is the location you will want to back up. (Be sure to follow standard MySQL backup practices, i.e. make sure things are consistent.)


Notes on Networking
-----

  - It is not necessary to start the Docker daemon with `--ipv6` or `--fixed-cidr-v6`. However, it is recommended to run `dockerd` with `--userland-proxy=false` to avoid 
    exposing ports on the host IPv6 address through `docker-proxy`.

  - This stack is IPv6-capable. To prevent evil people from abusing this app for DNS amplification attacks, it is highly recommended to rate limit requests by IP (or take 
    some smarter precaution). In particular, consider using the iptables hashlimit module, or dnsdist's traffic policy settings.

    When using iptables, note that whenever you restart the docker daemon or this application (`docker-compose down; docker-compose up`), docker will insert its own rules 
    at the top of the chain. You therefore have to make sure that these rules get re-applied whenever docker decides to jump the queue.
    See [this issue](https://github.com/docker/docker/issues/24848) for details and progress on this.
