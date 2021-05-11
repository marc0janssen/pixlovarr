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
	tzdata

RUN pip3 install --no-cache \
	python-telegram-bot \
	pycliarr \
	requests \
	imdbpy
	
RUN apk del \
	python3-dev \
	build-base \
	openssl \
	ca-certificates \
	linux-headers \
	libxml2-dev \
	libxslt-dev

RUN rm -f /var/cache/apk/* \
	&& rm -rf /tmp/*

RUN chmod +x /app/update_git.sh
RUN /app/update_git.sh

RUN chmod +x /app/pixlovarr.py

ENV TZ=Europe/Amsterdam

VOLUME /config

CMD ["/usr/bin/python3", "/app/pixlovarr.py"]