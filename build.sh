#!/bin/sh

docker build -t marc0janssen/pixlovarr:latest -f ./Dockerfile .

sh ./scripts/start_pixlovarr.sh