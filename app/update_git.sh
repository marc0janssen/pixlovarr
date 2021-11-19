#!/bin/sh

cd /tmp

git clone https://github.com/marc0janssen/pixlovarr.git
git clone https://github.com/marc0janssen/radarr-library-purge.git

cp /tmp/pixlovarr/app/* /app
cp /tmp/radarr-library-purge/app/* /app

chmod +x /app/pixlovarr.py
chmod +x /app/start.sh
chmod +x /app/update_git.sh
chmod +x /app/radarr_library_purge.py

rm -rf /tmp/*
