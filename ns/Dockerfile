FROM debian:stretch

RUN set -ex \
	# Prepare for adding repository
	&& apt-get update \
	&& apt-get install -y curl gnupg

RUN echo 'deb [arch=amd64] http://repo.powerdns.com/debian stretch-auth-42 main' \
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
	&& apt-get install -y pdns-server pdns-backend-mysql \
	# credentials management via envsubst
	&& apt-get -y install gettext-base \
	# Post-create cron hook
	&& apt-get -y install cron mariadb-client \
	# cleanup
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

RUN rm -rf /etc/powerdns/
COPY conf/ /etc/powerdns/

COPY ./entrypoint.sh /root/

CMD ["/root/entrypoint.sh"]
