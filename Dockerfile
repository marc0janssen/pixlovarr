FROM alpine:latest

RUN mkdir /app && mkdir /config

ADD /app/update_git.sh /app/update_git.sh 

RUN apk add --update \
	libxml2 \
	libxml2-dev \
	libxslt \
	libxslt-dev \
	git \
	python3 \
	python3-dev \
	py3-pip \
	build-base \
	openssl \
	ca-certificates \
	linux-headers \
	tzdata \
	&& pip3 install --no-cache \
	python-telegram-bot \
	pycliarr \
	requests \
	imdbpy \
	&& apk del \
	python3-dev \
	build-base \
	openssl \
	ca-certificates \
	linux-headers \
	libxml2-dev \
	libxslt-dev \
	&& rm -f /var/cache/apk/* \
	&& rm -rf /tmp/* \ 
	&& chmod +x /app/update_git.sh \
	&& /app/update_git.sh

ENV TZ=Europe/Amsterdam

VOLUME /config

CMD ["/usr/bin/python3", "/app/pixlovarr.py"]