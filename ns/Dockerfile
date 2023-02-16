ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}gentoo/portage:latest as portage
FROM ${DOCKER_REGISTRY}gentoo/stage3:amd64-systemd

# based on stage3 image
FROM gentoo/stage3:latest

# copy the entire portage volume in
COPY --from=portage /var/db/repos/gentoo /var/db/repos/gentoo

# configure portage
COPY portage/* /etc/portage/

RUN emerge mrouted iproute2 iptables
RUN emerge -uDt pdns

RUN rm -rf /etc/powerdns/
COPY conf/ /etc/powerdns/
COPY lua/ /usr/share/lua/5.1/

COPY ./*.sh /usr/bin/local/

CMD ["/usr/bin/local/entrypoint.sh"]
