#!/bin/sh

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-04-21 20:23:43
# update: 2021-05-14 22:16:33

docker image rm marc0janssen/pixlovarr:latest
docker build -t marc0janssen/pixlovarr:latest -f ./Dockerfile .
