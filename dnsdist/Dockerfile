ARG DOCKER_REGISTRY
FROM ${DOCKER_REGISTRY}debian:stretch

RUN set -ex \
	# Prepare for adding repository
	&& apt-get update \
	&& apt-get install -y curl gnupg

RUN echo 'deb [arch=amd64] http://repo.powerdns.com/debian stretch-dnsdist-15 main' \
      >> /etc/apt/sources.list \
 && echo 'Package: dnsdist*' \
      > /etc/apt/preferences.d/dnsdist \
 && echo 'Pin: origin repo.powerdns.com' \
      >> /etc/apt/preferences.d/dnsdist \
 && echo 'Pin-Priority: 600' \
      >> /etc/apt/preferences.d/dnsdist

RUN set -ex \
	&& curl https://repo.powerdns.com/FD380FBB-pub.asc | apt-key add - \
	&& apt-get update \
	&& apt-get install -y dnsdist \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN rm -rf /etc/dnsdist/
COPY conf/ /etc/dnsdist/

CMD ["dnsdist", "--supervised"]
