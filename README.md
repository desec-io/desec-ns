deSEC Slave
=====

This is a docker-compose application to run a nameserver frontend server. Zone data is automatically provided to this application via database replication. The application consists of

- `dnsdist`: Frontend DNS load balancer (dnsdist), currently forwarding to the `ns` container. It is mainly there to support more advanced features in the future.
- `ns`: Actual DNS server (PowerDNS).


Requirements
-----

Although most configuration is contained in this repository, some external dependencies need to be met before the application can be run. Dependencies are:

1.  We run this software with the `--userland-proxy=false` flag of the `dockerd` daemon, and recommend you do the same.

2.  Set sensitive information and network topology using environment variables or an `.env` file. You need (you can use the `env` file as a template):
    - network
      - `DESECSLAVE_IPV6_SUBNET`: IPv6 net, ideally /80
      - `DESECSLAVE_IPV6_ADDRESS`: IPv6 address of frontend container
    - ns-related
      - `DESECSLAVE_CARBONSERVER`: pdns `carbon-server` setting (optional)
      - `DESECSLAVE_CARBONOURNAME`: pdns `carbon-ourname` setting (optional)


How to Run
-----

    $ docker-compose build
    $ docker-compose up


Notes on Networking
-----

  - It is not necessary to start the Docker daemon with `--ipv6` or `--fixed-cidr-v6`. However, it is recommended to run `dockerd` with `--userland-proxy=false` to avoid 
    exposing ports on the host IPv6 address through `docker-proxy`.

  - This stack is IPv6-capable. To prevent evil people from abusing this app for DNS amplification attacks, it is highly recommended to rate limit requests by IP (or take 
    some smarter precaution). In particular, consider using the iptables hashlimit module, or dnsdist's traffic policy settings.

    When using iptables, note that whenever you restart the docker daemon or this application (`docker-compose down; docker-compose up`), docker will insert its own rules 
    at the top of the chain. You therefore have to make sure that these rules get re-applied whenever docker decides to jump the queue.
    See [this issue](https://github.com/docker/docker/issues/24848) for details and progress on this.
