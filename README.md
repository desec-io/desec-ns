deSEC Slave
=====

This is a docker-compose application to run a nameserver frontend server. Zone data is automatically provided to this application via database replication. The application consists of

- `ns`: Slave DNS server (PowerDNS).
- `db`: MariaDB database services for `ns`. Connects to another MySQL server to receive zone data via TLS-secured replication.


Requirements
-----

Although most configuration is contained in this repository, some external dependencies need to be met before the application can be run. Dependencies are:

1.  We run this software with the `--userland-proxy=false` flag of the `dockerd` daemon, and recommend you do the same.

2.  Set sensitive information and network topology using environment variables or an `.env` file. You need (you can use the `env` file as a template):
    - certificates
      - `DESECSLAVE_CERT_FOLDER`: `./path/to/certificates`
    - ns-related
      - `DESECSLAVE_ID`: MySQL replication slave `server-id` (must be unique across replication topology)
      - `DESECSLAVE_DB_PASSWORD_pdns`: mysql password for pdns on ns
    - master-related
      - `DESECSTACK_DBMASTER`: MySQL master hostname
      - `DESECSTACK_DBMASTER_USERNAME_replication`: slave replication username. Also used in the MariaDB `log-basename` setting, i.e. it can't contain `.` or `/`.
      - `DESECSTACK_DBMASTER_PASSWORD_replication`: slave replication password
      - `DESECSTACK_DBMASTER_SUBJECT_replication`: slave replication SSL certificate subject name


How to Run
-----

    $ docker-compose build
    $ docker-compose up

This fires up the database, retrieves and imports a copy of the pdns database from the database master host, sets up replication, and fires up the nameserver.


Storage
---
All data is stored in the database managed by the `db` container. It uses a Docker volume which, by default, resides in `/var/lib/docker/volumes/desecslave_db_mysql`.
This is the location you will want to back up. (Be sure to follow standard MySQL backup practices, i.e. make sure things are consistent.)
