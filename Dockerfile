FROM alpine:latest

RUN mkdir /app && mkdir /config

ADD /app/pycliarr /app/pycliarr/
ADD /app/pixlovarr.py /app/pixlovarr.py
ADD /app/pixlovarr.ini.example /app/pixlovarr.ini.example

RUN apk add --update \
	python3 \
	python3-dev \
	build-base \
	openssl \
	ca-certificates \
	linux-headers \
	tzdata \
	&& cd /tmp \
	&& wget https://bootstrap.pypa.io/get-pip.py \
	&& python3 get-pip.py \
	&& pip3 install --no-cache \
	python-telegram-bot \
	requests \
	&& apk del \
	python3-dev \
	build-base \
	openssl \
	ca-certificates \
	linux-headers \
	&& rm -f /var/cache/apk/* 

RUN chmod +x /app/pixlovarr.py

ENV TZ=Europe/Amsterdam

VOLUME /config

CMD ["/usr/bin/python3", "/app/pixlovarr.py"]