#!/bin/sh

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-12-09 16:39:44

docker run -d \
	--name=pixlovarr \
	--restart=always \
	-v /volume1/docker/pixlovarr/config:/config \
	-v /volume1/video/movies:/movies \
	-v /volume2/video2/movies:/movies2 \
	marc0janssen/pixlovarr:latest
