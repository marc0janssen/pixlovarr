#!/bin/sh

cd /tmp

git clone https://github.com/marc0janssen/pixlovarr.git

cp /tmp/pixlovarr/app/* /app

chmod +x /app/pixlovarr.py
chmod +x /app/update_git.sh

rm -rf /tmp/*
