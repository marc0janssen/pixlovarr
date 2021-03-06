#!/bin/bash

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-19 18:53:35
# update: 2021-11-25 21:31:52

echo "*** Setting Crontab for Pixlovarr"
if grep  -qF  '/pixlovarr_prune.py' /etc/crontabs/root; then
	echo "*** Confirmed: Pixlovarr Prune in Crontab"
else
	echo "*** Adding: Pixlovarr Prune to Crontab"
    echo "${PRUNE_CRON} python3 /pixlovarr_prune.py &> /proc/1/fd/1" >> /etc/crontabs/root
fi

echo "*** Starting the crond process"
nohup crond -l 2 -f &

echo "*** Starting the main process"
nohup /usr/bin/python3 /pixlovarr.py &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?