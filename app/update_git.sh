#!/bin/sh

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-19 18:54:36
# update: 2021-12-27 10:58:29

cd /tmp

git clone https://github.com/marc0janssen/pixlovarr.git

cp /tmp/pixlovarr/app/* /app
cp /tmp/pixlovarr/pixlovarr* /

chmod +x /pixlovarr.py
chmod +x /pixlovarr_prune.py
chmod +x /app/start.sh
chmod +x /app/update_git.sh

rm -rf /tmp/*
