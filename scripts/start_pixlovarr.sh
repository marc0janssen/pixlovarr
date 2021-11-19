#!/bin/sh

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-05-02 10:11:33

docker run -d \
	--name=pixlovarr \
	--restart=always \
	-v /docker/pixlovarr/config:/config \
	-v /docker/pixlovarr/logs:/logs \
	marc0janssen/pixlovarr:latest
