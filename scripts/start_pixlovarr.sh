#!/bin/sh

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-12-09 16:39:44

docker run -d \
	--name=pixlovarr \
	--restart=always \
	-v /path/to/config/:/config \
	-v /path/to/movies/:/movies \
	marc0janssen/pixlovarr:latest
