ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}ubuntu:jammy

RUN set -ex \
	# Prepare for adding repository
	&& apt-get update \
	&& apt-get install -y curl gnupg

RUN echo 'deb [signed-by=/etc/apt/keyrings/auth-49-pub.asc arch=amd64] http://repo.powerdns.com/ubuntu jammy-auth-49 main' \
      >> /etc/apt/sources.list \
 && echo 'Package: pdns-*' \
      > /etc/apt/preferences.d/pdns \
 && echo 'Pin: origin repo.powerdns.com' \
      >> /etc/apt/preferences.d/pdns \
 && echo 'Pin-Priority: 600' \
      >> /etc/apt/preferences.d/pdns

RUN set -ex \
	&& install -d /etc/apt/keyrings && curl https://repo.powerdns.com/FD380FBB-pub.asc > /etc/apt/keyrings/auth-49-pub.asc \
	&& apt-get update \
	&& apt-get install -y pdns-server pdns-backend-lmdb \
	# credentials management via envsubst
	&& apt-get -y install gettext-base \
	# VPN route & multicast
	&& apt-get -y install iproute2 smcroute \
	# DoX routing
	&& apt-get -y install iptables \
	# cleanup
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN rm -rf /etc/powerdns/
COPY conf/ /etc/powerdns/
COPY lua/ /usr/share/lua/5.1/

COPY ./*.sh /usr/bin/local/

CMD ["/usr/bin/local/entrypoint.sh"]
