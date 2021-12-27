FROM alpine:latest

RUN apk update && apk upgrade && apk add --update \
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
	feedparser \
	python-telegram-bot \
	pycliarr \
	arrapi \
	requests \
	imdbpy \
	chump \
	&& apk del \
	python3-dev \
	build-base \
	openssl \
	ca-certificates \
	linux-headers \
	libxml2-dev \
	libxslt-dev \
	&& rm -f /var/cache/apk/* \
	&& rm -rf /tmp/*

RUN mkdir /app /config /log

COPY /app/ /app/

RUN chmod +x /app/*.sh

RUN echo '0	4	*   *   *   python3 /app/pixlovarr_prune.py &> /proc/1/fd/1' >> /etc/crontabs/root

RUN ln -s /config /root/config && ln -s /app /root/app && ln -s /log /root/log

ENV TZ=Europe/Amsterdam

VOLUME /config
VOLUME /Log

ENTRYPOINT ["/app/start.sh"]
