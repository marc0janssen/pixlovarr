#!/bin/ash

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-19 18:53:35
# update: 2021-11-25 21:31:52

# Set Crons for Pixlovarr
echo '${PRUNE_CRON} python3 /app/pixlovarr_prune.py &> /proc/1/fd/1 2>&1' >> /etc/crontabs/root

# Start the cron process
nohup crond -l 2 -f &

# Start the main process
nohup /usr/bin/python3 /app/pixlovarr.py &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?