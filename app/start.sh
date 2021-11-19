#!/bin/ash

# Name: Pixlovarr
# Coder: Marco Janssen (twitter @marc0janssen)
# date: 2021-11-19 18:53:35
# update: 2021-11-19 18:53:39

# Start the first process
/usr/bin/python3 /app/pixlovarr.py &
  
# Start the second process
crond -l 2 -f &
  
# Wait for any process to exit
wait -n
  
# Exit with status of process that exited first
exit $?