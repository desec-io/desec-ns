ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}ubuntu:bionic

RUN set -ex \
	# Prepare for adding repository
	&& apt-get update \
	&& apt-get install -y curl gnupg smcroute

RUN echo 'deb [arch=amd64] http://repo.powerdns.com/ubuntu bionic-auth-45 main' \
      >> /etc/apt/sources.list \
 && echo 'Package: pdns-*' \
      > /etc/apt/preferences.d/pdns \
 && echo 'Pin: origin repo.powerdns.com' \
      >> /etc/apt/preferences.d/pdns \
 && echo 'Pin-Priority: 600' \
      >> /etc/apt/preferences.d/pdns

RUN set -ex \
	&& curl https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - \
	&& apt-get update \
	&& apt-get install -y pdns-server pdns-backend-lmdb \
	# credentials management via envsubst
	&& apt-get -y install gettext-base \
	# VPN route
	&& apt-get -y install iproute2 \
	# cleanup
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN rm -rf /etc/powerdns/
COPY conf/ /etc/powerdns/

COPY ./entrypoint.sh /root/

CMD ["/root/entrypoint.sh"]
