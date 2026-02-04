ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}cznic/knot:v3.5.3

RUN set -ex \
	&& apt-get update \
	# VPN route & multicast
	&& apt-get -y install iproute2 smcroute gettext-base \
	# cleanup
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN mkdir -p /etc/knot
COPY conf/knot.conf.var /etc/knot/

COPY ./*.sh /usr/local/bin/

CMD ["/usr/local/bin/entrypoint.sh"]
