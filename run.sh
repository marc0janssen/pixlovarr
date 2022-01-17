#!/bin/bash

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-12-24 22:20:12

echo "Removing old container names 'pixlovarr' if exists"
docker rm -f -v pixlovarr || true

echo "Start pixlovarr container."
docker run -d \
    --name pixlovarr \
    --restart=always \
    -v /path/to/config/:/config \
    -v /path/to/movies/:/movies \
    -v /path/to/series/:/series \
    pixlovarr
