deSEC Slave
=====

This is a docker-compose application to run a nameserver frontend server. Zone data is automatically provided to this application via database replication. The application consists of

- `dnsdist`: Frontend DNS load balancer (dnsdist), currently forwarding to the `ns` container. It is mainly there to support more advanced features in the future.
- `ns`: Actual DNS server (PowerDNS).
- `openvpn-client`: OpenVPN client container providing network services for `ns` and `replicator`.


Requirements
-----

Although most configuration is contained in this repository, some external dependencies need to be met before the application can be run. Dependencies are:

1.  We run this software with the `--userland-proxy=false` flag of the `dockerd` daemon, and recommend you do the same.

2.  Set sensitive information and network topology using environment variables or an `.env` file. You need (you can use the `env` file as a template):
    - network
      - `DESECSLAVE_IPV6_SUBNET`: IPv6 net, ideally /80
      - `DESECSLAVE_IPV6_ADDRESS`: IPv6 address of frontend container
    - ns-related
      - `DESECSLAVE_NS_APIKEY`: `ns` API key needed for replication operations
      - `DESECSLAVE_CARBONSERVER`: pdns `carbon-server` setting (optional)
      - `DESECSLAVE_CARBONOURNAME`: pdns `carbon-ourname` setting (optional)
    - master-related
      - `DESECSTACK_VPN_SERVER`: VPN server hostname

3.  Set up secrets for the VPN: Before setting up a deSEC slave, you will have to deploy the [deSEC main stack](https://github.com/desec-io/desec-stack) so that the slave can connect to it in order to fetch DNS data.
    In the process of setting up the stack deployment, you will have created a PKI, for example using [easy-rsa](https://github.com/OpenVPN/easy-rsa) and [this tutorial](https://github.com/OpenVPN/easy-rsa/blob/master/README.quickstart.md).
    Use this PKI now in order to create a new `client.key` and `client.crt` pair, and transfer these file securely to the slave, along with `ca.crt` and `ta.key` from the main stack deployment, and copy them into `openvpn-client/secrets/`.
    (You can also create `client.key` locally on the slave and transfer a certificate signing request to the host at which your PKI is located.)


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
