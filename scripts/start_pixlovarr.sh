#!/bin/sh

docker run -d \
	--name=pixlovarr \
	--restart=always \
	--label=com.centurylinklabs.watchtower.enable=false \
	-v /docker/pixlovarr/config:/config \
	marc0janssen/pixlovarr
